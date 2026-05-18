# ShipCheck Report

Target: `active-project`
Risk score: **33/100**
Verdict: **needs_work**

Address the listed production-readiness gaps before launch.

## Top Risks

1. [MEDIUM] Client-side route protection found; verify server-side API enforcement
2. [MEDIUM] Wide-open policy on table gem_credit_costs
3. [MEDIUM] Wide-open policy on table gem_credit_costs
4. [MEDIUM] No CI workflow found
5. [MEDIUM] No tests found

## Category Breakdown

- secrets: 0/25
- auth: 4/20
- database: 8/20
- payments: 1/15
- reliability: 10/10
- trust: 10/10

## Findings

### 1. [MEDIUM] Client-side route protection found; verify server-side API enforcement

- Category: `auth`
- Location: `repo`
- Evidence: `No direct snippet`
- Why it matters: React Router guards protect navigation UX, but API and paid flows still need server-side authorization checks.
- Remediation: Verify Vercel/Cloud Run/API handlers check Supabase auth or service boundaries before mutating user data.

### 2. [MEDIUM] Wide-open policy on table gem_credit_costs

- Category: `database`
- Location: `supabase/migrations/create_gem_credits.sql:15`
- Evidence: `CREATE POLICY Allow read access ON public.gem_credit_costs FOR SELECT USING (true);`
- Why it matters: ShipCheck could not classify gem_credit_costs sensitivity; verify this public policy is intentional.
- Remediation: Replace true with an explicit ownership, role, or public-read condition.

### 3. [MEDIUM] Wide-open policy on table gem_credit_costs

- Category: `database`
- Location: `supabase/migrations/create_gem_results.sql:95`
- Evidence: `CREATE POLICY Anyone can read gem credit costs ON public.gem_credit_costs FOR SELECT TO PUBLIC USING (TRUE);`
- Why it matters: ShipCheck could not classify gem_credit_costs sensitivity; verify this public policy is intentional.
- Remediation: Replace true with an explicit ownership, role, or public-read condition.

### 4. [MEDIUM] No CI workflow found

- Category: `reliability`
- Location: `repo`
- Evidence: `No direct snippet`
- Why it matters: Critical flows need automated checks before launch.
- Remediation: Add a GitHub Actions workflow for tests and linting.

### 5. [MEDIUM] No tests found

- Category: `reliability`
- Location: `repo`
- Evidence: `No direct snippet`
- Why it matters: Payment and auth regressions are easy to ship without tests.
- Remediation: Add focused tests for auth, payments, and core flows.

### 6. [MEDIUM] Empty catch block found

- Category: `reliability`
- Location: `components/Generator/HistoryCard.tsx:109`
- Evidence: `} catch {}`
- Why it matters: Swallowed errors hide production failures.
- Remediation: Log, rethrow, or return a controlled error response.

### 7. [LOW] Stripe price ID is hard-coded

- Category: `payments`
- Location: `pages/Pricing.tsx:1`
- Evidence: `price_...`
- Why it matters: Hard-coded price IDs make environment separation fragile.
- Remediation: Read price IDs from environment config.

### 8. [LOW] Generic AI launch copy found

- Category: `trust`
- Location: `README.md:1`
- Evidence: `generic AI copy marker`
- Why it matters: Generic launch copy makes the app feel unfinished.
- Remediation: Use concrete customer outcomes and specific product language.

### 9. [LOW] Generic AI launch copy found

- Category: `trust`
- Location: `cloudrun/src/routes/storybook.ts:1`
- Evidence: `generic AI copy marker`
- Why it matters: Generic launch copy makes the app feel unfinished.
- Remediation: Use concrete customer outcomes and specific product language.

### 10. [LOW] Generic AI launch copy found

- Category: `trust`
- Location: `constants/generatorModels.ts:1`
- Evidence: `generic AI copy marker`
- Why it matters: Generic launch copy makes the app feel unfinished.
- Remediation: Use concrete customer outcomes and specific product language.

### 11. [LOW] Generic AI launch copy found

- Category: `trust`
- Location: `constants/showcase.ts:1`
- Evidence: `generic AI copy marker`
- Why it matters: Generic launch copy makes the app feel unfinished.
- Remediation: Use concrete customer outcomes and specific product language.

### 12. [LOW] Generic AI launch copy found

- Category: `trust`
- Location: `pages/FAQ.tsx:1`
- Evidence: `generic AI copy marker`
- Why it matters: Generic launch copy makes the app feel unfinished.
- Remediation: Use concrete customer outcomes and specific product language.

### 13. [LOW] Generic AI launch copy found

- Category: `trust`
- Location: `pages/ImageEdit.tsx:1`
- Evidence: `generic AI copy marker`
- Why it matters: Generic launch copy makes the app feel unfinished.
- Remediation: Use concrete customer outcomes and specific product language.

### 14. [LOW] Placeholder copy found

- Category: `trust`
- Location: `pages/Login.tsx:35`
- Evidence: `setError(Email login coming soon!);`
- Why it matters: Placeholder content reduces buyer trust.
- Remediation: Replace placeholders with specific product copy.

### 15. [LOW] Placeholder copy found

- Category: `trust`
- Location: `pages/Signup.tsx:34`
- Evidence: `setError(Email signup coming soon!);`
- Why it matters: Placeholder content reduces buyer trust.
- Remediation: Replace placeholders with specific product copy.

### 16. [LOW] Generic AI launch copy found

- Category: `trust`
- Location: `scripts/seed-community.js:1`
- Evidence: `generic AI copy marker`
- Why it matters: Generic launch copy makes the app feel unfinished.
- Remediation: Use concrete customer outcomes and specific product language.

### 17. [LOW] Placeholder copy found

- Category: `trust`
- Location: `video-apis/README.md:92`
- Evidence: `The codebase includes placeholder API calls in `/api/generate-video.ts`:`
- Why it matters: Placeholder content reduces buyer trust.
- Remediation: Replace placeholders with specific product copy.




