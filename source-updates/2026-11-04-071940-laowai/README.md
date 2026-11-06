# 4 November 2026, 07:19 UTC source projection — draft

Local source-bound proposal, not published or app-runtime approval. Each locale contains 125,365 current source records. Against the retained 3 November 00:50 UTC projection, 8 records were added, 5 have changed source meanings and 3 retired; the complete prior snapshot remains intact. The 13 new or changed targets per locale were independently AI-reviewed against the current source. Unchanged translations retain their original provenance, including CFDICT’s CC BY-SA 3.0 source status. Whole-record translations do not claim one-to-one alignment of individual senses. See ATTRIBUTION.md.

The bundled standalone validator checks the exact source, prior projection, delta, payload hashes and JSON/CSV/XML agreement. It does not replay private review evidence or independently approve this public projection. From this directory in a repository containing the retained 3 November 00:50 UTC snapshot, run the corresponding locale command:

```sh
python3 validate_public_advance.py fr --source source-records.json.gz --prior ../2026-11-03-005019-laowai/fr/dictionary.json.gz
python3 validate_public_advance.py uk --source source-records.json.gz --prior ../2026-11-03-005019-laowai/uk/dictionary.json.gz
```

No application row IDs, HSK memberships, user progress, lesson content or media are exported. No new human validation is claimed.
