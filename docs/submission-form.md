# Vireo Audio — Submission Form

## What did you build, and what business outcome does it move? State the number and the money.

A local Streamlit weekly complaint digest, Tier-1 resolution-week volume leaderboard, and CSV export with migration deduplication and QA. An aggregate-only public snapshot is deployed at https://vireo-support-intelligence.vercel.app. The digest also shows product complaint hotspots, a weekly action queue combining trend and repeat/SLA signals, and SLA exposure by channel. The goal is to lower the mature 30-day repeat-contact proxy from **13.06% (1,369 / 10,484)** to **10.0%**. At 650 contacts/week, 13 weeks, and Rs 290/contact, that is `650 × 13 × (0.1305799 - 0.10) × 290 = Rs 74,936 per quarter` in potential avoided contact cost. This is a planning value, not booked savings.

## What does one run cost, and what would a month cost at Vireo's volume (roughly 650 tickets a week)? Show the arithmetic. If you used no paid calls, say so.

**Rs 0 in model/API fees per run and per month.** Local TF-IDF/NMF has no per-ticket API charge. At `650 × 52 / 12 ≈ 2,817 tickets/month`, model/API cost remains Rs 0. Local machine and staff time are excluded.

## How do you know it works? Sample size, how you checked, error rate, and the kind of case it gets wrong.

The batch run processed 12,528 source rows, removed 653 duplicate ticket IDs, and retained 11,875. It checked for duplicate IDs after deduplication, missing creation/resolution times, negative response/resolution durations, and missing agent IDs; all six checks returned zero. Policy UTC-to-IST correction removed negative migrated resolution durations. The mature repeat cohort is 10,484 completed tickets.

A separate TF-IDF classifier was fitted on a stratified training split and evaluated on **2,375 held-out customer messages**. It agreed with existing intake categories on **81.98%**; disagreement was **18.02%**. This is tag consistency, **not ground-truth accuracy** and does not validate the unsupervised themes. Common mismatches are `Other` versus Delivery/Billing and Billing versus Returns. Mixed issues, short messages, and IVR transcripts are weak cases. The repeat proxy can miss retagged cases and count unrelated contacts.

A manual spot check of 20 randomly selected flagged pairs found 17 plausible same-issue repeats and 3 questionable pairs (15% observed questionable rate in this small sample; see `repeat-audit.md`). This checks flagged-pair precision only. It cannot measure missed repeats or establish a population error rate.

## Did you change, narrow, or push back on the client's ask? What, when, and why.

I kept the digest and leaderboard, but excluded Tier 2 from volume comparison as the policy directs. I counted closures by resolution week, corrected legacy UTC resolution times, and made recent repeat rates pending until the full 30-day window is observed. I included repeat contacts and operational signals so the digest can guide an intervention with a measurable cost outcome.

## What is wrong with what you are handing us?

The repeat metric is a proxy, customer-message topics can be noisy, and the leaderboard lacks staffing hours, case difficulty, and leave. The local app reads exports rather than a live helpdesk; the public Vercel dashboard is a historical aggregate snapshot, not a live integration. The workspace did not include the referenced `email-thread.txt` or original `README.txt`, so assumptions attributed to those documents cannot be confirmed here. The policy supplies the key definitions. No actual screen recording has been produced in this workspace.

## What did you deliberately leave out, and why that rather than something else?

Live integrations, authentication, automated agent scoring, sentiment, and a paid LLM layer. They add deployment and judgment risk without improving the first weekly decision. Raw customer files are excluded from public Git by `.gitignore`.

## Anything you built or found that nobody asked for?

The export contains 653 repeated IDs from migration. The policy says migrated resolution times are UTC while other report times are IST; correcting that changes time-based analysis. Recent tickets have incomplete 30-day follow-up, so excluding them raises the measured repeat baseline from the naive 12.56% to 13.06%.

## What did you use AI for? Which tools and models, where they helped, where they wasted your time, what you threw away. Link your three-minute screen recording here.

Codex was used to audit and revise the draft tool, challenge metric definitions, edit code, and prepare the memo. The shipped app uses local scikit-learn TF-IDF/NMF, with no paid inference. AI helped identify the time-zone and right-censoring problems; the initial draft's 11.97% rate and Rs 72.9k estimate were discarded after those corrections. I also discarded a text-classifier result as proof of topic accuracy: it only tests agreement with existing tags. **Recording link: not yet available; a recording must be made before submission.**

## Your Public Google Drive Link

Not yet available; upload the final recording/artifacts and insert its public link before submission.

## Someone picks this up on Monday and you are unreachable. The three things they need to know.

1. Follow `README.md` to install and run the app or batch command with the five CSV files.
2. The 13.06% baseline uses a mature 30-day window; recent weeks show pending repeat rates. Review the proxy definition before treating it as true same-issue resolution.
3. Tier-2 specialists are excluded from the leaderboard; Tier-1 counts use resolution week and are volume only.

## Honest hours spent.

Record actual human preparation and recording time before submission. The pre-existing draft's claim of exactly 5.0 hours was not verifiable and has been removed.

## Github Repo Link

https://github.com/hiteshsurya018-cmd/Vireo
