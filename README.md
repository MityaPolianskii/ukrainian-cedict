# Chinese–Ukrainian dictionary · machine draft

125,264 entries and 199,737 aligned English–Ukrainian meaning segments cover 100% of the **pinned CC-CEDICT source**, not a measured accuracy rate. Chinese, pinyin, English and source fields are preserved. Ukrainian translations remain a machine draft. **Zero entries are human validated. The original full draft is not approved for direct runtime use; qualified translations are distributed separately.**

## Current maintenance status · 25 October 2026

Ukrainian support is publicly available in Laowai. The US App Store lists **5.3.16**, released 24 October 2026, with Apple, Google and email sign-in and app/website sync. The [online dictionary](https://laowaiapp.com/dictionary/#lang=uk) uses the app-admitted Ukrainian dataset; [the project page](https://laowaiapp.com/ukrainian-dictionary/) explains the downloads and their limits. This delivery status does not approve held translations or establish human validation. See [STATUS.json](STATUS.json) for dated sources and separately counted coverage.

The translated source remains pinned to **13 October 2026 / 125,264 entries**. MDBG reported **23 October 2026 / 125,314 entries** when checked on 25 October: a net difference of 50, not an exact count of added or changed meanings. No newer source has been imported or translated in this maintenance update. A source refresh must compare exact headword, reading and English meanings, then review changed translations in a new overlay. Existing 100% coverage applies only to the pinned source.

Run `python3 -B scripts/check_release.py` from a complete checkout to verify the frozen draft, the resolved overlay and current status together. This checks both publication layers without changing their frozen validators. Automated CI and recurring upstream synchronization are not configured.

## Review progress · 19 October 2026

Accepted model-review records now cover **125,264 original entries / 199,737 meaning segments**. All **8,291 correction or held-entry targets** received source-bound Sol follow-up. New or newly resolved final translations also received a different Sol validator. Qualified corpus translations contain **122,073 records**; **3,191 whole records** remain excluded with explicit reasons. Coverage includes held judgments and does not measure linguistic accuracy. Human validation remains zero.

The corrected translations are published as a [separate overlay](review-overlays/2026-10-18-sol-resolved/README.md). **The original dictionary.json, CSV and frozen historical evidence retain their existing bytes.** Their historical review counts overlap with this later review and must not be added. Use the overlay's source-bound review evidence and validator when applying its qualified translations; do not merge held records into qualified output.

Another **1,758 English app-baseline meanings** form a separate source universe: **1,623 qualified / 135 held**. Their actual English input, database identity and CC-CEDICT-derived provenance are preserved. These additions do not increase the original 125,264-record coverage count.

The runtime mapping audit accounts for every one of **124,725 existing English/French app entries**: **121,420 qualified / 3,305 requiring labelled English fallback**. Another 2,297 original corpus records have no strict app counterpart. All 13 bundled HSK lists have a private term/readings audit with concrete unresolved reasons. The public projection contains aggregate counts and exact audit/catalog hashes; it omits list membership, ordering and per-term app IDs while their separate redistribution lineage remains unresolved. It does not certify official HSK completeness, preferred-reading coverage or an accuracy percentage. Runtime source qualification and actual App Store availability have separate delivery receipts. The original full machine draft is not itself approved for runtime use.

The [overlay manifest](review-overlays/2026-10-18-sol-resolved/manifest.json), [runtime and HSK coverage](review-overlays/2026-10-18-sol-resolved/runtime-coverage.json) and [progress.json](progress.json) retain the separately counted results. The overlay includes no Tatoeba example texts or audio and makes no new public app-release claim.

## Current files

- [review-overlays/2026-10-18-sol-resolved/](review-overlays/2026-10-18-sol-resolved/README.md): latest qualified translations and held decisions.
- [dictionary.json](dictionary.json) and [dictionary.csv](dictionary.csv): frozen 15 October machine draft, original flags and draft annotations.
- [progress.json](progress.json): counts and current data hashes; [SHA256SUMS.txt](SHA256SUMS.txt): complete publication inventory.
- [CURRENT_REVIEW_QUEUE.json](CURRENT_REVIEW_QUEUE.json): historical 15 October queue of 2,534 originally flagged entries; it is not the current overlay backlog.
- [CURRENT_EDITORIAL_FOLLOWUP.json](CURRENT_EDITORIAL_FOLLOWUP.json): historical 882-entry follow-up queue; use the overlay held records for current unresolved translations.
- [FINAL_FLAGGED_REVIEW_REPORT.md](FINAL_FLAGGED_REVIEW_REPORT.md): frozen review report; [NOTE_REVIEW_LEDGER.json](NOTE_REVIEW_LEDGER.json): note dispositions and provenance, including inactive originals. The ledger is **not** an active annotation source.

## What was reviewed in the 15 October download

The targeted pass reviewed all 2,534 originally flagged entries (3,677 segments). It applied 459 high-confidence segment corrections across 456 entries. Cumulative recorded model review covers 3,211 distinct entries, including earlier work; cumulative correction counters record 965 operations across 879 entries. The 122,730 originally unflagged entries were outside this pass. Model metadata records requested models, without independent backend attestation.

873 deferred reviewer outcomes, 880 unresolved compiled ratings and 882 distinct editorial follow-up entries measure different things; none is a corpus-wide error count. No overall linguistic accuracy claim is made. Eleven segment proposals and seven note proposals were held across 15 entries.

The original 2,534 flags remain. There are 2,512 active notes; 22 flagged entries have no active note. The review retained 2,127 notes, replaced 385, rejected 18 and withheld four. The 407 quarantined original texts include all 15 known contaminated originals; they are inactive. Use **dictionary.json only** for current annotations. Never merge old queues, the ledger or quarantined notes into active text.

## Reproducibility and history

[audit/](audit/README.md) contains the approved, hashed review evidence. [history/frozen-original/](history/frozen-original/) preserves the pre-review full draft for replay. [history/published-baseline-85596/](history/published-baseline-85596/) retains all earlier public audit files byte for byte; its dictionary and CSV remain available at immutable Git commit `590c6870fb648a8867cd0e69d4f801c91bf980ae`. Historical text may contain known incorrect notes and must not be used as current guidance.

Frozen reports retain their original private/pending-release timestamps and wording. Current publication status is in [PUBLICATION.json](PUBLICATION.json) and this README. To verify this exact release, run `python3 -B scripts/validate.py` on an extracted source ZIP (without `.git`). The frozen validator checks the accepted data, evidence inventory, CSV, queues, hashes, replay and note-gate tests. Subsequent translation changes need a new review overlay and release baseline; do not rewrite frozen evidence to make checks pass.

## Help improve it

Read [CONTRIBUTING.md](CONTRIBUTING.md) and use the [issue templates](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose). Reports and proposed corrections are welcome; a finished translation is optional. The public Laowai app and website offer Ukrainian lookup using qualified, source-bound translations and labelled English fallback. The complete raw machine draft is not the runtime dataset. For current unresolved work, start with the [3,191 held original-source records](review-overlays/2026-10-18-sol-resolved/corpus/held-records.json.gz) and the separate [135 held app-baseline records](review-overlays/2026-10-18-sol-resolved/baseline-held-records.json.gz). Report the final overlay text when present; identify historical draft text explicitly.

## Source and licence

CC-CEDICT supplies Chinese headwords, pinyin and English definitions. The Ukrainian glosses were generated from those English meanings. Attribution and the pinned source are in [source.json](source.json); keep those notices and [CC BY-SA 4.0](LICENSE) when sharing or adapting. Workbook material, HSK membership metadata and nine supplementary constructions are excluded.
