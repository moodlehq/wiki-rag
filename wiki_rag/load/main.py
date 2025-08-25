#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Main entry point for the document loader."""

import logging
import os
import sys

from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from wiki_rag import LOG_LEVEL, ROOT_DIR, __version__
from wiki_rag.load.util import (
    get_mediawiki_pages_list,
    get_mediawiki_parsed_pages,
    save_parsed_pages,
)
from wiki_rag.util import setup_logging


def main():
    """Load and parse all the files, storing the information in a file with date."""
    setup_logging(level=LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("wiki_rag-load starting up...")

    # Print the version of the bot.
    logger.warning(f"Version: {__version__}")

    dotenv_file = ROOT_DIR / ".env"
    if dotenv_file.exists():
        logger.warning("Loading environment variables from %s", dotenv_file)
        logger.warning("Note: .env files are not supposed to be used in production. Use env secrets instead.")
        load_dotenv(dotenv_file)

    mediawiki_url = os.getenv("MEDIAWIKI_URL")
    if not mediawiki_url:
        logger.error("Mediawiki URL not found in environment. Exiting.")
        sys.exit(1)

    mediawiki_namespaces = os.getenv("MEDIAWIKI_NAMESPACES")
    if not mediawiki_namespaces:
        logger.error("Mediawiki namespaces not found in environment. Exiting.")
        sys.exit(1)
    mediawiki_namespaces = mediawiki_namespaces.split(",")
    mediawiki_namespaces = [int(ns.strip()) for ns in mediawiki_namespaces]  # no whitespace and int.
    mediawiki_namespaces = list(set(mediawiki_namespaces))  # unique

    loader_dump_path = os.getenv("LOADER_DUMP_PATH")
    if loader_dump_path:
        loader_dump_path = Path(loader_dump_path)
    else:
        loader_dump_path = ROOT_DIR / "data"
    # If the directory does not exist, create it.
    if not loader_dump_path.exists():
        logger.warning(f"Data directory {loader_dump_path} not found. Creating it.")
        try:
            loader_dump_path.mkdir()
        except Exception:
            logger.error(f"Could not create data directory {loader_dump_path}. Exiting.")
            sys.exit(1)

    # The format for now is a semicolon separated list of "type", colon and comma
    # separated list of values, for example:
    # MEDIAWIKI_EXCLUDED="categories:Plugin, Contributed code;wikitext:Hi world, ho world
    # TODO: Move this also to the config YAML file.
    excluded = os.getenv("MEDIAWIKI_EXCLUDED")
    exclusions = {}
    # Let's process the exclusions and return them in a nice dict.
    if excluded:
        for exclusion in excluded.split(";"):
            exclusion_type, exclusion_values = exclusion.split(":")
            exclusion_values = [value.strip() for value in exclusion_values.split(",")]
            exclusions[exclusion_type] = exclusion_values
    logger.info(f"Applying exclusions: {exclusions}")

    # The list of templates, comma separated, that we want to keep in the wiki text. Others will be removed.
    keep_templates = os.getenv("MEDIAWIKI_KEEP_TEMPLATES")
    if keep_templates:
        keep_templates = [template.strip() for template in keep_templates.split(",")]
    else:
        keep_templates = []
    logger.info(f"Keeping templates: {keep_templates}")

    collection_name = os.getenv("COLLECTION_NAME")
    if not collection_name:
        logger.error("Collection name not found in environment. Exiting.")
        sys.exit(1)
    # File name is the collection name + toady's date and time (hours and minutes) + .json
    dump_filename = loader_dump_path / f"{collection_name}-{datetime.now(UTC).strftime('%Y-%m-%d-%H-%M')}.json"

    user_agent = os.getenv("USER_AGENT")
    if not user_agent:
        logger.info("User agent not found in environment. Using default.")
        user_agent = "Moodle Research Crawler/{version} (https://git.in.moodle.com/research)"
    user_agent = f"{user_agent.format(version=__version__)}"

    enable_rate_limiting_setting: str | None = os.getenv("ENABLE_RATE_LIMITING")
    if not enable_rate_limiting_setting:
        logger.info("ENABLE_RATE_LIMITING setting not found in environment. Using the default value 'true'")
        enable_rate_limiting_setting = "true"
    
    enable_rate_limiting_setting = enable_rate_limiting_setting.lower() # lowercase it to accept different cases of true and false

    if enable_rate_limiting_setting == "true":
        enable_rate_limiting = True
        logger.info("Rate limiting is enabled.")
    elif enable_rate_limiting_setting == "false":
        enable_rate_limiting = False
        logger.info("Rate limiting is disabled.")
    else:
        logger.error("ENABLE_RATE_LIMITING environment variable can only get values 'true' or 'false'. Exiting.")
        sys.exit(1)

    logger.info(f"Pre-loading page list for mediawiki: {mediawiki_url}, namespaces: {mediawiki_namespaces}")
    pages = get_mediawiki_pages_list(mediawiki_url, mediawiki_namespaces, user_agent)
    logger.info(f"Loaded {len(pages)} pages.")

    logger.info("Fetching, parsing and splitting pages")
    parsed_pages = get_mediawiki_parsed_pages(mediawiki_url, pages, user_agent, exclusions, keep_templates, enable_rate_limiting)
    logger.info(f"Parsed {len(parsed_pages)} pages.")

    logger.info(f"Saving parsed pages to {dump_filename}")
    save_parsed_pages(parsed_pages, dump_filename)

    logger.info("wiki_rag-load finished.")


if __name__ == "__main__":
    main()
