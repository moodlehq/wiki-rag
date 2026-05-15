#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Util functions to use langgraph to conduct simple searches against the indexed database."""

import asyncio
import logging
import pprint

from typing import Annotated, Literal, TypedDict

from cachetools import TTLCache, cached
from langchain_core.messages import BaseMessage
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langfuse.model import TextPromptClient
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.runtime import Runtime
from langsmith.client import Client
from pydantic import SecretStr

import wiki_rag.config as _config_module
import wiki_rag.vector as vector

from wiki_rag.config import LOG_LEVEL, Config

logger = logging.getLogger(__name__)


class ContextSchema(TypedDict):
    """Define the context (immutable properties) that the graph will use.

    Used to validate the configuration passed to the RunnableConfig of the graph.
    """

    prompt_name: str
    product: str
    task_def: str
    kb_name: str
    kb_url: str
    collection_name: str
    embedding_model: str
    embedding_dimension: int
    llm_model: str
    contextualisation_model: str
    hyde_model: str
    hyde_enabled: bool
    hyde_passages: int
    search_distance_cutoff: float
    max_completion_tokens: int
    temperature: float
    top_p: float
    stream: bool
    wrapper_chat_max_turns: int
    wrapper_chat_max_tokens: int
    wrapper_model_name: str
    langsmith_prompts: bool
    langsmith_prompt_prefix: str
    langfuse_prompts: bool
    langfuse_prompt_prefix: str
    langfuse_callback: CallbackHandler | None
    embedding_api_base: str
    llm_api_base: str
    contextualisation_api_base: str
    hyde_api_base: str
    embedding_api_key: str
    llm_api_key: str
    contextualisation_api_key: str
    hyde_api_key: str


def build_context_schema(
    cfg: Config,
    stream: bool = False,
    langfuse_callback: CallbackHandler | None = None,
) -> ContextSchema:
    """Build a :class:`ContextSchema` from a resolved :class:`~wiki_rag.config.Config`.

    Args:
        cfg: The loaded Config instance.
        stream: Whether the response should be streamed.
        langfuse_callback: Optional Langfuse tracing callback.

    Returns:
        Populated ContextSchema ready for use as a LangGraph context.

    """
    wrapper_model_name = cfg.wrapper.model_name or cfg.collection_name

    # Resolve model fallback chain: contextualisation → openai; hyde → contextualisation → openai.
    resolved_ctx_model = cfg.contextualisation_model or cfg.openai_model or ""
    resolved_hyde_model = cfg.hyde_model or resolved_ctx_model

    # Resolve per-model API base URLs with fallback chain (no llm-specific layer).
    resolved_ctx_base = cfg.contextualisation_api_base or cfg.openai_api_base
    resolved_hyde_base = cfg.hyde_api_base or resolved_ctx_base
    resolved_embedding_base = cfg.embedding_api_base or cfg.openai_api_base

    # Resolve per-model API keys with fallback chain (same structure as base URLs).
    resolved_ctx_key = cfg.contextualisation_api_key or cfg.openai_api_key or ""
    resolved_hyde_key = cfg.hyde_api_key or resolved_ctx_key
    resolved_embedding_key = cfg.embedding_api_key or cfg.openai_api_key or ""

    return ContextSchema(
        prompt_name=cfg.search.prompt_name,
        product=cfg.search.product,
        task_def=cfg.search.task_def,
        kb_name=cfg.search.kb_name,
        kb_url=cfg.mediawiki.url,
        collection_name=cfg.collection_name,
        embedding_model=cfg.embedding_model,
        embedding_dimension=cfg.embedding_dimensions,
        llm_model=cfg.openai_model or "",
        contextualisation_model=resolved_ctx_model,
        hyde_model=resolved_hyde_model,
        hyde_enabled=cfg.search.hyde_enabled,
        hyde_passages=cfg.search.hyde_passages,
        search_distance_cutoff=cfg.search.distance_cutoff,
        max_completion_tokens=cfg.search.max_completion_tokens,
        temperature=cfg.search.temperature,
        top_p=cfg.search.top_p,
        stream=stream,
        wrapper_chat_max_turns=cfg.wrapper.chat_max_turns,
        wrapper_chat_max_tokens=cfg.wrapper.chat_max_tokens,
        wrapper_model_name=wrapper_model_name,
        langsmith_prompts=cfg.langsmith.prompts,
        langsmith_prompt_prefix=cfg.langsmith.prompt_prefix,
        langfuse_prompts=cfg.langfuse.prompts,
        langfuse_prompt_prefix=cfg.langfuse.prompt_prefix,
        langfuse_callback=langfuse_callback,
        embedding_api_base=resolved_embedding_base,
        llm_api_base=cfg.openai_api_base,
        contextualisation_api_base=resolved_ctx_base,
        hyde_api_base=resolved_hyde_base,
        embedding_api_key=resolved_embedding_key,
        llm_api_key=cfg.openai_api_key or "",
        contextualisation_api_key=resolved_ctx_key,
        hyde_api_key=resolved_hyde_key,
    )


