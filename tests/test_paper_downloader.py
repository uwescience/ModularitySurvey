#!/usr/bin/env python3
"""
Tests for src/paper_downloader.py.
Run standalone:  python3 tests/test_paper_downloader.py
Run via discovery: python3 -m unittest discover tests
"""

import importlib.util
import io
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

_SRC = pathlib.Path(__file__).parent.parent / "src" / "paper_downloader.py"
_spec = importlib.util.spec_from_file_location("paper_downloader", _SRC)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

sanitize_doi       = _mod.sanitize_doi
safe_filename      = _mod.safe_filename
title_slug         = _mod.title_slug
extract_doi_from_url = _mod.extract_doi_from_url
normalize_title    = _mod.normalize_title
titles_match       = _mod.titles_match
is_pdf_content     = _mod.is_pdf_content
try_download       = _mod.try_download
determine_filename = _mod.determine_filename
load_bib_title_doi = _mod.load_bib_title_doi
lookup_doi_by_title = _mod.lookup_doi_by_title


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

class TestSanitizeDoi(unittest.TestCase):
    def test_strips_doi_org_prefix(self):
        self.assertEqual(sanitize_doi("https://doi.org/10.1038/s41467-021-21146-y"),
                         "10.1038/s41467-021-21146-y")

    def test_strips_dx_doi_org_prefix(self):
        self.assertEqual(sanitize_doi("https://dx.doi.org/10.1038/s41467-021-21146-y"),
                         "10.1038/s41467-021-21146-y")

    def test_http_doi_org(self):
        self.assertEqual(sanitize_doi("http://doi.org/10.1016/j.cell.2018.06.010"),
                         "10.1016/j.cell.2018.06.010")

    def test_passthrough_non_doi_url(self):
        url = "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/bies.202300188"
        self.assertEqual(sanitize_doi(url), url)

    def test_strips_trailing_slash(self):
        self.assertEqual(sanitize_doi("https://doi.org/10.1038/abc/"), "10.1038/abc")

    def test_strips_whitespace(self):
        self.assertEqual(sanitize_doi("  https://doi.org/10.1038/abc  "), "10.1038/abc")

    def test_bare_doi_passthrough(self):
        self.assertEqual(sanitize_doi("10.1038/abc"), "10.1038/abc")


class TestSafeFilename(unittest.TestCase):
    def test_replaces_slashes(self):
        self.assertEqual(safe_filename("10.1038/s41467-021"), "10.1038_s41467-021")

    def test_preserves_dots_and_dashes(self):
        result = safe_filename("10.1038/s41467-021-21146-y")
        self.assertNotIn("/", result)
        self.assertIn(".", result)
        self.assertIn("-", result)

    def test_replaces_spaces(self):
        self.assertNotIn(" ", safe_filename("hello world"))

    def test_alphanumeric_unchanged(self):
        self.assertEqual(safe_filename("abc123"), "abc123")


class TestTitleSlug(unittest.TestCase):
    def test_lowercases(self):
        self.assertEqual(title_slug("Hello World"), "hello_world")

    def test_replaces_non_alphanumeric(self):
        slug = title_slug("A: Test (paper)")
        self.assertNotIn(":", slug)
        self.assertNotIn("(", slug)

    def test_truncates_at_80(self):
        long_title = "a" * 100
        self.assertLessEqual(len(title_slug(long_title)), 80)

    def test_strips_leading_trailing_underscores(self):
        slug = title_slug("!hello!")
        self.assertFalse(slug.startswith("_"))
        self.assertFalse(slug.endswith("_"))

    def test_unicode_title(self):
        # Should not crash on unicode
        slug = title_slug("Modular‐level alterations")
        self.assertIsInstance(slug, str)


