# ShipCheck

Production-readiness audit for AI-built SaaS apps.

ShipCheck is a deterministic Python CLI for reviewing small SaaS repositories before launch. v1 focuses on Next.js, Supabase, and Stripe projects.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
shipcheck .
shipcheck . --json
shipcheck . --markdown report.md
shipcheck . --threshold 50
shipcheck https://github.com/owner/repo --markdown report.md
```

## What It Checks

- secrets and unsafe environment handling
- auth and access-control gaps
- Supabase/Postgres RLS and migration evidence
- Stripe webhook and entitlement mistakes
- reliability basics such as tests, CI, logging, and rate limiting
- trust surface such as privacy, terms, support, and placeholder copy

## Scoring

Scores are risk scores. Higher is worse.

- `0-24`: `launchable`
- `25-49`: `needs_work`
- `50-74`: `high_risk`
- `75-100`: `do_not_launch`

Each category has a cap, so repeated low-value issues cannot outweigh critical launch blockers.

## GitHub Action

```yaml
name: ShipCheck
on: [pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install shipcheck
      - run: shipcheck . --threshold 50
```

## What It Does Not Do

ShipCheck is heuristic. It does not prove your app is secure, replace a senior review, scan dependencies for CVEs, modify target repositories, upload code, or use an LLM. Findings are evidence-based but may include false positives or miss framework-specific patterns.