class RagState(TypedDict):
    """Overall state to follow the RAG graph execution."""

    history: list[BaseMessage]
    question: str
    hyde_texts: list[str]
    vector_search: list[dict]
    context: list[str]
    sources: list[str]
    answer: str | None


class ContextualisedAnswer(TypedDict):
    """Contextualised question to be used in the RAG graph execution."""

    type: Annotated[str, "question", "The type of the answer (question or chitchat"]
    content: Annotated[str, ..., "The answer, that can be a question or some chitchat text"]


def build_graph(context: ContextSchema) -> CompiledStateGraph:
    """Build the graph for the langgraph search."""
    graph_builder = StateGraph(RagState, ContextSchema)
    graph_builder.add_node(query_rewrite)
    graph_builder.add_node(hyde_rewrite)
    graph_builder.add_sequence([
        retrieve,
        optimise,
        generate
    ])
    graph_builder.add_conditional_edges("query_rewrite", route_after_rewrite, {
        "retrieve": "retrieve",
        "hyde_rewrite": "hyde_rewrite",
        "chitchat": END,
    })
    graph_builder.add_edge("hyde_rewrite", "retrieve")

    graph_builder.add_edge(START, "query_rewrite")
    graph: CompiledStateGraph = graph_builder.compile().with_config(
        {"callbacks": [context["langfuse_callback"]]} if context["langfuse_callback"] else None
    )   # pyright: ignore[reportAssignmentType]. Note this is correct, but for some reason, pyright is not able.

    return graph


def route_after_rewrite(state: RagState, runtime: Runtime[ContextSchema]) -> Literal["retrieve", "hyde", "chitchat"]:
    """Route after query rewrite: to chitchat, HyDE, or direct retrieval.

    This is used to decide the next step after the query rewrite node.
    """
    # If the answer has already been set, we are done (probably a chitchat).
    if "answer" in state:
        return "chitchat"

    # Route through HyDE when enabled and a model is available (hyde_model falls
    # back to contextualisation_model, so either one being set is sufficient).
    if runtime.context["hyde_enabled"] and runtime.context["hyde_model"]:
        return "hyde_rewrite"

    return "retrieve"  # Continue directly to retrieval.


