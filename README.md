# Chinese–Ukrainian dictionary · machine draft

125,264 entries and 199,737 aligned English–Ukrainian meaning segments cover 100% of the **pinned CC-CEDICT source**, not a measured accuracy rate. Chinese, pinyin, English and source fields are preserved. Ukrainian translations remain a machine draft. **Zero entries are human validated; app runtime use is not approved.**

## Current files

- [dictionary.json](dictionary.json) and [dictionary.csv](dictionary.csv): current translations, original flags and active notes.
- [progress.json](progress.json): counts and current data hashes; [SHA256SUMS.txt](SHA256SUMS.txt): complete publication inventory.
- [CURRENT_REVIEW_QUEUE.json](CURRENT_REVIEW_QUEUE.json): all 2,534 originally flagged entries, using current text.
- [CURRENT_EDITORIAL_FOLLOWUP.json](CURRENT_EDITORIAL_FOLLOWUP.json): 882 distinct priority entries for further editorial work.
- [FINAL_FLAGGED_REVIEW_REPORT.md](FINAL_FLAGGED_REVIEW_REPORT.md): frozen review report; [NOTE_REVIEW_LEDGER.json](NOTE_REVIEW_LEDGER.json): note dispositions and provenance, including inactive originals. The ledger is **not** an active annotation source.

## What was reviewed

The targeted pass reviewed all 2,534 originally flagged entries (3,677 segments). It applied 459 high-confidence segment corrections across 456 entries. Cumulative recorded model review covers 3,211 distinct entries, including earlier work; cumulative correction counters record 965 operations across 879 entries. The 122,730 originally unflagged entries were outside this pass. Model metadata records requested models, without independent backend attestation.

873 deferred reviewer outcomes, 880 unresolved compiled ratings and 882 distinct editorial follow-up entries measure different things; none is a corpus-wide error count. No overall linguistic accuracy claim is made. Eleven segment proposals and seven note proposals were held across 15 entries.

The original 2,534 flags remain. There are 2,512 active notes; 22 flagged entries have no active note. The review retained 2,127 notes, replaced 385, rejected 18 and withheld four. The 407 quarantined original texts include all 15 known contaminated originals; they are inactive. Use **dictionary.json only** for current annotations. Never merge old queues, the ledger or quarantined notes into active text.

## Reproducibility and history

[audit/](audit/README.md) contains the approved, hashed review evidence. [history/frozen-original/](history/frozen-original/) preserves the pre-review full draft for replay. [history/published-baseline-85596/](history/published-baseline-85596/) retains all earlier public audit files byte for byte; its dictionary and CSV remain available at immutable Git commit `590c6870fb648a8867cd0e69d4f801c91bf980ae`. Historical text may contain known incorrect notes and must not be used as current guidance.

Frozen reports retain their original private/pending-release timestamps and wording. Current publication status is in [PUBLICATION.json](PUBLICATION.json) and this README. To verify this exact release, run `python3 -B scripts/validate.py` on an extracted source ZIP (without `.git`). The frozen validator checks the accepted data, evidence inventory, CSV, queues, hashes, replay and note-gate tests. Subsequent translation changes need a new review overlay and release baseline; do not rewrite frozen evidence to make checks pass.

## Help improve it

Read [CONTRIBUTING.md](CONTRIBUTING.md) and use the [issue templates](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose). Reports and proposed corrections are welcome; a finished translation is optional. The Laowai app currently offers English and French dictionaries. This public draft is not integrated into the app.

## Source and licence

CC-CEDICT supplies Chinese headwords, pinyin and English definitions. The Ukrainian glosses were generated from those English meanings. Attribution and the pinned source are in [source.json](source.json); keep those notices and [CC BY-SA 4.0](LICENSE) when sharing or adapting. Workbook material, HSK membership metadata and nine supplementary constructions are excluded.
