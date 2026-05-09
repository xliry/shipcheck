# SPEC: ShipCheck - Vibe-Coded SaaS Production Audit

**Target repo:** new project (`shipcheck/`)
**Working dir:** new - initialize fresh under `builds/shipcheck/` if built locally
**Estimated effort:** 8-10 hours of agent time
**Total LOC budget:** under 1,200 lines for MVP application code
**Output:** Python CLI that audits a SaaS repo for production-readiness risks and writes Markdown/JSON reports
**Target Agent:** Codex / Codex sub-agent / external coding agent
**Status:** DRAFT
**Version:** 1
**Created:** 2026-05-09

---

## 0. CONTEXT (Read this first)

ShipCheck is a deterministic audit tool for AI-built or "vibe-coded" SaaS projects.

The market signal is clear: AI tools make demos and proof-of-concepts extremely fast, but founders are shipping fragile applications without production fundamentals. The visible pain is not "AI code is bad" in a generic sense. The pain is more specific:

- missing auth boundaries
- exposed secrets
- unsafe environment handling
- weak database row-level security
- Stripe/webhook mistakes
- no audit logs
- no error handling
- no migration discipline
- no tests around critical flows
- generic AI-generated landing pages that reduce buyer trust

This spec turns that pain into a narrow first product: a CLI that scans a repository and produces a prioritized production-readiness report.

**Hard rule:** Do not build a generic SAST platform. ShipCheck v1 is a focused readiness audit for small SaaS repos, especially Next.js/Supabase/Stripe-style apps. Keep the tool deterministic, fast, explainable, and cheap to run.

**Taste rule:** The output must feel like a senior engineer reviewing a launch candidate, not like a noisy linter dumping 400 findings.

---

## 1. GOAL (One-Line)

> Build a deterministic CLI that audits a SaaS repository for production-readiness risks and outputs a practical launch report with severity, evidence, and remediation steps.

---

## 2. PRODUCT POSITIONING

### 2.1 Product Name

ShipCheck

### 2.2 One-line Pitch

"Before you ship your vibe-coded SaaS, run ShipCheck and find the production risks your demo hides."

### 2.3 Target Users

- solo founders building with Claude Code, Codex, Cursor, Lovable, Bolt, Replit, v0, or similar tools
- micro-SaaS builders preparing for Product Hunt or Reddit launches
- small agencies delivering AI-built SaaS prototypes to clients
- technical advisors reviewing founder-built MVPs
- engineering teams accepting AI-generated internal tools

### 2.4 Initial Wedge

Start as a CLI and GitHub Action. Do not start as a SaaS dashboard. A CLI is easier to trust, easier to dogfood, and easier to sell as a developer tool.

### 2.5 Why Now

The cultural discussion has shifted from "AI can build apps" to "AI-built apps fail in production." That creates a window for tools that sit between AI-generated output and real launch.

---

## 3. INPUTS / OUTPUTS

### 3.1 CLI Input

```bash
shipcheck <path-or-github-url> [--json] [--markdown FILE] [--threshold N] [--profile PROFILE] [--max-files N]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `target` | positional | required | Local path or public GitHub URL |
| `--json` | flag | false | Print JSON report to stdout |
| `--markdown FILE` | path | `shipcheck-report.md` | Write human-readable report |
| `--threshold N` | int | none | Exit 1 if risk score is greater than N |
| `--profile` | enum | `next-supabase-stripe` | Audit profile; v1 supports one real profile |
| `--max-files` | int | 500 | Cap scanned source/config files |
| `--include-tests` | flag | false | Include test files in scan evidence |

### 3.2 Supported Targets in v1

- local repository path
- public GitHub URL cloned with `git clone --depth=1`

### 3.3 Supported Stack in v1

Primary stack:

- Next.js / React / TypeScript
- Supabase
- Stripe
- common env files
- basic Node package metadata

Secondary signals:

- generic JavaScript/TypeScript source
- Python API helpers if present
- README and landing copy

### 3.4 Markdown Output

```markdown
# ShipCheck Report

Target: ./my-saas
Risk score: 74/100
Verdict: high risk

## Top Risks
1. [CRITICAL] Supabase service role key appears in client-accessible code
2. [HIGH] Stripe webhook handler does not verify signatures
3. [HIGH] No protected route middleware found

