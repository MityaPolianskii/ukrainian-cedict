# 31 October current-source public dictionary projections — draft

Local source-bound proposal, not published or app-runtime approval. Each locale contains 125,330 current source records. Against the reviewed 29 October projection, 12 entries are newly added, 16 have changed source meanings and 6 retired identities are omitted from this current view; the complete prior snapshot remains intact. The 28 new/changed targets per locale were independently AI-reviewed against the current source. Unchanged translations retain their original provenance, including CFDICT’s CC BY-SA 3.0 source status. Whole-record translations do not claim one-to-one alignment of individual senses. See ATTRIBUTION.md.

The bundled standalone validator checks the exact source, prior projection, delta, payload hashes and JSON/CSV/XML agreement. It does not replay private review evidence or independently approve this public projection. Exact prior dictionary SHA-256 values are pinned in validate_public_advance.py. From this directory in a repository containing the retained sibling 29 October snapshot, run the corresponding locale command:

```sh
python3 validate_public_advance.py fr --source source-records.json.gz --prior ../2026-10-29-laowai/fr/dictionary.json.gz
python3 validate_public_advance.py uk --source source-records.json.gz --prior ../2026-10-29-laowai/uk/dictionary.json.gz
```

No application row IDs, HSK memberships, user progress, lesson content or media are exported. No new human validation is claimed.
