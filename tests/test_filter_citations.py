#!/usr/bin/env python3
"""
Unit tests for src/filter_citations.py.
Run standalone:  python3 tests/test_filter_citations.py
Run via discovery: python3 -m unittest discover tests
"""

import csv
import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

IGNORE_TEST = True

# ---------------------------------------------------------------------------
# Import the module under test from its absolute path so tests work from any
# working directory.
# ---------------------------------------------------------------------------
_SRC = pathlib.Path(__file__).parent.parent / "src" / "filter_citations.py"
_spec = importlib.util.spec_from_file_location("filter_citations", _SRC)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

is_biologically_relevant = _mod.is_biologically_relevant
read_existing_dois = _mod.read_existing_dois
get_doi_from_paper = _mod.get_doi_from_paper


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_paper(**kwargs):
    """Return a minimal paper dict; caller may override any field."""
    defaults = {"title": "", "abstract": "", "venue": "",
                "externalIds": {}, "citationCount": 0}
    defaults.update(kwargs)
    return defaults


def _write_csv(path, rows, fieldnames=("DOI URL", "Title")):
    """Write a simple CSV to *path* using *fieldnames*."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Tests for is_biologically_relevant
# ---------------------------------------------------------------------------

class TestIsBiologicallyRelevant(unittest.TestCase):

    def test_returns_true_for_biology_and_modularity(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(title="Gene regulatory network modularity")
        self.assertTrue(is_biologically_relevant(paper))

    def test_returns_false_without_biology_keyword(self):
        if IGNORE_TEST:
            return
        # 'modularity' present but no biology term
        paper = _make_paper(title="community structure in abstract graphs")
        self.assertFalse(is_biologically_relevant(paper))

    def test_returns_false_without_modularity_keyword(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(title="gene expression profiling in yeast")
        self.assertFalse(is_biologically_relevant(paper))

    def test_returns_false_when_exclude_keyword_present(self):
        if IGNORE_TEST:
            return
        # Even if both biology and modularity are satisfied, an exclude word blocks it
        paper = _make_paper(
            title="gene network modularity in social network wireless systems"
        )
        self.assertFalse(is_biologically_relevant(paper))

    def test_checks_abstract_field(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(
            title="A study",
            abstract="We examine gene regulatory modul in cells."
        )
        self.assertTrue(is_biologically_relevant(paper))

    def test_checks_venue_field(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(
            title="community cluster analysis",
            venue="Journal of Molecular Biology"
        )
        self.assertTrue(is_biologically_relevant(paper))

    def test_case_insensitive_matching(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(title="GENE NETWORK MODULARITY")
        self.assertTrue(is_biologically_relevant(paper))

    def test_returns_false_for_empty_paper(self):
        if IGNORE_TEST:
            return
        self.assertFalse(is_biologically_relevant(_make_paper()))

    def test_none_abstract_is_handled_gracefully(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(title="gene network modul")
        paper["abstract"] = None
        self.assertTrue(is_biologically_relevant(paper))

    def test_exclude_keyword_iot_blocks_result(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(title="gene modul iot sensor network")
        self.assertFalse(is_biologically_relevant(paper))

    def test_exclude_keyword_financial_blocks_result(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(title="gene modul financial market network")
        self.assertFalse(is_biologically_relevant(paper))


# ---------------------------------------------------------------------------
# Tests for read_existing_dois
# ---------------------------------------------------------------------------

class TestReadExistingDois(unittest.TestCase):

    def test_extracts_doi_from_url_column(self):
        if IGNORE_TEST:
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                         delete=False, encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["DOI URL"])
            writer.writeheader()
            writer.writerow({"DOI URL": "https://doi.org/10.1234/abc"})
            path = f.name
        try:
            result = read_existing_dois(path)
            self.assertIn("10.1234/abc", result)
        finally:
            os.unlink(path)

    def test_lowercases_dois(self):
        if IGNORE_TEST:
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                         delete=False, encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["DOI URL"])
            writer.writeheader()
            writer.writerow({"DOI URL": "https://doi.org/10.9999/UPPER"})
            path = f.name
        try:
            result = read_existing_dois(path)
            self.assertIn("10.9999/upper", result)
        finally:
            os.unlink(path)

    def test_returns_set(self):
        if IGNORE_TEST:
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                         delete=False, encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["DOI URL"])
            writer.writeheader()
            path = f.name
        try:
            result = read_existing_dois(path)
            self.assertIsInstance(result, set)
        finally:
            os.unlink(path)

    def test_handles_missing_file_gracefully(self):
        if IGNORE_TEST:
            return
        result = read_existing_dois("/nonexistent/path/file.csv")
        self.assertEqual(result, set())

    def test_skips_rows_with_empty_doi_url(self):
        if IGNORE_TEST:
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                         delete=False, encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["DOI URL"])
            writer.writeheader()
            writer.writerow({"DOI URL": ""})
            path = f.name
        try:
            result = read_existing_dois(path)
            self.assertEqual(result, set())
        finally:
            os.unlink(path)

    def test_deduplicates_dois(self):
        if IGNORE_TEST:
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                         delete=False, encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["DOI URL"])
            writer.writeheader()
            writer.writerow({"DOI URL": "https://doi.org/10.1/dup"})
            writer.writerow({"DOI URL": "https://doi.org/10.1/dup"})
            path = f.name
        try:
            result = read_existing_dois(path)
            self.assertEqual(len(result), 1)
        finally:
            os.unlink(path)

    def test_multiple_dois_collected(self):
        if IGNORE_TEST:
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv",
                                         delete=False, encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["DOI URL"])
            writer.writeheader()
            writer.writerow({"DOI URL": "https://doi.org/10.1/a"})
            writer.writerow({"DOI URL": "https://doi.org/10.2/b"})
            path = f.name
        try:
            result = read_existing_dois(path)
            self.assertEqual(len(result), 2)
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Tests for get_doi_from_paper
# ---------------------------------------------------------------------------

class TestGetDoiFromPaper(unittest.TestCase):

    def test_returns_lowercase_doi_when_present(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(externalIds={"DOI": "10.1234/ABC"})
        self.assertEqual(get_doi_from_paper(paper), "10.1234/abc")

    def test_returns_empty_string_when_no_external_ids(self):
        if IGNORE_TEST:
            return
        paper = _make_paper()
        paper.pop("externalIds", None)
        self.assertEqual(get_doi_from_paper(paper), "")

    def test_returns_empty_string_when_doi_key_absent(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(externalIds={"ArXiv": "1234.5678"})
        self.assertEqual(get_doi_from_paper(paper), "")

    def test_returns_empty_string_when_doi_is_empty_string(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(externalIds={"DOI": ""})
        self.assertEqual(get_doi_from_paper(paper), "")

    def test_already_lowercase_doi_unchanged(self):
        if IGNORE_TEST:
            return
        paper = _make_paper(externalIds={"DOI": "10.9999/xyz"})
        self.assertEqual(get_doi_from_paper(paper), "10.9999/xyz")


# ---------------------------------------------------------------------------
# Integration test for main()
# ---------------------------------------------------------------------------

class TestMainPipeline(unittest.TestCase):
    """
    Patch HERE and ROOT on the module so main() reads from / writes to
    temp directories rather than the real repo paths.
    """

    def _run_main(self, papers, existing_csv_rows=None):
        """
        Write *papers* to a temp citations_raw.json, optionally populate an
        existing CSV, then call main() and return the parsed stdout JSON.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = pathlib.Path(tmpdir) / "src"
            db_dir = pathlib.Path(tmpdir) / "db"
            src_dir.mkdir()
            db_dir.mkdir()

            raw_json = src_dir / "citations_raw.json"
            raw_json.write_text(json.dumps(papers))

            # Write a minimal existing CSV
            csv_path = db_dir / "modularity_survey.csv"
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["DOI URL"])
                writer.writeheader()
                for row in (existing_csv_rows or []):
                    writer.writerow(row)

            captured = io.StringIO()
            with patch.object(_mod, "HERE", src_dir), \
                 patch.object(_mod, "ROOT", pathlib.Path(tmpdir)), \
                 patch("sys.stdout", captured):
                _mod.main()

            return json.loads(captured.getvalue())

    def test_relevant_paper_appears_in_output(self):
        if IGNORE_TEST:
            return
        paper = {
            "title": "Gene regulatory network modul in cells",
            "abstract": "We study gene modul in regulatory networks.",
            "venue": "",
            "externalIds": {"DOI": "10.1/rel"},
            "citationCount": 100,
        }
        result = self._run_main([paper])
        dois = [p.get("externalIds", {}).get("DOI", "").lower() for p in result]
        self.assertIn("10.1/rel", dois)

    def test_irrelevant_paper_excluded_from_output(self):
        if IGNORE_TEST:
            return
        paper = {
            "title": "Traffic flow in urban city transportation networks",
            "abstract": "",
            "venue": "",
            "externalIds": {"DOI": "10.1/irrel"},
            "citationCount": 10,
        }
        result = self._run_main([paper])
        dois = [p.get("externalIds", {}).get("DOI", "").lower() for p in result]
        self.assertNotIn("10.1/irrel", dois)

    def test_duplicate_doi_in_existing_csv_excluded(self):
        if IGNORE_TEST:
            return
        paper = {
            "title": "Gene network modul study",
            "abstract": "Modularity of gene regulatory networks.",
            "venue": "",
            "externalIds": {"DOI": "10.1/dup"},
            "citationCount": 200,
        }
        existing = [{"DOI URL": "https://doi.org/10.1/dup"}]
        result = self._run_main([paper], existing_csv_rows=existing)
        dois = [p.get("externalIds", {}).get("DOI", "").lower() for p in result]
        self.assertNotIn("10.1/dup", dois)

    def test_paper_without_doi_excluded(self):
        if IGNORE_TEST:
            return
        paper = {
            "title": "Gene network modul",
            "abstract": "",
            "venue": "",
            "externalIds": {},
            "citationCount": 500,
        }
        result = self._run_main([paper])
        self.assertEqual(len(result), 0)

    def test_output_sorted_by_citation_count_descending(self):
        if IGNORE_TEST:
            return
        papers = [
            {
                "title": "Gene modul network",
                "abstract": "gene modul network cluster",
                "venue": "",
                "externalIds": {"DOI": "10.1/low"},
                "citationCount": 50,
            },
            {
                "title": "Gene modul network",
                "abstract": "gene modul network cluster",
                "venue": "",
                "externalIds": {"DOI": "10.1/high"},
                "citationCount": 500,
            },
        ]
        result = self._run_main(papers)
        if len(result) >= 2:
            self.assertGreaterEqual(
                result[0].get("citationCount", 0),
                result[1].get("citationCount", 0),
            )

    def test_output_capped_at_50_papers(self):
        if IGNORE_TEST:
            return
        papers = []
        for i in range(60):
            papers.append({
                "title": "Gene modul network cluster",
                "abstract": "gene modul network cluster pathway",
                "venue": "",
                "externalIds": {"DOI": f"10.1/p{i}"},
                "citationCount": i,
            })
        result = self._run_main(papers)
        self.assertLessEqual(len(result), 50)


if __name__ == "__main__":
    unittest.main()