@cached(cache=TTLCache(maxsize=64, ttl=0 if LOG_LEVEL == "DEBUG" else 300))
def load_prompts_for_rag(prompt_name: str) -> ChatPromptTemplate:
    """Load the prompts for the RAG model.

    This function results are cached for 5 minutes to avoid unnecessary
    calls to the LangSmith/Langsmith APIs.
    """
    prefixed_prompt_name = prompt_name  # We'll add the prefix later, depending on the provider.
    prompt_provider = "local"

    assert _config_module.cfg is not None, "load_config() must be called before load_prompts_for_rag()"
    _cfg = _config_module.cfg

    # TODO: Be able to fallback to env/config based prompts too. Or also from other prompt providers.
    try:
        if _cfg.langsmith.prompts:
            prefixed_prompt_name = f"{_cfg.langsmith.prompt_prefix}{prompt_name}"
            logger.info(f"Loading the prompt {prefixed_prompt_name} from LangSmith.")
            prompt_provider = "LangSmith"
            chat_prompt = Client(
                api_url=_cfg.langsmith.endpoint,
                api_key=_cfg.langsmith_api_key,
            ).pull_prompt(prefixed_prompt_name)
        elif _cfg.langfuse.prompts:
            langfuse = Langfuse(
                secret_key=_cfg.langfuse_secret_key,
                public_key=_cfg.langfuse_public_key,
                host=_cfg.langfuse.host,
            )
            prefixed_prompt_name = f"{_cfg.langfuse.prompt_prefix}{prompt_name}"
            logger.info(f"Loading the prompt {prefixed_prompt_name} from Langfuse.")
            prompt_provider = "Langfuse"
            langfuse_prompt = langfuse.get_prompt(prefixed_prompt_name)
            # Convert the prompt to a LangChain compatible one.
            chat_prompt = convert_prompts_for_rag_from_langfuse(langfuse_prompt)
            langfuse.shutdown()
        else:
            chat_prompt = load_prompts_for_rag_from_local(prompt_name)
    except Exception as e:
        logger.warning(
            f"Error loading the prompt {prefixed_prompt_name} from {prompt_provider}: {e}. Applying default one."
        )
        chat_prompt = load_prompts_for_rag_from_local(prompt_name)

    logger.debug(f"Returning the prompt {prompt_name}: {chat_prompt}")
    return chat_prompt


def convert_prompts_for_rag_from_langfuse(langfuse_prompt: TextPromptClient) -> ChatPromptTemplate:
    """Convert the prompt from the Langfuse API.

    We need to make this prompt truly langchain compatible, so we need to
      - Create the system prompt template (from the first element coming from langfuse).
      - Insert the MessagesPlaceholder for the history.
      - Create the user message template (from the second element coming from langfuse).

      We do all the above by iterating over the langfuse prompt and creating the needed
      messages. Special attention to the {history} placeholder that is only supported by
      LangSmith/LangChain, so we simulate it in Langfuse with a normal user message with
      {{history}} as the content.
    """
    logger.debug(f"Converting Langfuse prompt {langfuse_prompt.name} to langchain format")

    langchain_list = langfuse_prompt.get_langchain_prompt()

    messages = []
    for langchain in langchain_list:
        if langchain[0] == "system":
            messages.append(SystemMessagePromptTemplate.from_template(langchain[1]))
        elif langchain[0] == "user":
            if langchain[1] == "{history}":  # Special placeholder to be replaced by the history.
                messages.append(MessagesPlaceholder("history", optional=True))
            else:
                messages.append(HumanMessagePromptTemplate.from_template(langchain[1]))
        else:
            logger.warning(f"Unknown prompt type ({langchain[0]}) detected in langfuse prompt: {langfuse_prompt.name}")

    chat_prompt = ChatPromptTemplate.from_messages(messages)
    return chat_prompt


