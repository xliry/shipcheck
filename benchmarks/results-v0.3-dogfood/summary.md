# ShipCheck v0.3 Fresh Repo Dogfood Summary

Run date: 2026-05-12

Command shape:

```bash
shipcheck <github-url> --json
```

This dogfood pass used 5 fresh repositories that were not part of the original 8-target v0.1/v0.2/v0.3 benchmark set. The goal was not to prove traction or production quality. The goal was to manually check whether v0.3 behavior generalizes, especially nested multi-app route detection and tutorial/multi-app dedup.

## Targets

| Target | Files | Score | Verdict | Findings | Dedup groups | Suppressed duplicates |
|---|---:|---:|---|---:|---:|---:|
| `Razikus/supabase-nextjs-template` | 117 | 41 | needs_work | 15 | 0 | 0 |
| `DanieII/instant-saas` | 53 | 19 | launchable | 7 | 0 | 0 |
| `dzlau/stripe-supabase-saas-template` | 57 | 44 | needs_work | 12 | 0 | 0 |
| `duartefdias/NextJsSaasTemplate` | 78 | 38 | needs_work | 16 | 0 | 0 |
| `nextjs/saas-starter` | 52 | 20 | launchable | 8 | 0 | 0 |

## Parse / Run Health

- Targets run: 5
- JSON files: 5
- Parse failures: 0
- Highest score: 44 (`dzlau/stripe-supabase-saas-template`)
- Lowest score: 19 (`DanieII/instant-saas`)

## Finding Distribution

| Finding id | Count | Read |
|---|---:|---|
| `trust.placeholder_copy` | 15 | Still common; needs manual review because some may be normal UI or docs copy. |
| `reliability.no_rate_limit` | 5 | Concentrated in normal top-level app API routes, not nested multi-app paths. |
| `payments.no_idempotency` | 5 | Useful payment review signal remains visible. |
| `reliability.no_ci` | 5 | Expected launch-readiness hygiene signal. |
| `reliability.no_tests` | 5 | Expected launch-readiness hygiene signal. |
| `trust.missing_legal` | 4 | Trust-surface signal remains visible. |
| `reliability.no_error_boundary` | 4 | Low-severity app resilience signal. |
| `trust.generic_ai_copy` | 3 | Mostly docs/terms/template-ish copy; worth manual precision review later. |
| `database.no_rls_evidence` | 2 | Useful when Supabase evidence exists but RLS enable statements are absent. |

## Nested Multi-App Route Review

No nested `app/api` auth/rate-limit findings appeared in this 5-repo dogfood set.

This is useful negative evidence:

- The v0.3 benchmark's nested route signal did not explode across fresh repos.
- Top-level route findings still appeared where expected, especially in `duartefdias/NextJsSaasTemplate`.
- There is not enough evidence yet to call nested route detection proven, but this pass did not reveal obvious broad noise.

## Dedup Review

- Duplicate groups found: 0
- Suppressed duplicates: 0

This is also useful:

- The tutorial dedup logic did not accidentally collapse findings in normal fresh repos.
- The v0.3 benchmark dedup behavior still looks specific to repeated tutorial/example structure.

## Supabase Policy Severity Review

No `database.wide_open_policy` findings appeared in this dogfood set.

This means the dogfood pass did not add new positive evidence for table-aware policy severity. The existing v0.3 benchmark and tests remain the main evidence for that behavior.

## Manual Reads

- `DanieII/instant-saas`: low score, payment idempotency and hygiene findings only. Looks like ShipCheck is behaving as a review assistant rather than a blocker.
- `duartefdias/NextJsSaasTemplate`: multiple top-level AI API routes without rate-limit evidence. These look useful to review manually, not nested-path noise.
- `dzlau/stripe-supabase-saas-template`: database RLS/policy evidence gaps plus payment idempotency. Useful but still heuristic.
- `Razikus/supabase-nextjs-template`: committed `.env` under mobile template triggered a critical JWT secret finding. This looks like a real review prompt.
- `nextjs/saas-starter`: moderate payment/hygiene findings; no Supabase-specific policy signal because it is not a Supabase target.

## Decision

ShipCheck v0.3 passed the first fresh-repo dogfood check for the nested-route concern:

- no nested-route false-positive burst
- no accidental dedup suppression
- useful payment/reliability/trust signals preserved

Do not create v0.4 yet. The next better move is manual review of the `trust.placeholder_copy` examples from this dogfood run, because it is still the most frequent signal and likely the next precision bottleneck.

