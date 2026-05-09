# Shipping Readiness

Use this skill when a coding agent finishes building or modifying a SaaS app and needs to decide whether it is safe to call the work done.

## Goal

Run ShipCheck as a launch-readiness gate before final handoff. Do not mark the task complete while critical or high-risk findings remain unreviewed.

## Workflow

1. Install project dependencies for the target app as needed.
2. Install ShipCheck if it is not available:

   ```bash
   python -m pip install shipcheck-ai
   ```

3. Run the audit from the target repository root:

   ```bash
   shipcheck . --threshold 50
   ```

4. If a Markdown report is useful for handoff, also run:

   ```bash
   shipcheck . --markdown shipcheck-report.md
   ```

5. If structured output is needed, run:

   ```bash
   shipcheck . --json
   ```

## Agent Rules

- Treat ShipCheck as a deterministic readiness audit, not a security proof.
- Read the JSON or Markdown report before claiming the build is done.
- Do not ignore `critical` or `high` findings.
- Fix critical/high findings when they are real, then rerun ShipCheck.
- If a finding is a false positive, document why in the handoff.
- Do not upload source code anywhere; run ShipCheck locally in the target repo.
- Do not say "done" while `shipcheck . --threshold 50` fails unless the user explicitly accepts the remaining risk.
