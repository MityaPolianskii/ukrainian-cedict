# Ukrainian CEDICT: flagged-entry model review completed

PRIVATE CANDIDATE. No publication or runtime promotion has been performed. Parent release decision is pending. This is a machine-translated dictionary with model review, not human validation or corpus-wide accuracy certification.

## Current data

[Dictionary JSON](dictionary.json) and [CSV](dictionary.csv): 125,264 entries / 199,737 aligned segments, 100% coverage of the pinned CC-CEDICT source. Source coverage does not imply translation accuracy. Chinese, pinyin, English and source identity fields remain unchanged.

Only dictionary.json supplies current annotations. [Current review queue](CURRENT_REVIEW_QUEUE.json) contains the same current records for all 2,534 original flags. Flags remain present even when no note is active. [Note disposition ledger](NOTE_REVIEW_LEDGER.json) is provenance evidence and includes inactive original text; never render every ledger note as active.

## What this review established

All 2,534 originally flagged entries / 3,677 source segments received model review. The 122,730 originally unflagged entries were outside this pass; no broad HSK/unflagged review was performed. There are zero human-validated entries. Requested model selection is recorded, without independent runtime backend attestation.

This pass applied 459 high-confidence segment corrections across 456 entries. Eleven segment proposals and seven note proposals were held, affecting 15 entries. Cumulative counts including earlier work: 3,211 model-reviewed entries; 965 corrected segments across 879 entries.

## Remaining uncertainty: different measures

- 873 entries received a deferred reviewer outcome.
- 880 entries have unresolved compiled ratings.
- 882 distinct entries are in the editorial-priority follow-up inventory.
- 1,978 entries appear in the broader reviewer-uncertainty inventory.

These are different documented concepts, not interchangeable counts of mistranslations. See [review report](FINAL_FLAGGED_REVIEW_REPORT.md), [current editorial records](CURRENT_EDITORIAL_FOLLOWUP.json), and historical explanatory evidence under audit/review/EDITORIAL_FOLLOWUP_QUEUE.json.

## Active notes and quarantine

2,127 original notes were retained after review and 385 replaced: 2,512 active notes. Eighteen attachments were rejected and four reviewed attachments remain withheld: 22 flagged entries have no active note. All 2,534 original flags are preserved. 407 original note texts are quarantined as history, including superseded originals; quarantine does not mean every original assertion is false. No originally flagged entry remains unreviewed.

All content under audit/ and history/ is evidence, not current annotation data. Older dictionaries, note quarantine, proposed corrections and historical queues must never be merged into active notes. The complete 154-file hashed review inventory and frozen original are included for portable reconstruction. Checkpoint 001 archives remain separately preserved.

## Reproduce and verify

Run python -B audit/review/replay_cumulative_overlay.py --baseline history/frozen-original/dictionary.json --candidate-dir audit/review/candidate-checkpoint-009. This reconstructs the final candidate without intermediate dictionaries. Run python -B scripts/validate.py --root . to check current derived data and packaged evidence. Gate regression tests are in audit/review/test_note_gate.py.

[LICENSE](LICENSE) and [source metadata](source.json) are preserved unchanged.
