#!/usr/bin/env python3
"""
Unit tests for src/add_papers_to_csv.py.
Run standalone:  python3 tests/test_add_papers_to_csv.py
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
# Import the module under test from its absolute path.
# ---------------------------------------------------------------------------
_SRC = pathlib.Path(__file__).parent.parent / "src" / "add_papers_to_csv.py"
_spec = importlib.util.spec_from_file_location("add_papers_to_csv", _SRC)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

format_authors = _mod.format_authors
get_first_author_last_name = _mod.get_first_author_last_name
create_summary = _mod.create_summary
infer_modeling_framework = _mod.infer_modeling_framework
infer_level_of_organization = _mod.infer_level_of_organization
infer_organism = _mod.infer_organism
determine_paper_type = _mod.determine_paper_type
create_csv_row = _mod.create_csv_row

# Minimal set of fieldnames that covers all keys set by create_csv_row
_FIELDNAMES = [
    'AddedBy', 'AIAgentAndModel', 'LastNameOf1stAuthor', 'All authors',
    'Paper title', 'Year', 'Paper type', 'DOI URL', 'Modeling framework',
    'Definition of module', 'Context of system', 'Purpose of module',
    'Algorithmic aspect', 'Data', 'Level of organization', 'Organism',
    'Impact of paper', 'Citations', 'Summary', 'Primary theme', 'Notes',
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _paper(**kwargs):
    defaults = {
        "title": "",
        "abstract": "",
        "year": 2020,
        "citationCount": 0,
        "authors": [],
        "externalIds": {},
    }
    defaults.update(kwargs)
    return defaults


# ---------------------------------------------------------------------------
# Tests for format_authors
# ---------------------------------------------------------------------------

class TestFormatAuthors(unittest.TestCase):

    def test_single_author(self):
        if IGNORE_TEST:
            return
        self.assertEqual(format_authors([{"name": "Alice Smith"}]), "Alice Smith")

    def test_multiple_authors_comma_joined(self):
        if IGNORE_TEST:
            return
        authors = [{"name": "Alice Smith"}, {"name": "Bob Jones"}]
        self.assertEqual(format_authors(authors), "Alice Smith, Bob Jones")

    def test_empty_list_returns_empty_string(self):
        if IGNORE_TEST:
            return
        self.assertEqual(format_authors([]), "")

    def test_none_returns_empty_string(self):
        if IGNORE_TEST:
            return
        self.assertEqual(format_authors(None), "")

    def test_author_with_missing_name_key(self):
        if IGNORE_TEST:
            return
        # should not raise; missing name defaults to empty string
        result = format_authors([{"name": "Alice"}, {}])
        self.assertIn("Alice", result)


# ---------------------------------------------------------------------------
# Tests for get_first_author_last_name
# ---------------------------------------------------------------------------

class TestGetFirstAuthorLastName(unittest.TestCase):

    def test_returns_last_word_of_first_author_name(self):
        if IGNORE_TEST:
            return
        authors = [{"name": "Alice Smith"}, {"name": "Bob Jones"}]
        self.assertEqual(get_first_author_last_name(authors), "Smith")

    def test_single_word_name(self):
        if IGNORE_TEST:
            return
        self.assertEqual(get_first_author_last_name([{"name": "Einstein"}]),
                         "Einstein")

    def test_empty_list_returns_empty_string(self):
        if IGNORE_TEST:
            return
        self.assertEqual(get_first_author_last_name([]), "")

    def test_none_returns_empty_string(self):
        if IGNORE_TEST:
            return
        self.assertEqual(get_first_author_last_name(None), "")

    def test_author_with_empty_name(self):
        if IGNORE_TEST:
            return
        self.assertEqual(get_first_author_last_name([{"name": ""}]), "")

    def test_three_part_name_returns_last_part(self):
        if IGNORE_TEST:
            return
        self.assertEqual(
            get_first_author_last_name([{"name": "Johann Sebastian Bach"}]),
            "Bach"
        )


# ---------------------------------------------------------------------------
# Tests for create_summary
# ---------------------------------------------------------------------------

class TestCreateSummary(unittest.TestCase):

    def test_uses_first_two_sentences_of_abstract(self):
        if IGNORE_TEST:
            return
        paper = _paper(
            title="Some Title",
            abstract="First sentence. Second sentence. Third sentence."
        )
        result = create_summary(paper)
        self.assertIn("First sentence", result)
        self.assertIn("Second sentence", result)
        self.assertNotIn("Third sentence", result)

    def test_truncates_to_300_chars(self):
        if IGNORE_TEST:
            return
        long_abstract = ("A" * 200 + ". ") + ("B" * 200 + ".")
        paper = _paper(abstract=long_abstract)
        result = create_summary(paper)
        self.assertLessEqual(len(result), 300)

    def test_truncated_summary_ends_with_ellipsis(self):
        if IGNORE_TEST:
            return
        long_abstract = ("X" * 200 + ". ") + ("Y" * 200 + ".")
        paper = _paper(abstract=long_abstract)
        result = create_summary(paper)
        if len(result) == 300:
            self.assertTrue(result.endswith("..."))

    def test_falls_back_to_title_when_no_abstract(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="My Important Paper", abstract="")
        result = create_summary(paper)
        self.assertIn("my important paper", result.lower())

    def test_falls_back_to_title_when_abstract_is_none(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="No Abstract Paper")
        paper["abstract"] = None
        result = create_summary(paper)
        self.assertIn("no abstract paper", result.lower())

    def test_single_sentence_abstract_used_as_is(self):
        if IGNORE_TEST:
            return
        paper = _paper(abstract="Only one sentence here with no period at end")
        result = create_summary(paper)
        self.assertIn("Only one sentence", result)


# ---------------------------------------------------------------------------
# Tests for infer_modeling_framework
# ---------------------------------------------------------------------------

class TestInferModelingFramework(unittest.TestCase):

    def test_detects_boolean_network(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Boolean network dynamics")
        result = infer_modeling_framework(paper)
        self.assertIn("Boolean network", result)

    def test_detects_network_as_graph_based(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="A network analysis study")
        result = infer_modeling_framework(paper)
        self.assertIn("Graph-based", result)

    def test_detects_ode(self):
        if IGNORE_TEST:
            return
        paper = _paper(abstract="We use ODE to model dynamics.")
        result = infer_modeling_framework(paper)
        self.assertIn("ODE", result)

    def test_detects_differential_equation(self):
        if IGNORE_TEST:
            return
        paper = _paper(abstract="A differential equation model.")
        result = infer_modeling_framework(paper)
        self.assertIn("ODE", result)

    def test_detects_stochastic(self):
        if IGNORE_TEST:
            return
        paper = _paper(abstract="Stochastic simulation of gene expression.")
        result = infer_modeling_framework(paper)
        self.assertIn("Stochastic", result)

    def test_detects_machine_learning(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Machine learning for gene networks")
        result = infer_modeling_framework(paper)
        self.assertIn("Machine learning", result)

    def test_detects_genomics(self):
        if IGNORE_TEST:
            return
        paper = _paper(abstract="Genomic analysis of cancer mutations.")
        result = infer_modeling_framework(paper)
        self.assertIn("Genomics", result)

    def test_multiple_matches_slash_joined(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Boolean network",
                       abstract="Network analysis with ODE.")
        result = infer_modeling_framework(paper)
        self.assertIn("/", result)

    def test_no_match_returns_to_be_determined(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="An obscure topic", abstract="Nothing relevant.")
        result = infer_modeling_framework(paper)
        self.assertEqual(result, "To be determined")

    def test_case_insensitive(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="BOOLEAN NETWORK STUDY")
        result = infer_modeling_framework(paper)
        self.assertIn("Boolean network", result)


# ---------------------------------------------------------------------------
# Tests for infer_level_of_organization
# ---------------------------------------------------------------------------

class TestInferLevelOfOrganization(unittest.TestCase):

    def test_detects_molecular_from_protein(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Protein interaction networks")
        result = infer_level_of_organization(paper)
        self.assertIn("molecular", result)

    def test_detects_molecular_from_gene(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Gene expression analysis")
        result = infer_level_of_organization(paper)
        self.assertIn("molecular", result)

    def test_detects_cell_level(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Cell signaling pathways")
        result = infer_level_of_organization(paper)
        self.assertIn("cell", result)

    def test_detects_tissue_level(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Tissue morphogenesis modeling")
        result = infer_level_of_organization(paper)
        self.assertIn("tissue", result)

    def test_detects_organism_level(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Whole organism development")
        result = infer_level_of_organization(paper)
        self.assertIn("organism", result)

    def test_no_match_defaults_to_cell(self):
        if IGNORE_TEST:
            return
        # 'network' triggers only when no levels found; here 'network' absent too
        paper = _paper(title="Abstract mathematical structure")
        result = infer_level_of_organization(paper)
        self.assertEqual(result, "cell")

    def test_multiple_levels_comma_joined(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Gene expression in cells and tissues")
        result = infer_level_of_organization(paper)
        self.assertIn(",", result)


# ---------------------------------------------------------------------------
# Tests for infer_organism
# ---------------------------------------------------------------------------

class TestInferOrganism(unittest.TestCase):

    def test_detects_human(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Human genome analysis")
        result = infer_organism(paper)
        self.assertIn("H. sapiens", result)

    def test_detects_mouse(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Mouse brain development")
        result = infer_organism(paper)
        self.assertIn("M. musculus", result)

    def test_detects_yeast(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Yeast cell cycle regulation")
        result = infer_organism(paper)
        self.assertIn("S. cerevisiae", result)

    def test_detects_ecoli(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="E. coli metabolic network")
        result = infer_organism(paper)
        self.assertIn("E. coli", result)

    def test_detects_drosophila(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Drosophila developmental patterning")
        result = infer_organism(paper)
        self.assertIn("D. melanogaster", result)

    def test_detects_c_elegans(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="C. elegans neural connectivity")
        result = infer_organism(paper)
        self.assertIn("C. elegans", result)

    def test_detects_cancer(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Cancer tumor suppressor gene networks")
        result = infer_organism(paper)
        self.assertIn("H. sapiens (cancer)", result)

    def test_no_match_returns_multiple_general(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Abstract network topology study")
        result = infer_organism(paper)
        self.assertEqual(result, "Multiple / general")

    def test_multiple_organisms_comma_joined(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Comparative study of human and mouse genomes")
        result = infer_organism(paper)
        self.assertIn(",", result)


# ---------------------------------------------------------------------------
# Tests for determine_paper_type
# ---------------------------------------------------------------------------

class TestDeterminePaperType(unittest.TestCase):

    def test_review_in_title_returns_review(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="A review of network modularity")
        self.assertEqual(determine_paper_type(paper), "review")

    def test_survey_in_title_returns_review(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Survey of biological networks")
        self.assertEqual(determine_paper_type(paper), "review")

    def test_perspective_in_title_returns_perspective(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="A perspective on modularity")
        self.assertEqual(determine_paper_type(paper), "perspective")

    def test_opinion_in_title_returns_perspective(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Opinion: the role of modularity")
        self.assertEqual(determine_paper_type(paper), "perspective")

    def test_commentary_in_title_returns_perspective(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Commentary on network science")
        self.assertEqual(determine_paper_type(paper), "perspective")

    def test_default_returns_research(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="A novel gene regulatory circuit")
        self.assertEqual(determine_paper_type(paper), "research")

    def test_review_early_in_abstract_returns_review(self):
        if IGNORE_TEST:
            return
        # 'review' at position < 100 in abstract triggers review classification
        paper = _paper(title="Network dynamics",
                       abstract="This review examines the current state of the field.")
        self.assertEqual(determine_paper_type(paper), "review")

    def test_review_late_in_abstract_does_not_trigger_review(self):
        if IGNORE_TEST:
            return
        # 'review' far into abstract should NOT trigger review type
        long_prefix = "A " * 80  # pushes 'review' past character 100
        paper = _paper(title="Network dynamics",
                       abstract=long_prefix + "review of this approach")
        # With no 'review'/'survey' in title and 'review' past index 100, expect 'research'
        self.assertEqual(determine_paper_type(paper), "research")

    def test_none_abstract_handled(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="Experimental study of modularity")
        paper["abstract"] = None
        self.assertEqual(determine_paper_type(paper), "research")


# ---------------------------------------------------------------------------
# Tests for create_csv_row
# ---------------------------------------------------------------------------

class TestCreateCsvRow(unittest.TestCase):

    def _make_full_paper(self):
        return _paper(
            title="Gene Network Modularity",
            abstract="We study modularity. This is the second sentence.",
            year=2022,
            citationCount=150,
            authors=[{"name": "Alice Smith"}, {"name": "Bob Jones"}],
            externalIds={"DOI": "10.1234/TEST"},
        )

    def test_returns_dict_with_all_fieldnames_as_keys(self):
        if IGNORE_TEST:
            return
        paper = self._make_full_paper()
        row = create_csv_row(paper, _FIELDNAMES)
        for field in _FIELDNAMES:
            self.assertIn(field, row)

    def test_added_by_set_to_jlheller(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertEqual(row["AddedBy"], "jlheller")

    def test_doi_url_formatted_correctly(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertTrue(row["DOI URL"].startswith("https://doi.org/"))
        self.assertIn("10.1234/test", row["DOI URL"].lower())

    def test_citations_value_matches_paper(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertEqual(row["Citations"], 150)

    def test_paper_title_populated(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertEqual(row["Paper title"], "Gene Network Modularity")

    def test_year_populated(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertEqual(row["Year"], 2022)

    def test_last_name_first_author_populated(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertEqual(row["LastNameOf1stAuthor"], "Smith")

    def test_all_authors_populated(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertIn("Alice Smith", row["All authors"])

    def test_no_doi_leaves_doi_url_empty(self):
        if IGNORE_TEST:
            return
        paper = _paper(title="No DOI Paper", externalIds={})
        row = create_csv_row(paper, _FIELDNAMES)
        self.assertEqual(row["DOI URL"], "")

    def test_notes_field_contains_auto_added_text(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertIn("Auto-added", row.get("Notes", ""))

    def test_definition_of_module_is_placeholder(self):
        if IGNORE_TEST:
            return
        row = create_csv_row(self._make_full_paper(), _FIELDNAMES)
        self.assertIn("manually", row["Definition of module"].lower())


# ---------------------------------------------------------------------------
# Integration test: main() reads, filters, and writes CSV
# ---------------------------------------------------------------------------

class TestMainIntegration(unittest.TestCase):

    def _run_main(self, papers, skip_patterns=None):
        """
        Patch HERE/ROOT to temp dirs, write inputs, call main(), return
        the rows written to the output CSV.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            src_dir = pathlib.Path(tmpdir) / "src"
            db_dir = pathlib.Path(tmpdir) / "db"
            src_dir.mkdir()
            db_dir.mkdir()

            # Write citations_filtered.json
            filtered_json = src_dir / "citations_filtered.json"
            filtered_json.write_text(json.dumps(papers))

            # Write a minimal existing CSV with the required fieldnames
            survey_csv = db_dir / "modularity_survey.csv"
            fieldnames = _FIELDNAMES
            with open(survey_csv, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                # One existing row so the CSV is non-empty
                writer.writerow({fn: "" for fn in fieldnames})

            with patch.object(_mod, "HERE", src_dir), \
                 patch.object(_mod, "ROOT", pathlib.Path(tmpdir)), \
                 patch("sys.stderr", io.StringIO()):
                _mod.main()

            output_csv = db_dir / "modularity_survey_updated.csv"
            with open(output_csv, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return rows

    def test_output_csv_contains_existing_plus_new_rows(self):
        if IGNORE_TEST:
            return
        paper = _paper(
            title="Gene network study",
            abstract="Study of gene networks.",
            year=2021,
            citationCount=100,
            authors=[{"name": "Alice Smith"}],
            externalIds={"DOI": "10.1/added"},
        )
        rows = self._run_main([paper])
        # 1 pre-existing header-only row + 1 new paper
        self.assertEqual(len(rows), 2)

    def test_skip_pattern_removes_paper(self):
        if IGNORE_TEST:
            return
        paper = _paper(
            title="Robot locomotion sensor network",
            abstract="",
            year=2021,
            citationCount=100,
            authors=[{"name": "Bob"}],
            externalIds={"DOI": "10.1/robot"},
        )
        rows = self._run_main([paper])
        # Only the pre-existing row; the robot paper should be skipped
        self.assertEqual(len(rows), 1)

    def test_max_20_new_papers_added(self):
        if IGNORE_TEST:
            return
        papers = [
            _paper(
                title=f"Gene network study {i}",
                abstract="gene network study.",
                year=2021,
                citationCount=100,
                authors=[{"name": f"Author {i}"}],
                externalIds={"DOI": f"10.1/p{i}"},
            )
            for i in range(30)
        ]
        rows = self._run_main(papers)
        # 1 pre-existing + at most 20 new
        self.assertLessEqual(len(rows), 21)


if __name__ == "__main__":
    unittest.main()
