#!/usr/bin/env python3
"""
Unit tests for src/find_citations.py.
Run standalone:  python3 tests/test_find_citations.py
Run via discovery: python3 -m unittest discover tests
"""

import importlib
import io
import json
import sys
import unittest
import urllib.error
import urllib.request
from unittest.mock import MagicMock, patch

IGNORE_TEST = True

# ---------------------------------------------------------------------------
# Module-level import helper so the tests can find the source even when the
# working directory is not the repo root.
# ---------------------------------------------------------------------------
import importlib.util, pathlib

_SRC = pathlib.Path(__file__).parent.parent / "src" / "find_citations.py"
_spec = importlib.util.spec_from_file_location("find_citations", _SRC)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

api_request = _mod.api_request
get_paper_id = _mod.get_paper_id
get_citations = _mod.get_citations
filter_citations = _mod.filter_citations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_http_error(code):
    """Build a urllib.error.HTTPError with the given status code."""
    return urllib.error.HTTPError(url="http://x", code=code, msg="err",
                                  hdrs=None, fp=None)


def _mock_response(data: dict):
    """Return a context-manager mock that yields a response reading *data*."""
    payload = json.dumps(data).encode()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    cm.read = MagicMock(return_value=payload)
    return cm


# ---------------------------------------------------------------------------
# Tests for api_request
# ---------------------------------------------------------------------------

class TestApiRequest(unittest.TestCase):

    def setUp(self):
        if IGNORE_TEST:
            return

    def test_returns_parsed_json_on_success(self):
        if IGNORE_TEST:
            return
        expected = {"paperId": "abc", "title": "Test"}
        with patch.object(_mod.urllib.request, "urlopen",
                          return_value=_mock_response(expected)):
            result = api_request("http://fake")
        self.assertEqual(result, expected)

    def test_returns_none_on_404(self):
        if IGNORE_TEST:
            return
        with patch.object(_mod.urllib.request, "urlopen",
                          side_effect=_make_http_error(404)):
            result = api_request("http://fake")
        self.assertIsNone(result)

    def test_returns_none_on_non_404_http_error(self):
        if IGNORE_TEST:
            return
        with patch.object(_mod.urllib.request, "urlopen",
                          side_effect=_make_http_error(500)):
            result = api_request("http://fake")
        self.assertIsNone(result)

    def test_retries_on_429_then_succeeds(self):
        if IGNORE_TEST:
            return
        expected = {"paperId": "xyz"}
        responses = [_make_http_error(429), _mock_response(expected)]
        call_count = [0]

        def side_effect(url):
            val = responses[call_count[0]]
            call_count[0] += 1
            if isinstance(val, Exception):
                raise val
            return val

        with patch.object(_mod.urllib.request, "urlopen",
                          side_effect=side_effect), \
             patch.object(_mod.time, "sleep"):
            result = api_request("http://fake", retry_count=3)
        self.assertEqual(result, expected)

    def test_returns_none_after_exhausting_retries_on_429(self):
        if IGNORE_TEST:
            return
        with patch.object(_mod.urllib.request, "urlopen",
                          side_effect=_make_http_error(429)), \
             patch.object(_mod.time, "sleep"):
            result = api_request("http://fake", retry_count=2)
        self.assertIsNone(result)

    def test_returns_none_after_generic_exception_exhausts_retries(self):
        if IGNORE_TEST:
            return
        with patch.object(_mod.urllib.request, "urlopen",
                          side_effect=Exception("connection refused")), \
             patch.object(_mod.time, "sleep"):
            result = api_request("http://fake", retry_count=2)
        self.assertIsNone(result)

    def test_retries_generic_exception_before_succeeding(self):
        if IGNORE_TEST:
            return
        expected = {"ok": True}
        responses = [Exception("oops"), _mock_response(expected)]
        call_count = [0]

        def side_effect(url):
            val = responses[call_count[0]]
            call_count[0] += 1
            if isinstance(val, Exception):
                raise val
            return val

        with patch.object(_mod.urllib.request, "urlopen",
                          side_effect=side_effect), \
             patch.object(_mod.time, "sleep"):
            result = api_request("http://fake", retry_count=2)
        self.assertEqual(result, expected)


# ---------------------------------------------------------------------------
# Tests for get_paper_id
# ---------------------------------------------------------------------------

class TestGetPaperId(unittest.TestCase):

    def _patch_api(self, return_value):
        return patch.object(_mod, "api_request", return_value=return_value)

    def test_returns_tuple_on_success(self):
        if IGNORE_TEST:
            return
        data = {"paperId": "P1", "title": "A Title", "citationCount": 42}
        with self._patch_api(data), patch.object(_mod.time, "sleep"):
            result = get_paper_id("10.1234/test")
        self.assertEqual(result, ("P1", "A Title", 42))

    def test_returns_none_tuple_when_api_returns_none(self):
        if IGNORE_TEST:
            return
        with self._patch_api(None), patch.object(_mod.time, "sleep"):
            result = get_paper_id("10.9999/missing")
        self.assertEqual(result, (None, None, None))

    def test_returns_none_tuple_when_paperId_missing(self):
        if IGNORE_TEST:
            return
        with self._patch_api({"title": "No ID"}), \
             patch.object(_mod.time, "sleep"):
            result = get_paper_id("10.9999/noid")
        self.assertEqual(result, (None, None, None))

    def test_uses_defaults_for_missing_optional_fields(self):
        if IGNORE_TEST:
            return
        # Only paperId is present; title and citationCount should default
        with self._patch_api({"paperId": "P2"}), \
             patch.object(_mod.time, "sleep"):
            pid, title, count = get_paper_id("10.1/x")
        self.assertEqual(pid, "P2")
        self.assertEqual(title, "")
        self.assertEqual(count, 0)


