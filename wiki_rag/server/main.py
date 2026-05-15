#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Main entry point for the knowledge base OpenAI compatible server."""

import logging

import uvicorn

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

import wiki_rag.vector as vector

from wiki_rag import __version__, server
from wiki_rag.config import LOG_LEVEL, load_config
from wiki_rag.search.util import build_context_schema, build_graph
from wiki_rag.server.server import app
from wiki_rag.util import setup_logging
from wiki_rag.vector import load_vector_store


def main():
    """Run the OpenAI server with all the configuration in place."""
    setup_logging(level=LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("wiki_rag-server starting up...")
    logger.warning(f"Version: {__version__}")

    cfg = load_config(command="server")

    if cfg.wrapper.auth_required:
        if not cfg.auth_tokens and not cfg.auth_url:
            logger.warning(
                "Authentication is enabled but neither AUTH_TOKENS nor AUTH_URL is configured"
                " — no client will be able to connect."
            )
    else:
        logger.warning("Authentication is DISABLED — the server is running open with no auth required.")

    # Parse the bind address from wrapper.api_base.
    parts = cfg.wrapper.api_base.split(":")
    wrapper_server = parts[0]
    wrapper_port = int(parts[1]) if len(parts) > 1 else 8000

    langfuse_callback = None
    if cfg.langfuse.tracing:
        # Register the global singleton with explicit credentials so CallbackHandler
        # picks them up automatically. Creating a new handler per request has a large
        # impact on threads and performance.
        Langfuse(
            public_key=cfg.langfuse_public_key,
            secret_key=cfg.langfuse_secret_key,
            host=cfg.langfuse.host,
        )
        langfuse_callback = CallbackHandler()

    server.context = build_context_schema(cfg, langfuse_callback=langfuse_callback)

    vector.store = load_vector_store(cfg.index_vendor)

    logger.info("Building the graph")
    server.graph = build_graph(server.context)

    # Start the web server
    uvicorn.run(
        app,
        host=wrapper_server,
        port=wrapper_port,
    )

    logger.info("wiki_rag-server finished.")


if __name__ == "__main__":
    main()
