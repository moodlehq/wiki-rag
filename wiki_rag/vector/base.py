#  Copyright (c) 2025, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""Base vector interface that every vector-store backend must implement.

All vector implementations must inherit from :class:`GenericVector` and
override every abstract method.  The rest of the application only
interacts with the vector store through this narrow contract, making it
trivial to swap backends by changing the `INDEX_VENDOR` environment
variable. And a few more, specific for each vector store (url, key, port, ...).
"""

import logging

from abc import ABC, abstractmethod
from typing import Any

from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

import wiki_rag.config as _config_module

logger = logging.getLogger(__name__)


class BaseVector(ABC):
    """Minimal contract that every vector-store backend must implement."""

    @abstractmethod
    def create_collection(self, collection_name: str, embedding_dimension: int) -> None:
        """Create (or recreate) a collection / index with the required schema.

        If a collection with the same name already exists it must be
        dropped first.

        Args:
            collection_name: Name of the target collection / index.
            embedding_dimension: Dimensionality of the dense vector that
                will be stored (e.g. 778, 1024, ...).

        """

    @abstractmethod
    def insert_batch(self, collection_name: str, records: list[dict[str, Any]]) -> None:
        """Insert a batch of records into the collection.

        Args:
            collection_name: Target collection / index.
            records: List of dictionaries that contain at least the keys
                defined in the schema built by `create_collection`.

        """

    @abstractmethod
    def delete_by_page_ids(self, collection_name: str, page_ids: list[int]) -> None:
        """Delete all sections belonging to the given page IDs from the collection.

        Must be a no-op when `page_ids` is empty.

        Args:
            collection_name: Target collection / index.
            page_ids: List of integer page IDs whose sections should be removed.

        """

    @abstractmethod
    def get_documents_contents_by_id(self,
        collection_name: str,
        ids: list[str],
    ) -> dict[str, str]:
        """Retrieve documents (output columns) matching the given ids.

        Args:
            collection_name: Target collection / index.
            ids: List of ids to retrieve.

        Returns:
            dictionary of document ids as keys and document contents as values.

        """

    @abstractmethod
    def retrieve(self,
        collection_name: str,
        embedding_model: str,
        embedding_dimensions: int,
        queries: list[str],
        sparse_query: str | None = None,
        embedding_api_base: str = "",
        embedding_api_key: str = "",
    ) -> list[dict]:
        """Retrieve the best matches for a question from the vector store.

        The function embeds all strings in `queries` and averages the resulting
        vectors for the dense search. `sparse_query` is used as-is for any
        text-based sparse search (e.g. BM25); when omitted it defaults to
        `queries[0]`. A single-element `queries` list with no `sparse_query`
        is equivalent to the previous single-query behaviour.

        When HyDE is active, callers should pass only the hypothetical passages
        in `queries` (for faithful document-to-document dense retrieval) and
        supply the original rewritten question as `sparse_query` so that the
        BM25 channel still operates on the actual user query.

        The `_embed_and_average_queries()` helper is available to compute the
        averaged embedding from any OpenAI-compatible endpoint.

        Args:
            collection_name: Target collection / index.
            embedding_model: Embedding model to use.
            embedding_dimensions: Embedding dimensions to use.
            queries: One or more query strings embedded and averaged for dense
                search. When HyDE is enabled these should be the hypothetical
                passages only (not the original query).
            sparse_query: Raw text for sparse (BM25) search. Defaults to
                ``queries[0]`` when ``None``.
            embedding_api_base: Base URL for the OpenAI-compatible embedding
                endpoint.  Passed directly to ``OpenAIEmbeddings(base_url=)``.
            embedding_api_key: API key for the embedding endpoint.  Passed
                directly to ``OpenAIEmbeddings(api_key=)``.

        Returns:
            list of matching results

        """

    @abstractmethod
    def collection_exists(self, name: str) -> bool:
        """Return True if the collection / index exists.

        Args:
            name: Collection / index name.

        Returns:
            Existence flag.

        """

    @abstractmethod
    def drop_collection(self, name: str) -> None:
        """Delete the collection / index.

        Args:
            name: Collection / index name.

        """

    @abstractmethod
    def rename_collection(self, old: str, new: str) -> None:
        """Rename a collection / index (atomic operation provided by most stores).

        Args:
            old: Current name.
            new: Desired name.

        """

    def flush_collection(self, name: str) -> None:
        """Flush all in-memory data to persistent storage, sealing any growing segments.

        Must be called before compaction to ensure all inserted data is included.
        Backends that do not require an explicit flush should leave this as a no-op.

        Args:
            name: Collection / index name.

        """

    @abstractmethod
    def compact_collection(self, name: str) -> None:
        """Trigger maintenance / compaction on the collection / index.

        For stores that do not support compaction this method must be a
        no-op.

        Args:
            name: Collection / index name.

        """

    def load_collection(self, name: str) -> None:
        """Load the collection / index into memory for querying.

        Backends that do not require an explicit load should leave this as a
        no-op.

        Args:
            name: Collection / index name.

        """

    def _embed_and_average_queries(self,
        embedding_model: str,
        embedding_dimensions: int,
        queries: list[str],
        api_base: str = "",
        api_key: str = "",
    ) -> list[float]:
        """Return averaged embeddings for one or more query strings.

        For a single query, returns the embedding directly (fast path).
        For multiple queries, embeds all strings and returns the element-wise
        average of the resulting vectors.

        Args:
            embedding_model: Embedding model to use.
            embedding_dimensions: Embedding dimensions to use.
            queries: One or more query strings to embed and average.
            api_base: Base URL for the OpenAI-compatible embedding endpoint.
            api_key: API key for the embedding endpoint.

        Returns:
            list of (float) embeddings representing the averaged vector.

        """
        assert queries, "queries must not be empty"
        embeddings = OpenAIEmbeddings(
            model=embedding_model,
            dimensions=embedding_dimensions,
            check_embedding_ctx_length=False,
            base_url=api_base or None,
            api_key=SecretStr(api_key) if api_key else None,
        )
        if len(queries) == 1:
            return embeddings.embed_query(queries[0].strip())

        all_embeddings = embeddings.embed_documents([q.strip() for q in queries])
        n = len(all_embeddings)
        dims = len(all_embeddings[0])
        return [sum(vec[i] for vec in all_embeddings) / n for i in range(dims)]


def load_vector_store(name: str) -> "BaseVector":
    """Instantiate a vector store by its name.

    The resolved :data:`~wiki_rag.config.cfg` singleton is passed to the
    vector-store constructor so that backends can read connection settings
    without calling ``os.getenv()`` directly.

    For example ``"milvus"`` will instantiate
    :class:`wiki_rag.vector.milvus.MilvusVector`.

    Args:
        name: Name of the vector store backend (e.g. ``"milvus"``).

    Returns:
        Initialised :class:`BaseVector` instance.

    Raises:
        RuntimeError: When the backend module or class cannot be imported.

    """
    assert _config_module.cfg is not None, "load_config() must be called before load_vector_store()"

    module_name = f"wiki_rag.vector.{name}"
    class_name = f"{name.capitalize()}Vector"

    try:
        module = __import__(module_name, fromlist=[class_name])
        vector_class = getattr(module, class_name)
        vector_instance = vector_class(_config_module.cfg)
    except Exception as exc:
        msg = f"Cannot load vector backend {class_name!r} from {module_name!r}"
        raise RuntimeError(msg) from exc

    return vector_instance
