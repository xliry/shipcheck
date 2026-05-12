# ShipCheck v0.4 Dogfood Summary: Trust Placeholder Precision

Run date: 2026-05-12

Command shape:

```bash
shipcheck <github-url> --json
```

This dogfood reruns the same 5 fresh repositories from `benchmarks/results-v0.3-dogfood/`. The goal is only to evaluate `trust.placeholder_copy` precision after v0.4 filtering. It is not a traction, production-readiness, or market-validity claim.

## Target Results

| Target | Files | Score v0.3 | Score v0.4 | Delta | Verdict v0.3 | Verdict v0.4 | Findings v0.3 | Findings v0.4 | Placeholder v0.3 | Placeholder v0.4 |
|---|---:|---:|---:|---:|---|---|---:|---:|---:|---:|
| DanieII/instant-saas | 53 | 19 | 19 | 0 | launchable | launchable | 7 | 7 | 2 | 2 |
| duartefdias/NextJsSaasTemplate | 78 | 38 | 38 | 0 | needs_work | needs_work | 16 | 16 | 0 | 0 |
| dzlau/stripe-supabase-saas-template | 57 | 44 | 44 | 0 | needs_work | needs_work | 12 | 12 | 2 | 2 |
| nextjs/saas-starter | 52 | 20 | 18 | -2 | launchable | launchable | 8 | 6 | 3 | 1 |
| Razikus/supabase-nextjs-template | 117 | 41 | 34 | -7 | needs_work | needs_work | 15 | 8 | 8 | 1 |

## Run Health

- Targets run: 5
- JSON files: 5
- Parse failures: 0
- Total `trust.placeholder_copy`: 15 -> 6
- Total findings: 58 -> 49

## Manual-Review False Positives Removed

The v0.4 rule suppressed the reviewed code-symbol false positives:

- `placeholder?: string`
- `placeholder-gray-500` and `placeholder:*` Tailwind classes
- `placeholderTextColor={...}` and destructured `placeholder,` prop usage
- `todo_list` table/type references
- `getMyTodoList` function names
- `LucideListTodo` / `ListTodo` imports
- code TODO comments
- generic demo feature copy mentioning a todo system

## True Positives Preserved

The remaining 6 `trust.placeholder_copy` dogfood findings match the manual-review true-positive classes:

- `DanieII/instant-saas`: two `Lorem ipsum` rendered/prose findings.
- `dzlau/stripe-supabase-saas-template`: two `Acme Inc` rendered/a11y brand findings.
- `nextjs/saas-starter`: one `ACME` rendered brand finding.
- `Razikus/supabase-nextjs-template`: one explicit placeholder pricing finding.

## Unexpected Changes

- No non-placeholder rule category was intentionally changed.
- Score drops were limited to targets where placeholder false positives were removed: `nextjs/saas-starter` and `Razikus/supabase-nextjs-template`.
- No full 8-target benchmark was run because dogfood showed the expected targeted precision improvement and no broad side effects.

## Recommendation

Accept v0.4 as a narrow precision improvement with normal heuristic risk. The next best move is to stop rule hardening briefly and use ShipCheck on real projects or fresh manual reviews before opening another v0.5 spec.
