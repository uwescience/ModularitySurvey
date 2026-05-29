# Information Filler Agent

This agent fills in columns of `db/modularity_survey.csv` for a given paper. Use this specification to determine what content belongs in each column.

## Column Specifications

### Administrative

**Added by**
The last name of the human person adding this entry. Do not use an AI agent name here.

**AI agent and model**
The name of the AI agent and its model version used to assist with this entry (e.g., `Claude claude-sonnet-4-6`). Leave blank if no AI was used.

### Bibliographic

**Last name of 1st author**
The last name of the first listed author of the paper.

**All authors**
A complete list of all authors exactly as they appear in the paper.

**Paper title**
The full title of the paper exactly as published.

**Year**
The four-digit publication year.

**Paper type**
The type of published article. Use one of: `research`, `review`, `perspective`, or a similar keyword that describes the article genre.

**DOI URL**
The full DOI URL in the form `https://doi.org/<suffix>`.

### Technical Content

**Modeling framework**
The mathematical or computational modeling framework used in the article. Use controlled keywords such as: `Boolean network`, `ODE`, `graph based`, `stochastic`. Multiple keywords are permitted, comma-separated.

**Definition of module**
A description of how the paper defines a "module". Address the following aspects where applicable:
- Is the structure directed or undirected?
- Is it hierarchical?
- Can modules share elements or intersect?
- Can modules be nested?
- Does the definition include structural (graph-based) components?
- Does the definition include functional components?

Include both the mathematical formulation and the biological interpretation given by the authors.

**Context of system**
The biological setting and intended use of the module concept in the paper. Briefly describe:
- Evolved vs. engineered system
- Type of network (e.g., gene regulatory network, signaling network, metabolic network)
- Purpose of the modularity analysis (analysis, control, design, validation, etc.)

**Purpose of module**
The motivation for defining a module in this paper. Explain what biological phenomenon the module definition is intended to capture.

**Algorithmic aspect**
Whether an algorithm or computational implementation accompanies the module definition. Write `yes` or `no`. If `yes`, add a brief description of the algorithm(s) provided.

**Data**
Whether the paper includes data, and if so, what kind and how it is used. Distinguish between:
- Empirical data
- Simulated data
- Benchmark datasets
- Literature-curated data

State `none` if the paper contains no data.

### Biological Context

**Level of organization**
The biological level(s) of organization addressed. Use keywords such as: `cell`, `tissue`, `organism`, `population`, or similar. Multiple levels may be listed.

**Organism**
The organism(s) studied. Use standard abbreviated conventions (e.g., `C. elegans`, `S. cerevisiae`, `E. coli`, `H. sapiens`). Write `generic` or `none` if no specific organism is used.

### Impact and Summary

**Impact of paper**
An assessment of the paper's impact with justification. Do not rely solely on citation count. Consider:
- Breadth of adoption of the work
- Historical impact up to the present
- Existence of notable follow-up papers
- Subdiscipline(s) in which the work is influential

**Citations**
The current number of citations for this paper (from Google Scholar or a similar source).

**Summary**
A short (1–2 sentence) summary of the paper suitable for an annotated bibliography. Focus on the main contribution and significance.

**Primary theme**
A brief keyword or phrase capturing the primary thematic focus of the paper (e.g., `evolutionary modularity`, `network decomposition`, `Boolean network analysis`).

### Review Tracking

**Read by / Notes** (columns 21–24)
Reviewer name and free-form notes from a human reader who has read the paper in detail. Multiple reviewer columns are provided; fill the next available pair.
