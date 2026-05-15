#  Copyright (c) 2026, Moodle HQ - Research
#  SPDX-License-Identifier: BSD-3-Clause

"""wiki_rag.index.util tests."""

import unittest

from unittest.mock import MagicMock, patch

from wiki_rag.index.util import (
    index_pages,
    index_pages_incremental,
    replace_previous_collection,
)


def _make_section(page_id: int, idx: int = 0) -> dict:
    """Return a minimal section dict for testing."""
    return {
        "id": f"sec-{page_id}-{idx}",
        "title": f"Section {idx}",
        "doc_title": f"Page {page_id}",
        "text": "Some text content",
        "source": f"https://example.com/page_{page_id}",
        "parent": None,
        "children": [],
        "previous": [],
        "next": [],
        "relations": [],
        "page_id": page_id,
        "doc_id": f"doc-{page_id}",
        "doc_hash": f"hash-{page_id}",
    }


def _make_page(page_id: int, change_type: str | None = None, num_sections: int = 1) -> dict:
    """Return a minimal page dict with the given change_type."""
    page: dict = {
        "id": page_id,
        "title": f"Page {page_id}",
        "sections": [_make_section(page_id, i) for i in range(num_sections)],
        "categories": [],
        "templates": [],
        "internal_links": [],
        "external_links": [],
        "language_links": [],
    }
    if change_type is not None:
        page["change_type"] = change_type
    return page


class TestIndexPagesSkipsDeletedPages(unittest.TestCase):
    """index_pages() must skip pages whose change_type is 'deleted'."""

    @patch("wiki_rag.index.util.vector")
    @patch("wiki_rag.index.util.OpenAIEmbeddings")
    def test_index_pages_skips_deleted_pages(self, mock_embeddings_cls, mock_vector):
        """Deleted pages produce zero insert_batch calls."""
        mock_embeddings_cls.return_value.embed_documents.return_value = [[0.1] * 4]

        pages = [_make_page(1, change_type="deleted", num_sections=2)]
        index_pages(pages, "test_col", "model", 4)

        mock_vector.store.insert_batch.assert_not_called()

    @patch("wiki_rag.index.util.vector")
    @patch("wiki_rag.index.util.OpenAIEmbeddings")
    def test_index_pages_indexes_non_deleted_pages(self, mock_embeddings_cls, mock_vector):
        """Pages without change_type (full dump) are indexed normally."""
        mock_embeddings_cls.return_value.embed_documents.return_value = [[0.1] * 4]

        pages = [_make_page(1, num_sections=2)]  # no change_type key
        index_pages(pages, "test_col", "model", 4)

        self.assertEqual(2, mock_vector.store.insert_batch.call_count)


class TestIndexPagesIncremental(unittest.TestCase):
    """index_pages_incremental() must route pages correctly."""

    def _run(self, pages: list[dict]) -> tuple[dict, MagicMock, MagicMock]:
        """Run index_pages_incremental with mocked vector store and embeddings."""
        with (
            patch("wiki_rag.index.util.vector") as mock_vector,
            patch("wiki_rag.index.util.OpenAIEmbeddings") as mock_embeddings_cls,
        ):
            mock_embeddings_cls.return_value.embed_documents.return_value = [[0.1] * 4]
            summary = index_pages_incremental(pages, "live_col", "model", 4)
            return summary, mock_vector, mock_embeddings_cls

    def test_incremental_deleted_pages_triggers_deletion(self):
        """delete_by_page_ids called with correct IDs; no insertions."""
        pages = [_make_page(10, change_type="deleted")]
        summary, mock_vector, _ = self._run(pages)

        mock_vector.store.delete_by_page_ids.assert_called_once_with("live_col", [10])
        mock_vector.store.insert_batch.assert_not_called()

    def test_incremental_created_pages_triggers_insertion(self):
        """Insertions only for created pages; no deletions."""
        pages = [_make_page(20, change_type="created", num_sections=1)]
        summary, mock_vector, _ = self._run(pages)

        mock_vector.store.delete_by_page_ids.assert_called_once_with("live_col", [])
        self.assertEqual(1, mock_vector.store.insert_batch.call_count)

    def test_incremental_updated_pages_deletes_then_inserts(self):
        """Updated page ID appears in deletion list and is also re-inserted."""
        pages = [_make_page(30, change_type="updated", num_sections=1)]
        summary, mock_vector, _ = self._run(pages)

        mock_vector.store.delete_by_page_ids.assert_called_once_with("live_col", [30])
        self.assertEqual(1, mock_vector.store.insert_batch.call_count)

    def test_incremental_unchanged_pages_skipped(self):
        """Pages with change_type=None trigger neither deletion nor insertion."""
        pages = [_make_page(40, change_type=None)]
        summary, mock_vector, _ = self._run(pages)

        mock_vector.store.delete_by_page_ids.assert_called_once_with("live_col", [])
        mock_vector.store.insert_batch.assert_not_called()

    def test_incremental_mixed_changes(self):
        """All four change types are routed correctly in a single call."""
        pages = [
            _make_page(1, change_type="deleted", num_sections=2),
            _make_page(2, change_type="updated", num_sections=1),
            _make_page(3, change_type="created", num_sections=3),
            _make_page(4, change_type=None, num_sections=1),
        ]
        summary, mock_vector, _ = self._run(pages)

        # Pages 1 (deleted) and 2 (updated) must be in the delete call.
        mock_vector.store.delete_by_page_ids.assert_called_once_with("live_col", [1, 2])
        # Pages 2 (updated) and 3 (created) are inserted: 1 + 3 = 4 sections.
        self.assertEqual(4, mock_vector.store.insert_batch.call_count)

    def test_incremental_returns_summary_counts(self):
        """Returned summary dict contains correct per-category counts."""
        pages = [
            _make_page(1, change_type="deleted"),
            _make_page(2, change_type="updated", num_sections=2),
            _make_page(3, change_type="created", num_sections=1),
            _make_page(4, change_type=None),
        ]
        summary, _, _ = self._run(pages)

        self.assertEqual(1, summary["deleted"])
        self.assertEqual(1, summary["updated"])
        self.assertEqual(1, summary["created"])
        self.assertEqual(1, summary["skipped"])
        self.assertEqual(3, summary["sections_indexed"])  # 2 (updated) + 1 (created)


class TestReplacePreviousCollection(unittest.TestCase):
    """replace_previous_collection() must flush, compact, drop old, rename temp, then load."""

    @patch("wiki_rag.index.util.vector")
    def test_replace_drops_old_renames_temp_and_loads(self, mock_vector):
        """flush, compact, drop, rename, and load are called in the correct order."""
        mock_vector.store.collection_exists.return_value = True

        replace_previous_collection("my_col", "my_col_temp")

        mock_vector.store.flush_collection.assert_called_once_with("my_col_temp")
        mock_vector.store.compact_collection.assert_called_once_with("my_col_temp")
        mock_vector.store.drop_collection.assert_called_once_with("my_col")
        mock_vector.store.rename_collection.assert_called_once_with("my_col_temp", "my_col")
        mock_vector.store.load_collection.assert_called_once_with("my_col")

        calls = [c[0] for c in mock_vector.store.method_calls]
        self.assertLess(calls.index("flush_collection"), calls.index("compact_collection"))


if __name__ == "__main__":
    unittest.main()
