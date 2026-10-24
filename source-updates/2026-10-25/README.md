# Source refresh · 25 October 2026

This separate release imports the official CC-CEDICT gzip dated **2026-10-23T23:15:44Z**, with 125,314 records and 199,726 English segments. The raw upstream bytes and parsed rows are preserved, including line numbers. The [manifest](manifest.json) pins every released data file by SHA-256 and size, and binds the frozen 13 October source and 19 October overlay.

The diff is 83 added, 33 retired, 77 changed English and 125,154 unchanged English records. Identity is the first 16 hexadecimal characters of SHA-256 over case-sensitive traditional, simplified and numbered pinyin separated by tabs. No case-folding or reading normalization is used.

- `upstream.txt.gz`: exact downloaded official snapshot, SHA-256 `e6e14c761ebc1e66ae2ad7b08fc4c577d6927472bb059d70db6111f0c06abee9`.
- `source-records.json.gz`: parsed complete source; `source-diff.json`: exact identity/meaning diff.
- `translations.json.gz`: 122,291 qualified exact-upstream translations; `held-records.json.gz`: 3,023 excluded rows and reasons.
- `qualified-revisions.json.gz`: 1,266 independently accepted frozen-source translations, upstream replacements or local source corrections, with exact candidates and verdicts. Local corrections do not silently rewrite CC-CEDICT.
- `held-resolution-outcomes.json.gz`: outcomes of every one of the 3,191 original and 135 baseline prior holds, including 2,042 original and 11 baseline unresolved parents.
- `revision-identity-groups.json`: candidate targets grouped by exact headword/reading identity, including 2 overlapping targets. These remain separate proposals with no automatic alias, merge or overwrite.
- `review-bundle.json.gz`: all current source-bound primary judgments, candidates, independent verdicts and preserved superseded evidence.
- `human-validation.json`: three maintainer gloss approvals against English; zero Chinese-language validations.

To replay from the repository root:

```sh
python3 -B scripts/test_refresh_release.py
python3 -B scripts/refresh_release.py validate
python3 -B scripts/check_release.py
```

The refresh validator verifies upstream bytes, exact carry-forward source matching, all 160 changed/new admissions, complete 3,326 prior-hold coverage, candidate/source/parent/prior-review hashes, segment alignment, preserved Chinese/pinyin references and different-agent exact-hash acceptance. Unknown upstream bytes, edited translations with stale approvals, self-review, and model claims of human/runtime approval fail closed. The complete checker also replays both historical publication layers with their original validators. Model-agent keys distinguish workers in this run; they are not independently attested model backend identities.

Accepted local source corrections are reviewable proposals for a separate integration layer. Do not inject them into app data by parent ID alone: compare all source fields, resolve new headword/reading identities and collisions, and run a new app mapping audit. This release is not approved as an automatic runtime replacement. Unresolved records remain excluded. Human feedback is scoped to the exact displayed English and Ukrainian text; it does not certify Chinese or overall accuracy.

Official source: [MDBG CC-CEDICT](https://www.mdbg.net/chinese/dictionary?page=cc-cedict), [gzip export](https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz). Attribution: CC-CEDICT contributors, MDBG, founder Paul Andrew Denisowski and Ukrainian project contributors. Source-derived adaptations are distributed under [CC BY-SA 4.0](../../LICENSE). External dictionary and institutional references support individual factual checks; their prose or bulk datasets are not included in this release.
