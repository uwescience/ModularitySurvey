#!/usr/bin/env python3
"""
Three components:

1. search_for_pdf(title, authors) -> str | None
   Searches Semantic Scholar, then OpenAlex, then CrossRef + Unpaywall for an
   open-access PDF URL for the given paper title and author list.

2. get_abstracts_metadata() -> list[dict]
   Reads all .md files in db/abstracts/, extracts the "Title:" and "Authors:"
   header lines, and returns a list of dicts with keys: title, authors, filename.

3. main()
   Calls get_abstracts_metadata(), searches for each paper, and writes
   db/pdf_search_results.csv with columns: title, authors, pdf_url.
"""

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
ABSTRACTS_DIR = BASE_DIR / "db" / "abstracts"
OUTPUT_CSV = BASE_DIR / "db" / "pdf_search_results.csv"

EMAIL = "joseph.hellerstein@gmail.com"
USER_AGENT = f"ModularitySurveyBot/1.0 (mailto:{EMAIL})"
TITLE_MATCH_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------

def _fetch_json(url: str, timeout: int = 15) -> Optional[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _normalize(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def _titles_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return SequenceMatcher(None, _normalize(a), _normalize(b)).ratio() >= TITLE_MATCH_THRESHOLD


# ---------------------------------------------------------------------------
# Per-source search helpers
# ---------------------------------------------------------------------------

def _semantic_scholar_pdf(title: str) -> Optional[str]:
    """Return an OA PDF URL from Semantic Scholar, or None."""
    query = urllib.parse.quote(title)
    url = (
        f"https://api.semanticscholar.org/graph/v1/paper/search"
        f"?query={query}&fields=title,openAccessPdf&limit=3"
    )
    data = _fetch_json(url)
    if not data:
        return None
    for item in data.get("data", []):
        if _titles_match(title, item.get("title", "")):
            pdf = item.get("openAccessPdf") or {}
            if pdf.get("url"):
                return pdf["url"]
    return None


def _openalex_pdf(title: str) -> Optional[str]:
    """Return an OA URL from OpenAlex, or None."""
    query = urllib.parse.quote(title)
    url = (
        f"https://api.openalex.org/works"
        f"?search={query}&mailto={EMAIL}&per-page=3"
    )
    data = _fetch_json(url)
    if not data:
        return None
    for item in data.get("results", []):
        if _titles_match(title, item.get("display_name", "")):
            oa = item.get("open_access") or {}
            if oa.get("oa_url"):
                return oa["oa_url"]
    return None


def _crossref_doi(title: str) -> Optional[str]:
    """Return a DOI string via CrossRef title search, or None."""
    query = urllib.parse.quote(title)
    url = f"https://api.crossref.org/works?query.title={query}&rows=3"
    data = _fetch_json(url)
    if not data:
        return None
    for item in data.get("message", {}).get("items", []):
        cr_titles = item.get("title") or []
        cr_title = cr_titles[0] if cr_titles else ""
        if _titles_match(title, cr_title):
            return item.get("DOI")
    return None


def _unpaywall_pdf(doi: str) -> Optional[str]:
    """Return an OA PDF URL from Unpaywall for a known DOI, or None."""
    url = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL}"
    data = _fetch_json(url)
    if not data:
        return None
    best = data.get("best_oa_location") or {}
    if best.get("url_for_pdf"):
        return best["url_for_pdf"]
    for loc in data.get("oa_locations") or []:
        if loc.get("url_for_pdf"):
            return loc["url_for_pdf"]
    return None


# ---------------------------------------------------------------------------
# Public search function
# ---------------------------------------------------------------------------

def search_for_pdf(title: str, authors: str) -> Optional[str]:
    """
    Search for an open-access PDF URL for the paper identified by *title* and
    *authors*. Tries three sources in order:

      1. Semantic Scholar (direct OA PDF field)
      2. OpenAlex (open_access.oa_url)
      3. CrossRef (DOI lookup) → Unpaywall (PDF URL)

    Returns the first PDF URL found, or None if nothing is available.
    The *authors* parameter is accepted for future use (e.g., disambiguation)
    but the current implementation relies primarily on the title.
    """
    pdf_url = _semantic_scholar_pdf(title)
    if pdf_url:
        return pdf_url

    time.sleep(0.5)
    pdf_url = _openalex_pdf(title)
    if pdf_url:
        return pdf_url

    time.sleep(0.5)
    doi = _crossref_doi(title)
    if doi:
        pdf_url = _unpaywall_pdf(doi)
        if pdf_url:
            return pdf_url

    return None


# ---------------------------------------------------------------------------
# Abstract metadata reader
# ---------------------------------------------------------------------------

def get_abstracts_metadata() -> list:
    """
    Read all .md files in db/abstracts/ and return a list of dicts:
      {title: str, authors: str, filename: str}

    Only the first five lines of each file are scanned for the "Title:" and
    "Authors:" header lines. Files that lack either header are included with
    empty strings for the missing field.
    """
    records = []
    for path in sorted(ABSTRACTS_DIR.glob("*.md")):
        title = ""
        authors = ""
        with path.open(encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= 5:
                    break
                if line.startswith("Title: "):
                    title = line[7:].strip()
                elif line.startswith("Authors: "):
                    authors = line[9:].strip()
        records.append({"title": title, "authors": authors, "filename": path.name})
    return records


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search for OA PDF URLs for every paper in db/abstracts/."
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only process the first N abstracts."
    )
    parser.add_argument(
        "--delay", type=float, default=1.0,
        help="Extra seconds to sleep between papers (default 1.0)."
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_CSV,
        help=f"Path for the output CSV (default: {OUTPUT_CSV})."
    )
    args = parser.parse_args()

    records = get_abstracts_metadata()
    if args.limit:
        records = records[: args.limit]

    results = []
    total = len(records)
    for i, rec in enumerate(records, start=1):
        title = rec["title"]
        authors = rec["authors"]
        print(f"[{i}/{total}] {title[:70]}")
        pdf_url = search_for_pdf(title, authors)
        status = "found" if pdf_url else "not_found"
        print(f"        {status}: {pdf_url or '-'}")
        results.append({"title": title, "authors": authors, "pdf_url": pdf_url or ""})
        time.sleep(args.delay)

    output_path: Path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "authors", "pdf_url"])
        writer.writeheader()
        writer.writerows(results)

    found = sum(1 for r in results if r["pdf_url"])
    print()
    print(f"Results written to: {output_path}")
    print(f"PDF found:  {found}/{total}")
    print(f"Not found:  {total - found}/{total}")


if __name__ == "__main__":
    main()
