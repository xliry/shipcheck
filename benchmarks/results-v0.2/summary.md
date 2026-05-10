# ShipCheck v0.2 Benchmark Summary

Run date: 2026-05-11

Command shape:

```bash
shipcheck <github-url> --json
```

This is the after-run for ShipCheck v0.2 rule hardening. It compares against the v0.1 raw results in `benchmarks/results/`. Targets are public starter/template/tutorial repositories, so findings are heuristic launch-readiness signals, not claims that a repository is unsafe.

## Target Results

| Target | Files | Score v0.1 | Score v0.2 | Delta | Verdict v0.1 | Verdict v0.2 | Findings v0.1 | Findings v0.2 | Delta |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|
| ShenSeanChen/launch-mvp-stripe-nextjs-supabase | 80 | 64 | 63 | -1 | high_risk | high_risk | 25 | 24 | -1 |
| KolbySisk/next-supabase-stripe-starter | 67 | 68 | 38 | -30 | high_risk | needs_work | 15 | 9 | -6 |
| dijonmusters/build-a-saas-with-next-js-supabase-and-stripe | 384 | 55 | 55 | 0 | high_risk | high_risk | 59 | 39 | -20 |
| saumya66/Next-Supabase-Stripe-Starter | 42 | 60 | 51 | -9 | high_risk | high_risk | 20 | 18 | -2 |
| mustafacagri/next-stripe-supabase-tailwind-typescript | 47 | 86 | 62 | -24 | do_not_launch | high_risk | 24 | 16 | -8 |
| Jacob-A11/Next-Supabase-Stripe | 50 | 39 | 36 | -3 | needs_work | needs_work | 14 | 11 | -3 |
| jesse-lane-ai/supabase-stripe-nextjs-template | 72 | 65 | 52 | -13 | high_risk | high_risk | 24 | 14 | -10 |
| SydilSohan/nextjs-supabase-stripe-starter | 100 | 55 | 29 | -26 | high_risk | needs_work | 20 | 10 | -10 |

## Score Range

- Targets run: 8
- Successful JSON results: 8
- Failed targets: 0
- Highest score before: 86 (`mustafacagri/next-stripe-supabase-tailwind-typescript`)
- Highest score after: 63 (`ShenSeanChen/launch-mvp-stripe-nextjs-supabase`)
- Lowest score before: 39 (`Jacob-A11/Next-Supabase-Stripe`)
- Lowest score after: 29 (`SydilSohan/nextjs-supabase-stripe-starter`)

## Finding Deltas

| Finding id | v0.1 | v0.2 | Delta | Read |
|---|---:|---:|---:|---|
| `trust.placeholder_copy` | 59 | 38 | -21 | Reduced JSX/form/Tailwind placeholder noise while keeping visible unfinished copy. |
| `payments.webhook_no_signature` | 17 | 0 | -17 | Removed path-name overmatching from tutorial folders; fixture coverage still catches unverified real webhook routes. |
| `auth.api_mutation_no_guard` | 9 | 3 | -6 | Stripe webhook routes no longer require app-user auth; normal mutation routes still flag. |
| `reliability.no_rate_limit` | 14 | 8 | -6 | Stripe webhook routes no longer receive generic rate-limit findings. |
| `payments.hardcoded_price` | 8 | 5 | -3 | Generated/type-file price ID noise reduced. |
| `secrets.public_secret_name` | 3 | 0 | -3 | Publishable Google Maps public key noise removed. |
| `database.service_role_browser` | 2 | 0 | -2 | Server/admin helper files no longer called browser exposure without stronger evidence. |
| `secrets.client_service_role` | 2 | 0 | -2 | Same server/generated context improvement. |

## Useful Findings Preserved

- `database.wide_open_policy` stayed at 14. This may still need table-aware severity, but v0.2 did not hide it.
- `payments.no_idempotency` stayed at 10, preserving Stripe event handling review prompts.
- `reliability.no_ci` stayed at 8 and `reliability.no_tests` stayed at 7.
- `database.no_migrations` stayed at 6 and `database.no_rls_evidence` stayed at 4.
- `trust.missing_legal` stayed at 7, preserving trust-surface prompts.

## False Positive Reduction

- Tutorial folder names containing `webhooks` no longer cause every file under the folder to be treated as a webhook handler.
- Verified Stripe webhook routes are no longer treated like normal app-user mutation routes.
- UI placeholders such as form input hints and Tailwind placeholder classes are filtered out.
- Generated Supabase type files are skipped for hard-coded Stripe price ID checks.
- Known publishable browser key names such as `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY` are not treated as high secret findings.

## Concerning Disappeared Signals

- `payments.webhook_no_signature` dropped to 0 in the public benchmark. This looks desirable for the current target set because v0.1 was path-noisy, but the rule must keep fixture coverage for real unverified webhook routes.
- Service-role browser exposure dropped to 0. This removes noisy server helper findings, but without import graph analysis ShipCheck still cannot prove whether an ambiguous helper is browser-reachable.

## Product Read

ShipCheck v0.2 is closer to a useful launch-review assistant. It still should not be marketed as a hard launch gate because some remaining rules are heuristic and context-light, especially RLS policy interpretation and tutorial repository structure. The benchmark now reads less like a loud string scanner and more like a focused production-readiness review.

Recommended next step: keep the same benchmark set and add a small v0.3 task for table-aware Supabase policy severity and tutorial/multi-app de-duplication.