def load_prompts_for_rag_from_local(prompt_name: str) -> ChatPromptTemplate:
    """Load the prompts from the local configuration."""
    # TODO: Be able to fallback to env/config based prompts too. Or also from other prompt providers.
    logger.info(f"Loading the prompt {prompt_name} from local.")

    # TODO: We should move the local handling of prompts to another place, this is not
    #   the best solution (say some local prompt management or whatever).

    # This is the default prompt that we use in the wiki-rag project.
    system_prompt = SystemMessagePromptTemplate.from_template(
        "You are an assistant for question-answering tasks related to {task_def}, "
        "using the information present in {kb_name}, publicly available at {kb_url}."
        ""
        "Try to answer with a few phrases in a concise and clear way."
        "If the user asks for more details or explanations the answer can be longer."
        ""
        "You are provided with a <CONTEXT> XML element, that will be used to generate the answer."
        'Only the information present in the "Context" element and the provided chat history'
        "will be used to generate the answer. This is the unique knowledge that can be used."
        ""
        "You are provided with a <SOURCES> XML element, with a list of URLs, that will be used "
        "to generate up to three references at the end of the answer."
        'Only the information present in the "Sources" element will be used to generate the references.'
        ""
        "If the Context information doesn't lead to a good answer, don't invent anything, "
        "just say that you don't know."
        'Avoid the term "context" in the answer.'
        "Avoid repeating the question in the answer."
        ""
        "The information is in mediawiki format, convert it to markdown in the answer."
        'Convert the links from mediawiki format "[url|text]" to markdown format [text](url)".'
    )
    user_message = HumanMessagePromptTemplate.from_template(
        "Question: {question}"
        ""
        "<CONTEXT>{context}</CONTEXT>"
        ""
        "<SOURCES>{sources}</SOURCES>"
        ""
        "Answer: "
    )

    # If we are using the wiki-rag-context-query prompt, let's update the needed pieces.
    if prompt_name == "wiki-rag-context-query":
        system_prompt = SystemMessagePromptTemplate.from_template(
            "Given the chat history and the original question which might reference "
            "context in the chat history, rephrase and expand the original question "
            "so it  can be understood without the chat history. Do NOT answer to the "
            "original question or ask for clarifications or details about it."
            ""
            "When not sure, always assume that the request is related to some {product} concept, "
            "for example: 'What is a capability' should be transformed to include the "
            "'{product}' text and look like 'What is a {product} capability'."
            ""
            "Always return a valid JSON structure with two elements:"
            '1. A "type" element with value "rewrite".'
            '2. A "content" element containing the rephrased question.'
            ""
            "If the original user question is not a question or a request for help, but a expression or some "
            "unrelated text, then answer to it in an educated and positive way. In this case, "
            'the "type" element on the required JSON structure will be "chitchat" instead of "rewrite".'
            ""
            "Do NOT make any reference in the answer to these guidelines."
        )
        user_message = HumanMessagePromptTemplate.from_template(
            "Question: {question}"
            ""
            "Answer: "
        )

    # If we are using the wiki-rag-hyde prompt, let's update the needed pieces.
    elif prompt_name == "wiki-rag-hyde":
        system_prompt = SystemMessagePromptTemplate.from_template(
            "You are an expert technical writer for {task_def}. "
            ""
            "Given a question, write a short passage (2 to 4 sentences) that would appear "
            "in {kb_name} as the answer to the question. "
            ""
            "Write the passage as if it were an excerpt from the official documentation. "
            ""
            "Do not include any preamble, metadata, or references. "
            ""
            "The passage should be factual in tone and directly address the question, "
            "even if you need to hypothesise the answer. "
            ""
            "Focus on {product} concepts and terminology."
        )
        user_message = HumanMessagePromptTemplate.from_template(
            "Question: {question}"
            ""
            "Hypothetical documentation passage: "
        )

    # Let's build the complete prompt with the system, the history and the user message.
    messages = (
        system_prompt,
        MessagesPlaceholder("history", optional=True),
        user_message,
    )
    chat_prompt = ChatPromptTemplate.from_messages(messages)
    return chat_prompt


async def query_rewrite(state: RagState, runtime: Runtime[ContextSchema]) -> dict:
    """Rewrite the question using the contextualisation model.

    This is a simple query rewrite model that will be used to rewrite the question
    before sending it to the search engine. It will be used to improve the search results.

    The model will return a JSON object with the following fields:
    - type: The type of the answer (rewrite or chitchat)
    - content: The answer, that can be a question or some chitchat text

    In the case of a chitchat, the answer will be used as the final answer, otherwise
    the question will be rewritten (made context-aware) and used for the search.
    """
    if runtime.context["contextualisation_model"]:
        contextualise_prompt = load_prompts_for_rag(
            f"{runtime.context['prompt_name']}-context-query"
        )

        contextualised_answer = await contextualise_question(
            prompt=contextualise_prompt,
            question=state["question"],
            history=state["history"],
            product=runtime.context["product"],
            model=runtime.context["contextualisation_model"],
            api_base=runtime.context["contextualisation_api_base"],
            api_key=runtime.context["contextualisation_api_key"],
        )

        if contextualised_answer["type"] == "chitchat":
            # If the answer is a chitchat, we are going to use it as the final answer,
            # Let's generate a custom event to notify it to the graph caller about the chitchat answer.
            writer = get_stream_writer()
            writer(contextualised_answer)
            return {"answer": contextualised_answer["content"]}

        if contextualised_answer["type"] == "rewrite":
            # If the answer is a question, we are going to use it as the new question.
            return {"question": contextualised_answer["content"]}

    # No changes to the state, if arrived here.
    return {}