class TestExtractDoiFromUrl(unittest.TestCase):
    def test_doi_org_url(self):
        self.assertEqual(
            extract_doi_from_url("https://doi.org/10.1038/s41467-021-21146-y"),
            "10.1038/s41467-021-21146-y",
        )

    def test_doi_embedded_in_journal_path(self):
        result = extract_doi_from_url(
            "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/bies.202300188"
        )
        self.assertEqual(result, "10.1002/bies.202300188")

    def test_no_doi_in_url(self):
        self.assertIsNone(extract_doi_from_url("https://www.ncbi.nlm.nih.gov/pmc/articles/6867028"))

    def test_strips_trailing_punctuation(self):
        result = extract_doi_from_url("https://doi.org/10.1038/abc.")
        self.assertFalse(result.endswith("."))

    def test_no_doi_returns_none(self):
        self.assertIsNone(extract_doi_from_url("https://escholarship.org/content/qt0465k3fx/qt0465k3fx.pdf"))

    def test_hdl_handle_has_no_doi(self):
        self.assertIsNone(extract_doi_from_url("http://hdl.handle.net/11858/00-001M-0000-002D-88EA-3"))


class TestNormalizeTitle(unittest.TestCase):
    def test_lowercases(self):
        self.assertEqual(normalize_title("Hello World"), "hello world")

    def test_strips_punctuation(self):
        result = normalize_title("A: Study of (Modules)")
        self.assertNotIn(":", result)
        self.assertNotIn("(", result)

    def test_strips_unicode_dash(self):
        result = normalize_title("Modular‐level")
        self.assertNotIn("‐", result)


class TestTitlesMatch(unittest.TestCase):
    def test_identical_titles_match(self):
        t = "Modular organization of the brain"
        self.assertTrue(titles_match(t, t))

    def test_clearly_different_titles_dont_match(self):
        self.assertFalse(titles_match("Brain modularity", "Gut microbiome diversity"))

    def test_empty_string_returns_false(self):
        self.assertFalse(titles_match("", "Something"))
        self.assertFalse(titles_match("Something", ""))

    def test_near_identical_matches(self):
        self.assertTrue(titles_match(
            "A mechanistic model of connector hubs, modularity and cognition",
            "A mechanistic model of connector hubs modularity and cognition",
        ))


# ---------------------------------------------------------------------------
# PDF detection
# ---------------------------------------------------------------------------

class TestIsPdfContent(unittest.TestCase):
    PDF_MAGIC = b"%PDF-1.4 rest of content here"
    HTML_BYTES = b"<!DOCTYPE html><html>"

    def test_pdf_content_type_recognized(self):
        self.assertTrue(is_pdf_content(self.HTML_BYTES, "application/pdf", "http://x.com/a"))

    def test_content_type_with_charset_recognized(self):
        self.assertTrue(is_pdf_content(self.HTML_BYTES, "application/pdf; charset=utf-8", "http://x.com/a"))

    def test_html_content_type_not_pdf(self):
        self.assertFalse(is_pdf_content(self.HTML_BYTES, "text/html; charset=utf-8", "http://x.com/a"))

    def test_url_ending_pdf_recognized(self):
        self.assertTrue(is_pdf_content(self.HTML_BYTES, "text/html", "http://x.com/paper.pdf"))

    def test_magic_bytes_recognized(self):
        self.assertTrue(is_pdf_content(self.PDF_MAGIC, "application/octet-stream", "http://x.com/a"))

    def test_html_bytes_with_html_content_type_not_pdf(self):
        self.assertFalse(is_pdf_content(self.HTML_BYTES, "text/html", "http://x.com/a"))


# ---------------------------------------------------------------------------
# Download logic (mocked HTTP)
# ---------------------------------------------------------------------------

def _make_response(content: bytes, content_type: str, url: str = "http://x.com/"):
    """Build a mock urllib response."""
    resp = MagicMock()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    resp.read.return_value = content
    resp.headers = MagicMock()
    resp.headers.get.return_value = content_type
    resp.url = url
    return resp


PDF_BYTES = b"%PDF-1.4 fake content"
HTML_BYTES = b"<!DOCTYPE html><html><body></body></html>"


