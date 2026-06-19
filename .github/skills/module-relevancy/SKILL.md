---
name: module-relevancy 
description: 'This skill analyzes the relevance of papers to the topic of modularity.'
argument-hint: 'The user can pass the title or author of a specific paper.'
---

# Relevance analyzer

You are an expert in Systems Biology. Your job is to determine if a particular article is relevant to the topic of modularity.

## Paper summaries

Summaries of the papers under consideration can be found in @db/bibliography.csv. Hereafter, this file is referred to as the **original bibliography**.

## Context first

1. Identify papers that do not have an entry in the "Relevancy" column of the original bibliography, i.e. the field is empty (the common case), or contains only the column-header description text rather than an actual assessment.
2. Use the DOI URL in the original bibliography to locate the paper or papers desired. If no DOI URL is present, attempt to locate the paper using its title and authors instead.
3. Use the DOI URL (or title/author search) to download the paper, or its abstract if the full paper is not available. Provide a notification if the download fails. If no version of the paper can be found at all, classify it as "uncertain" (see "What to write") using only the information already present in the bibliography row (e.g. Summary, Definition of module).
4. Read the paper carefully and do the analysis as described below.

Steps 1-4 above, together with "How to analyze the paper" and "What to write" below, describe the procedure each of the 5 processes in "Orchestration" runs independently for its assigned subset of papers.

## Orchestration

1. Assign a roughly equal number of unique papers identified in Context First (step 1) to 5 processes, unless there is more than one entry for a paper, in which case all entries for that paper should be included in the same process and receive the same classification and explanation.
   - If fewer than 10 papers are in scope, skip parallelization and process them directly in a single pass instead of spawning 5 background processes.
2. Create a separate CSV file called the **process bibliography** for each of the processes where they write their results. Each process bibliography has the same columns as the original bibliography, containing only the rows assigned to that process, with the "Relevancy" field updated.
Put these files in the directory ~/Documents/process_bibliographies/n.csv,
where n is the number of the process (1-5).
3. Run these five processes in background and wait for them to complete.
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

1. For each paper under consideration, write a short (1-2 sentence) summary as to why the paper is or is not relevant to modularity.
2. Based on the analysis, classify the paper as one of:
   - **Highly relevant**: modularity (or an explicit synonym such as "module," "component," "subsystem") is a central, explicit framework the paper builds its contribution around.
   - **Moderately relevant**: modularity concepts appear and inform part of the analysis, but are secondary to the paper's main contribution.
   - **Not relevant**: the paper does not meaningfully engage with modularity, components, or their interactions.
   - **Uncertain**: no version of the paper could be located, or the evidence is genuinely mixed or contradictory.
3. Update the "Relevancy" field in the process bibliography with the classification and summary together, in the format "<Classification>: <summary>" (e.g., "Highly relevant: the paper defines modules as...").