async def hyde_rewrite(state: RagState, runtime: Runtime[ContextSchema]) -> dict:
    """Generate hypothetical document embeddings (HyDE) for the question.

    Instead of using the question directly for dense vector search, generate one or more
    hypothetical passages that would appear in the knowledge base if the answer existed.
    The passages are embedded and their embeddings are averaged. This averaged embedding
    is then used for the dense search in the retrieve step, while the original (rewritten)
    question is still used for the BM25 sparse search.

    The number of passages is controlled by `runtime.context["hyde_passages"]` (default 1).
    When multiple passages are generated, they are produced in parallel.
    """
    hyde_prompt = load_prompts_for_rag(f"{runtime.context['prompt_name']}-hyde")

    n = max(1, runtime.context["hyde_passages"])
    model = runtime.context["hyde_model"]
    assert model  # Guaranteed by route_after_rewrite; satisfies type checker.

    async def generate_passage() -> str:
        """Generate a single hypothetical passage."""
        chat = await hyde_prompt.ainvoke({
            "question": state["question"],
            "product": runtime.context["product"],
            "task_def": runtime.context["task_def"],
            "kb_name": runtime.context["kb_name"],
            "history": [],
        })
        hyde_key = runtime.context["hyde_api_key"]
        llm = ChatOpenAI(
            model=model,
            base_url=runtime.context["hyde_api_base"],
            api_key=SecretStr(hyde_key) if hyde_key else None,
            max_completion_tokens=256,  # TODO: Make these 3 configurable.
            top_p=0.85,
            temperature=1.0,  # High, more varietè.
            disable_streaming=True,
        )
        response = await llm.ainvoke(chat)
        return str(response.content)

    passages = await asyncio.gather(*[generate_passage() for _ in range(n)])
    logger.debug(f"HyDE generated {n} passage(s): {passages}")

    return {"hyde_texts": list(passages)}


async def contextualise_question(
        prompt: ChatPromptTemplate,
        question: str,
        history: list[BaseMessage],
        product: str,
        model: str,
        api_base: str,
        api_key: str,
) -> dict:
    """Contextualise the question with the history and the model.

    This makes the RAG questions way better, context/history aware. The question
    only will be contextualised if there is some history and the model decides
    to provide a better alternative.

    Note that the history at this point has been already filtered, does not contain
    any system prompts and is already in the format expected.
    """
    logger.debug(f"Contextualising the question: {question}")
    chat = await prompt.ainvoke({
        "question": question,
        "history": history,
        "product": product,
    })

    llm = ChatOpenAI(
        model=model,
        base_url=api_base,
        api_key=SecretStr(api_key) if api_key else None,
        max_completion_tokens=256,  # TODO: Make these 3 configurable.
        top_p=0.85,
        temperature=0.1,
        disable_streaming=True,
    )
    json_llm = llm.with_structured_output(ContextualisedAnswer)

    answer = await json_llm.ainvoke(chat)

    logger.debug(f"Contextualised result: {answer}")

    return answer


