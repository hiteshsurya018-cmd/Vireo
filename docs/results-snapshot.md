# Verified results snapshot

Run: `python scripts/run_digest.py --data-dir data/raw --out-dir outputs`

| Measure | Result |
|---|---:|
| Source rows | 12,528 |
| Duplicate ticket IDs | 653 |
| Unique tickets | 11,875 |
| Completed tickets | 11,266 |
| Completed with full 30-day observation | 10,484 |
| Repeat proxy in mature cohort | 1,369 / 10,484 = 13.06% |
| Target | 10.0% |
| Quarterly planning value | Rs 74,936 |
| First-response SLA breach rate | 8.85% |
| Tickets with a transfer | 8.76% |

Quarterly value: `650 × 13 × (0.1305799 - 0.10) × Rs 290`. This assumes avoided contacts, not just better labels. The export ends 30 June 2026; later resolved tickets cannot have a full 30-day observation period.

Repeat-rate hotspots in the mature cohort: Delivery & Shipping 17.1% (322/1,887), Audio Quality 16.7% (114/684), Charging & Battery 16.1% (132/819). These are proxy rates, not confirmed same-issue labels.

Latest full creation week begins 22 June 2026: 199 tickets. Recent repeat metrics are pending. The week beginning 29 June is partial. The separate category-consistency holdout has 2,375 tickets and 81.98% agreement with intake tags (18.02% disagreement); it does not validate the NMF theme labels.
