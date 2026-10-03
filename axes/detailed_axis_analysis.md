# Detailed Axis Analysis

## Prompt

Use the techniques described in @axes/axes_analysis.md  to analyze the 227 papers considered hihgly relevant in the bibliography. Create a CSV file with columns: paper title, DOI, trait_axis, network_score, function_score, evolution_trajectory_score hierarchy_score. The latter scorieeach paper's relevance to topics. The paper should be scored primarily based on keywords, but also score based on a more detailed reading. The score should be in the range [0, 100]. A separate column labelled "notes" should describe scores that are based on considerations beyond the keyword matches.

## Claude response

I scored the highly relevant papers on the five axes in [highly_relevant_axis_scores.csv](axes/highly_relevant_axis_scores.csv): one row per paper, every score from 0 to 100, and a `notes` entry on every row.

**Paper count:** the file has 209 rows, not 227. The 227 "Highly relevant" rows include 18 repeated DOIs (for example, *The Architecture of Complexity* appears 5 times), so I scored each unique paper once.

**How the scores were set**
- **Keywords:** each score starts from the number of distinct keywords from [axes_analysis.md](axes/axes_analysis.md) that a paper matches. 10 matches gives 100 for the three axes; for evolution it takes 6 and for hierarchy 4, because those keyword lists are shorter. The text matched is the title, the module definition, the summary, and the abstract file if there is one, otherwise the first page of the PDF.
- **Reading:** I read the abstract and module definition for all 209 papers. For 196 of them I changed at least one score, and the `notes` column says why. For the other 13, the note says the reading agreed with the keywords.
- **Kinds of changes:**
  - Lowering false hits, e.g. "development" in "drug development" or "tumour development".
  - Raising axes the keywords can't see, e.g. a paper that combines traits and networks (a hyper module).
  - Matching your note's own placements, e.g. the knockout gene network under Networks.

**Results**
- Network scores are highest overall: 116 papers score 50 or more on Networks, 95 on Functions, 29 on evolutionary trajectory, 25 on hierarchy and 16 on Traits.
- Reading changed 439 of the 1,045 individual scores.

**Things to check**
- **Column name:** I named the first score column `trait_score` rather than `trait_axis`, to match the other columns. Tell me if you want `trait_axis`.
- **Summary-only papers:** about 30 papers have neither an abstract file nor a PDF, so their scores rest on the bibliography summary alone. Their notes say so.
- **Wrong abstracts:** two papers in the bibliography have a DOI that points to a different paper, so the abstract on file is the wrong one: *Cell Signaling as a Cognitive Process* and *Modular Analysis and Design of Biological Circuits*. I scored them from the title and module definition and flagged this in their notes.
- **Non-biology papers:** about 15 papers are not about biology (sociology, food trade, artificial neural networks, category theory). Their notes say so; you may want to remove them.

After the eight requested columns, the CSV keeps the keyword-only scores and the matched terms so each change can be audited. I also updated [classify_axes.py](src/classify_axes.py) so the whole file can be regenerated:
```
python src/classify_axes.py --highly-relevant --adjustments axes/axis_adjustments.csv --output axes/highly_relevant_axis_scores.csv
```
My reading-based scores and notes live in [axis_adjustments.csv](axes/axis_adjustments.csv), and the script applies them on top of the keyword scores. Nothing is committed.