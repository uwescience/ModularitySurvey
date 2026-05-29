# Literature Search Agent Summary Report
**Date:** 2026-05-21
**Agent:** literature-search-agent (Claude Sonnet 4.5)
**Operator:** jlheller

## Overview
Extended the modularity survey bibliography by finding papers that cite influential works in the database. Focused on recent (2015-2025), highly-cited papers (>50 citations) relevant to biological modularity. There may be multiple entries for a single paper, indicating that multiple operators have added it. This is not a problem because different operators may have different choices for the fields.

## Methodology

### 1. Seed Papers Selected
Use all of the papers in the database with >100 citations as seeds for the search. These are highly influential papers that have likely inspired relevant follow-up work.

### 2. Search and Filtering Pipeline

1. **Citation Collection:**
   - Queried Semantic Scholar API for papers citing each seed
   - Retrieved ~1000 citations per seed paper (API limit)
   - Total raw citations collected: ~5,000
   - **Validation:** If result count deviates >10% from expected, log a warning to `logs/pipeline.log` and continue; do not halt.

2. **Initial Filtering:**
   - Year range: 2015-2025
   - Minimum citations: 50
   - Result: 188 papers
   - **Validation:** If result count deviates >10% from expected, log a warning to `logs/pipeline.log` and continue; do not halt.

3. **Biological Relevance Filtering:**
   - Required both biology keywords AND modularity keywords
   - Full keyword lists are defined in `config/biology_keywords.txt` and `config/modularity_keywords.txt`. Matching is case-insensitive substring match against title and abstract. Update these files to change filtering behavior.
   - Example biology keywords: gene, protein, cell, regulatory, etc.
   - Example modularity keywords: module, network, cluster, pathway, etc.
   - Apply a secondary domain exclusion list (`config/excluded_domains.txt`) to remove papers from non-target fields. Current exclusions: sociohydrology, robotics, polymers. Add new domains to this file to extend filtering without code changes.
   - Result: 150 papers
   - **Validation:** If result count deviates >10% from expected, log a warning to `logs/pipeline.log` and continue; do not halt.

4. **Deduplication:**
   - Removed papers already in database (66 existing DOIs)
   - Removed internal duplicates (2 papers)
   - Result: 82 unique new papers
   - **Validation:** If result count deviates >10% from expected, log a warning to `logs/pipeline.log` and continue; do not halt.

5. **Selection and Output:**
   - Ranked by citation count and relevance score
   - Selected top 20 papers for manual review
   - Write the final 20 papers to `output/new_papers.csv` with columns: DOI, title, year, citation_count, relevance_score. Also append them to the master database file using appropriate tools.

## Python Scripts

Run the following scripts in order:
1. `src/find_citations.py --seeds db/modularity_survey.csv --min-citations 100` for citation collection
2. `src/filter_citations.py --year-start 2015 --year-end 2025 --min-citations 50` for initial and biological relevance filtering
3. `src/add_papers_to_csv.py --input output/new_papers.csv --output db/modularity_survey.csv` to add selected papers to the database