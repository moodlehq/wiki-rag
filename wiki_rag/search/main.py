#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Main entry point for the KB retriever and search system."""

import argparse
import asyncio
import logging
import signal
import sys
import traceback

from langchain_core.messages import AIMessageChunk
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

import wiki_rag.vector as vector

from wiki_rag import __version__
from wiki_rag.config import LOG_LEVEL, load_config
from wiki_rag.search.util import build_context_schema, build_graph
from wiki_rag.util import setup_logging
from wiki_rag.vector import load_vector_store


async def run():
    """Perform a search with all the configuration in place."""
    setup_logging(level=LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("wiki_rag-search starting up...")
    logger.warning(f"Version: {__version__}")

    cfg = load_config(command="search")

    # Let's accept arg[1] as the question to be asked.
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="+", help="The question to be asked.")
    parser.add_argument("--stream", "-s", action="store_true", help="Stream the output.")

    args = parser.parse_args()

    question = " ".join(args.question)
    stream = args.stream if args.stream else False

    logger.debug(f'Question: "{question}"')

    vector.store = load_vector_store(cfg.index_vendor)

    langfuse_callback = None
    if cfg.langfuse.tracing:
        Langfuse(
            public_key=cfg.langfuse_public_key,
            secret_key=cfg.langfuse_secret_key,
            host=cfg.langfuse.host,
        )
        langfuse_callback = CallbackHandler()

    context = build_context_schema(cfg, stream=stream, langfuse_callback=langfuse_callback)

    logger.info("Building the graph")
    graph = build_graph(context)

    # And, finally, run a search.
    if not stream:
        logger.info("Running the search (non-streaming)")
        response = await graph.ainvoke(
            input={"question": question, "history": []},
            context=context  # pyright: ignore[reportArgumentType]. This is correct, but defined as None somewhere.
        )
        print(f"\033[93m{response["answer"]}\033[0m", end="")
    else:
        logger.info("Running the search (streaming)")
        # TODO: Encapsulate this, it's duplicated in the server.
        async for mode, info in graph.astream(
            input={"question": question, "history": []},
            context=context,  # pyright: ignore[reportArgumentType]. This is correct, but defined as None somewhere.
            stream_mode=["custom", "messages"],
        ):
            # See if the streamed event needs to be considered.
            process_event = False
            content = ""
            # Accept custom events coming from the query_rewrite node.
            if (
                mode == "custom"
                and isinstance(info, dict)
                and info.get("type", "") == "chitchat"
            ):
                process_event = True
                content = info.get(
                    "content", "There was a problem talking with you, I'm sorry."
                )

            # Accept AI message chunks events coming from the generate node.
            if mode == "messages":
                # Message events (when using multiple stream mode, like here) are
                # tuples with the message and metadata. When not using multiple stream mode,
                # but only one, they come as 2 returned values (message, metadata), without mode.
                message = info[0]
                metadata = info[1]
                if (
                    isinstance(message, AIMessageChunk)
                    and isinstance(metadata, dict)
                    and metadata.get("langgraph_node", "") == "generate"
                    and message.content
                ):
                    process_event = True
                    content = message.content

            if process_event:
                print(f"\033[93m{content}\033[0m", end="", flush=True)

    print("", end="\n\n")

    logger.info("wiki_rag-search finished.")


async def release(signum: int) -> None:
    """Signal handler for SIGINT and SIGTERM. It will release resources and exit gracefully."""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}, releasing resources.")

    # Add all the cleanup code here.

    # Cancel all tasks, so we can exit.
    for task in asyncio.all_tasks():
        logger.debug(f"Cancelling task {task}")
        task.cancel()

    logger.info("Resources released. Exiting.")


def add_signal_handlers(run_loop) -> None:
    """Register async signal handlers (SIGINT/ctrl+c, SIGTERM/kill).

    Do it in own async loop, so we can release stuff gracefully.
    """
    run_loop.add_signal_handler(
        signal.SIGINT,
        lambda: asyncio.create_task(release(signal.SIGINT))
    )
    run_loop.add_signal_handler(
        signal.SIGTERM,
        lambda: asyncio.create_task(release(signal.SIGTERM))
    )


def main():
    """Prepare the async loop for operation and graceful shutdown, then run()."""
    # Create the event loop, set it as current and add the signal handlers.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    add_signal_handlers(loop)
    exitcode = 0
    try:
        loop.run_until_complete(run())  # Run the main loop.
    except Exception:
        traceback.print_exc()
        exitcode = 1
    finally:
        loop.close()
        sys.exit(exitcode)


if __name__ == "__main__":
    main()
