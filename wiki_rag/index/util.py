#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Util functions to proceed to index to some collection is a vector store / index."""

import json
import logging

from datetime import UTC, datetime, timedelta
from pathlib import Path

from jsonschema import ValidationError, validate
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from tqdm import tqdm

import wiki_rag.vector as vector

from wiki_rag import ROOT_DIR

logger = logging.getLogger(__name__)


def load_parsed_information(input_file: Path) -> dict:
    """Load the parsed information from the file."""
    information = []
    try:
        with open(input_file) as f:
            information = json.load(f)
    except Exception as e:
        logger.error(f"Error loading the parsed information from {input_file}: {e}")

    # If the old format (array of pages) is detected, let's convert it to the new format,
    # (basic information in "meta" and pages in "sites").
    if isinstance(information, list):
        logger.warning(f"Old format detected in {input_file}, converting to new format.")
        file_mod_time = datetime.fromtimestamp(input_file.stat().st_mtime, UTC)
        two_days_ago = file_mod_time - timedelta(days=2)  # ftime -48h so we don't miss anything on incremental index.
        information = {
            "meta": {
                "timestamp": two_days_ago.isoformat(),
                "num_sites": 1,
            },
            "sites": [
                {
                    "site_url": "unknown",
                    "dump_type": "full",
                    "base_dump": None,
                    "num_pages": len(information),
                    "pages": information,
                }
            ]
        }

    # Let's validate the schema as much as we can.
    schema = json.load(open(ROOT_DIR / "wiki_rag/schema.json"))
    try:
        validate(information, schema)
        logger.debug("Successfully parsed the JSON information")
    except ValidationError as e:
        msg = f"Error validating the JSON information from {input_file}: {e}"
        logger.error(msg)
        exit(1)

    return information


def create_temp_collection_schema(collection_name: str, embedding_dimension: int) -> None:
    """Create a temporary schema for the collection."""
    vector.store.create_collection(collection_name, embedding_dimension)


def index_pages(
        pages: list[dict],
        collection_name: str,
        embedding_model: str,
        embedding_dimension: int,
        embedding_api_base: str = "",
        embedding_api_key: str = "",
) -> list[int]:
    """Index the pages to the collection."""
    logging.getLogger("httpx").setLevel(logging.WARNING)  # Don't log (INFO) all http requests.

    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        dimensions=embedding_dimension,
        check_embedding_ctx_length=False,
        base_url=embedding_api_base or None,
        api_key=SecretStr(embedding_api_key) if embedding_api_key else None,
    )

    num_pages = 0
    num_sections = 0

    for page in tqdm(pages, desc="Processing pages", unit="pages"):
        if page.get("change_type") == "deleted":
            continue
        for section in page["sections"]:
            # Calculate the preamble text (doc + section title).
            text_preamble = section["doc_title"]
            if section["title"] != section["doc_title"]:
                text_preamble = text_preamble + f" / {section['title']}"
            text_preamble = text_preamble.strip()

            # Calculate the complete text (preamble + text, if existing).
            text_content = section["text"] if section["text"] else ""
            if len(text_content) > 5000:
                # TODO: We need to split the text in smaller chunks here, say 2500 max or so. For now, just trim.
                text_content = text_content[:5000].strip()
                logger.warning(f'Text too long for section "{text_preamble}", trimmed to 5000 characters.')
            complete_text = text_preamble + "\n\n" + text_content
            logger.debug(f"Embedding {text_preamble}, text len {len(text_content)}")

            dense_embedding = embeddings.embed_documents([complete_text])
            logger.debug(f"Embedding for {text_preamble}, dim len {len(dense_embedding[0])}")
            record = {
                "id": str(section["id"]),
                "title": section["title"],
                "text": text_content,
                "source": section["source"],
                "dense_vector": dense_embedding[0],
                "parent": str(section["parent"]) if section["parent"] else None,
                "children": [str(child) for child in section["children"]],
                "previous": [str(prv) for prv in section["previous"]],
                "next": [str(nxt) for nxt in section["next"]],
                "relations": [str(rel) for rel in section["relations"]],
                "page_id": int(section["page_id"]),
                "doc_id": str(section["doc_id"]),
                "doc_title": section["doc_title"],
                "doc_hash": str(section["doc_hash"]),
            }
            try:
                vector.store.insert_batch(collection_name, [record])
                num_sections += 1
            except Exception as e:
                logger.error(f"Failed to insert data: {e}")
        num_pages += 1

    return [num_pages, num_sections]


def index_pages_incremental(
        pages: list[dict],
        collection_name: str,
        embedding_model: str,
        embedding_dimension: int,
        embedding_api_base: str = "",
        embedding_api_key: str = "",
) -> dict[str, int]:
    """Incrementally update the live collection based on each page's change_type.

    Pages with `change_type` of ``"deleted"`` or ``"updated"`` have their
    existing sections removed from the collection first. Pages with
    ``"created"`` or ``"updated"`` are then re-embedded and inserted.
    Pages with no `change_type` (``None``) are unchanged and skipped.

    Args:
        pages: List of page dicts from the incremental dump.
        collection_name: Name of the live collection to update in-place.
        embedding_model: Embedding model to use for new/updated pages.
        embedding_dimension: Embedding vector dimensions.
        embedding_api_base: Base URL for the OpenAI-compatible embedding endpoint.
        embedding_api_key: API key for the embedding endpoint.

    Returns:
        Summary dict with keys ``"deleted"``, ``"updated"``, ``"created"``,
        ``"skipped"``, and ``"sections_indexed"``.

    """
    delete_ids: list[int] = []
    pages_to_insert: list[dict] = []
    counts = {"deleted": 0, "updated": 0, "created": 0, "skipped": 0}

    for page in pages:
        change_type = page.get("change_type")
        if change_type == "deleted":
            delete_ids.append(page["id"])
            counts["deleted"] += 1
        elif change_type == "updated":
            delete_ids.append(page["id"])
            pages_to_insert.append(page)
            counts["updated"] += 1
        elif change_type == "created":
            pages_to_insert.append(page)
            counts["created"] += 1
        else:
            counts["skipped"] += 1

    vector.store.delete_by_page_ids(collection_name, delete_ids)

    [_, sections_indexed] = index_pages(
        pages_to_insert, collection_name, embedding_model, embedding_dimension,
        embedding_api_base, embedding_api_key,
    )
    counts["sections_indexed"] = sections_indexed

    return counts


def replace_previous_collection(collection_name: str, temp_collection_name: str) -> None:
    """Replace the previous collection with the new one.

    Compacts the temporary collection, drops any existing live collection,
    renames the temporary collection to the live name, and then loads the
    renamed collection into memory so it is immediately ready for querying.

    Args:
        collection_name: Name of the live collection to replace.
        temp_collection_name: Name of the temporary collection that holds the
            freshly indexed data.

    """
    if not vector.store.collection_exists(temp_collection_name):
        msg = f"Collection {temp_collection_name} does not exist."
        raise ValueError(msg)

    logger.info(f"Flushing collection {temp_collection_name!r} to seal segments before compaction")
    vector.store.flush_collection(temp_collection_name)
    logger.info(f"Compacting collection {temp_collection_name!r}")
    vector.store.compact_collection(temp_collection_name)

    if vector.store.collection_exists(collection_name):
        vector.store.drop_collection(collection_name)
    vector.store.rename_collection(temp_collection_name, collection_name)

    logger.info(f"Loading collection {collection_name!r} into memory for querying")
    vector.store.load_collection(collection_name)
