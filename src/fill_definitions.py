"""
Fill in empty/placeholder "Definition of module" cells in modularity_survey.csv.
Reads API key from ~/claude_api.txt. Writes output to db/modularity_survey_filled.csv.
Saves a checkpoint after every batch so the run is restartable.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import anthropic

# ── Config ────────────────────────────────────────────────────────────────────
CSV_IN  = Path(__file__).parent.parent / "db" / "modularity_survey.csv"
CSV_OUT = Path(__file__).parent.parent / "db" / "modularity_survey_filled.csv"
CKPT    = Path(__file__).parent.parent / "db" / ".fill_definitions_checkpoint.json"
KEY_FILE = Path.home() / "claude_api.txt"
MODEL   = "claude-haiku-4-5-20251001"
BATCH   = 10          # rows per API call
MAX_TOKENS = 4096
PLACEHOLDERS = {"To be manually curated", "N/A", "TBD", ""}

# ── Helpers ───────────────────────────────────────────────────────────────────

def read_csv(path: Path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames

def write_csv(path: Path, rows: list, fieldnames: list):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def is_placeholder(val: str) -> bool:
    return val.strip() in PLACEHOLDERS

def row_metadata(r: dict) -> str:
    return (
        f"Title: {r['Paper title']}\n"
        f"Year: {r['Year']} | Type: {r['Paper type']}\n"
        f"Modeling framework: {r['Modeling framework']}\n"
        f"Context of system: {r['Context of system']}\n"
        f"Purpose of module: {r['Purpose of module']}\n"
        f"Algorithmic aspect: {r['Algorithmic aspect']}\n"
        f"Summary: {r['Summary']}\n"
        f"Primary theme: {r['Primary theme']}"
    )

# ── Prompt construction ────────────────────────────────────────────────────────

SYSTEM = """\
You are a biology/systems-biology expert helping to build a research survey database.
Your task: write a "Definition of module" for each paper listed.

The definition describes what the word "module" (or "modularity") specifically means
in the context of that paper — how the authors conceptualize, operationalize, and use
the concept of a module.  It should:
- Be 2–5 sentences, technical, and specific to that paper's framing
- Synthesise the modeling framework, context, and purpose information given
- Avoid generic statements that could apply to any paper
- Not copy verbatim from the examples below

Here are example input→definition pairs that show the required style:

EXAMPLE 1
Input:
  Title: Modularity in Biological Networks
  Framework: Graph-based / community detection
  Context: Gene regulatory networks, protein interaction networks, metabolic networks
  Purpose: Comprehensive survey of modularity concepts and detection algorithms
  Summary: Reviews modularity across diverse biological network types
Definition:
  Modules are groups of biological entities (genes, proteins, metabolites) more
  densely interconnected with each other than with the rest of the network. The
  review surveys structural definitions (community structure), functional definitions
  (shared biological function), and their relationship. Different algorithms
  operationalize different aspects of this general definition. Modules may be
  hierarchical and overlapping depending on the method used.

EXAMPLE 2
Input:
  Title: Network motifs: theory and experimental approaches
  Framework: Graph-based regulatory networks; randomized-network motif detection
  Context: Transcription regulation networks; sensory and developmental contexts
  Purpose: Identify basic circuit building blocks and explain information-processing functions
  Summary: Synthesises theory and experiments on network motifs as recurring circuit patterns
Definition:
  The paper treats modules as network motifs: recurring regulation patterns or circuits
  that occur much more often than expected in randomized networks and can be viewed as
  basic building blocks of transcription networks. These motifs are directed subgraphs
  identified structurally but interpreted functionally, and they can overlap and combine
  into larger organizations. The review characterises specific motifs and links their
  topology to information-processing tasks such as delay, pulse generation, and memory.

EXAMPLE 3
Input:
  Title: A module of negative feedback regulators defines growth factor signaling
  Framework: Signaling network / kinetic systems analysis / network motifs
  Context: Mammalian growth-factor signaling (EGFR) in epithelial cells
  Purpose: Explain how growth-factor responses are made transient and robust by transcription-dependent feedback
  Summary: EGFR signaling induces waves of transcription including a delayed-early cluster of negative regulators