async def retrieve(state: RagState, runtime: Runtime[ContextSchema]) -> dict:
    """Retrieve the best matches from the indexed database."""
    hyde_texts = state.get("hyde_texts")
    if hyde_texts:
        # HyDE path: dense search uses only the hypothetical passages so it operates in
        # document space (document-to-document similarity — the core HyDE insight).
        # The original question is kept for BM25 sparse search where it belongs.
        queries = hyde_texts
        sparse_query = state["question"]
    else:
        queries = [state["question"]]
        sparse_query = None  # defaults to queries[0] inside retrieve()

    results = vector.store.retrieve(
        collection_name=runtime.context["collection_name"],
        embedding_model=runtime.context["embedding_model"],
        embedding_dimensions=runtime.context["embedding_dimension"],
        queries=queries,
        sparse_query=sparse_query,
        embedding_api_base=runtime.context["embedding_api_base"],
        embedding_api_key=runtime.context["embedding_api_key"],
    )

    # TODO: Return only the docs which distance is below the cutoff.
    # distance_cutoff = runtime.context["search_distance_cutoff"]
    # return {"vector_search": [doc for doc in retrieved_docs[0] if doc["distance"] >= distance_cutoff]}
    return {"vector_search": results}


async def optimise(state: RagState, runtime: Runtime[ContextSchema]) -> dict:
    """Optimise the retrieved documents to build the context for the answer.

    First, we'll weight the elements retrieved by "popularity" (how many times they are mentioned
    by other elements in the retrieved docs). Then, we'll build the context by using some strategy,
    like Parent, Own and Children (poc) elements.
    """
    # TODO: Play with alternative strategies, we also have prev/nex, related, ...
    if not state["vector_search"]:  # No results, no context.
        return {"context": [], "sources": []}

    top = 15  # TODO: Make this part of the state, configurable.

    # Let's count how many times each element is mentioned as id, parent, children, previous or next,
    # making a dictionary with the counts. They will be weighted differently, depending on where they
    # appear, multiplied by their original distance and with a decay by position applied.
    weight_as_id = 1.5  # The document appears as id
    weight_as_parent = 1.1  # The document appears as parent
    weight_as_children = 1.01  # The document appears as children
    weight_as_previous = 1.005  # The document appears as previous
    weight_as_next = 1.005   # The document appears as next
    # TODO: Also weight relations once we have them.

    element_counts = {}
    for position in range(len(state["vector_search"])):
        doc = state["vector_search"][position]
        distance = doc["distance"]
        decay = 0.93 ** position  # Decay (exponentially) by position.
        for element in ["id", "parent", "children", "previous", "next"]:
            if element in doc["entity"]:
                el = doc["entity"][element]
                # Empty elements are not counted.
                if not el:
                    continue
                # If it's a single string element, we'll count it.
                if el and isinstance(el, str):
                    if el not in element_counts:
                        element_counts[el] = 0
                    # Only "id" and "parent" can be here (str).
                    element_counts[el] += distance * decay * (weight_as_id if element == "id"
                        else weight_as_parent if element == "parent"
                        else 1)
                # Else for sure it's a list/array like (iterable) element, so we'll count each element in the list.
                else:
                    for el in doc["entity"][element]:
                        if isinstance(el, str):
                            if el not in element_counts:
                                element_counts[el] = 0
                            # Only "children", "previous" and "next" can be here (list)
                            element_counts[el] += distance * decay * (weight_as_children if element == "children"
                                else weight_as_previous if element == "previous"
                                else weight_as_next if element == "next"
                                else 1)

    # Sort them by the weighted popularity results, we'll build the context following this order.
    sorted_items = sorted(element_counts.items(), key=lambda item: item[1], reverse=True)
    logger.debug(f"Sorted items: {pprint.PrettyPrinter(2).pformat(sorted_items)}")

    # TODO: Add support for other variations, including prev/next, related, etc.
    # Build the POC (parent, own, children) context
    new_context, new_sources = build_poc_context(
        retrieved_docs=state["vector_search"],
        sorted_items=sorted_items,
        collection_name=runtime.context["collection_name"],
        top=top
    )

    return {"context": new_context, "sources": new_sources}


