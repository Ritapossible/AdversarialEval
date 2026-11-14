# Pool upload: SECURITY_REVIEW_GENERAL (2026-11-14)

First network action of the project (testnet, node `https://devnode.telegraphprotocol.com`).
Uploaded through the Anjoman dashboard (Evaluators, Contribute evaluation material), signed
in the browser by the contributor wallet `0x31Cf659edcDd1A6bF98302cbA5E7CEA8dc143095`
(Sepolia). Dashboard reply: "Sent. 81 stored, 0 already there, 0 refused."

What was uploaded: 81 OSV-generated preference pairs (F2 version ranges, F7 field
contradictions, F1 misattributed ids), each citing its GitHub advisory URL
(`source_kind: advisory`). OSV's version query checked every label, and Ritapossible
human-reviewed and approved every pair on 2026-11-14. Kit dataset gate PASS; strongest
naive scorer 54%. Row content stays private (`data/private/`, git-ignored).

## Verified with the node API (pasted output)

`GET /api/evalpool/submissions/mine?submitter=0x31Cf...3095&intent_id=SECURITY_REVIEW_GENERAL`

- rows: **81**; status: {'admitted': 81}; provenance_class: {'attested': 81}
- first row: `{"intent_id": "SECURITY_REVIEW_GENERAL", "row_hash": "8227e5f9c4e6b64734066b48ca4e9d4b91d3473c1113cd0d7733a0ee90a09056", "case_id": "3e52d013538700ad38503c2abd0b12026dbbe15ce433fac793313ce4aaad4102", "status": "admitted", "provenance_class": "attested", "quality_rules_version": "evalpool-quality-v1", "created_at": "2026-11-14T20:21:25.557257Z", "updated_at": "2026-11-14T20:21:25.560125Z"}`

`GET /api/evalpool/status?intent_id=SECURITY_REVIEW_GENERAL`

```
{"counts": [{"status": "admitted", "count": 81}, {"status": "eligible", "count": 199}, {"status": "quarantine", "reason": "rate_limited", "count": 555}, {"status": "rejected", "reason": "near_duplicate", "count": 7}], "by_state": {"admitted": 81, "eligible": 199, "quarantine": 555, "rejected": 7}, "submitters": 10, "eligible_submitters": 9}
active snapshot: {"corpus_version": "6f993408a062a1d44f860ef26e370a19dab11502284f118e347b868c9d84e0fa", "rows": 199, "submitters": 9, "qualification": 102, "ranking": 97, "published_at": "2026-11-12T03:45:02.886353Z", "activation_epoch": 2071}
```

## Reading

- All 81 rows are **admitted** and **attested**: each has an http(s) `source_url` and a
  `source_kind` that isn't one of the generated kinds. None was refused or flagged as a
  near-duplicate.
- Admitted rows are re-checked and frozen at the next epoch rollover, and join the active
  corpus (now 199 rows from 9 submitters) from the epoch after. We are the 10th submitter.
  Re-query after the rollover to confirm `eligible` before claiming the rows are in use.
