"""
Scores papers against the axes of biological modularity described in the note
"Axes for Defining Biological Modularity" (Traits, Networks, Functions, plus the
evolutionary-trajectory and hierarchy operators). The method is described in
axes/axes_analysis.md.

Each axis has a lexicon of keywords/phrases derived from the examples cited in
the note. A paper's text (title + "Definition of module" + Summary + abstract
from db/abstracts, or else the first page of the PDF in db/papers) is matched
against each lexicon. The raw score for an axis is the number of distinct lexicon
entries found; it is scaled to [0, 100] by dividing by SATURATION.

Scores from a closer reading of a paper can override keyword scores. They are
kept in an adjustments CSV (DOI, one column per axis/operator, notes); a blank
cell keeps the keyword score.

Usage:
  python src/classify_axes.py DOI [DOI ...]
  python src/classify_axes.py --file dois.txt
  python src/classify_axes.py --highly-relevant --adjustments axes/axis_adjustments.csv \\
      --output axes/highly_relevant_axis_scores.csv

Output (default axes/axis_keyword_scores.csv): one row per paper with per-axis
keyword counts, 0-100 scores, matched terms, and final scores and notes.
"""

import argparse
import csv
import re
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
BIB_PATH = BASE_DIR / "db" / "bibliography.csv"
ABSTRACTS_DIR = BASE_DIR / "db" / "abstracts"
PAPERS_DIR = BASE_DIR / "db" / "papers"
OUTPUT_PATH = BASE_DIR / "axes" / "axis_keyword_scores.csv"

# Entries are regular expressions matched case-insensitively at a word start.
AXES = ["traits", "networks", "functions"]
OPERATORS = ["evolution", "hierarchy"]
LEXICON = {
    # Elements (individuals/species) carrying traits; module = set of traits shared/covarying.
    # Examples: lanternfish (evo.12743), marine microbial communities (cub.2019.03.047),
    # mammalian backbone (s12862-018-1282-2).
    "traits": [
        r"traits?\b", r"phenotypic (integration|variation|trait)", r"morpholog",
        r"morphometric", r"geometric morphometric", r"landmarks?", r"shape (variation|evolution|diversity)",
        r"(morphological|phenotypic) integration", r"covariation", r"covariance", r"co-?var(y|ies|ying)",
        r"evolutionary rates?", r"rates? of (morphological )?evolution", r"disparity",
        r"skull", r"crani", r"mandib", r"vertebra", r"backbone", r"skelet", r"limbs?\b", r"teeth|dental",
        r"anatomical", r"body plan", r"phylogenetic comparative", r"phylogenetic signal",
        r"variational modul", r"species composition", r"guilds?\b", r"community assembly",
        r"taxa\b", r"allometr",
    ],
    # Nodes and links; module = subgraph more densely connected internally than externally.
    # Examples: Newman complex networks review (S003614450342480), gene knockout interaction
    # network (lsa.201800278).
    "networks": [
        r"networks?\b", r"nodes?\b", r"edges?\b", r"links?\b", r"graphs?\b", r"subgraph", r"subnetwork",
        r"community structure", r"community detection", r"protein communities", r"densely (inter)?connected",
        r"hubs?\b", r"connector", r"clustering coefficient", r"degree distribution", r"scale-free",
        r"power-law", r"small-world", r"modularity (score|index|q)\b", r"interaction network",
        r"protein[- ]protein interaction", r"interactome", r"genetic interaction", r"co-?expression network",
        r"co-?occurrence network", r"connectome", r"connectivity", r"markov clustering", r"topolog",
        r"wiring diagram", r"nestedness", r"intermodule|between-module", r"keystone",
    ],
    # Elements transformed by functions with inputs/outputs/internals; module = recurring function.
    # Examples: LRR synaptic adhesion proteins (neuron.2018.06.026), ribosome-demand controller
    # (s41467-018-07899-z), miRNA -> protein translation (compbiomed.2019.103380).
    "functions": [
        r"inputs?\b", r"outputs?\b", r"input[- ]output", r"pathways?\b", r"metabolic pathway",
        r"biosynth", r"enzym", r"catalytic", r"reactions?\b", r"(gene|genetic|synthetic) circuits?",
        r"circuits?\b", r"cassettes?", r"devices?\b", r"insulat", r"retroactivity", r"\bload\b",
        r"context[- ]dependen", r"resource (competition|demand)", r"ribosom", r"compos(e|able|ition|ing)",
        r"plug-and-play", r"building blocks?", r"reusab", r"protein complex", r"transcription",
        r"translation", r"(gene )?expression", r"mirna", r"signal(l)?ing", r"decod", r"controller",
        r"feedback", r"combinatorial", r"glycolysis", r"co-?essential", r"microcompartment",
    ],
    # Operator: evolutionary trajectory of the objects of an axis over time/space.
    "evolution": [
        r"evolution", r"evolv", r"phylogen", r"lineages?\b", r"speciation", r"duplication",
        r"selection", r"ontogen", r"development", r"over time", r"trajector", r"radiation",
        r"domestication", r"million years|\bmy\b",
    ],
    # Operator: nested objects (modules within modules, multiple scales).
    "hierarchy": [
        r"hierarch", r"nested", r"multi-?scale", r"multi-?level", r"multi-?layer",
        r"levels? of (biological )?organi[sz]ation", r"sub-?modules?", r"higher-order",
    ],
}
COMPILED = {k: [(p, re.compile(r"\b" + p, re.IGNORECASE)) for p in v] for k, v in LEXICON.items()}
# Number of distinct matched entries that earns a score of 100.
SATURATION = {"traits": 10, "networks": 10, "functions": 10, "evolution": 6, "hierarchy": 4}
# Output column names for the final scores.
SCORE_COLUMNS = {
    "traits": "trait_score",
    "networks": "network_score",
    "functions": "function_score",
    "evolution": "evolution_trajectory_score",
    "hierarchy": "hierarchy_score",
}
HYPER_RATIO = 0.6  # second axis within this fraction of the top axis => candidate hyper module
MIN_HYPER_SCORE = 4