class TestTryDownload(unittest.TestCase):
    def test_returns_content_when_pdf_content_type(self):
        mock_resp = _make_response(PDF_BYTES, "application/pdf")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            content, detail = try_download("http://x.com/paper")
        self.assertEqual(content, PDF_BYTES)

    def test_returns_content_when_magic_bytes(self):
        mock_resp = _make_response(PDF_BYTES, "application/octet-stream")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            content, detail = try_download("http://x.com/paper")
        self.assertEqual(content, PDF_BYTES)

    def test_returns_none_on_403(self):
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
                "http://x.com/", 403, "Forbidden", {}, None)):
            content, detail = try_download("http://x.com/paper")
        self.assertIsNone(content)
        self.assertIn("403", detail)

    def test_html_response_attempts_pdf_suffix(self):
        """First call returns HTML; second (with /pdf suffix) returns PDF."""
        html_resp = _make_response(HTML_BYTES, "text/html")
        pdf_resp  = _make_response(PDF_BYTES,  "application/pdf", "http://x.com/paper/pdf")

        call_count = 0
        def fake_urlopen(req, timeout=None):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return html_resp
            return pdf_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            content, detail = try_download("http://x.com/paper")

        self.assertEqual(content, PDF_BYTES, "Should have succeeded via /pdf fallback")
        self.assertEqual(call_count, 2)

    def test_html_response_no_pdf_fallback_returns_none(self):
        """Both original URL and /pdf suffix return HTML."""
        html_resp = _make_response(HTML_BYTES, "text/html")

        with patch("urllib.request.urlopen", return_value=html_resp):
            content, detail = try_download("http://x.com/paper")

        self.assertIsNone(content)
        self.assertIn("Not a PDF", detail)

    def test_url_ending_in_pdf_not_doubled(self):
        """URLs ending in .pdf should NOT get an extra /pdf appended."""
        pdf_resp = _make_response(HTML_BYTES, "text/plain", "http://x.com/a.pdf")

        calls = []
        def fake_urlopen(req, timeout=None):
            calls.append(req.full_url)
            return pdf_resp

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            try_download("http://x.com/a.pdf")

        self.assertEqual(len(calls), 1, "Should not try /pdf suffix when URL already ends with .pdf")

    def test_url_error_returns_none(self):
        with patch("urllib.request.urlopen",
                   side_effect=urllib.error.URLError("connection refused")):
            content, detail = try_download("http://unreachable.example/")
        self.assertIsNone(content)
        self.assertIn("URLError", detail)


# ---------------------------------------------------------------------------
# Filename determination
# ---------------------------------------------------------------------------

class TestDetermineFilename(unittest.TestCase):
    def _bib(self, title, doi_url):
        return {normalize_title(title): doi_url}

    def test_doi_extracted_from_url(self):
        bib = {}
        stem = determine_filename(
            "Some Paper",
            "https://doi.org/10.1038/s41467-021-21146-y",
            bib,
        )
        self.assertEqual(stem, "10.1038_s41467-021-21146-y")

    def test_doi_extracted_from_journal_url(self):
        bib = {}
        stem = determine_filename(
            "Some Paper",
            "https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/bies.202300188",
            bib,
        )
        self.assertEqual(stem, "10.1002_bies.202300188")

    def test_bib_lookup_used_when_no_doi_in_url(self):
        bib = self._bib("Mapping the genetic landscape", "https://doi.org/10.1016/j.cell.2018.06.010")
        stem = determine_filename(
            "Mapping the genetic landscape",
            "https://escholarship.org/content/qt0465k3fx/qt0465k3fx.pdf",
            bib,
        )
        self.assertEqual(stem, "10.1016_j.cell.2018.06.010")

    def test_title_slug_fallback_when_no_doi(self):
        bib = {}
        stem = determine_filename(
            "Modular Brain Networks in Health",
            "https://www.ncbi.nlm.nih.gov/pmc/articles/6867028",
            bib,
        )
        self.assertIn("modular", stem)
        self.assertNotIn(" ", stem)

    def test_doi_url_in_bib_preferred_over_title_slug(self):
        bib = self._bib("Some PMC Paper", "https://doi.org/10.9999/xyz")
        stem = determine_filename(
            "Some PMC Paper",
            "https://www.ncbi.nlm.nih.gov/pmc/articles/1234567",
            bib,
        )
        self.assertEqual(stem, "10.9999_xyz")