## Category Breakdown
- Secrets: 25/25
- Auth: 18/20
- Database security: 12/20
- Payments: 10/15
- Reliability: 5/10
- Trust surface: 4/10

## Findings
...
```

### 3.5 JSON Output

```json
{
  "target": "./my-saas",
  "files_scanned": 142,
  "score": 74,
  "verdict": "high_risk",
  "summary": "Launch should be blocked until critical secrets and Stripe issues are fixed.",
  "categories": {
    "secrets": {"score": 25, "max_score": 25},
    "auth": {"score": 18, "max_score": 20}
  },
  "findings": [
    {
      "id": "secrets.client_service_role",
      "severity": "critical",
      "category": "secrets",
      "title": "Supabase service role key appears in client-accessible code",
      "file": "app/lib/supabase.ts",
      "line": 12,
      "evidence": "SUPABASE_SERVICE_ROLE_KEY",
      "why_it_matters": "...",
      "remediation": "..."
    }
  ]
}
```

### 3.6 Verdict Thresholds

- `0-24`: `launchable`
- `25-49`: `needs_work`
- `50-74`: `high_risk`
- `75-100`: `do_not_launch`

The score is a risk score, not a quality score. Higher is worse.

---

## 4. ARCHITECTURAL DECISIONS (Approved)

### 4.1 Deterministic Rules First

ShipCheck v1 must not require an LLM. The core audit should be reproducible, cheap, and CI-friendly. LLM-based remediation text can be a future paid layer, but v1 findings must come from deterministic rules.

### 4.2 CLI Before SaaS

Start with a CLI because trust matters. The target user is already worried about security. Asking them to upload their repo to a random web app creates friction. A local CLI can later power a GitHub Action or hosted dashboard.

### 4.3 Profile-Based Audits

Do not pretend to understand every stack. v1 supports one primary profile: `next-supabase-stripe`. The audit engine should be profile-based so future profiles can add Rails, Django, Laravel, Firebase, Clerk, Prisma, or FastAPI.

### 4.4 Evidence-Based Findings

Every finding must include:

- file path
- line number when possible
- compact evidence
- severity
- why it matters
- remediation

Do not output abstract advice with no source evidence.

### 4.5 Practical Scoring

Scoring should prioritize launch-blocking risk. A single exposed secret can push the score high. Ten minor copy issues should not outweigh one critical auth bug.

### 4.6 No Full Static Analysis Platform

Use simple parsers and targeted heuristics. Avoid building a full TypeScript compiler integration in v1. Read files, parse JSON/TOML/YAML where needed, and use robust pattern detection.

### 4.7 Reports Are the Product

The Markdown report must be polished enough to send to a founder/client. It should be actionable, short enough to read, and opinionated about what blocks launch.

---

## 5. AUDIT CATEGORIES

### 5.1 Secrets (25 points)

Goal: catch leaked or risky secrets.

Rules:

- `SUPABASE_SERVICE_ROLE_KEY` referenced in client-accessible code
- high-entropy tokens committed in source
- `.env` or `.env.local` committed
- `NEXT_PUBLIC_` used with secret-like variable names
- Stripe secret key in frontend bundle path
- OpenAI/Anthropic/Gemini keys in source
- missing `.env.example`
- `.gitignore` does not ignore env files

Severity mapping:

- critical: secret value present or service-role key in client code
- high: secret-like env exposed through public prefix
- medium: missing `.env.example`
- low: weak env hygiene

### 5.2 Auth and Access Control (20 points)

Goal: catch apps that look functional but do not protect user data.

Rules:

- no middleware/protected route pattern in Next.js app
- API routes without auth guard
- admin path without role check
- client-side-only auth enforcement
- use of `getUser`/session checks absent in server handlers
- hard-coded user IDs or demo bypasses
- `TODO auth`, `skip auth`, `temporary auth` markers

Severity mapping:

- critical: admin or data mutation endpoint with no auth
- high: protected route only guarded client-side
- medium: inconsistent auth pattern
- low: missing auth docs

### 5.3 Database Security (20 points)

Goal: detect common Supabase/Postgres launch risks.

Rules:

- no migrations directory
- no SQL files containing `enable row level security`
- SQL policies absent
- service role used for normal app operations
- wide-open policies such as `using (true)` without admin context
- direct table access from browser client for sensitive tables
- table names like `users`, `customers`, `payments`, `subscriptions` with no RLS evidence

Severity mapping:

- critical: service role used client-side or RLS disabled for sensitive data
- high: no RLS evidence in Supabase app
- medium: no migrations discipline
- low: missing schema docs

### 5.4 Payments (15 points)

Goal: detect Stripe mistakes that cause money or entitlement bugs.

Rules:

- Stripe webhook handler does not verify signature
- webhook secret missing
- checkout success URL grants entitlement without webhook confirmation
- no idempotency handling
- no subscription status sync
- test keys used in production config
- price IDs hard-coded without environment separation

Severity mapping:

- critical: payment grants access client-side
- high: no webhook signature verification
- medium: no idempotency
- low: weak payment docs

### 5.5 Reliability and Operations (10 points)

Goal: catch basic production reliability gaps.

Rules:

- no error boundary in Next.js app
- no structured logging or error tracking evidence
- empty catch blocks
- broad `catch (e) {}` with no handling
- no rate limiting around public API routes
- no health check endpoint
- no tests for critical flows
- no CI config

Severity mapping:

- high: public mutation endpoint with no rate limiting
- medium: no tests or CI
- low: missing health check

### 5.6 Trust Surface (10 points)

Goal: identify visible signs that reduce buyer trust.

Rules:

- generic AI words in landing copy
- missing privacy policy or terms
- missing contact/support path
- fake testimonials markers
- placeholder content
- lorem ipsum
- inconsistent brand names
- no pricing clarity

Severity mapping:

- medium: missing privacy/terms in app collecting user data
- low: generic AI copy or placeholder content

---

## 6. REPOSITORY ORIENTATION (Step 1, do this first)

This is a new project. Initialize a fresh package:

```bash
mkdir -p builds/shipcheck
cd builds/shipcheck
python -m venv .venv
pip install -U pip
pip install click rich pytest gitpython pyyaml tomli
```

Create a Python package with this structure:

```text
shipcheck/
  __init__.py
  cli.py
  scanner.py
  models.py
  engine.py
  scoring.py
  report.py
  rules/
    __init__.py
    secrets.py
    auth.py
    database.py
    payments.py
    reliability.py
    trust.py
