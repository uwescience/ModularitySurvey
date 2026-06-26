"""
Downloads PDFs listed in db/pdf_search_results.csv.

Naming strategy (same convention as paper_url_finder.py):
  1. Extract a DOI from the pdf_url (doi.org link or embedded 10.XXXX pattern).
  2. If no DOI in the URL, match the title against db/bibliography.csv to find one.
  3. Fall back to a title-derived slug.
  Then sanitize_doi() + safe_filename() produce the final <name>.pdf path.

Output:
  db/papers/<name>.pdf               – downloaded PDFs
  db/pdf_download_failures.csv       – one row per failure with reason
"""

import csv
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
RESULTS_PATH = BASE_DIR / "db" / "pdf_search_results.csv"
BIB_PATH = BASE_DIR / "db" / "bibliography.csv"
PAPERS_DIR = BASE_DIR / "db" / "papers"
FAILURES_PATH = BASE_DIR / "db" / "pdf_download_failures.csv"

EMAIL = "joseph.hellerstein@gmail.com"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
DOI_PATTERN = re.compile(r"(10\.\d{4,}/[^\s,\"'<>]+)")
TITLE_MATCH_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# Naming helpers (mirrors paper_url_finder.py)
# ---------------------------------------------------------------------------

def sanitize_doi(doi_url: str) -> str:
    doi = doi_url.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi.strip().strip("/")


def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def title_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    return slug[:80]


def extract_doi_from_url(url: str) -> Optional[str]:
    """Return the first DOI found in *url*, or None."""
    m = DOI_PATTERN.search(url)
    return m.group(1).rstrip(".,)") if m else None


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def titles_match(a: str, b: str) -> bool:
    if not a or not b:
        return False
    ratio = SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()
    return ratio >= TITLE_MATCH_THRESHOLD


# ---------------------------------------------------------------------------
# Bibliography title → DOI index
# ---------------------------------------------------------------------------

def load_bib_title_doi(bib_path: Path) -> dict:
    index: dict = {}
    if not bib_path.exists():
        return index
    with open(bib_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            title = row.get("Paper title", "").strip()
            doi_url = row.get("DOI URL", "").strip()
            if title and doi_url:
                index[normalize_title(title)] = doi_url
    return index


def lookup_doi_by_title(title: str, index: dict) -> Optional[str]:
    norm = normalize_title(title)
    # exact match first
    if norm in index:
        return index[norm]
    # fuzzy fallback
    best_ratio, best_doi = 0.0, None
    for idx_title, doi_url in index.items():
        r = SequenceMatcher(None, norm, idx_title).ratio()
        if r > best_ratio:
            best_ratio, best_doi = r, doi_url
    return best_doi if best_ratio >= TITLE_MATCH_THRESHOLD else None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def fetch_bytes(url: str, timeout: int = 30) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/pdf,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def is_pdf_content(content: bytes, content_type: str, url: str) -> bool:
    if "pdf" in content_type.lower():
        return True
    if url.lower().endswith(".pdf"):
        return True
    # PDF magic bytes
    return content[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Download attempt
# ---------------------------------------------------------------------------

def try_download(url: str) -> tuple:
    """
    Attempt to fetch a PDF from *url*.
    Returns (bytes, content_type) on success, or (None, reason_string) on failure.
    """
    try:
        content, ct = fetch_bytes(url)
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, f"URLError: {e.reason}"
    except Exception as e:
        return None, f"Error: {e}"

    if is_pdf_content(content, ct, url):
        return content, ct

    # Not a PDF — try appending /pdf for journal article pages
    if not url.lower().endswith(".pdf"):
        pdf_url = url.rstrip("/") + "/pdf"
        try:
            content2, ct2 = fetch_bytes(pdf_url)
            if is_pdf_content(content2, ct2, pdf_url):
                return content2, ct2
        except Exception:
            pass

    return None, f"Not a PDF (Content-Type: {ct})"


# ---------------------------------------------------------------------------
# Per-row processing
# ---------------------------------------------------------------------------

def determine_filename(title: str, pdf_url: str, bib_index: dict) -> str:
    """Return a safe filename stem (no extension) for this paper."""
    doi = extract_doi_from_url(pdf_url)
    if not doi:
        doi_url = lookup_doi_by_title(title, bib_index)
        if doi_url:
            doi = sanitize_doi(doi_url)
    if doi:
        return safe_filename(doi)
    return safe_filename(title_slug(title))


def already_downloaded(stem: str) -> bool:
    return (PAPERS_DIR / f"{stem}.pdf").exists()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Download PDFs from db/pdf_search_results.csv."
    )
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Seconds to sleep between requests (default 1).")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only process the first N rows.")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip papers already in db/papers/ (default on).")
    args = parser.parse_args()

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)

    bib_index = load_bib_title_doi(BIB_PATH)

    with open(RESULTS_PATH, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if args.limit:
        rows = rows[: args.limit]

    failures = []
    counts: Counter = Counter()

    for i, row in enumerate(rows):
        title = row.get("title", "").strip()
        pdf_url = row.get("pdf_url", "").strip()
        label = f"[{i+1}/{len(rows)}]"

        if not pdf_url:
            reason = "no URL in csv"
            print(f"{label} SKIP  — {reason} — {title[:60]!r}")
            failures.append({"title": title, "pdf_url": pdf_url, "reason": reason})
            counts["no_url"] += 1
            continue

        stem = determine_filename(title, pdf_url, bib_index)
        out_path = PAPERS_DIR / f"{stem}.pdf"

        if args.skip_existing and already_downloaded(stem):
            print(f"{label} EXISTS — {out_path.name} — {title[:60]!r}")
            counts["already_downloaded"] += 1
            continue

        content, detail = try_download(pdf_url)
        if content is not None:
            out_path.write_bytes(content)
            print(f"{label} OK    — {out_path.name} — {title[:60]!r}")
            counts["downloaded"] += 1
        else:
            print(f"{label} FAIL  — {detail} — {title[:60]!r}")
            failures.append({"title": title, "pdf_url": pdf_url, "reason": detail})
            counts["failed"] += 1

        time.sleep(args.delay)

    with open(FAILURES_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "pdf_url", "reason"])
        writer.writeheader()
        writer.writerows(failures)

    print()
    print("Summary")
    print("-------")
    print(f"Downloaded:        {counts['downloaded']}")
    print(f"Already present:   {counts['already_downloaded']}")
    print(f"Failed:            {counts['failed']}")
    print(f"No URL:            {counts['no_url']}")
    print(f"\nFailure log: {FAILURES_PATH}")


if __name__ == "__main__":
    main()
