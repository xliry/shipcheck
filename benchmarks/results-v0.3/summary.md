# ShipCheck v0.3 Benchmark Summary

Run date: 2026-05-12

Command shape:

```bash
shipcheck <github-url> --json
```

This is the after-run for ShipCheck v0.3 policy severity and tutorial/multi-app duplicate grouping. It compares against `benchmarks/results-v0.2/`. Targets are public starter/template/tutorial repositories, so findings are heuristic launch-readiness signals, not claims that a repository is unsafe.

## Target Results

| Target | Files | Score v0.2 | Score v0.3 | Delta | Verdict v0.2 | Verdict v0.3 | Findings v0.2 | Findings v0.3 | Delta | Wide-open policies v0.2 | Wide-open policies v0.3 | Dedup groups | Suppressed duplicates |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|---|---:|---:|
| ShenSeanChen/launch-mvp-stripe-nextjs-supabase | 80 | 63 | 63 | 0 | high_risk | high_risk | 24 | 23 | -1 | 6 high | 5 high | 0 | 0 |
| KolbySisk/next-supabase-stripe-starter | 67 | 38 | 24 | -14 | needs_work | launchable | 9 | 9 | 0 | 2 high | 2 low | 0 | 0 |
| dijonmusters/build-a-saas-with-next-js-supabase-and-stripe | 384 | 55 | 44 | -11 | high_risk | needs_work | 39 | 12 | -27 | 0 | 0 | 2 | 27 |
| saumya66/Next-Supabase-Stripe-Starter | 42 | 51 | 37 | -14 | high_risk | needs_work | 18 | 18 | 0 | 2 high | 2 low | 0 | 0 |
| mustafacagri/next-stripe-supabase-tailwind-typescript | 47 | 62 | 63 | +1 | high_risk | high_risk | 16 | 20 | +4 | 0 | 0 | 0 | 0 |
| Jacob-A11/Next-Supabase-Stripe | 50 | 36 | 36 | 0 | needs_work | needs_work | 11 | 11 | 0 | 0 | 0 | 0 | 0 |
| jesse-lane-ai/supabase-stripe-nextjs-template | 72 | 52 | 36 | -16 | high_risk | needs_work | 14 | 14 | 0 | 4 high | 4 low | 0 | 0 |
| SydilSohan/nextjs-supabase-stripe-starter | 100 | 29 | 29 | 0 | needs_work | needs_work | 10 | 10 | 0 | 0 | 0 | 0 | 0 |

## Score Range

- Targets run: 8
- Successful JSON results: 8
- Parse failures: 0
- Highest score before: 63 (`ShenSeanChen/launch-mvp-stripe-nextjs-supabase`)
- Highest score after: 63 (`mustafacagri/next-stripe-supabase-tailwind-typescript`)
- Lowest score before: 29 (`SydilSohan/nextjs-supabase-stripe-starter`)
- Lowest score after: 24 (`KolbySisk/next-supabase-stripe-starter`)
- Total findings: 141 -> 117

## Supabase Policy Severity

- `database.wide_open_policy` changed from 14 high-severity findings to 13 findings: 8 low and 5 high.
- Public catalog reads on `products` and `prices` now produce low-severity verification prompts instead of high-severity warnings.
- Service-role `FOR ALL` policies on user, subscription, and email-log tables remained high.
- One `USING (true)` plus `WITH CHECK (true)` policy is now represented as one policy block instead of two line-level findings.

This looks like a quality improvement: public product/price catalog reads are still visible, but they no longer dominate the database score like customer or write-heavy policies.

## Duplicate Grouping

- Duplicate groups found: 2
- Suppressed duplicate findings: 27
- Grouping happens after rule emission and before scoring, so representative findings still contribute to the score.

Grouped examples:

- `payments.no_idempotency` in `dijonmusters/build-a-saas-with-next-js-supabase-and-stripe`: one representative plus 4 repeated tutorial locations.
- `trust.placeholder_copy` in `dijonmusters/build-a-saas-with-next-js-supabase-and-stripe`: one representative plus 23 repeated tutorial locations.

The grouped findings expose `duplicate_count`, `duplicate_examples`, `deduped_by`, and `suppressed_duplicates` in JSON. The duplicates are not silently deleted.

## Useful Findings Preserved

- `reliability.no_ci`: 8 -> 8
- `reliability.no_tests`: 7 -> 7
- `trust.missing_legal`: 7 -> 7
- `database.no_migrations`: 6 -> 6
- `database.no_rls_evidence`: 4 -> 4
- `payments.hardcoded_price`: 5 -> 5
- `payments.no_idempotency`: 10 -> 6 because repeated tutorial copies were grouped; representative findings remain.

## New / Concerning Signals

- `mustafacagri/next-stripe-supabase-tailwind-typescript` moved from 62 to 63 because nested `app/api` routes are now recognized under multi-app/tutorial paths. This surfaced two auth and two rate-limit findings. It may be useful signal, but should be manually reviewed before treating nested-app route detection as fully proven.
- Some repositories moved from `needs_work` or `high_risk` to `launchable`/`needs_work` mostly because public catalog reads were downgraded. This is expected for product/price tables, but the benchmark does not prove those tables contain only public data.
- The 8-target benchmark is still a small heuristic sample, not production validation.

## Recommendation

ShipCheck v0.3 is a better reviewer than v0.2 for the two targeted risks:

- table-aware RLS severity makes database findings more trustworthy
- tutorial dedup reduces inflated confidence from repeated lesson folders

Recommended next step: dogfood ShipCheck on 3-5 fresh repos manually before another rule-hardening spec. Do not automatically create v0.4 from this benchmark alone.
