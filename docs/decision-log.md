# Decision log

1. **Deduplicate migration copies.** Keep one ticket ID, preferring current `helpdesk`; otherwise 653 IDs inflate volume.
2. **Correct legacy resolution times.** Policy section 9 says migrated resolution times came from UTC logs while the report displays IST. Add 5:30 before time comparisons and weekly closure counts.
3. **Use a mature repeat cohort.** The 30-day outcome requires 30 days of subsequent data. Include open follow-up tickets. Exclude completed tickets resolved less than 30 days before export end from the baseline.
4. **Use a stated proxy.** The policy says same issue, but no issue ID exists; same customer/product/category is a tractable proxy with unknown error.
5. **Count agent work when it completes.** Leaderboard uses resolution week, excludes Tier 2 as policy directs, and is explicitly volume only.
6. **Keep text AI small.** Local NMF surfaces wording; existing categories drive counts. A text classifier checks category consistency, but cannot prove NMF topic accuracy.
7. **Exclude raw data from Git.** The export has identifiable customer text. No production integration or automated staff decisions are included.
8. **Missing pack items.** `email-thread.txt` and the original `README.txt` are absent from this workspace. The policy and CSV headers supply current definitions; any email-specific preference needs later review.
