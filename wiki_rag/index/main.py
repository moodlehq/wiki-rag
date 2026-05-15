#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Main entry point for the document indexer."""

import argparse
import logging
import sys

import wiki_rag.vector as vector

from wiki_rag import __version__
from wiki_rag.config import LOG_LEVEL, load_config
from wiki_rag.index.util import (
    create_temp_collection_schema,
    index_pages,
    index_pages_incremental,
    load_parsed_information,
    replace_previous_collection,
)
from wiki_rag.util import instance_lock, setup_logging
from wiki_rag.vector import load_vector_store


def main():
    """Make an index from the json information present in the specified file."""
    parser = argparse.ArgumentParser(description="Index parsed MediaWiki pages into a vector store.")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Force a full reindex (blue/green swap) even when the dump is incremental.",
    )
    args = parser.parse_args()

    setup_logging(level=LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("wiki_rag-index starting up...")
    logger.warning(f"Version: {__version__}")

    cfg = load_config(command="index")

    with instance_lock(cfg.collection_name, cfg.loader.dump_path):
        vector.store = load_vector_store(cfg.index_vendor)

        input_candidate = ""
        # TODO: Implement CLI argument to accept the input file here.

        # No candidate yet, let's find the last file in the directory (with collection_name
        # as prefix to filter out other files).
        for file in sorted(cfg.loader.dump_path.iterdir()):
            if (
                file.is_file()
                and file.name.startswith(f"{cfg.collection_name}-")
                and file.name.endswith(".json")
            ):
                input_candidate = file
        if not input_candidate:
            logger.error(
                f"No input file found in {cfg.loader.dump_path} "
                f"with collection name {cfg.collection_name}. Exiting."
            )
            sys.exit(1)

        # TODO: Make this to accept CLI argument or, by default, use the last file in the directory.
        input_file = cfg.loader.dump_path / input_candidate

        # Skip indexing if this dump has already been indexed and --full was not requested.
        marker_file = cfg.loader.dump_path / f"{cfg.collection_name}.indexed"
        if not args.full and marker_file.exists() and marker_file.read_text().strip() == input_file.name:
            logger.info(f"Dump {input_file.name} was already indexed. Nothing to do.")
            return

        logger.info(
            f"Loading parsed pages from JSON: {input_file}, "
            f"namespaces: {cfg.mediawiki.namespaces}"
        )
        information = load_parsed_information(input_file)
        # TODO: Multiple site information handling should be implemented here.
        pages = information["sites"][0]["pages"]
        logger.info(f"Loaded {len(pages)} pages from JSON file")

        dump_type = information["sites"][0].get("dump_type", "full")
        use_incremental = not args.full and dump_type == "incremental"

        embedding_api_base = cfg.embedding_api_base or cfg.openai_api_base
        embedding_api_key = cfg.embedding_api_key or cfg.openai_api_key or ""

        if use_incremental:
            logger.info("Incremental indexing mode: updating live collection in-place.")
            if not vector.store.collection_exists(cfg.collection_name):
                logger.error(
                    f'Collection "{cfg.collection_name}" does not exist. '
                    "Cannot perform incremental indexing. Run with --full to create it."
                )
                sys.exit(1)
            summary = index_pages_incremental(
                pages, cfg.collection_name, cfg.embedding_model, cfg.embedding_dimensions,
                embedding_api_base, embedding_api_key,
            )
            logger.info(
                f"Incremental index complete — "
                f"deleted: {summary['deleted']}, updated: {summary['updated']}, "
                f"created: {summary['created']}, skipped: {summary['skipped']}, "
                f"sections indexed: {summary['sections_indexed']}."
            )
            logger.info(f"Flushing collection {cfg.collection_name}")
            vector.store.flush_collection(cfg.collection_name)
            logger.info(f"Compacting collection {cfg.collection_name}")
            vector.store.compact_collection(cfg.collection_name)
        else:
            if args.full and dump_type == "incremental":
                logger.info("--full flag set: forcing full reindex despite incremental dump.")
            temp_collection_name = f"{cfg.collection_name}_temp"
            logger.info(f'Preparing new temp collection "{temp_collection_name}" schema')
            create_temp_collection_schema(temp_collection_name, cfg.embedding_dimensions)
            logger.info(f'Collection "{temp_collection_name}" created.')

            logger.info(f'Indexing pages into temp collection "{temp_collection_name}"')
            [total_pages, total_sections] = index_pages(
                pages, temp_collection_name, cfg.embedding_model, cfg.embedding_dimensions,
                embedding_api_base, embedding_api_key,
            )
            logger.info(f"Indexed {total_pages} pages ({total_sections} sections/chunks).")

            logger.info(
                f'Replacing previous collection "{cfg.collection_name}" '
                f'with new collection "{temp_collection_name}"'
            )
            replace_previous_collection(cfg.collection_name, temp_collection_name)
            logger.info(f"Collection {cfg.collection_name} replaced with {temp_collection_name}.")

        marker_file.write_text(input_file.name)
        logger.info(f"Marked {input_file.name} as indexed ({marker_file.name}).")
        logger.info("wiki_rag-index finished.")


if __name__ == "__main__":
    main()