def normalize_doi(doi: str) -> str:
    return doi.strip().replace("https://doi.org/", "").lower()


def load_bibliography() -> dict:
    """Maps lower-cased DOI to its first bibliography row."""
    rows = {}
    with open(BIB_PATH, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            rows.setdefault(normalize_doi(row.get("DOI URL", "")), row)
    return rows


def highly_relevant_dois(bib: dict) -> list:
    """DOIs whose Relevancy starts with 'Highly relevant', in bibliography order."""
    return [doi for doi, row in bib.items()
            if doi and row.get("Relevancy", "").strip().lower().startswith("highly relevant")]


def find_file(directory: Path, doi: str, suffix: str):
    name = (doi.replace("/", "_") + suffix).lower()
    matches = [p for p in directory.glob("*" + suffix) if p.name.lower() == name]
    return matches[0] if matches else None


def pdf_first_page(path: Path) -> str:
    try:
        result = subprocess.run(["pdftotext", "-l", "1", str(path), "-"],
                                capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


def paper_text(row: dict, doi: str) -> tuple:
    """Returns (text, source) where source names the extra text used beyond the bibliography row."""
    parts = [row.get("Paper title", ""), row.get("Definition of module", ""), row.get("Summary", "")]
    source = "bibliography"
    abstract = find_file(ABSTRACTS_DIR, doi, ".md")
    if abstract:
        parts.append(abstract.read_text(encoding="utf-8"))
        source = "abstract"
    else:
        pdf = find_file(PAPERS_DIR, doi, ".pdf")
        text = pdf_first_page(pdf) if pdf else ""
        if text:
            parts.append(text)
            source = "pdf"
    return "\n".join(parts), source


def score_text(text: str) -> dict:
    """Returns {axis_or_operator: [matched lexicon entries]}."""
    return {k: [p for p, rx in pats if rx.search(text)] for k, pats in COMPILED.items()}


def scale(key: str, count: int) -> int:
    return round(100 * min(1.0, count / SATURATION[key]))


def classify(matches: dict) -> tuple:
    """Returns (primary axis, hyper-module axes or '')."""
    scores = sorted(((len(matches[a]), a) for a in AXES), reverse=True)
    primary = scores[0][1]
    hyper = [a for s, a in scores if s >= MIN_HYPER_SCORE and s >= HYPER_RATIO * scores[0][0]]
    return primary, "+".join(hyper) if len(hyper) > 1 else ""


def load_adjustments(path) -> dict:
    """Maps DOI to {score column or 'notes': value} for non-blank cells."""
    if not path:
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {normalize_doi(r["DOI"]): {k: v.strip() for k, v in r.items() if k != "DOI" and v and v.strip()}
                for r in csv.DictReader(f)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dois", nargs="*")
    parser.add_argument("--file", help="file with one DOI per line")
    parser.add_argument("--highly-relevant", action="store_true", help="score all 'Highly relevant' papers")
    parser.add_argument("--adjustments", help="CSV of reading-based score overrides and notes")
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()
    bib = load_bibliography()
    dois = list(args.dois)
    if args.file:
        dois += [l.strip() for l in Path(args.file).read_text().splitlines() if l.strip()]
    if args.highly_relevant:
        dois += highly_relevant_dois(bib)
    adjustments = load_adjustments(args.adjustments)
    fields = (["paper title", "DOI"] + list(SCORE_COLUMNS.values()) + ["notes", "auto_primary", "auto_hyper", "text_source"]
              + [f"{k}_keyword_score" for k in LEXICON] + [f"{k}_terms" for k in LEXICON])
    seen = set()
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for doi in dois:
            key = normalize_doi(doi)
            if key in seen:
                continue
            seen.add(key)
            row = bib.get(key)
            if row is None:
                print(f"Not in bibliography: {doi}")
                continue
            text, source = paper_text(row, key)
            matches = score_text(text)
            primary, hyper = classify(matches)
            adjust = adjustments.get(key, {})
            out = {"paper title": row.get("Paper title", ""), "DOI": key, "auto_primary": primary,
                   "auto_hyper": hyper, "text_source": source, "notes": adjust.get("notes", "")}
            for k, terms in matches.items():
                out[f"{k}_keyword_score"] = scale(k, len(terms))
                out[f"{k}_terms"] = "; ".join(terms)
                out[SCORE_COLUMNS[k]] = int(adjust.get(SCORE_COLUMNS[k], out[f"{k}_keyword_score"]))
            writer.writerow(out)
    print(f"Wrote {args.output} ({len(seen)} papers)")


if __name__ == "__main__":
    main()
