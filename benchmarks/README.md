# ShipCheck Benchmarks

This directory defines public benchmark targets for checking ShipCheck's signal quality against real Next.js/Supabase/Stripe-style repositories.

The benchmark manifest is `targets.json`. It intentionally does not include scores yet. Do not invent results; run the benchmark and record observations separately.

## Run A Single Target

```bash
shipcheck https://github.com/ShenSeanChen/launch-mvp-stripe-nextjs-supabase --json
```

## Run All Targets

Example shell loop:

```bash
python - <<'PY'
import json
import subprocess

targets = json.load(open("benchmarks/targets.json"))["targets"]
for target in targets:
    print(f"== {target['name']} ==")
    subprocess.run([
        "shipcheck",
        target["repo"],
        "--json",
        "--max-files",
        "800",
    ], check=False)
PY
```

## What To Record

- score and verdict
- top critical/high findings
- obvious false positives
- obvious false negatives
- whether generated/vendor files were skipped correctly
- whether the report feels short enough for a launch review

Keep raw outputs out of the manifest unless they have been reviewed. The manifest should remain a target list, not a claims file.
