"""
Downloads papers (or abstracts, as a fallback) for every row in db/bibliography.csv,
using the "DOI URL" column to locate content.

Strategy per row:
  1. Resolve the DOI via Crossref (sanity check + title cross-reference).
  2. Try Unpaywall for a legal open-access PDF; download it if found.
  3. If no OA PDF, fall back to an abstract from Semantic Scholar, then OpenAlex.
  4. If nothing is found, record why (missing DOI, DOI doesn't resolve, DOI resolves
     to a different title than the bibliography row, or no content available).

Output:
  db/papers/<doi>.pdf       - downloaded full papers
  db/abstracts/<doi>.md     - downloaded abstracts
  db/download_log.csv       - one row per bibliography entry with the outcome
"""

# TODO: Create a csv that maps paper title to paper name

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
BIB_PATH = BASE_DIR / "db" / "bibliography.csv"
PAPERS_DIR = BASE_DIR / "db" / "papers"
ABSTRACTS_DIR = BASE_DIR / "db" / "abstracts"
LOG_PATH = BASE_DIR / "db" / "download_log.csv"

EMAIL = "joseph.hellerstein@gmail.com"
USER_AGENT = f"ModularitySurveyBot/1.0 (mailto:{EMAIL})"
TITLE_MATCH_THRESHOLD = 0.6


def sanitize_doi(doi_url: str) -> str:
    doi = doi_url.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi.strip().strip("/")


def safe_filename(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", doi)


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def titles_match(a: str, b: str) -> bool:
    if not a or not b:
        return True  # nothing to compare against, don't flag a mismatch
    ratio = SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()
    return ratio >= TITLE_MATCH_THRESHOLD


def fetch_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def fetch_bytes(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def crossref_lookup(doi: str):
    """Return the Crossref title for this DOI, or None if it doesn't resolve."""
    url = f"https://api.crossref.org/works/{doi}"
    try:
        data = fetch_json(url)
    except Exception:
        return None
    titles = data.get("message", {}).get("title")
    return titles[0] if titles else ""


def unpaywall_pdf_url(doi: str):
    url = f"https://api.unpaywall.org/v2/{doi}?email={EMAIL}"
    try:
        data = fetch_json(url)
    except Exception:
        return None
    best = data.get("best_oa_location") or {}
    if best.get("url_for_pdf"):
        return best["url_for_pdf"]
    if best.get("url"):
        return best["url"]
    for loc in data.get("oa_locations") or []:
        if loc.get("url_for_pdf"):
            return loc["url_for_pdf"]
    return None


def semantic_scholar_abstract(doi: str):
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=abstract"
    try:
        data = fetch_json(url)
    except Exception:
        return None
    return data.get("abstract") or None


def openalex_abstract(doi: str):
    url = f"https://api.openalex.org/works/doi:{doi}?mailto={EMAIL}"
    try:
        data = fetch_json(url)
    except Exception:
        return None
    inv = data.get("abstract_inverted_index")
    if not inv:
        return None
    positions = {}
    for word, idxs in inv.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def process_row(row_num: int, doi_url: str, bib_title: str) -> dict:
    result = {
        "row": row_num,
        "title": bib_title,
        "doi": doi_url,
        "status": None,
        "detail": "",
    }

    if not doi_url or not doi_url.strip():
        result["status"] = "missing_doi"
        return result

    doi = sanitize_doi(doi_url)
    fname = safe_filename(doi)

    crossref_title = crossref_lookup(doi)
    if crossref_title is None:
        result["status"] = "invalid_doi"
        result["detail"] = "DOI does not resolve via Crossref"
        return result

    if not titles_match(bib_title, crossref_title):
        result["status"] = "doi_title_mismatch"
        result["detail"] = f"Crossref title: {crossref_title!r}"
        # Still try to fetch content for the *actual* paper at this DOI,
        # since it may simply be a metadata error in the bibliography row.

    pdf_url = unpaywall_pdf_url(doi)
    if pdf_url:
        try:
            content, content_type = fetch_bytes(pdf_url)
            if "pdf" in content_type.lower() or pdf_url.lower().endswith(".pdf"):
                out_path = PAPERS_DIR / f"{fname}.pdf"
                out_path.write_bytes(content)
                if result["status"] != "doi_title_mismatch":
                    result["status"] = "paper_downloaded"
                result["detail"] = (result["detail"] + f" | saved {out_path}").strip(" |")
                return result
        except Exception:
            pass  # fall through to abstract

    abstract = semantic_scholar_abstract(doi) or openalex_abstract(doi)
    if abstract:
        out_path = ABSTRACTS_DIR / f"{fname}.md"
        out_path.write_text(abstract, encoding="utf-8")
        if result["status"] != "doi_title_mismatch":
            result["status"] = "abstract_downloaded"
        result["detail"] = (result["detail"] + f" | saved {out_path}").strip(" |")
        return result

    if result["status"] != "doi_title_mismatch":
        result["status"] = "no_content_found"
        result["detail"] = "DOI resolves but no OA PDF or abstract was found"
    return result


def already_done(doi_url: str):
    if not doi_url or not doi_url.strip():
        return None
    fname = safe_filename(sanitize_doi(doi_url))
    if (PAPERS_DIR / f"{fname}.pdf").exists():
        return "paper_downloaded"
    if (ABSTRACTS_DIR / f"{fname}.md").exists():
        return "abstract_downloaded"
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Download papers/abstracts for bibliography rows via DOI."
    )
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N rows.")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds to sleep between rows.")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                         help="Skip rows whose paper/abstract is already downloaded (default on).")
    args = parser.parse_args()

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    ABSTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(BIB_PATH, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if args.limit:
        rows = rows[: args.limit]

    results = []
    for i, row in enumerate(rows):
        row_num = i + 2  # account for the header line
        doi_url = row.get("DOI URL", "")
        title = row.get("Paper title", "")

        if args.skip_existing:
            existing = already_done(doi_url)
            if existing:
                results.append({"row": row_num, "title": title, "doi": doi_url,
                                 "status": existing, "detail": "already present"})
                print(f"[{i+1}/{len(rows)}] row {row_num}: {existing} (cached) — {title[:60]}")
                continue

        result = process_row(row_num, doi_url, title)
        results.append(result)
        print(f"[{i+1}/{len(rows)}] row {row_num}: {result['status']} — {title[:60]}")

        time.sleep(args.delay)

    with open(LOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["row", "title", "doi", "status", "detail"])
        writer.writeheader()
        writer.writerows(results)

    counts = Counter(r["status"] for r in results)
    print()
    print("Summary")
    print("-------")
    print(f"Papers downloaded:        {counts.get('paper_downloaded', 0)}")
    print(f"Abstracts downloaded:     {counts.get('abstract_downloaded', 0)}")
    print(f"Missing DOI:              {counts.get('missing_doi', 0)}")
    print(f"Invalid DOI (no resolve): {counts.get('invalid_doi', 0)}")
    print(f"DOI/title mismatch:       {counts.get('doi_title_mismatch', 0)}")
    print(f"No content found:        {counts.get('no_content_found', 0)}")
    print(f"\nFull log written to: {LOG_PATH}")


if __name__ == "__main__":
    main()