tests/
  fixtures/
    next_supabase_bad/
    next_supabase_clean/
  test_scanner.py
  test_secrets.py
  test_auth.py
  test_database.py
  test_payments.py
  test_report.py
README.md
pyproject.toml
```

Verification of orientation:

```bash
pip install -e .
shipcheck --help
pytest -q
```

---

## 7. ARCHITECTURE

### 7.1 Flow

```text
1. CLI parses target and options.
2. scanner resolves target:
   - GitHub URL -> clone depth=1 to temp dir
   - local path -> scan directly
3. scanner collects relevant files:
   - .ts, .tsx, .js, .jsx, .mjs, .cjs
   - .py
   - .sql
   - package.json
   - README.md
   - .env.example
   - config files
4. engine runs all profile rules.
5. each rule emits zero or more Finding objects.
6. scoring aggregates findings by category.
7. report renders Markdown and/or JSON.
8. CLI exits non-zero if threshold exceeded.
```

### 7.2 Data Models

Use dataclasses. Keep them boring.

```python
@dataclass
class Finding:
    id: str
    category: str
    severity: str
    title: str
    file: str | None = None
    line: int | None = None
    evidence: str | None = None
    why_it_matters: str = ""
    remediation: str = ""
```

### 7.3 Rule Contract

Every rule module exposes:

```python
def check(ctx: AuditContext) -> list[Finding]:
    ...
