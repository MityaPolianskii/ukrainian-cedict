# Chinese–Ukrainian dictionary · machine draft

The current project download uses the **23 October 2026 CC-CEDICT snapshot: 125,314 records / 199,726 English meaning segments**. It contains **122,291 qualified, source-bound Ukrainian translations**, with 3,023 exact-upstream records still held. Accepted local source corrections are a separate layer. Model review is not an accuracy measurement. **Three Ukrainian glosses have maintainer approval against their English source; zero records have human Chinese-language validation.**

## New contribution for review · 28 October 2026

[Laowai record-level proposals](contributions/2026-10-28-laowai/README.md) add 3,184 independently AI-reviewed whole-record translations: 3,018 currently held exact-upstream records and 166 alternatives. This is a separately validated contribution layer, with zero new human validation and no automatic runtime or current-release approval. Existing release counts and frozen data remain unchanged. These whole-record glosses need an editorial segmentation step before import into the current per-sense format.

## Source refresh · 25 October 2026

[Download format and replay instructions](source-updates/2026-10-25/README.md) · [manifest](source-updates/2026-10-25/manifest.json) · [translations JSON.gz](source-updates/2026-10-25/translations.json.gz) · [accepted source revisions](source-updates/2026-10-25/qualified-revisions.json.gz) · [STATUS.json](STATUS.json)

The verified source comparison found **83 additions, 33 retirements and 77 changed English records**; 125,154 records have unchanged English. All **160 added or changed records** have individually authored translations and an exact-hash check by a different model agent. Qualified prior translations are carried forward only when Chinese, pinyin and English meanings match exactly.

All **3,191 original-source holds and 135 app-baseline holds** were reaudited against their preserved source and prior judgment. **1,149 original and 124 baseline parents now have accepted revisions, reviewed upstream replacements or source retirement (6 original parents retired; 1 replaced by reviewed upstream changes); 2,042 original and 11 baseline parents remain unresolved.** The release contains 1,266 independently accepted revision candidates. A source correction can resolve a historical parent while the exact upstream row remains held; these counts describe different layers and must not be added.

The [first human review batch](source-updates/2026-10-25/human-validation.json) records approval of 門窗 / 门窗, 三思 and 收稿 against the displayed English meanings. It does not claim Chinese-language validation, a corpus-wide human review, or measured linguistic accuracy. Historical zero-human figures below describe their dated releases.

