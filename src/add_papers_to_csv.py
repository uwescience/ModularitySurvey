#!/usr/bin/env python3
"""
Add filtered papers to the modularity survey CSV.
"""

import json
import csv
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent

def format_authors(authors):
    """Format author list."""
    if not authors:
        return ""
    return ", ".join([a.get('name', '') for a in authors])

def get_first_author_last_name(authors):
    """Extract last name of first author."""
    if not authors:
        return ""
    first_author = authors[0].get('name', '')
    parts = first_author.split()
    return parts[-1] if parts else ""

def create_summary(paper):
    """Generate a summary from title and abstract."""
    title = paper.get('title', '')
    abstract = paper.get('abstract', '')
    
    if abstract:
        # Take first 2 sentences of abstract
        sentences = abstract.split('. ')[:2]
        summary = '. '.join(sentences)
        if len(summary) > 300:
            summary = summary[:297] + "..."
        return summary
    else:
        return f"Study on {title.lower()}"

def infer_modeling_framework(paper):
    """Infer modeling framework from title/abstract."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    
    frameworks = []
    if 'network' in text:
        frameworks.append('Graph-based / network analysis')
    if 'boolean' in text or 'discrete' in text:
        frameworks.append('Boolean network')
    if 'differential equation' in text or 'ode' in text or 'dynamical system' in text:
        frameworks.append('ODE / dynamical systems')
    if 'stochastic' in text or 'probabilistic' in text:
        frameworks.append('Stochastic / probabilistic')
    if 'machine learning' in text or 'deep learning' in text:
        frameworks.append('Machine learning')
    if 'proteom' in text or 'mass spectrometry' in text:
        frameworks.append('Proteomics')
    if 'genom' in text or 'rna-seq' in text or 'transcriptom' in text:
        frameworks.append('Genomics / transcriptomics')
    
    return ' / '.join(frameworks) if frameworks else 'To be determined'

def infer_level_of_organization(paper):
    """Infer biological level from text."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    
    levels = []
    if 'molecular' in text or 'protein' in text or 'gene' in text:
        levels.append('molecular')
    if 'cell' in text or 'cellular' in text:
        levels.append('cell')
    if 'tissue' in text:
        levels.append('tissue')
    if 'organ' in text or 'organism' in text:
        levels.append('organism')
    if 'network' in text and not levels:
        levels.append('molecular, cell')
    
    return ', '.join(levels) if levels else 'cell'

def infer_organism(paper):
    """Infer organism from text."""
    text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
    
    organisms = []
    if 'human' in text or 'homo sapiens' in text:
        organisms.append('H. sapiens')
    if 'mouse' in text or 'mice' in text or 'murine' in text:
        organisms.append('M. musculus')
    if 'yeast' in text or 'cerevisiae' in text:
        organisms.append('S. cerevisiae')
    if 'e. coli' in text or 'escherichia' in text:
        organisms.append('E. coli')
    if 'drosophila' in text or 'melanogaster' in text:
        organisms.append('D. melanogaster')
    if 'elegans' in text or 'c. elegans' in text or 'caenorhabditis' in text:
        organisms.append('C. elegans')
    if 'cancer' in text or 'tumor' in text:
        organisms.append('H. sapiens (cancer)')
    
    return ', '.join(organisms) if organisms else 'Multiple / general'

def determine_paper_type(paper):
    """Determine if paper is research, review, or perspective."""
    title = paper.get('title', '').lower()
    abstract = paper.get('abstract', '').lower() if paper.get('abstract') else ''
    
    if 'review' in title or 'survey' in title or ('review' in abstract and abstract.index('review') < 100):
        return 'review'
    elif 'perspective' in title or 'opinion' in title or 'commentary' in title:
        return 'perspective'
    else:
        return 'research'

def create_csv_row(paper, fieldnames):
    """Create a CSV row for a paper."""
    authors = paper.get('authors', [])
    external_ids = paper.get('externalIds', {})
    doi = external_ids.get('DOI', '')
    
    # Create row with empty values for all fields
    row = {field: '' for field in fieldnames}
    
    # Fill in known values
    row['AddedBy'] = 'jlheller'
    row['AIAgentAndModel'] = 'literature-search-agent, Claude Sonnet 4.5'
    row['LastNameOf1stAuthor'] = get_first_author_last_name(authors)
    row['All authors'] = format_authors(authors)
    row['Paper title'] = paper.get('title', '')
    row['Year'] = paper.get('year', '')
    row['Paper type'] = determine_paper_type(paper)
    row['DOI URL'] = f"https://doi.org/{doi}" if doi else ''
    row['Modeling framework'] = infer_modeling_framework(paper)
    row['Definition of module'] = 'To be manually curated'
    row['Context of system'] = 'To be manually curated'
    row['Purpose of module'] = 'To be manually curated'
    row['Algorithmic aspect'] = 'To be determined'
    row['Data'] = 'To be determined'
    row['Level of organization'] = infer_level_of_organization(paper)
    row['Organism'] = infer_organism(paper)
    row['Impact of paper'] = 'Moderate to high (highly cited recent work)'
    row['Citations'] = paper.get('citationCount', '')
    row['Summary'] = create_summary(paper)
    row['Primary theme'] = 'To be determined'
    
    # Find the first Notes column and add our note there
    notes_index = [i for i, f in enumerate(fieldnames) if f == 'Notes']
    if notes_index:
        notes_field = fieldnames[notes_index[0]]
        row[notes_field] = f'Auto-added {datetime.now().strftime("%Y-%m-%d")}. Manual curation needed.'
    
    return row

def main():
    # Read filtered papers
    with open(HERE / 'citations_filtered.json', 'r') as f:
        papers = json.load(f)

    print(f"Processing {len(papers)} papers", file=sys.stderr)

    # Read existing CSV (using utf-8-sig to handle BOM)
    with open(ROOT / 'db' / 'modularity_survey.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)

    # Build set of existing DOIs and titles to avoid duplicates
    existing_dois = {r.get('DOI URL', '').strip().lower() for r in existing_rows if r.get('DOI URL', '').strip()}
    existing_titles = {r.get('Paper title', '').strip().lower() for r in existing_rows if r.get('Paper title', '').strip()}

    print(f"Existing entries: {len(existing_rows)} (with {len(existing_dois)} DOIs)", file=sys.stderr)

    selected_papers = []
    skipped_duplicate = 0
    for paper in papers:
        doi = paper.get('externalIds', {}).get('DOI', '')
        doi_url = f"https://doi.org/{doi}".lower() if doi else ''
        title = paper.get('title', '').strip().lower()

        if doi_url and doi_url in existing_dois:
            skipped_duplicate += 1
            continue
        if title and title in existing_titles:
            skipped_duplicate += 1
            continue

        selected_papers.append(paper)

    print(f"Skipped {skipped_duplicate} duplicates, adding {len(selected_papers)} new papers", file=sys.stderr)

    # Create new rows
    new_rows = [create_csv_row(paper, fieldnames) for paper in selected_papers]

    # Write updated CSV in-place
    with open(ROOT / 'db' / 'modularity_survey.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing_rows)
        writer.writerows(new_rows)

    print(f"Added {len(new_rows)} papers to db/modularity_survey.csv (total rows: {len(existing_rows) + len(new_rows)})", file=sys.stderr)

if __name__ == "__main__":
    main()