```

### 7.4 AuditContext

AuditContext should include:

- root path
- file index
- package metadata
- env files
- source file text
- helper methods for search

The context is read-only after construction.

---

## 8. STEP-BY-STEP IMPLEMENTATION

### Step 1 - Package Setup (30 min)

Create `pyproject.toml`, package directories, empty rule modules, and Click CLI stub.

Checkpoint:

```bash
pip install -e .
shipcheck --help
```

### Step 2 - Scanner (60 min)

Implement target resolution, GitHub shallow clone, file collection, and text loading.

Skip:

- `.git`
- `node_modules`
- `.next`
- `dist`
- `build`
- `.venv`
- coverage folders
- binary/media files

Checkpoint:

```bash
shipcheck tests/fixtures/next_supabase_bad --json
```

It should print a valid empty report before rules exist.

### Step 3 - Models and Engine (45 min)

Implement `Finding`, `AuditContext`, `AuditReport`, and engine dispatch.

Checkpoint:

```bash
pytest tests/test_scanner.py tests/test_report.py -q
```

### Step 4 - Secrets Rules (75 min)

Implement high-value secret checks first.

Required checks:

- committed `.env`
- missing env ignore
- public secret variable names
- actual API key patterns
- Supabase service role references
- Stripe secret key references

Checkpoint:

```bash
pytest tests/test_secrets.py -q
```

### Step 5 - Auth Rules (60 min)

Implement basic Next.js auth checks.

Required checks:

- no middleware in app with auth dependency
- API route mutation without auth keyword
- admin route without role keyword
- client-only route protection markers

Checkpoint:

```bash
pytest tests/test_auth.py -q
```

### Step 6 - Database Rules (60 min)

Implement Supabase/Postgres checks.

Required checks:

- no migrations directory
- no RLS enable statements
- wide-open policies
- service role used in browser paths

Checkpoint:

```bash
pytest tests/test_database.py -q
```

### Step 7 - Payments Rules (45 min)

Implement Stripe checks.

Required checks:

- webhook route exists but no signature verification
- `checkout.session.completed` absent while Stripe checkout exists
- entitlement granted from success URL
- test/production key confusion

Checkpoint:

```bash
pytest tests/test_payments.py -q
```

### Step 8 - Reliability and Trust Rules (45 min)

Implement lightweight operations and landing trust checks.

Required checks:

- empty catch blocks
- no tests
- no CI
- no privacy/terms pages
- placeholder copy
- generic AI launch copy

Checkpoint:

```bash
pytest tests/test_reliability.py tests/test_trust.py -q
```

### Step 9 - Scoring and Report (60 min)

Implement weighted category scoring, verdicts, Markdown report, JSON report, and Rich terminal summary.

Checkpoint:

```bash
shipcheck tests/fixtures/next_supabase_bad --markdown report.md
shipcheck tests/fixtures/next_supabase_bad --json | python -m json.tool
```

### Step 10 - Fixtures and Integration Tests (60 min)

Create two fixtures:

- `next_supabase_bad`: intentionally unsafe
- `next_supabase_clean`: minimal safer baseline

The bad fixture should score high risk. The clean fixture should score launchable or needs_work.

Checkpoint:

```bash
pytest -q
```

### Step 11 - README and Handoff (45 min)

Write README with:

- what ShipCheck does
- install
- CLI examples
- GitHub Action example
- scoring explanation
- limitations

Write `runs/handoff.md`.

Checkpoint:

```bash
shipcheck --help
shipcheck tests/fixtures/next_supabase_bad
pytest -q
```

---

## 9. CODE SKELETONS

### 9.1 pyproject.toml

```toml
[project]
name = "shipcheck"
version = "0.1.0"
description = "Production-readiness audit for AI-built SaaS projects"
requires-python = ">=3.10"
dependencies = [
  "click>=8.1",
  "rich>=13.0",
  "gitpython>=3.1",
  "pyyaml>=6.0",
  "tomli>=2.0; python_version<'3.11'"
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "ruff>=0.1.0", "black>=23.0"]

[project.scripts]
shipcheck = "shipcheck.cli:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
```

### 9.2 cli.py

```python
from pathlib import Path
import sys
import click

from .engine import run_audit
from .report import render_json, render_markdown, render_terminal


@click.command()
@click.argument("target")
@click.option("--json", "as_json", is_flag=True, help="Print JSON report")
@click.option("--markdown", type=click.Path(), default="shipcheck-report.md")
@click.option("--threshold", type=int, default=None)
@click.option("--profile", default="next-supabase-stripe")
@click.option("--max-files", type=int, default=500)
@click.option("--include-tests", is_flag=True, default=False)
def main(target: str, as_json: bool, markdown: str, threshold: int | None,
         profile: str, max_files: int, include_tests: bool) -> None:
    report = run_audit(
        target=target,
        profile=profile,
        max_files=max_files,
        include_tests=include_tests,
    )
    if as_json:
        click.echo(render_json(report))
    else:
        render_terminal(report)
        Path(markdown).write_text(render_markdown(report), encoding="utf-8")
        click.echo(f"Wrote {markdown}")

    if threshold is not None and report.score > threshold:
        sys.exit(1)
