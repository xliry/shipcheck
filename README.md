# ShipCheck

Launch-readiness gate for vibe-coded SaaS apps.

ShipCheck is a deterministic Python CLI for reviewing AI-built SaaS repositories before launch. It is not a security scanner, SAST platform, dependency vulnerability database, or secret-revocation tool. It is a launch checklist/audit tool for the failure modes that often hide behind working demos.

ShipCheck does not compete with Semgrep, Snyk, or Gitleaks. Use those tools for static analysis, dependency risk, and dedicated secret scanning. Use ShipCheck as a practical launch-readiness gate that asks: "Would a senior engineer block this vibe-coded SaaS from shipping?"

The v1 wedge is deliberately narrow: Next.js + Supabase + Stripe. Rules are deterministic, evidence-based, CI-friendly, and designed to produce a short report rather than a noisy lint dump.

## Install

```bash
pip install shipcheck-ai
```

For local development:

```bash
python -m pip install -e ".[dev]"
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
      - run: pip install shipcheck-ai
      - run: shipcheck . --threshold 50
```

## What It Does Not Do

ShipCheck is heuristic. It does not prove your app is secure, replace a senior review, scan dependencies for CVEs, modify target repositories, upload code, or use an LLM. Findings are evidence-based but may include false positives or miss framework-specific patterns.

It is also not a replacement for Semgrep, Snyk, Gitleaks, npm audit, or a penetration test. ShipCheck sits after "the app works" and before "we launch" as a focused readiness gate for AI-built SaaS projects.
