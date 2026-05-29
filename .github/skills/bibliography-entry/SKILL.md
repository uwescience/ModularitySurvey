---
name: bibliography-entry
description: 'Add new papers to the modularity survey CSV database. Use when adding bibliography entry, adding paper to survey, adding research article, or appending to modularity_survey.csv.'
argument-hint: 'Paper title, DOI, or description of paper to add'
---

# Bibliography Entry Skill

Add new papers to the modularity survey database with proper formatting and all required fields.

**Operating Mode**: This skill operates in agentic mode with file system and web access. Only ask the user for fields that cannot be retrieved from online sources (AddedBy name, custom annotations).

## When to Use

- Adding a new research paper, review, or perspective to the survey
- Importing papers found via literature search
- Bulk adding multiple papers from a citation list (expects newline-separated list of DOIs or titles; process each sequentially, reporting success or failure per entry)

## CSV Column Structure

The CSV columns in order are:
```
AddedBy,AIAgentAndModel,LastNameOf1stAuthor,All authors,Paper title,Year,Paper type,DOI URL,Modeling framework,Definition of module,Context of system,Purpose of module,Algorithmic aspect,Data,Level of organization,Organism,Impact of paper,Citations,Summary,Primary theme,Read by,Notes,Read by,Notes,...
```

## Fields to Collect

### User-Provided Fields (Always Ask)

1. **AddedBy** — Ask the user for their name if not already provided in the conversation. Do not infer or guess.
2. **AIAgentAndModel** — Automatically fill with current agent name and model version (e.g., "GitHub Copilot, Claude Sonnet 4.5")

### Paper Metadata (Retrieve from Online Sources)

3. **LastNameOf1stAuthor** — First author's last name
4. **All authors** — Complete author list
5. **Paper title** — Full title
6. **Year** — Publication year
7. **Paper type** — Infer from abstract/content: "research", "review", "perspective"
8. **DOI URL** — Format as `https://doi.org/...`
9. **Citations** — Citation count from Google Scholar or similar

### Content Analysis (Extract from Paper/Abstract)

10. **Modeling framework** — Keywords: "Boolean network", "ODE", "graph based", "stochastic"
11. **Definition of module** — Mathematical and biological description (see schema in CSV row 2)
12. **Context of system** — Biological setting and intended use
13. **Purpose of module** — What biological phenomena being captured
14. **Algorithmic aspect** — "yes" or "no" with brief description if yes
15. **Data** — Type of data used (empirical, simulated, benchmark, literature-curated)
16. **Level of organization** — Keywords: "cell", "tissue", "organism"
17. **Organism** — Use convention: C. elegans, S. cerevisiae, etc.
18. **Impact of paper** — 1-2 sentences describing the paper's methodological or conceptual contribution to the field, independent of citation count (e.g., "Introduced widely adopted spectral partitioning algorithm for community detection")
19. **Summary** — 1-2 sentence summary for annotated bibliography
20. **Primary theme** — Main topic area

## Procedure

### 0. Check for Duplicates

Before adding any paper:
- Search `db/modularity_survey.csv` for matching DOI or title
- If a duplicate is found, notify the user: "This paper already exists at row [N]. Aborting. Do you want to update the existing entry instead?" and stop

### 1. Gather Paper Information

**Priority: Online retrieval first, then user input for gaps**

If given a DOI or paper title:
1. Search for the paper online or use web tools to retrieve metadata
2. Extract: authors, title, year, abstract, citation count
3. Identify modeling framework and biological context from abstract/paper
4. If a search returns zero results, report failure and ask user for alternative identifier
5. If a search returns multiple results, present the top 3 candidates and ask user to confirm before proceeding
6. If DOI resolves but metadata is incomplete, fill what is available and ask only for the remaining gaps

If given minimal information with no DOI/title:
- Ask user to provide at least a DOI or full paper title to proceed

### 2. Format the Entry

Format as a single CSV row with proper escaping:
- Quote fields containing commas
- Escape internal quotes by doubling them
- Fill all paper metadata and content analysis fields from online sources
- Leave optional fields empty if information is unavailable (but include the comma separators to maintain column alignment)
- Always ask user for AddedBy; auto-fill AIAgentAndModel

### 3. Append to Database

```bash
# Back up first
cp db/modularity_survey.csv db/modularity_survey.csv.backup

# Append new entry (ensure proper CSV formatting)
echo "new,entry,data..." >> db/modularity_survey.csv
```

**Error handling**: If the append command fails (e.g., file not found, permission denied), report the exact error to the user and do not mark the entry as added. Suggest running `ls -la db/` to verify the file path and permissions.

### 4. Validate

- Check CSV syntax is valid
- Confirm DOI format is correct (`https://doi.org/...`)
- Ensure keywords match controlled vocabulary from existing entries
- Verify paper metadata fields (authors, title, year) are populated

## Example Workflow

User: "Add the Newman 2006 modularity matrix paper"

1. Search for paper: "Newman MEJ (2006) Modularity and community structure in networks"
2. Retrieve: Authors, DOI (10.1073/pnas.0601602103), year, citations
3. Read abstract to determine: modeling framework (graph based), level (general), algorithmic aspect (yes - spectral partitioning)
4. Format entry with all fields
5. Append to `db/modularity_survey.csv`
6. Report: "Added Newman 2006 to database (row N)"

## Controlled Vocabulary

Maintain consistency with existing entries:

- **Paper type**: research, review, perspective
- **Modeling framework**: Boolean network, ODE, graph based, stochastic, logic-based
- **Level of organization**: cell, tissue, organism, molecular, ecosystem
- **Data types**: empirical, simulated, benchmark, literature-curated

## Tips

- AIAgentAndModel is auto-filled with current agent info
- For bulk input, process papers one at a time to ensure quality and proper error reporting
- For high-impact papers, provide detailed summaries and impact justifications
- If the paper is not freely available online, ask the user if they have access or can provide the abstract