```

### 9.3 models.py

```python
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    path: Path
    rel_path: str
    text: str


@dataclass(frozen=True)
class Finding:
    id: str
    category: str
    severity: str
    title: str
    file: str | None = None
    line: int | None = None
    evidence: str | None = None
    why_it_matters: str = ""
    remediation: str = ""


@dataclass
class AuditContext:
    root: Path
    files: list[SourceFile]
    profile: str

    def by_suffix(self, *suffixes: str) -> list[SourceFile]:
        return [f for f in self.files if f.rel_path.endswith(suffixes)]

    def find_text(self, needle: str) -> list[tuple[SourceFile, int, str]]:
        matches = []
        for source in self.files:
            for idx, line in enumerate(source.text.splitlines(), 1):
                if needle in line:
                    matches.append((source, idx, line.strip()))
        return matches


@dataclass
class AuditReport:
    target: str
    profile: str
    files_scanned: int
    score: int
    verdict: str
    categories: dict[str, dict[str, int]]
    findings: list[Finding] = field(default_factory=list)
```

### 9.4 scanner.py

```python
from pathlib import Path
import shutil
import tempfile
from git import Repo

from .models import SourceFile

SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", ".venv", "coverage"}
TEXT_SUFFIXES = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".sql",
    ".json", ".md", ".yml", ".yaml", ".toml", ".env", ".example",
}


def resolve_target(target: str) -> tuple[Path, Path | None]:
    if target.startswith(("http://", "https://", "git@")):
        tmp = Path(tempfile.mkdtemp(prefix="shipcheck-"))
        Repo.clone_from(target, tmp, depth=1)
        return tmp, tmp
    return Path(target).resolve(), None


def cleanup_tmp(tmp: Path | None) -> None:
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)


