from __future__ import annotations

from shipcheck.models import AuditContext, Finding
from .common import code_files, finding, is_generated_file, is_stripe_webhook_route, line_has, verifies_stripe_signature


def check(ctx: AuditContext) -> list[Finding]:
    out: list[Finding] = []
    scan_files = [f for f in code_files(ctx) if not is_generated_file(f.rel_path, f.text)]
    stripe_files = [f for f in scan_files if "stripe" in f.text.lower() or "stripe" in f.rel_path.lower()]
    uses_checkout = any(line_has(f.text, "checkout.sessions.create", "stripe.redirecttocheckout", "price_") for f in scan_files)
    has_completed = ctx.any_text("checkout.session.completed")
    for f in scan_files:
        low_path = f.rel_path.lower()
        low_text = f.text.lower()
        is_stripe_related = f in stripe_files
        if is_stripe_webhook_route(f) and not verifies_stripe_signature(f.text):
            out.append(finding("payments.webhook_no_signature", "payments", "high", "Stripe webhook does not verify signatures", f, 1, "webhook route without constructEvent", "Unsigned webhooks can be forged to grant access.", "Use stripe.webhooks.constructEvent with STRIPE_WEBHOOK_SECRET."))
        if "success" in low_path and line_has(low_text, "subscription", "entitlement", "premium", "paid", "active") and not line_has(low_text, "webhook"):
            out.append(finding("payments.success_grants_entitlement", "payments", "critical", "Checkout success path appears to grant entitlement", f, 1, "success route entitlement marker", "Success redirects are user-controlled and should not be the source of truth.", "Grant access only after verified Stripe webhook events."))
        if is_stripe_related and "sk_test_" in f.text and ("production" in f.text.lower() or ".env.production" in f.rel_path):
            out.append(finding("payments.test_key_production", "payments", "medium", "Stripe test key appears in production context", f, 1, "sk_test_...REDACTED", "Test keys in production break real payment flows.", "Separate test and live Stripe configuration by environment."))
        if is_stripe_related and "price_" in f.text and "process.env" not in f.text:
            out.append(finding("payments.hardcoded_price", "payments", "low", "Stripe price ID is hard-coded", f, 1, "price_...", "Hard-coded price IDs make environment separation fragile.", "Read price IDs from environment config."))
        has_idempotency_evidence = any(
            marker in low_text
            for marker in ("idempotency", "stripe_payment_id", "processed_event", "processed_events", "event.id")
        )
        if is_stripe_related and not has_idempotency_evidence and any(word in low_text for word in ("checkout.session.completed", "invoice.paid", "customer.subscription")):
            out.append(finding("payments.no_idempotency", "payments", "medium", "Stripe event handling lacks idempotency evidence", f, 1, "event handler without idempotency keyword", "Stripe may retry events, causing duplicate grants or updates.", "Store processed event IDs or use idempotent writes."))
    if uses_checkout and not has_completed:
        out.append(finding("payments.no_checkout_completed", "payments", "high", "Stripe checkout exists without checkout.session.completed handling", evidence="checkout.sessions.create", why="Entitlements should be confirmed by webhook events.", fix="Handle checkout.session.completed in a verified webhook route."))
    return out
