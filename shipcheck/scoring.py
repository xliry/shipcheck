from __future__ import annotations

CATEGORY_MAX = {"secrets": 25, "auth": 20, "database": 20, "payments": 15, "reliability": 10, "trust": 10}
SEVERITY_POINTS = {"critical": 15, "high": 8, "medium": 4, "low": 1}


def score_findings(findings):
    categories = {name: {"score": 0, "max_score": max_score} for name, max_score in CATEGORY_MAX.items()}
    for finding in findings:
        cat = categories[finding.category]
        cat["score"] = min(cat["max_score"], cat["score"] + SEVERITY_POINTS[finding.severity])
    total = min(100, sum(c["score"] for c in categories.values()))
    return total, verdict(total), categories


def verdict(score: int) -> str:
    if score <= 24:
        return "launchable"
    if score <= 49:
        return "needs_work"
    if score <= 74:
        return "high_risk"
    return "do_not_launch"


def summary(score: int) -> str:
    if score <= 24:
        return "No launch-blocking evidence found by ShipCheck heuristics."
    if score <= 49:
        return "Address the listed production-readiness gaps before launch."
    if score <= 74:
        return "Launch is risky until the high-severity findings are fixed."
    return "Launch should be blocked until critical findings are fixed."
