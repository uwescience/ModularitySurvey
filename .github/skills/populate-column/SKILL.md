---
name: populate-column
description: 'This skill populates a bibliography column in a CSV file with values based on a given specification. The user can specify the column to populate, the source of the values, and any transformation or filtering to apply.'
source: The source is @db/bibliography.csv referred to as the **original bibliography**. 
argument-hint: 'The **target column** (to populate), the source of the values, and any transformation or filtering to apply.'
---

# Context

You are an expert in Systems Biology. Your job is to determine if the values of fields in the bibliography are relevant to the topic of modularity.

## Finding the paper or abstract for a row

1. Identify rows in the original bibliography that do not have an entry for the target column of the original bibliography, i.e. the field is empty (the common case), or contains only the column-header description text rather than an actual assessment.
2. For each row, use the DOI URL as transformed in ``sanitize_doi`` in @download_papers.py to locate the paper or abstract that provides more detailed information.
3. Read the paper carefully.
4. Analyze the paper to determine the information to put in the target column, based on the source of the values and any transformation or filtering to apply.

Steps 1-4 above, together with "How to analyze the paper" and "What to write" below, describe the procedure each of the 5 processes in "Orchestration" runs independently for its assigned subset of papers.

## Orchestration

1. Assign a roughly equal number of unique papers identified in Context First (step 1) to 5 processes, unless there is more than one entry for a paper, in which case all entries for that paper should be included in the same process and receive the same classification and explanation.
   - If fewer than 10 papers are in scope, skip parallelization and process them directly in a single pass instead of spawning 5 background processes.
2. Create a separate CSV file called the **process bibliography** for each of the processes where they write their results. Each process bibliography has the same columns as the original bibliography, containing only the rows assigned to that process, with the "Relevancy" field updated.
Put these files in the directory ~/Documents/process_bibliographies/n.csv,
where n is the number of the process (1-5).
3. Run the five processes in background and wait for them to complete.
Each process should report its progress every 10 papers, and notify when it has
completed.
4. Merge the results of these 5 processes to create the file ~/Documents/new_bibliography.csv. This file will contain only the papers that were missing a Relevancy value at the start of this run (per Context First), not the full original bibliography. Note that bibliography entries may be duplicated, and
bibliography.csv is not updated (since this is done manually).
5. Report process failures or errors that occurred during the analysis.

## How to analyze the paper

Assess the extent to which the paper focuses on concepts of components and their interactions.
The analysis should focus on the presence of these terms and how they relate to the concept of modularity,
especially looking for references to "module" (and variations of this word), "pattern", "component" and similar words.
Consider the number of occurrences of these terms, the extent to which the paper cites highly cited papers on modularity (e.g., Herbert Simon), and the overall focus of the paper on these concepts.

## What to write
1. Write the information as described in a separate skill file that is an argument to this skill.