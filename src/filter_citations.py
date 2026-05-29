#!/usr/bin/env python3
"""
Process collected citations and filter for biological modularity relevance.
"""

import json
import csv
import sys
import re
from pathlib import Path
from typing import List, Dict, Set

HERE = Path(__file__).parent
ROOT = HERE.parent

# Keywords that indicate biological relevance
BIOLOGY_KEYWORDS = [
    'gene', 'protein', 'cell', 'molecular', 'biological', 'regulatory', 'network',
    'metabolic', 'signaling', 'pathway', 'organism', 'genomic', 'transcription',
    'yeast', 'bacteria', 'mammalian', 'human', 'mouse', 'drosophila', 'elegans',
    'evolution', 'developmental', 'neural', 'brain', 'tissue', 'organ',
    'phenotype', 'genotype', 'mutation', 'expression', 'biochemical',
    'enzyme', 'receptor', 'ligand', 'hormone', 'cytoplasm', 'nucleus',
    'chromosome', 'dna', 'rna', 'mrna', 'protein complex', 'interaction',
    'cancer', 'disease', 'immune', 'inflammatory', 'therapeutic'
]

# Keywords that indicate modularity relevance
MODULARITY_KEYWORDS = [
    'modul', 'communit', 'cluster', 'network', 'motif', 'subnetwork',
    'decompos', 'hierarchi', 'partition', 'component', 'subsystem',
    'feedback', 'control', 'circuit', 'pathway', 'cascade', 'retroactivity',
    'insulation', 'coupling', 'composability', 'architecture'
]

# Exclude certain domains
EXCLUDE_KEYWORDS = [
    'irrigation', 'iot', 'sensor network', 'wireless', 'social network',
    'twitter', 'facebook', 'supply chain', 'transportation', 'traffic',
    'power grid', 'electrical', 'recommendation', 'collaborative filtering',
    'financial', 'economic', 'urban', 'city', 'building'
]

def is_biologically_relevant(paper: Dict) -> bool:
    """Check if a paper is relevant to biological modularity."""
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower() if paper.get('abstract') else ''
    venue = paper.get('venue', '').lower()
    
    text = f"{title} {abstract} {venue}"
    
    # Check for exclude keywords first
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in text:
            return False
    
    # Check for biology AND modularity keywords
    has_biology = any(kw in text for kw in BIOLOGY_KEYWORDS)
    has_modularity = any(kw in text for kw in MODULARITY_KEYWORDS)
    
    return has_biology and has_modularity

def read_existing_dois(csv_path: str) -> Set[str]:
    """Read existing DOIs from the CSV to avoid duplicates."""
    dois = set()
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doi_url = row.get('DOI URL', '')
                if doi_url:
                    # Extract DOI from URL
                    match = re.search(r'10\.\d+/[^\s,]+', doi_url)
                    if match:
                        dois.add(match.group(0).lower())
    except Exception as e:
        print(f"Warning: Could not read existing DOIs: {e}", file=sys.stderr)
    
    return dois

def get_doi_from_paper(paper: Dict) -> str:
    """Extract DOI from paper external IDs."""
    external_ids = paper.get('externalIds', {})
    doi = external_ids.get('DOI', '')
    return doi.lower() if doi else ''

def main():
    # Read collected citations
    with open(HERE / 'citations_raw.json', 'r') as f:
        papers = json.load(f)

    print(f"Total papers collected: {len(papers)}", file=sys.stderr)

    # Read existing DOIs
    existing_dois = read_existing_dois(ROOT / 'db' / 'modularity_survey.csv')
    print(f"Existing papers in database: {len(existing_dois)}", file=sys.stderr)
    
    # Filter for biological relevance
    relevant_papers = []
    seen_dois = set()
    
    for paper in papers:
        doi = get_doi_from_paper(paper)
        
        # Skip if no DOI or duplicate
        if not doi:
            continue
        if doi in seen_dois or doi in existing_dois:
            continue
        
        # Check relevance
        if is_biologically_relevant(paper):
            relevant_papers.append(paper)
            seen_dois.add(doi)
    
    print(f"Filtered to {len(relevant_papers)} biologically relevant, unique papers", file=sys.stderr)
    
    # Sort by citation count (descending)
    relevant_papers.sort(key=lambda p: p.get('citationCount', 0), reverse=True)
    
    # Output all papers
    print(json.dumps(relevant_papers, indent=2))

if __name__ == "__main__":
    main()