def collect_files(root: Path, max_files: int, include_tests: bool = False) -> list[SourceFile]:
    files: list[SourceFile] = []
    for path in sorted(root.rglob("*")):
        if len(files) >= max_files:
            break
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        parts = set(path.relative_to(root).parts)
        if parts & SKIP_DIRS:
            continue
        if not include_tests and any(p in {"test", "tests", "__tests__"} for p in parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in {".env", ".env.local", ".gitignore"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        files.append(SourceFile(path=path, rel_path=rel, text=text))
    return files
```

### 9.5 engine.py

```python
from .models import AuditContext, AuditReport, Finding
from .scanner import cleanup_tmp, collect_files, resolve_target
from .scoring import score_findings
from .rules import auth, database, payments, reliability, secrets, trust

RULE_MODULES = [secrets, auth, database, payments, reliability, trust]


def run_audit(target: str, profile: str, max_files: int, include_tests: bool) -> AuditReport:
    root, tmp = resolve_target(target)
    try:
        files = collect_files(root, max_files=max_files, include_tests=include_tests)
        ctx = AuditContext(root=root, files=files, profile=profile)
        findings: list[Finding] = []
        for module in RULE_MODULES:
            findings.extend(module.check(ctx))
        score, verdict, categories = score_findings(findings)
        return AuditReport(
            target=target,
            profile=profile,
            files_scanned=len(files),
            score=score,
            verdict=verdict,
            categories=categories,
            findings=findings,
        )
    finally:
        cleanup_tmp(tmp)
```

### 9.6 scoring.py

```python
CATEGORY_MAX = {
    "secrets": 25,
    "auth": 20,
    "database": 20,
    "payments": 15,
    "reliability": 10,
    "trust": 10,
}

SEVERITY_POINTS = {
    "critical": 15,
    "high": 8,
    "medium": 4,
    "low": 1,
}


def score_findings(findings):
    categories = {name: {"score": 0, "max_score": max_score}
                  for name, max_score in CATEGORY_MAX.items()}
    for finding in findings:
        points = SEVERITY_POINTS[finding.severity]
        cat = categories[finding.category]
        cat["score"] = min(cat["max_score"], cat["score"] + points)
    total = sum(c["score"] for c in categories.values())
    return total, verdict(total), categories


def verdict(score: int) -> str:
    if score <= 24:
        return "launchable"
    if score <= 49:
        return "needs_work"
    if score <= 74:
        return "high_risk"
    return "do_not_launch"
```

### 9.7 rules/secrets.py

```python
import re
from shipcheck.models import AuditContext, Finding

SECRET_PATTERNS = [
    ("OPENAI key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("Stripe secret key", re.compile(r"sk_(live|test)_[A-Za-z0-9]{20,}")),
    ("Supabase JWT", re.compile(r"eyJ[A-Za-z0-9_-]{20,}\\.[A-Za-z0-9_-]{20,}")),
]

PUBLIC_SECRET_NAMES = [
    "NEXT_PUBLIC_SUPABASE_SERVICE_ROLE",
    "NEXT_PUBLIC_STRIPE_SECRET",
    "NEXT_PUBLIC_OPENAI_API_KEY",
    "NEXT_PUBLIC_ANTHROPIC_API_KEY",
]


def check(ctx: AuditContext) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_env_files(ctx))
    findings.extend(_public_secret_names(ctx))
    findings.extend(_literal_secrets(ctx))
    findings.extend(_service_role_client(ctx))
    return findings


def _env_files(ctx: AuditContext) -> list[Finding]:
    out = []
    for f in ctx.files:
        if f.rel_path in {".env", ".env.local"}:
            out.append(Finding(
                id="secrets.env_committed",
                category="secrets",
                severity="critical",
                title="Environment file appears committed",
                file=f.rel_path,
                why_it_matters="Committed env files often contain production secrets.",
                remediation="Remove the file from git history and commit only .env.example.",
            ))
    return out
```

### 9.8 report.py

```python
import json
from dataclasses import asdict
from rich.console import Console
from rich.table import Table

console = Console()


def render_json(report) -> str:
    return json.dumps(asdict(report), indent=2, default=str)


def render_terminal(report) -> None:
    table = Table(title=f"ShipCheck: {report.score}/100 ({report.verdict})")
    table.add_column("Category")
    table.add_column("Score", justify="right")
    for name, data in report.categories.items():
        table.add_row(name, f"{data['score']}/{data['max_score']}")
    console.print(table)
    for finding in report.findings[:10]:
        console.print(f"[bold]{finding.severity.upper()}[/bold] {finding.title}")


def render_markdown(report) -> str:
    lines = [
        "# ShipCheck Report",
        "",
        f"Target: `{report.target}`",
        f"Risk score: **{report.score}/100**",
        f"Verdict: **{report.verdict}**",
        "",
        "## Category Breakdown",
        "",
    ]
    for name, data in report.categories.items():
        lines.append(f"- {name}: {data['score']}/{data['max_score']}")
    lines.extend(["", "## Findings", ""])
    for i, f in enumerate(report.findings, 1):
        loc = f"{f.file}:{f.line}" if f.file and f.line else (f.file or "repo")
        lines.extend([
            f"### {i}. [{f.severity.upper()}] {f.title}",
            "",
            f"- Category: `{f.category}`",
            f"- Location: `{loc}`",
            f"- Evidence: `{f.evidence or ''}`",
            f"- Why it matters: {f.why_it_matters}",
            f"- Remediation: {f.remediation}",
            "",
        ])
    return "\n".join(lines)
```

---

## 10. TEST FIXTURES

### 10.1 Bad Fixture

`tests/fixtures/next_supabase_bad` should contain:

- `.env.local` with fake but realistic keys
- `.gitignore` missing `.env*`
- `app/api/admin/route.ts` with POST handler and no auth
- `app/api/stripe/webhook/route.ts` without signature verification
- `lib/supabase.ts` using `SUPABASE_SERVICE_ROLE_KEY`
- `supabase/migrations/001.sql` with `using (true)`
- landing page with placeholder testimonials and generic AI copy

Expected:

- score >= 60
- at least one critical secrets finding
- at least one high payments finding
- at least one auth finding

### 10.2 Clean Fixture

`tests/fixtures/next_supabase_clean` should contain:

- `.env.example`
- `.gitignore` ignoring env files
- middleware or server auth helper
- Stripe webhook signature check
- RLS enable statement and scoped policy
- privacy and terms pages
- minimal test file

Expected:

- score <= 30
- no critical findings

---

## 11. FAILURE MODES TO AVOID

1. **Do not output noisy low-value findings.** A report with 80 weak findings will feel useless.
2. **Do not claim certainty without evidence.** Use wording like "No evidence found" when absence is heuristic.
3. **Do not require an LLM.** Determinism is part of the trust story.
4. **Do not scan `node_modules`.** It will make the tool slow and noisy.
5. **Do not print full secret values.** Redact evidence after a few characters.
6. **Do not treat all TODOs as findings.** Only auth/security/payment TODOs matter.
7. **Do not build a web dashboard in v1.** CLI/report first.
8. **Do not support every stack.** v1 is Next.js/Supabase/Stripe first.
9. **Do not make score equal count of findings.** Severity and category caps matter.
10. **Do not silently fail on bad files.** Warn and continue.
11. **Do not mutate target repos.** ShipCheck is read-only.
12. **Do not upload source code anywhere.** Local-only is a positioning advantage.
13. **Do not write giant abstractions.** Rule modules should be plain functions.
14. **Do not hide limitations.** README must explain heuristic false positives and false negatives.

---

## 12. RUN COMMANDS (Final Smoke Test)

```bash
cd builds/shipcheck
pip install -e ".[dev]"

shipcheck --help

shipcheck tests/fixtures/next_supabase_bad --markdown bad-report.md
shipcheck tests/fixtures/next_supabase_bad --json | python -m json.tool

shipcheck tests/fixtures/next_supabase_clean --markdown clean-report.md

shipcheck tests/fixtures/next_supabase_bad --threshold 50
echo $?  # expected non-zero

pytest -q
```

Optional public repo test:

```bash
shipcheck https://github.com/<owner>/<repo> --markdown report.md
```

---

## 13. SUCCESS CRITERIA

1. `pip install -e ".[dev]"` succeeds.
2. `shipcheck --help` shows usage.
3. Bad fixture produces score >= 60.
4. Clean fixture produces score <= 30.
5. JSON output is valid JSON.
6. Markdown report is readable and includes top risks.
7. Threshold exits non-zero when score exceeds threshold.
8. No finding prints complete secret values.
9. Scanner skips `node_modules`, `.next`, `.git`, and build outputs.
10. Tests pass with `pytest -q`.
11. Application code stays under 1,200 LOC.
12. README includes install, examples, scoring, limitations, and GitHub Action example.

---

## 14. OUT OF SCOPE

- hosted SaaS dashboard
- account system
- paid billing
- real-time GitHub app
- full TypeScript AST parsing
- full SAST replacement
- dependency vulnerability database
- secret revocation automation
- automatic code modification
- private GitHub auth
- multi-language support beyond lightweight text scanning
- LLM-generated remediation
- SOC2/GDPR certification claims

---

## 15. README REQUIREMENTS

README must include:

```markdown
# ShipCheck

Production-readiness audit for AI-built SaaS apps.

## Install

pip install shipcheck

## Usage

shipcheck .
shipcheck . --json
shipcheck . --threshold 50

## What It Checks

- secrets
- auth
- database security
- payments
- reliability
- trust surface

## What It Does Not Do

ShipCheck is heuristic. It does not prove your app is secure.

## GitHub Action

...
```

---

## 16. RUN REPORT TEMPLATE

When implementation is done, write `runs/handoff.md`:

```markdown
# ShipCheck Handoff

## What I built
- Files created:
- Total application LOC:
- Tests added:

## Verification results
- [ ] pip install works
- [ ] shipcheck --help works
- [ ] bad fixture scores high
- [ ] clean fixture scores low
- [ ] JSON validates
- [ ] threshold exits correctly
- [ ] pytest passes
- [ ] LOC under budget

## Sample output

$ shipcheck tests/fixtures/next_supabase_bad
...

## What did not work
- ...

## Follow-up ideas
- GitHub Action
- hosted dashboard
- LLM remediation
- Clerk/Firebase profiles
```

---

## 17. CONSTRAINTS

- Python 3.10+
- Type hints on public functions
- Use `pathlib.Path`
- Keep rules plain and testable
- Prefer deterministic checks
- No network calls except optional GitHub clone
- No LLM dependency
- No writes inside target repo
- Do not print full secrets
- Conventional commits if committing

---

## 18. FUTURE VERSIONS

### v1.1 GitHub Action

Add `.github/actions/shipcheck` or documented action usage.

### v1.2 Clerk/Firebase Profiles

Add auth-provider-specific rules.

### v1.3 LLM Remediation

Optional local or API-based remediation generator, never required for core scoring.

### v2 Hosted Dashboard

Private repo integration, team reports, trends over time.

---

**End of spec.**
