#!/usr/bin/env python3
"""
Find papers citing influential works in the modularity survey using Semantic Scholar API.
"""

import json
import time
import urllib.request
import urllib.error
import sys
import csv
import re
from pathlib import Path
from typing import List, Dict, Set

MIN_CITATIONS = 50
SEED_MIN_CITATIONS = 100  # Only use papers with >100 citations as seeds
YEAR_MIN = 2015
YEAR_MAX = 2025
API_BASE = "https://api.semanticscholar.org/graph/v1"

HERE = Path(__file__).parent
ROOT = HERE.parent

def load_seed_dois_from_database(min_citations: int = SEED_MIN_CITATIONS) -> List[str]:
    """Load DOIs from database CSV for papers with high citation counts."""
    seed_dois = []
    csv_path = ROOT / 'db' / 'modularity_survey.csv'
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doi_url = row.get('DOI URL', '').strip()
                citations_str = row.get('Citations', '').strip()
                
                # Skip if no DOI
                if not doi_url:
                    continue
                
                # Extract DOI from URL (format: https://doi.org/10.xxxx/yyyy)
                match = re.search(r'10\.\d+/[^\s,]+', doi_url)
                if not match:
                    continue
                doi = match.group(0)
                
                # Check citation count
                try:
                    citations = int(citations_str) if citations_str else 0
                    if citations >= min_citations:
                        seed_dois.append(doi)
                except ValueError:
                    # Skip if citations can't be parsed
                    continue
        
        print(f"Loaded {len(seed_dois)} seed papers with >{min_citations} citations from database", file=sys.stderr)
        return seed_dois
        
    except FileNotFoundError:
        print(f"Error: Database file not found at {csv_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading database: {e}", file=sys.stderr)
        sys.exit(1)

def api_request(url: str, retry_count: int = 3) -> Dict:
    """Make API request with retry logic."""
    for attempt in range(retry_count):
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Rate limited
                print(f"    Rate limited, waiting 10 seconds...", file=sys.stderr)
                time.sleep(10)
                continue
            elif e.code == 404:
                return None
            else:
                print(f"    HTTP Error {e.code}: {e.reason}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)
            if attempt < retry_count - 1:
                time.sleep(2)
                continue
            return None
    return None

def get_paper_id(doi: str) -> tuple:
    """Resolve DOI to Semantic Scholar paper ID."""
    url = f"{API_BASE}/paper/DOI:{doi}?fields=paperId,title,year,citationCount"
    data = api_request(url)
    time.sleep(1)  # Rate limiting
    
    if data and 'paperId' in data:
        return data['paperId'], data.get('title', ''), data.get('citationCount', 0)
    return None, None, None

def get_citations(paper_id: str, limit: int = 100) -> List[Dict]:
    """Get all citations for a paper."""
    all_citations = []
    offset = 0
    
    while True:
        url = f"{API_BASE}/paper/{paper_id}/citations?fields=paperId,title,year,citationCount,authors,externalIds,abstract,venue&limit={limit}&offset={offset}"
        print(f"    Fetching citations offset={offset}...", file=sys.stderr)
        
        data = api_request(url)
        time.sleep(1)  # Rate limiting
        
        if not data or 'data' not in data:
            break
            
        citations = data['data']
        if not citations:
            break
            
        print(f"    Got {len(citations)} citations", file=sys.stderr)
        all_citations.extend(citations)
        
        offset += limit
        
        # Check if there are more results
        if 'next' not in data or offset >= 1000:  # Limit to 1000 results per seed
            break
    
    return all_citations

def filter_citations(citations: List[Dict]) -> List[Dict]:
    """Filter citations by year and citation count."""
    filtered = []
    
    for item in citations:
        citing_paper = item.get('citingPaper', {})
        year = citing_paper.get('year')
        cites = citing_paper.get('citationCount')
        
        # Handle None values for citations
        if cites is None:
            cites = 0
        
        if year and YEAR_MIN <= year <= YEAR_MAX and cites >= MIN_CITATIONS:
            filtered.append(citing_paper)
    
    return filtered

def main():
    # Load seed papers from database
    seed_dois = load_seed_dois_from_database()
    
    if not seed_dois:
        print("Error: No seed papers found in database", file=sys.stderr)
        sys.exit(1)
    
    print(f"Starting citation search for {len(seed_dois)} seed papers...", file=sys.stderr)
    print(f"Filtering for papers with >{MIN_CITATIONS} citations from {YEAR_MIN}-{YEAR_MAX}", file=sys.stderr)
    
    all_filtered_papers = []
    processed_seed_count = 0
    failed_seed_count = 0
    
    for doi in seed_dois:
        print(f"\nProcessing DOI: {doi}", file=sys.stderr)
        
        paper_id, title, cite_count = get_paper_id(doi)
        
        if not paper_id:
            print(f"  Could not resolve DOI: {doi}", file=sys.stderr)
            failed_seed_count += 1
            continue
        
        print(f"  Found: {title} (ID: {paper_id}, {cite_count} citations)", file=sys.stderr)
        processed_seed_count += 1
        
        # Get citations
        citations = get_citations(paper_id)
        
        # Filter
        filtered = filter_citations(citations)
        print(f"  Filtered to {len(filtered)} papers (>{MIN_CITATIONS} cites, {YEAR_MIN}-{YEAR_MAX})", file=sys.stderr)
        
        all_filtered_papers.extend(filtered)
    
    print(f"\nTotal papers collected: {len(all_filtered_papers)}", file=sys.stderr)
    print(f"Successfully processed: {processed_seed_count} seed papers", file=sys.stderr)
    print(f"Failed to resolve: {failed_seed_count} seed papers", file=sys.stderr)
    
    # Output as JSON
    print(json.dumps(all_filtered_papers, indent=2))

if __name__ == "__main__":
    main()
