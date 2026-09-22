# Vireo Audio support intelligence

Streamlit dashboard and CSV digest for the supplied support export. The weekly view includes interactive charts for ticket volume, complaint mix, repeat rates, product hotspots, category movement, and channel SLA. Python 3.11+ is required.

## Start

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app/app.py
```

On macOS/Linux, replace `.venv\Scripts\python` with `.venv/bin/python`. Place the five supplied CSV files in `data/raw/`, or enter another folder in the app sidebar. Raw files are excluded from Git.

For batch output and evaluation:

```powershell
.venv\Scripts\python scripts/run_digest.py --data-dir data/raw --out-dir outputs
.venv\Scripts\python scripts/evaluate_text_consistency.py --data-dir data/raw --out outputs/evaluation.json
```

## Definitions

- Deduplicate by ticket ID, preferring `helpdesk` over `legacy_fd`.
- Add 5 hours 30 minutes to legacy resolution timestamps to convert policy-defined UTC to IST. Creation and first response are already IST.
- Completed means `resolved` or `closed`. Weekly complaint volume uses creation week; the Tier-1 agent leaderboard uses resolution week.
- Repeat-contact proxy: a later ticket from the same customer for the same product and category, created within 30 days after resolution. Open follow-up tickets count. The rate uses only completed tickets with a full 30-day observation window before the export ends. Recent weeks show Pending.
- SLA breach is first response later than the policy's channel target. Local NMF customer-message themes are discovery hints, with approximate and possibly overlapping volumes.

## Business goal

Reduce the mature 30-day repeat-contact proxy from **13.06% (1,369 / 10,484)** to **10.0%**. At 650 contacts a week, 13 weeks, and the policy's Rs 290 blended contact cost, the planning value is **about Rs 74,900 per quarter**. Savings require actual avoided contacts; the tool helps find and track them.

## Validation and limits

The batch command writes a summary, weekly metrics, themes, leaderboard, category changes, product repeat hotspots, a weekly action queue, channel SLA exposure, and QA checks. The export has 12,528 rows, including 653 duplicate IDs; 11,875 IDs remain. QA finds no duplicate IDs, missing creation/resolution times for completed tickets, negative durations, or missing agent IDs after correcting legacy time.

A TF-IDF classifier agrees with existing intake categories on 81.98% of a stratified 2,375-ticket holdout; disagreement is 18.02%. This tests category consistency, **not** NMF theme accuracy or the repeat-contact proxy. Mixed issues, brief messages, and IVR transcripts remain difficult. The proxy has no issue ID, so it can miss retagged issues or count unrelated contacts.

A 20-pair manual spot check of flagged repeats found 17 plausible matches and 3 questionable pairs. See `docs/repeat-audit.md`; the sample is too small to establish a population error rate and does not measure missed repeats.

See `docs/` for the memo, submission form, decision log, and recording guide. The workspace lacks `email-thread.txt` and the original `README.txt`; assumptions based on those must be rechecked if the files become available.

## Public dashboard

`web/` is an aggregate-only historical snapshot for Vercel. It contains counts, rates, product/category summaries, and agent IDs; it does not contain ticket text, customer IDs, or raw CSVs. The live local Streamlit app remains the full analysis tool.

To refresh the public snapshot after receiving a new export, run:

```powershell
.venv\Scripts\python scripts/export_public_dashboard.py --data-dir data/raw --out web/data.json
```

Vercel serves `web/` through the root `vercel.json`. The public view has no live helpdesk connection and should be labelled with the export date shown on the page.
