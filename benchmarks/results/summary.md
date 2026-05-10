# ShipCheck Benchmark Summary

Run date: 2026-05-11

Command shape:

```bash
shipcheck <github-url> --json
```

All scores below come from raw JSON outputs in this directory. The benchmark targets are public starter/template/tutorial repositories, so findings should be read as heuristic launch-readiness signals, not as claims that a repository is unsafe.

## Target Results

| Target | Status | Files scanned | Score | Verdict | Findings |
|---|---:|---:|---:|---|---:|
| ShenSeanChen/launch-mvp-stripe-nextjs-supabase | ok | 80 | 64 | high_risk | 25 |
| KolbySisk/next-supabase-stripe-starter | ok | 67 | 68 | high_risk | 15 |
| dijonmusters/build-a-saas-with-next-js-supabase-and-stripe | ok | 384 | 55 | high_risk | 59 |
| saumya66/Next-Supabase-Stripe-Starter | ok | 42 | 60 | high_risk | 20 |
| mustafacagri/next-stripe-supabase-tailwind-typescript | ok | 47 | 86 | do_not_launch | 24 |
| Jacob-A11/Next-Supabase-Stripe | ok | 50 | 39 | needs_work | 14 |
| jesse-lane-ai/supabase-stripe-nextjs-template | ok | 72 | 65 | high_risk | 24 |
| SydilSohan/nextjs-supabase-stripe-starter | ok | 100 | 55 | high_risk | 20 |

## Score Range

- Targets run: 8
- Successful JSON results: 8
- Failed targets: 0
- Highest score: 86 (`mustafacagri/next-stripe-supabase-tailwind-typescript`)
- Lowest score: 39 (`Jacob-A11/Next-Supabase-Stripe`)

## Most Common Findings

| Finding id | Count | Notes |
|---|---:|---|
| `trust.placeholder_copy` | 59 | Most frequent, but also the noisiest signal. Many hits are UI placeholder attributes or tutorial sample text. |
| `payments.webhook_no_signature` | 17 | Mostly concentrated in the tutorial-style `dijonmusters` repo because the parent folder contains `webhooks`. |
| `database.wide_open_policy` | 14 | Often catches public read policies such as products/prices; needs table-aware severity. |
| `reliability.no_rate_limit` | 14 | Useful launch-readiness signal for mutation endpoints, but webhook endpoints need special handling. |
| `payments.no_idempotency` | 10 | Useful follow-up signal for Stripe event handling. |
| `auth.api_mutation_no_guard` | 9 | Useful for app APIs, noisy for Stripe webhook routes that use signature verification as the trust boundary. |

Most common category: `trust` with 72 total findings. This is directionally relevant for launch readiness, but the current implementation over-counts generic UI placeholder props and Tailwind `placeholder:` classes.

## Findings That Looked Useful

- Missing CI/tests appeared across multiple starter repos and is a reasonable production-readiness prompt.
- Missing RLS evidence or migrations is useful when Supabase usage is present, as long as the rule explains it as "no evidence found" rather than proof of exposure.
- Stripe idempotency findings are useful when webhook event handlers process subscription/payment events.
- Hard-coded Stripe price IDs are worth review in app code, though generated type files should probably be ignored.
- Missing legal/contact surfaces are reasonable trust-surface findings for SaaS templates that collect email, customer, subscription, or payment data.

## False Positive Candidates

- `trust.placeholder_copy` matched normal form placeholders such as `placeholder=Your email`, `placeholder=Search an address`, and Tailwind `placeholder:` utility classes. This should not be treated like placeholder marketing copy.
- `payments.webhook_no_signature` matched many files under `21-subscribe-to-stripe-webhooks-using-next-js-api-routes/` because `webhook` appeared in the directory path, not because each file was a webhook handler.
- `auth.api_mutation_no_guard` flagged Stripe webhook endpoints. If a route verifies Stripe signatures, it should not require app-user auth in the same way normal mutation routes do.
- `database.wide_open_policy` flagged public read-only policies for `products` and `prices`; those may be intentional public catalog reads.
- `secrets.public_secret_name` flagged `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`. Browser Google Maps keys are often publishable with domain restrictions, so this needs provider-specific handling.
- `database.service_role_browser` and `secrets.client_service_role` flagged server/admin helper files. These need import-graph or framework-context checks before calling them browser-reachable.

## Missing Checks / False Negative Risk

- The scanner does not distinguish tutorial multi-step repos from one deployable app, which inflated repeated findings in `dijonmusters`.
- The scanner does not inspect import graphs, so server-only helpers and client-reachable modules are sometimes indistinguishable.
- The scanner does not ignore generated type files, which can create price ID and schema noise.
- The scanner does not de-duplicate repeated equivalent findings across copied tutorial folders.
- The scanner does not yet classify Stripe webhook routes as their own endpoint type before auth/rate-limit checks.

## ShipCheck v0.2 Rule Improvements

1. Add context-aware endpoint classification: separate normal app mutation routes, Stripe webhooks, public callbacks, and admin routes before applying auth/rate-limit/payment rules.
2. Tighten trust-surface scanning: ignore JSX `placeholder=` props, Tailwind `placeholder:` classes, email examples, generated UI components, and focus on visible landing/README copy.
3. Add context filters for generated/server-only files: ignore generated Supabase type files, handle publishable provider keys, and require stronger evidence before treating service-role usage as browser-reachable.

## Product Read

ShipCheck is early but promising. It found useful launch-review prompts across real public repos, especially around tests/CI, Supabase evidence, Stripe event handling, and trust surfaces. It is not ready to be treated as a hard launch gate without v0.2 rule hardening because several high-frequency findings are noisy.

This benchmark supports keeping SkillOps proposal status cautious: stronger evidence than a single build episode, but not enough for automatic promotion without user approval and rule-hardening follow-up.