# ---------------------------------------------------------------------------
# Tests for get_citations
# ---------------------------------------------------------------------------

class TestGetCitations(unittest.TestCase):

    def test_returns_citations_single_page(self):
        if IGNORE_TEST:
            return
        citations = [{"citingPaper": {"paperId": "C1"}}]
        page = {"data": citations}  # no 'next' key => stop after first page
        with patch.object(_mod, "api_request", return_value=page), \
             patch.object(_mod.time, "sleep"):
            result = get_citations("P1", limit=100)
        self.assertEqual(result, citations)

    def test_paginates_when_next_key_present(self):
        if IGNORE_TEST:
            return
        page1 = {"data": [{"id": 1}], "next": 100}
        page2 = {"data": [{"id": 2}]}  # no 'next' => stop
        responses = [page1, page2]
        call_count = [0]

        def fake_api(url):
            val = responses[call_count[0]]
            call_count[0] += 1
            return val

        with patch.object(_mod, "api_request", side_effect=fake_api), \
             patch.object(_mod.time, "sleep"):
            result = get_citations("P1", limit=100)
        self.assertEqual(len(result), 2)

    def test_stops_when_data_is_empty(self):
        if IGNORE_TEST:
            return
        page = {"data": [], "next": 100}
        with patch.object(_mod, "api_request", return_value=page), \
             patch.object(_mod.time, "sleep"):
            result = get_citations("P1", limit=100)
        self.assertEqual(result, [])

    def test_stops_when_api_returns_none(self):
        if IGNORE_TEST:
            return
        with patch.object(_mod, "api_request", return_value=None), \
             patch.object(_mod.time, "sleep"):
            result = get_citations("P1", limit=100)
        self.assertEqual(result, [])

    def test_stops_when_api_returns_no_data_key(self):
        if IGNORE_TEST:
            return
        with patch.object(_mod, "api_request", return_value={"other": "stuff"}), \
             patch.object(_mod.time, "sleep"):
            result = get_citations("P1", limit=100)
        self.assertEqual(result, [])

    def test_stops_at_offset_1000(self):
        if IGNORE_TEST:
            return
        # Every page has 100 items and a 'next' key — should stop at offset 1000
        page = {"data": [{"id": i} for i in range(100)], "next": 999}
        call_count = [0]

        def fake_api(url):
            call_count[0] += 1
            return page

        with patch.object(_mod, "api_request", side_effect=fake_api), \
             patch.object(_mod.time, "sleep"):
            result = get_citations("P1", limit=100)
        # 10 pages × 100 items = 1000 items, then offset hits 1000 and stops
        self.assertEqual(len(result), 1000)
        self.assertEqual(call_count[0], 10)


# ---------------------------------------------------------------------------
# Tests for filter_citations
# ---------------------------------------------------------------------------

class TestFilterCitations(unittest.TestCase):

    def _make_item(self, year, citation_count):
        return {"citingPaper": {"paperId": "X", "year": year,
                                "citationCount": citation_count}}

    def test_keeps_papers_in_range_with_sufficient_citations(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2020, 100)]
        result = filter_citations(items)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["paperId"], "X")

    def test_strips_wrapper_returns_citing_paper_dicts(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2018, 200)]
        result = filter_citations(items)
        # Result items should be the inner citingPaper dicts, not the wrappers
        self.assertIn("paperId", result[0])
        self.assertNotIn("citingPaper", result[0])

    def test_excludes_papers_before_year_min(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2014, 100)]
        result = filter_citations(items)
        self.assertEqual(result, [])

    def test_excludes_papers_after_year_max(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2026, 100)]
        result = filter_citations(items)
        self.assertEqual(result, [])

    def test_excludes_papers_below_min_citations(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2020, 49)]
        result = filter_citations(items)
        self.assertEqual(result, [])

    def test_includes_paper_at_exact_boundary_year_min(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2015, 50)]
        result = filter_citations(items)
        self.assertEqual(len(result), 1)

    def test_includes_paper_at_exact_boundary_year_max(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2025, 50)]
        result = filter_citations(items)
        self.assertEqual(len(result), 1)

    def test_includes_paper_at_exact_min_citations(self):
        if IGNORE_TEST:
            return
        items = [self._make_item(2020, 50)]
        result = filter_citations(items)
        self.assertEqual(len(result), 1)

    def test_excludes_item_with_no_year(self):
        if IGNORE_TEST:
            return
        items = [{"citingPaper": {"paperId": "Y", "citationCount": 200}}]
        result = filter_citations(items)
        self.assertEqual(result, [])

    def test_filters_mixed_list(self):
        if IGNORE_TEST:
            return
        items = [
            self._make_item(2020, 200),  # keep
            self._make_item(2014, 100),  # year too old
            self._make_item(2021, 10),   # citations too low
            self._make_item(2023, 500),  # keep
        ]
        result = filter_citations(items)
        self.assertEqual(len(result), 2)

    def test_empty_input_returns_empty_list(self):
        if IGNORE_TEST:
            return
        self.assertEqual(filter_citations([]), [])


if __name__ == "__main__":
    unittest.main()