def build_poc_context(retrieved_docs, sorted_items, collection_name: str, top=5) -> list[list[str]]:
    """Given the originally retrieved docs and the sorted, weighted items, build the rag final context.

    POC: Build the new context by using Parent, Own and Children elements.
    """
    context_list = []
    sources_list = []
    not_retrieved = []
    current = 0
    while current < min(len(sorted_items), top):
        # Let's examine the element in the sorted_items list.
        element_id = sorted_items[current][0]
        # Find the element in the retrieved_docs list.
        if element := [doc for doc in retrieved_docs if doc["entity"]["id"] == element_id]:
            element = element[0]
            # If the element has a parent, let's find it and add it to the context list (if not added already).
            if element["entity"]["parent"] and element["entity"]["parent"] not in context_list:
                context_list.append(element["entity"]["parent"])
            # Now, add the element itself to the context list (if not added already).
            if element["entity"]["id"] not in context_list:
                context_list.append(element["entity"]["id"])
                # Build the mediawiki link for the source.
                link = ""
                if element["entity"]["parent"]:
                    link = f"{element['entity']['doc_title']}: "
                link = f"[{element['entity']['source']}|{link}{element['entity']['title']}]"
                sources_list.append(link)
            # If the element has children, let's find them and add them to the context list (if not added already).
            if element["entity"]["children"]:
                for child in element["entity"]["children"]:
                    if child not in context_list:
                        context_list.append(child)

        else:
            # The element is not in the list of retrieved docs.
            # Just it won't be so useful in isolation, we will add it at the end, without further processing.
            not_retrieved.append(element_id)
            # This is not going to be very useful, let's allow one more iteration to happen.
            top += 1

        current += 1

    # Add all the not retrieved elements to the context list (at the end), if they are not already there.
    for not_retrieved_id in not_retrieved:
        if not_retrieved_id not in context_list:
            context_list.append(not_retrieved_id)

    return [
        retrieve_all_elements(retrieved_docs, context_list, collection_name),
        sources_list
    ]


def retrieve_all_elements(retrieved_docs, context_list, collection_name: str) -> list[str]:
    """Given the already built content_List, let's retrieve all the texts for the elements in the list."""
    context_texts = {}
    context_missing = []
    for id in context_list:
        # First, verify if we already have the text in the retrieved_docs list.
        retrieved = [doc for doc in retrieved_docs if doc["entity"]["id"] == id]
        if retrieved:
            context_texts[id] = f"{retrieved[0]["entity"]["title"]}\n\n{retrieved[0]["entity"]["text"]}"
        else:
            context_texts[id] = None
            # If not, let's accumulate it for later id based retrieval.
            context_missing.append(id)

    missing_docs = get_missing_from_vector_store(context_missing, collection_name)

    # Finally, fill the gaps in the context_texts dictionary with the missing docs.
    for id, text in missing_docs.items():
        context_texts[id] = text

    # Now, iterate over the dictionary and return the list of texts.
    return [context_texts[id] for id in context_list]


def get_missing_from_vector_store(context_missing: list, collection_name: str) -> dict:
    """Given the missing elements, let's retrieve them from the vector store."""
    if not context_missing:  # No missing elements, nothing extra to retrieve.
        return {}

    return vector.store.get_documents_contents_by_id(collection_name, context_missing)


async def generate(state: RagState, runtime: Runtime[ContextSchema]) -> dict:
    """Generate the final answer for the question.

    This is the final generation step where the prompt, the chat history and the context
    are used to generate the final answer.
    """
    # Let's make the generation LLM call normally.
    llm_key = runtime.context["llm_api_key"]
    llm = ChatOpenAI(
        model=runtime.context["llm_model"],
        base_url=runtime.context["llm_api_base"],
        api_key=SecretStr(llm_key) if llm_key else None,
        max_completion_tokens=runtime.context["max_completion_tokens"],
        top_p=runtime.context["top_p"],
        temperature=runtime.context["temperature"],
    )

    docs_content = "\n\n".join(f"{doc}" for doc in state["context"])
    sources_content = "\n".join(f"* {source}" for source in state["sources"])

    chat_prompt = load_prompts_for_rag(runtime.context["prompt_name"])
    chat = await chat_prompt.ainvoke({
        "task_def": runtime.context["task_def"],
        "kb_name": runtime.context["kb_name"],
        "kb_url": runtime.context["kb_url"],
        "context": docs_content,
        "sources": sources_content,
        "question": state["question"],
        "history": state["history"]
    })

    response = await llm.ainvoke(chat)

    return {"answer": response.content}
