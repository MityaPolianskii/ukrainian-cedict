# Chinese–Ukrainian dictionary · machine draft

125,264 entries and 199,737 aligned English–Ukrainian meaning segments cover 100% of the **pinned CC-CEDICT source**, not a measured accuracy rate. Chinese, pinyin, English and source fields are preserved. Ukrainian translations remain a machine draft. **Zero entries are human validated; app runtime use is not approved.**

## Review progress · 19 October 2026

Accepted model-review records now cover **125,264 original entries / 199,737 meaning segments**. All **8,291 correction or held-entry targets** received source-bound Sol follow-up. New or newly resolved final translations also received a different Sol validator. Qualified corpus translations contain **122,073 records**; **3,191 whole records** remain excluded with explicit reasons. Coverage includes held judgments and does not measure linguistic accuracy. Human validation remains zero.

The corrected translations are published as a [separate overlay](review-overlays/2026-10-18-sol-resolved/README.md). **The original dictionary.json, CSV and frozen historical evidence retain their existing bytes.** Their historical review counts overlap with this later review and must not be added. Use the overlay's source-bound review evidence and validator when applying its qualified translations; do not merge held records into qualified output.

Another **1,758 English app-baseline meanings** form a separate source universe: **1,623 qualified / 135 held**. Their actual English input, database identity and CC-CEDICT-derived provenance are preserved. These additions do not increase the original 125,264-record coverage count.

The runtime mapping audit accounts for every one of **124,725 existing English/French app entries**: **121,420 qualified / 3,305 requiring labelled English fallback**. Another 2,297 original corpus records have no strict app counterpart. All 13 bundled HSK lists have a private term/readings audit with concrete unresolved reasons. The public projection contains aggregate counts and exact audit/catalog hashes; it omits list membership, ordering and per-term app IDs while their separate redistribution lineage remains unresolved. It does not certify official HSK completeness, preferred-reading coverage or an accuracy percentage. Runtime source qualification and actual App Store availability have separate delivery receipts. The original full machine draft is not itself approved for runtime use.

The [overlay manifest](review-overlays/2026-10-18-sol-resolved/manifest.json), [runtime and HSK coverage](review-overlays/2026-10-18-sol-resolved/runtime-coverage.json) and [progress.json](progress.json) retain the separately counted results. The overlay includes no Tatoeba example texts or audio and makes no new public app-release claim.

## Current files

- [dictionary.json](dictionary.json) and [dictionary.csv](dictionary.csv): current translations, original flags and active notes.
- [progress.json](progress.json): counts and current data hashes; [SHA256SUMS.txt](SHA256SUMS.txt): complete publication inventory.
- [CURRENT_REVIEW_QUEUE.json](CURRENT_REVIEW_QUEUE.json): all 2,534 originally flagged entries, using current text.
- [CURRENT_EDITORIAL_FOLLOWUP.json](CURRENT_EDITORIAL_FOLLOWUP.json): 882 distinct priority entries for further editorial work.
- [FINAL_FLAGGED_REVIEW_REPORT.md](FINAL_FLAGGED_REVIEW_REPORT.md): frozen review report; [NOTE_REVIEW_LEDGER.json](NOTE_REVIEW_LEDGER.json): note dispositions and provenance, including inactive originals. The ledger is **not** an active annotation source.

## What was reviewed in the 15 October download

The targeted pass reviewed all 2,534 originally flagged entries (3,677 segments). It applied 459 high-confidence segment corrections across 456 entries. Cumulative recorded model review covers 3,211 distinct entries, including earlier work; cumulative correction counters record 965 operations across 879 entries. The 122,730 originally unflagged entries were outside this pass. Model metadata records requested models, without independent backend attestation.

873 deferred reviewer outcomes, 880 unresolved compiled ratings and 882 distinct editorial follow-up entries measure different things; none is a corpus-wide error count. No overall linguistic accuracy claim is made. Eleven segment proposals and seven note proposals were held across 15 entries.

The original 2,534 flags remain. There are 2,512 active notes; 22 flagged entries have no active note. The review retained 2,127 notes, replaced 385, rejected 18 and withheld four. The 407 quarantined original texts include all 15 known contaminated originals; they are inactive. Use **dictionary.json only** for current annotations. Never merge old queues, the ledger or quarantined notes into active text.

## Reproducibility and history

[audit/](audit/README.md) contains the approved, hashed review evidence. [history/frozen-original/](history/frozen-original/) preserves the pre-review full draft for replay. [history/published-baseline-85596/](history/published-baseline-85596/) retains all earlier public audit files byte for byte; its dictionary and CSV remain available at immutable Git commit `590c6870fb648a8867cd0e69d4f801c91bf980ae`. Historical text may contain known incorrect notes and must not be used as current guidance.

Frozen reports retain their original private/pending-release timestamps and wording. Current publication status is in [PUBLICATION.json](PUBLICATION.json) and this README. To verify this exact release, run `python3 -B scripts/validate.py` on an extracted source ZIP (without `.git`). The frozen validator checks the accepted data, evidence inventory, CSV, queues, hashes, replay and note-gate tests. Subsequent translation changes need a new review overlay and release baseline; do not rewrite frozen evidence to make checks pass.

## Help improve it

Read [CONTRIBUTING.md](CONTRIBUTING.md) and use the [issue templates](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose). Reports and proposed corrections are welcome; a finished translation is optional. The public Laowai app offers English and French dictionaries. Ukrainian is in separate internal testing; the complete public draft is not integrated into the app.

## Source and licence

CC-CEDICT supplies Chinese headwords, pinyin and English definitions. The Ukrainian glosses were generated from those English meanings. Attribution and the pinned source are in [source.json](source.json); keep those notices and [CC BY-SA 4.0](LICENSE) when sharing or adapting. Workbook material, HSK membership metadata and nine supplementary constructions are excluded.