Definition:
  A module is a kinetically defined, coexpressed cluster of delayed early genes that
  functions as a negative-feedback unit attenuating growth factor signaling. The module
  is defined primarily by shared temporal behaviour and shared regulatory function rather
  than by a purely graph-theoretic partition. The authors also interpret the signalling
  network through smaller architectural motifs such as negative autoregulation and
  coherent/incoherent feed-forward loops.

Now generate definitions for the papers in the user message.
"""

def build_user_prompt(batch: list[tuple[int, dict]]) -> str:
    parts = ["Return a JSON array — one object per paper — in the same order as below.\n"
             'Each object: {"row": <int>, "definition": "<text>"}\n'
             "No extra keys. No markdown fences. Pure JSON only.\n\n"]
    for idx, (row_num, r) in enumerate(batch):
        parts.append(f"PAPER {idx+1} (row {row_num})\n{row_metadata(r)}\n")
    return "\n".join(parts)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Read API key
    api_key = KEY_FILE.read_text().strip()
    client = anthropic.Anthropic(api_key=api_key)

    # Read CSV
    rows, fieldnames = read_csv(CSV_IN)
    print(f"Loaded {len(rows)} rows from {CSV_IN.name}")

    # Identify targets
    target_indices = [i for i, r in enumerate(rows)
                      if is_placeholder(r["Definition of module"])]
    print(f"Targets (placeholders): {len(target_indices)}")

    # Load checkpoint
    done: dict[str, str] = {}  # str(row_index) → definition
    if CKPT.exists():
        done = json.loads(CKPT.read_text())
        print(f"Resuming from checkpoint: {len(done)} already done")

    remaining = [i for i in target_indices if str(i) not in done]
    print(f"Remaining: {len(remaining)}")

    flagged = []

    # Process in batches
    batches = [remaining[i:i+BATCH] for i in range(0, len(remaining), BATCH)]
    for b_num, batch_indices in enumerate(batches):
        batch = [(i + 2, rows[i]) for i in batch_indices]  # +2 for 1-indexed + header
        prompt = build_user_prompt(batch)

        for attempt in range(3):
            try:
                resp = client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = resp.content[0].text.strip()
                # Strip markdown fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                results = json.loads(raw)
                break
            except Exception as e:
                print(f"  Attempt {attempt+1} failed: {e}")
                if attempt == 2:
                    print(f"  Giving up on batch {b_num+1}. Skipping.")
                    results = []
                time.sleep(2 ** attempt)

        for item in results:
            row_num = item["row"]
            defn = item["definition"].strip()
            csv_index = row_num - 2  # reverse of +2 above

            # Flag anomalies: very short (<30 words) or very long (>200 words)
            word_count = len(defn.split())
            if word_count < 30 or word_count > 200:
                defn += " [REVIEW]"
                flagged.append(row_num)

            done[str(csv_index)] = defn

        # Save checkpoint after every batch
        CKPT.write_text(json.dumps(done))

        filled_so_far = len(done)
        print(f"Batch {b_num+1}/{len(batches)} done "
              f"({filled_so_far}/{len(target_indices)} total, "
              f"{len(flagged)} flagged)")

    # Apply definitions to rows
    changed = 0
    for i, r in enumerate(rows):
        if str(i) in done:
            r["Definition of module"] = done[str(i)]
            changed += 1

    # Write output
    write_csv(CSV_OUT, rows, fieldnames)

    # Clean up checkpoint
    if CKPT.exists():
        CKPT.unlink()

    print()
    print("Summary")
    print("-------")
    print(f"Input file:         {CSV_IN}")
    print(f"Output file:        {CSV_OUT}")
    print(f"Rows processed:     {changed} filled / {len(rows)} total")
    print(f"Examples used:      {len(rows) - len(target_indices)}")
    print(f"Flagged for review: {len(flagged)} rows"
          + (f"  {flagged}" if flagged else ""))


if __name__ == "__main__":
    main()