# ---------------------------------------------------------------------------
# Bibliography index
# ---------------------------------------------------------------------------

class TestLoadBibTitleDoi(unittest.TestCase):
    def _write_bib(self, rows):
        import csv, tempfile
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False,
                                        newline="", encoding="utf-8")
        writer = csv.DictWriter(f, fieldnames=["Paper title", "DOI URL", "Other"])
        writer.writeheader()
        writer.writerows(rows)
        f.close()
        return pathlib.Path(f.name)

    def test_loads_title_doi_pairs(self):
        p = self._write_bib([
            {"Paper title": "Brain Modularity", "DOI URL": "https://doi.org/10.1/a", "Other": ""},
        ])
        index = load_bib_title_doi(p)
        self.assertIn("brain modularity", index)

    def test_skips_rows_without_doi(self):
        p = self._write_bib([
            {"Paper title": "No DOI Paper", "DOI URL": "", "Other": ""},
        ])
        index = load_bib_title_doi(p)
        self.assertEqual(len(index), 0)

    def test_missing_file_returns_empty_dict(self):
        index = load_bib_title_doi(pathlib.Path("/nonexistent/file.csv"))
        self.assertEqual(index, {})


class TestLookupDoiByTitle(unittest.TestCase):
    def _index(self):
        return {
            normalize_title("Brain Modularity and Cognition"): "https://doi.org/10.1/brain",
            normalize_title("Gut Microbiome Diversity"):        "https://doi.org/10.2/gut",
        }

    def test_exact_match(self):
        doi = lookup_doi_by_title("Brain Modularity and Cognition", self._index())
        self.assertEqual(doi, "https://doi.org/10.1/brain")

    def test_fuzzy_match_near_identical(self):
        doi = lookup_doi_by_title("Brain Modularity and Cognition.", self._index())
        self.assertEqual(doi, "https://doi.org/10.1/brain")

    def test_no_match_returns_none(self):
        doi = lookup_doi_by_title("Completely Unrelated Topic About Rocks", self._index())
        self.assertIsNone(doi)


# ---------------------------------------------------------------------------
# Integration: verify first 10 rows fail for the RIGHT reasons
# ---------------------------------------------------------------------------

class TestFirst10RowsFailCorrectly(unittest.TestCase):
    """
    Confirms that the first 10 rows of pdf_search_results.csv fail due to
    server-side access restrictions (403 or HTML response), NOT code bugs.
    Each call is a live network request.
    """

    def _get_rows(self):
        import csv
        results_path = pathlib.Path(__file__).parent.parent / "db" / "pdf_search_results.csv"
        with open(results_path, encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))[:10]

    def test_failures_are_network_not_code_bugs(self):
        rows = self._get_rows()
        for row in rows:
            url = row.get("pdf_url", "").strip()
            if not url:
                continue  # expected empty — skip
            content, reason = try_download(url)
            self.assertIsNone(content,
                msg=f"Expected failure for {url!r} but got PDF ({len(content or b'')} bytes)")
            # Reason must be a server/network issue, not a Python exception or code bug
            self.assertTrue(
                any(k in reason for k in ("HTTP", "Not a PDF", "URLError")),
                msg=f"Unexpected failure reason {reason!r} for {url!r}",
            )


# ---------------------------------------------------------------------------
# Integration: a known open-access URL downloads successfully
# ---------------------------------------------------------------------------

class TestKnownGoodUrlDownloads(unittest.TestCase):
    """Live network test against a known open-access PDF."""

    ESCHOLARSHIP_URL = "https://escholarship.org/content/qt0465k3fx/qt0465k3fx.pdf"

    def test_escholarship_pdf_downloads(self):
        content, detail = try_download(self.ESCHOLARSHIP_URL)
        self.assertIsNotNone(content,
            msg=f"Expected PDF from escholarship but got: {detail}")
        self.assertEqual(content[:4], b"%PDF",
            msg="Downloaded content is not a valid PDF (bad magic bytes)")
        self.assertGreater(len(content), 10_000,
            msg=f"Downloaded PDF is suspiciously small: {len(content)} bytes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
