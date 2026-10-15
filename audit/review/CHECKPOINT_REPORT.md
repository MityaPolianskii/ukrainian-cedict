# Ukrainian CEDICT: independent model-review checkpoint 001

The completed original machine draft is preserved unchanged. This review is not human validation or a corpus-wide accuracy estimate.

## Completed

- 300 flagged entries, covering 920 aligned English/Ukrainian segments, individually reviewed with both Chinese forms and pinyin.
- 100 acceptable as translated; 138 deferred for source or specialist issues; 62 entries with correction proposals.
- 46 segment proposals; 42 high-confidence corrections applied only in the separate private candidate. Four medium-confidence or disputed source-interpretation proposals remain unapplied.
- All 125,264 source entries and 199,737 aligned segments preserved. Historical plus new explicitly model-reviewed records: 979; human-validated: zero.

## Metadata defect and containment

A full topic-alignment review of 167 effective notes in the first 10,000-entry expansion identified 15 contaminated or wrong-entry notes. They are already in the earlier 85,596-entry public baseline. Three other notes make directly false metadata claims, and three contain ambiguous preservation claims.

The defect predates final assembly. All 119,668 expansion entries matched their effective raw/correction outputs by ID, and the 15 affected Ukrainian gloss arrays describe their own entries. This does not establish the semantic accuracy of every gloss. Evidence supports stale positional note composition; the exact initial generation helper is unavailable, so no specific missing code line is claimed.

The new note gate binds each restoration to entry ID, full source fingerprint, baseline-record hash and exact original-note hash. All unreviewed legacy notes are inactive by default. Every original uncertainty flag remains intact; every displaced or unreviewed note is preserved in a separate evidence ledger.

- 272 reviewed original notes remain active.
- 15 notes are replaced with reviewed corrections.
- 13 reviewed notes are rejected and quarantined.
- 2,234 unreviewed notes are quarantined pending review.
- Active notes: 287. Original notes preserved in quarantine: 2,262, including the 15 superseded originals.
- All 15 confirmed contaminated originals are absent from active dictionary annotations.

The original frozen dictionary SHA-256 remains cdf73918ba4417090f8cdcc8d284ff3d47d65416e58de0efe7dcb610675fb465. The separate corrected dictionary SHA-256 is 1654a30902d133ad120128d43a8e44a4275bae440de8dc5ec7fe60a9d65c2781.

## Examples of language corrections

- Administrative “banner” → “адміністративна одиниця (хошун)”, rather than “прапор”.
- 事實上 / as a matter of fact → “насправді; фактично”.
- 組圖 / image → “зображення”, rather than abstract “образ”.
- 方陣 → “квадратна матриця”, with the broader English-source wording still documented.
- Correctly distinguish a prohibition (“off limits”) from simple inaccessibility.

## Verification and next scope

The gate has 20 regression tests, passing in ordinary and optimized Python. Tests include cross-entry substitution, stale source/note hashes, reordered batches, malformed notes, missing evidence, no-op and medium-confidence patches, reference loss, immutable originals and preserved flags. Final independent output validation and package-level checks are tracked separately.

Next: review the remaining 2,234 flagged entries in eight bounded checkpoints of at most 300 entries; keep source contradictions separate from Ukrainian mistranslations. Then use an explicitly versioned HSK/learner list to review common vocabulary, including currently unflagged entries. Specialist taxonomy, historical names and contradictory Chinese/English senses should remain unresolved until evidence supports a correction. Never label these model passes as human review.

The full remaining flagged queue is prepared with original context. No new public writes or runtime promotion were performed by this review.
