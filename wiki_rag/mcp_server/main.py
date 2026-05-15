#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Main entry point for the knowledge base MCP compatible server."""

import logging

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

import wiki_rag.mcp_server as mcp_global
import wiki_rag.vector as vector

from wiki_rag import __version__, server
from wiki_rag.config import LOG_LEVEL, load_config
from wiki_rag.mcp_server.server import mcp
from wiki_rag.search.util import build_context_schema
from wiki_rag.util import setup_logging
from wiki_rag.vector import load_vector_store


def main():
    """Run the MCP server with all the configuration in place."""
    setup_logging(level=LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("wiki_rag-server-mcp_server starting up...")
    logger.warning(f"Version: {__version__}")

    cfg = load_config(command="mcp")

    if cfg.mcp.auth_required:
        if not cfg.auth_tokens and not cfg.auth_url:
            logger.warning(
                "Authentication is enabled but neither AUTH_TOKENS nor AUTH_URL is configured"
                " — no client will be able to connect."
            )
    else:
        logger.warning("Authentication is DISABLED — the server is running open with no auth required.")

    # Parse the bind address from mcp.api_base.
    parts = cfg.mcp.api_base.split(":")
    mcp_server = parts[0]
    mcp_port = int(parts[1]) if len(parts) > 1 else 8081

    # Calculate the file that we are going to use as source for the resources.
    input_candidate = ""
    for file in sorted(cfg.loader.dump_path.iterdir()):
        if (
            file.is_file()
            and file.name.startswith(cfg.collection_name)
            and file.name.endswith(".json")
        ):
            input_candidate = file
    if input_candidate:
        mcp_global.res_file = cfg.loader.dump_path / input_candidate

    if not mcp_global.res_file:
        logger.warning(
            f"No input file found in {cfg.loader.dump_path} "
            f"with collection name {cfg.collection_name}."
        )

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

    # Start the mcp_server server
    if not cfg.mcp.auth_required:
        mcp.auth = None  # FastMCP reads self.auth at run() time, not at __init__ time.
    mcp.run("http", host=mcp_server, port=mcp_port)

    logger.info("wiki_rag-server-mcp_server finished.")


if __name__ == "__main__":
    main()
