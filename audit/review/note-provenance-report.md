# Note provenance diagnosis

The metadata contamination predates final assembly and affects the already-published 85,596-record baseline. All 85,596 baseline records are inherited unchanged by the frozen 125,264-record candidate.

- Reviewing every one of the first expansion’s 167 effective notes found 15 clearly misattached or contaminated notes, 3 directly false metadata claims, and 3 ambiguous preservation claims. The 146 remaining notes had no clear topic-attachment error in this pass; their factual claims and full translation quality are not certified.
- The 15 contaminated notes already occur in the original raw outputs. Corresponding Ukrainian glosses describe their own entries, not the unrelated note topics. This does not establish that every gloss is accurate.
- Across all 119,668 expansion entries and 1,197 batches, effective source IDs, source fields, segment counts, note text, and gloss text match the frozen assembly. Four separate early raw batches had missing/malformed IDs that their correction files already repair; those are outside the 15 note-defect batches. All checked raw hashes match saved validation checkpoints.
- Several notes point to exactly the same index in the preceding batch; other offsets vary, one target was outside the selected batch cohort, and some notes blend topics. This strongly supports stale positional note composition during generation. Exact first-cohort generation commands are not retained, so the originating implementation defect cannot be proven. Later saved helpers independently attach notes.get(i,[]) to rows and lack note-to-source identity checks.
- In an isolated audit copy, the unchanged existing validator accepted all 10 affected batches and all 15 contaminated notes. The current passing checks therefore cannot certify note semantics.

## Proposed containment

Create a new candidate only. Quarantine notes without explicit per-ID semantic review into an immutable sidecar, retain every original uncertainty flag, and restore only reviewed/reworded text under verified stable IDs. Never apply a global offset, guess a target for mixed notes, or clear flags through the current bool(notes) derivation. A first-cohort-only repair addresses known contamination, but cannot establish that later cohorts are clean. To claim all presented notes reliable before exhaustive review, quarantine every still-unreviewed note across all 2,534 current notes.

Future generation should key translations and notes by stable ID with source hash/headword assertions. Add all 15 counterexamples as regression fixtures, test batch repartitioning, and require complete note-association review coverage independently of gloss spot checks.

No frozen dictionary, published snapshot, raw output, or existing archive was changed. Full evidence, target candidates, hashes, limits and eight regression recommendations are in note-provenance-diagnosis.json.
