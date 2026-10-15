# Ukrainian CEDICT: completed flagged-entry model review

Date: 15 October 2026. Scope: the 2,534 entries flagged in the frozen 125,264-entry machine draft, reviewed in nine disjoint checkpoints. This is a completed targeted model-review pass, not a full-dictionary linguistic review or human validation.

## Result

- All 2,534 originally flagged entries and their 3,677 source-aligned segments were individually reviewed exactly once against traditional and simplified Chinese, pinyin, every English source segment, the Ukrainian translation, and attached notes.
- 459 high-confidence segment corrections were applied across 456 entries. Eleven additional segment proposals and seven note proposals were held with their reasons and original evidence preserved.
- The final dictionary contains 125,264 entries and 199,737 aligned segments. All original source fields, ordering, IDs and 2,534 uncertainty flags are preserved.
- Including earlier work, the dictionary records 3,211 model-reviewed entries, 965 historical correction operations and 879 entries with corrections. These totals must not be confused with the 459 new corrections in this pass.
- Human-validated entries: zero. Unflagged entries outside this pass: 122,730. No accuracy estimate for the complete dictionary can be inferred from this deliberately difficult, flagged subset.

Authoritative final dictionary SHA-256:
`166a286a68f278b73c3307284dbee879451c262608b1cbe0f8e9d6eca2d4474b`

Frozen original dictionary SHA-256:
`cdf73918ba4417090f8cdcc8d284ff3d47d65416e58de0efe7dcb610675fb465`

## Notes and the provenance repair

The original investigation confirmed 15 wrong-entry or contaminated notes. These were already present in the earlier public 85,596-entry snapshot. The same investigation found no assembly-time shifts of glosses across all 119,668 expansion entries in 1,197 batches: assembled source IDs, source fields and glosses matched their effective raw/correction outputs. That is an alignment result, not a guarantee that each translation was accurate.

Stale positional note composition during generation is strongly indicated by the recorded evidence; the exact original implementation was not retained, so its originating defect cannot be proved. No positional shift or guessed reassignment was used in the repair. Every presented note now has an exact entry/source binding and an explicit review disposition.

Final original-note dispositions:

| Disposition | Count |
| --- | ---: |
| Original note retained after review | 2,127 |
| Original superseded by a reviewed replacement | 385 |
| Original rejected and inactive | 18 |
| Original attachment still withheld and inactive | 4 |
| Total original notes | 2,534 |

There are 2,512 active notes and 407 quarantined originals. The latter includes 385 superseded originals, not just false notes. All 15 known contaminated originals are among the 18 rejected notes and remain inactive. The four withheld attachments belong to entries that have been reviewed; the internal legacy disposition label `quarantine_unreviewed` does not mean four entries were skipped. No originally flagged entry remains unreviewed.

All original uncertainty flags remain, including cases where a warning or translation was corrected. Consumers must not derive flags from whether the active notes list is empty.

## What remains uncertain

The reviewers recorded 1,109 acceptable outcomes, 552 correction-proposed outcomes and 873 deferred outcomes. Application review and conservative holds produce 880 unresolved compiled ratings. The editorial priority inventory contains 882 distinct entries: deferred reviewer outcomes, held proposals or withheld note attachments. Two entries with applied corrections also have held proposals and therefore belong in that inventory despite their other compiled ratings.

A separate inventory preserves the reviewers' verbatim uncertainty text for 1,978 entries. This is not a count of distinct verified defects: it also contains source caveats, unresolved terminology and issues partly addressed by corrections. The complete explanations and exact source/review bindings are in `EDITORIAL_FOLLOWUP_QUEUE.json`.

Unresolved topics include rare characters and readings, contradictory English source glosses, historical units and names, and specialist botanical, zoological or chemical terminology. Source Chinese, pinyin and English were intentionally not silently rewritten. Descriptive Ukrainian alternatives were preserved where a standardized name could not be established.

## Verification and reproducibility

- The final versioned independent verifier passed 59,649 structural/provenance checks.
- The combined independent final audit passed 37,902 checks and verified a 141-file evidence inventory. The component totals below are included in that combined count, not additional independent observations.
- A separate cumulative auditor reconstructed the dictionary, note ledger and quarantine without importing the compiler/gate or reading any intermediate dictionary; it passed 23,215 checks across 133 evidence files.
- The held-decision audit passed 6,213 checks, including exact applied/held bindings and conservative note activation.
- The separate editorial-queue audit passed 8,428 count, union and source/review-binding checks.
- Portable replay passed 46 mechanics and negative-probe checks, including isolated final-candidate reconstruction in normal and optimized Python, integrity/tamper rejection, and safe output handling. The isolated replay does not need earlier checkpoint dictionaries.
- The unchanged note-gate regression suite passed 20 tests in normal Python and the same 20 with `-O`.

The gate binds every patch and note event to an entry ID, exact source hash, baseline record hash and before-value. It fails closed on mismatches and protects reference tokens, original flags and source fields. This prevents a later positional attachment from silently entering the candidate; semantic review remains necessary to establish whether a note or gloss itself is sound.

For portable reconstruction, use the frozen original dictionary, the six final candidate files, `note_gate.py` and `replay_cumulative_overlay.py`. The final handoff and artifact inventory identify exact hashes. The candidate's frozen build summary retains its pre-verification status text; verification is recorded separately in `checkpoint-009/VERIFIED_CHECKPOINT.json` and the final independent audit files rather than rewriting an already-built candidate.

## Packaging boundary

Use only the final candidate dictionary as the source for current CSV, progress data, flags, notes and review metadata. `NOTE_REVIEW_LEDGER.json` describes dispositions; `NOTE_QUARANTINE.json`, the original dictionary and historical raw audits are evidence, not active annotation sources. Never merge superseded notes or historical review queues back into current output.

Earlier candidates, checkpoint evidence, original raw outputs and existing archives remain unchanged. Preserve the existing source attribution, license and source metadata. The final handoff separates active data, quarantined history, reproducibility materials and earlier evidence.

No public write or runtime promotion was performed by this review. Publication is a separate parent-controlled step. This bounded review stops here. After its handoff, sensible separately scoped work would be source-editor resolution of the flagged specialist issues, bilingual human validation, and a later learner/HSK pass over currently unflagged entries.
