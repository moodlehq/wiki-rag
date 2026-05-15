#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Simple MCP server example providing a few tools, resources and prompts."""

import logging

from fastmcp import FastMCP
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)

import wiki_rag.mcp_server as mcp_global

from wiki_rag import __version__, server
from wiki_rag.index.util import load_parsed_information
from wiki_rag.mcp_server.auth import WikiRagTokenVerifier
from wiki_rag.mcp_server.util import build_optimise_graph, build_retrieve_graph
from wiki_rag.search.util import build_graph, load_prompts_for_rag
from wiki_rag.server.server import invoke_graph
from wiki_rag.server.util import (
    Message,
    convert_from_openai_to_langchain,
    filter_completions_history,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Wiki-RAG MCP Server", version=__version__, auth=WikiRagTokenVerifier())


@mcp.tool()
async def retrieve(messages: list[Message]) -> dict[str, list[dict]]:
    """Get the raw results from the database."""
    assert server.context is not None

    # Extract the last message, our new question, out from history.
    question = messages.pop()["content"]

    # Convert the messages to the format expected by langgraph.
    history = convert_from_openai_to_langchain(messages)

    logger.info("Building the retrieve graph")
    server.graph = build_retrieve_graph(server.context)

    logger.info("Running retrieve (non-streaming)")
    response = await invoke_graph(
        question=question,
        history=history,
        context=server.context
    )
    logger.debug(f"Response: {response}")
    return {
        "vector_search": [
            {
                "distance": doc["distance"],
                "doc_id": doc["entity"]["doc_id"],
                "page_id": doc["entity"]["page_id"],
                "title": doc["entity"]["title"],
                "text": doc["entity"]["text"],
                "source": doc["entity"]["source"],
            } for doc in response["vector_search"]
        ],
    }


@mcp.tool()
async def optimise(messages: list[Message]) -> dict[str, list[str]]:
    """Get the optimised results from the retrieved ones."""
    assert server.context is not None

    # Extract the last message, our new question, out from history.
    question = messages.pop()["content"]

    # Convert the messages to the format expected by langgraph.
    history = convert_from_openai_to_langchain(messages)

    logger.info("Building the optimise graph")
    server.graph = build_optimise_graph(server.context)

    logger.info("Running optimise (non-streaming)")
    response = await invoke_graph(
        question=question, history=history, context=server.context
    )
    logger.debug(f"Response: {response}")
    return {
        "context": response["context"],
        "sources": response["sources"],
    }


@mcp.tool()
async def generate(messages: list[Message]) -> dict[str, str]:
    """Get the LLM generated answer after retrieving and optimising."""
    assert server.context is not None

    # Filter the messages to ensure they don't exceed the maximum number of turns and tokens.
    history = filter_completions_history(
        messages,
        max_turns_allowed=server.context["wrapper_chat_max_turns"],
        max_tokens_allowed=server.context["wrapper_chat_max_tokens"],
        remove_system_messages=True,
    )

    # Extract the last message, our new question, out from history.
    question = history.pop()["content"]

    # Convert the messages to the format expected by langgraph.
    history = convert_from_openai_to_langchain(history)

    logger.info("Building the generate complete graph")
    server.graph = build_graph(server.context)

    logger.info("Running generate (non-streaming)")
    response = await invoke_graph(
        question=question, history=history, context=server.context
    )
    logger.debug(f"Response: {response}")
    return {"result": response["answer"]}


# Add a resource that returns the first 10 parsed pages.
@mcp.resource("resource://get_10_pages")
def get_10_pages() -> list[dict]:
    """Get the first 10 parsed pages."""
    logger.info(f"Resource: Getting 10 pages from {mcp_global.res_file}")
    # First of all, load the json from the resource file and verify that everything is ok.
    if mcp_global.res_file is None:
        error_msg = "Error: resource file not set."
        raise RuntimeError(error_msg)
    information = load_parsed_information(mcp_global.res_file)
    if not information:
        error_msg = f"Error: loading and parsing the resource file {mcp_global.res_file}."
        raise RuntimeError(error_msg)

    return information["sites"][0]["pages"][:10]


# Add a resource that returns the first 100 parsed pages.
@mcp.resource("resource://get_100_pages")
def get_100_pages() -> list[dict]:
    """Get the first 100 parsed pages."""
    logger.info(f"Resource: Getting 100 pages from {mcp_global.res_file}")
    # First of all, load the json from the resource file and verify that everything is ok.
    if mcp_global.res_file is None:
        error_msg = "Error: resource file not set."
        raise RuntimeError(error_msg)
    information = load_parsed_information(mcp_global.res_file)
    if not information:
        error_msg = f"Error: loading and parsing the resource file {mcp_global.res_file}."
        raise RuntimeError(error_msg)

    return information["sites"][0]["pages"][:100]


# Add a resource template that accepts start and number of pages to return.
@mcp.resource("resource://get_pages/{start}/{number}")
def get_pages(start: int, number: int) -> list[dict]:
    """Get "number" parsed pages, starting from "start"."""
    logger.info(f"Resource: Getting {number} pages starting at {start} from {mcp_global.res_file}")
    # First of all, load the json from the resource file and verify that everything is ok.
    if mcp_global.res_file is None:
        error_msg = "Error: resource file not set."
        raise RuntimeError(error_msg)
    information = load_parsed_information(mcp_global.res_file)
    if not information:
        error_msg = f"Error: loading and parsing the resource file {mcp_global.res_file}."
        raise RuntimeError(error_msg)
    # Check that the start and number are valid.
    if (start - 1 + number) > len(information["sites"][0]["pages"]):
        error_msg = f"Error: start ({start}) and number ({number}) are out of range."
        raise ValueError(error_msg)
    if start < 1:
        error_msg = f"Error: start ({start}) must be greater than 0."
        raise ValueError(error_msg)

    return information["sites"][0]["pages"][start - 1:start - 1 + number]


@mcp.prompt()
def get_system_prompt(
        task_def: str = "{task_def}",
        kb_name: str = "{kb_name}",
        kb_url: str = "{kb_url}",
) -> str:
    """Get the system prompt used for LLM generation."""
    prompt: ChatPromptTemplate = load_prompts_for_rag("wiki-rag")  # Get the prompt.
    system_prompt = [
        message.prompt
        for message in prompt.messages
            if isinstance(message, SystemMessagePromptTemplate)
    ][0]
    assert (isinstance(system_prompt, PromptTemplate)), "System prompt not found."
    raw = system_prompt.template
    logger.debug(f"Raw system prompt: {raw}")
    return raw.format(
        task_def=task_def,
        kb_name=kb_name,
        kb_url=kb_url,
    )


@mcp.prompt()
def get_user_prompt(
        question: str = "{question}",
        context: str = "{context}",
        sources: str = "{sources}",
) -> str:
    """Get the user prompt used for LLM generation."""
    prompt: ChatPromptTemplate = load_prompts_for_rag(prompt_name="wiki-rag")  # Get the prompt.
    user_prompt = [
        message.prompt
        for message in prompt.messages
            if isinstance(message, HumanMessagePromptTemplate)
    ][0]
    assert (isinstance(user_prompt, PromptTemplate)), "User prompt not found."
    raw = user_prompt.template
    logger.debug(f"Raw user prompt: {raw}")
    return raw.format(
        question=question,
        context=context,
        sources=sources,
    )