Ukrainian support is already publicly available in Laowai; the US App Store listed **5.3.16**, released 24 October 2026. The [online dictionary](https://laowaiapp.com/dictionary/#lang=uk) uses the separately admitted app dataset. **This source refresh has not changed the app runtime dataset.** Its mapping, remaining fallbacks and future app admission need a separate audit. [Website project page](https://laowaiapp.com/ukrainian-dictionary/).

Run `python3 -B scripts/check_release.py` from a complete checkout to verify the frozen draft, previous overlay and new source refresh. `python3 -B scripts/check_release.py --status-only` checks metadata only. Automated CI and recurring upstream synchronization are not configured. The original `dictionary.json`, CSV, source metadata, historical judgments and frozen validators retain their existing bytes.

## Review progress · 19 October 2026

Accepted model-review records now cover **125,264 original entries / 199,737 meaning segments**. All **8,291 correction or held-entry targets** received source-bound Sol follow-up. New or newly resolved final translations also received a different Sol validator. Qualified corpus translations contain **122,073 records**; **3,191 whole records** remain excluded with explicit reasons. Coverage includes held judgments and does not measure linguistic accuracy. Human validation remains zero.

The corrected translations are published as a [separate overlay](review-overlays/2026-10-18-sol-resolved/README.md). **The original dictionary.json, CSV and frozen historical evidence retain their existing bytes.** Their historical review counts overlap with this later review and must not be added. Use the overlay's source-bound review evidence and validator when applying its qualified translations; do not merge held records into qualified output.

Another **1,758 English app-baseline meanings** form a separate source universe: **1,623 qualified / 135 held**. Their actual English input, database identity and CC-CEDICT-derived provenance are preserved. These additions do not increase the original 125,264-record coverage count.

The runtime mapping audit accounts for every one of **124,725 existing English/French app entries**: **121,420 qualified / 3,305 requiring labelled English fallback**. Another 2,297 original corpus records have no strict app counterpart. All 13 bundled HSK lists have a private term/readings audit with concrete unresolved reasons. The public projection contains aggregate counts and exact audit/catalog hashes; it omits list membership, ordering and per-term app IDs while their separate redistribution lineage remains unresolved. It does not certify official HSK completeness, preferred-reading coverage or an accuracy percentage. Runtime source qualification and actual App Store availability have separate delivery receipts. The original full machine draft is not itself approved for runtime use.

The [overlay manifest](review-overlays/2026-10-18-sol-resolved/manifest.json), [runtime and HSK coverage](review-overlays/2026-10-18-sol-resolved/runtime-coverage.json) and [progress.json](progress.json) retain the separately counted results. The overlay includes no Tatoeba example texts or audio and makes no new public app-release claim.

## Files and preserved history

- [source-updates/2026-10-25/](source-updates/2026-10-25/README.md): current source refresh, qualified translations, accepted local source corrections and held outcomes.
- [review-overlays/2026-10-18-sol-resolved/](review-overlays/2026-10-18-sol-resolved/README.md): preserved 19 October qualified translations and held decisions.
- [dictionary.json](dictionary.json) and [dictionary.csv](dictionary.csv): frozen 15 October machine draft, original flags and draft annotations.
- [progress.json](progress.json): frozen draft and 19 October counts and hashes; [SHA256SUMS.txt](SHA256SUMS.txt): complete publication inventory.
- [CURRENT_REVIEW_QUEUE.json](CURRENT_REVIEW_QUEUE.json): historical 15 October queue of 2,534 originally flagged entries; it is not the current overlay backlog.
- [CURRENT_EDITORIAL_FOLLOWUP.json](CURRENT_EDITORIAL_FOLLOWUP.json): historical 882-entry follow-up queue; use the current [source-updates/2026-10-25/held-records.json.gz](source-updates/2026-10-25/held-records.json.gz) and prior-hold outcomes for unresolved work.
- [FINAL_FLAGGED_REVIEW_REPORT.md](FINAL_FLAGGED_REVIEW_REPORT.md): frozen review report; [NOTE_REVIEW_LEDGER.json](NOTE_REVIEW_LEDGER.json): note dispositions and provenance, including inactive originals. The ledger is **not** an active annotation source.

## What was reviewed in the 15 October download

The targeted pass reviewed all 2,534 originally flagged entries (3,677 segments). It applied 459 high-confidence segment corrections across 456 entries. Cumulative recorded model review covers 3,211 distinct entries, including earlier work; cumulative correction counters record 965 operations across 879 entries. The 122,730 originally unflagged entries were outside this pass. Model metadata records requested models, without independent backend attestation.

873 deferred reviewer outcomes, 880 unresolved compiled ratings and 882 distinct editorial follow-up entries measure different things; none is a corpus-wide error count. No overall linguistic accuracy claim is made. Eleven segment proposals and seven note proposals were held across 15 entries.

The original 2,534 flags remain. There are 2,512 active notes; 22 flagged entries have no active note. The review retained 2,127 notes, replaced 385, rejected 18 and withheld four. The 407 quarantined original texts include all 15 known contaminated originals; they are inactive. Use **dictionary.json only** for current annotations. Never merge old queues, the ledger or quarantined notes into active text.

## Reproducibility and history

[audit/](audit/README.md) contains the approved, hashed review evidence. [history/frozen-original/](history/frozen-original/) preserves the pre-review full draft for replay. [history/published-baseline-85596/](history/published-baseline-85596/) retains all earlier public audit files byte for byte; its dictionary and CSV remain available at immutable Git commit `590c6870fb648a8867cd0e69d4f801c91bf980ae`. Historical text may contain known incorrect notes and must not be used as current guidance.

Frozen reports retain their original private/pending-release timestamps and wording. Current publication status is in [PUBLICATION.json](PUBLICATION.json) and this README. To verify this exact release, run `python3 -B scripts/validate.py` on an extracted source ZIP (without `.git`). The frozen validator checks the accepted data, evidence inventory, CSV, queues, hashes, replay and note-gate tests. Subsequent translation changes need a new review overlay and release baseline; do not rewrite frozen evidence to make checks pass.

## Help improve it

Read [CONTRIBUTING.md](CONTRIBUTING.md) and use the [issue templates](https://github.com/MityaPolianskii/ukrainian-cedict/issues/new/choose). Reports and proposed corrections are welcome; a finished translation is optional. The public Laowai app and website offer Ukrainian lookup using qualified, source-bound translations and labelled English fallback. The complete raw machine draft is not the runtime dataset. For unresolved work, use the [current exact-upstream holds](source-updates/2026-10-25/held-records.json.gz) and [outcomes of all 3,326 prior holds](source-updates/2026-10-25/held-resolution-outcomes.json.gz). Report the final overlay text when present; identify historical draft text explicitly.

## Source and licence

CC-CEDICT supplies Chinese headwords, pinyin and English definitions. The Ukrainian glosses were generated from those English meanings. Attribution and the pinned source are in [source.json](source.json); keep those notices and [CC BY-SA 4.0](LICENSE) when sharing or adapting. Workbook material, HSK membership metadata and nine supplementary constructions are excluded.
