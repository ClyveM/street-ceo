# Catalogue voice proposal controls — 2026-11-01

Task: CATALOGUE-VOICE-REVIEW-001. Ruzivo. Internal advisory code review, not
statutory certification.

**Verdict: approve with conditions for the connected sale demo.** No new
financially material posting bypass was found in the inspected catalogue proposal
and confirmation changes. Prior scoped sale/cash review conditions continue to
apply; this does not clear the separate full accounting review.

## Reviewed controls

- The AI receives bounded catalogue IDs, names and SKUs, without authority to set
  a price or execute a sale. Transcript item segments and explicit quantities are
  established before the provider call. Response schema, coverage, integer/type
  checks and lexical plausibility reject invented IDs, changed quantities, missing
  segments, unresolved products and ambiguous substitutions.
- A missing quantity stays a clarification question with no sale lines. The model
  cannot make a guessed quantity actionable. A quantity reply is associated with
  an existing same-shop clarification; a resolved contextual answer still requires
  explicit product confirmation.
- The API independently resolves proposed IDs against current shop products,
  rejects duplicate or unavailable products and invalid/excess quantities, and
  generates its confirmation summary from the server catalogue. Unknown/incomplete
  baskets produce no partial sale.
- A proposed match is stored as `needs_match_confirmation`, not a committed sale.
  `match_confirmed` is a strict boolean and defaults false. The API refuses a
  proposal commit without true approval, even if tender/cash is supplied. It
  requires the submitted line IDs/quantities to equal the stored review.
- The UI does not treat a proposal as committable. It reads the proposed product
  summary, accepts Yes/No/Cancel, and only Yes enables the next payment step. No or
  Cancel does not call sale commit. Cash words and ordinary replies are not an
  affirmative product confirmation. Direct complete exact-catalogue commands retain
  the previously reviewed quick-sale path.
- After approval, total and cash change are still calculated by the server from
  its catalogue prices and payment input. Stock validation, pre-sale COGS snapshot,
  atomic SQLite persistence and one-review/one-sale retry binding remain in place.
  The new approval flag participates in the commit fingerprint when true; false
  is omitted to preserve original exact-command replay fingerprints.

## Conditions and limits

Use the single-worker connected SQLite demo and supported modest integer-cent
catalogue prices. Observe the product summary and explicit Yes on the actual
phone; an AI proposal is not proof that speech was heard correctly. The matching
heuristics and provider schema are controls, not a guarantee of semantic accuracy
for all free-form speech. Confirmation must not be represented as an authenticated
or tamper-proof speech audit: the API trusts the operator client's explicit flag.

Provider/source labels and sanitized traces must remain truthful; deterministic
matching is not a Muse invocation. Preserve the original key for uncertain commit
recovery. Bank remains recorded tender rather than verified settlement. No new
ledger, profitability, day-close, invoice or return approval is issued.

## Evidence

Inspected `services/ai/catalogue_voice.py`, AI regression tests,
`services/api/app.py` resolution/transcript/commit paths,
`services/api/voice_boundary.py`, API catalogue tests, SQLite trace middleware,
frontend `VoiceCapture.tsx` and `quickSale.ts`, and the independent
`tests/catalogue_voice_client.mjs` contract fixtures. Tests inspected cover proposal
confirmation before tender/commit, changed or omitted approval, reopen/retry,
missing-quantity follow-up, incomplete/unknown basket rejection, model quantity
tampering and exact-command legacy fingerprints.

Parent reports 215 broad backend passes plus 18 independent confirmation tests,
four real-provider no-sale cases with correct outcomes, and 136 frontend passes.
These are attributed results, not fresh executions by Ruzivo. No live request,
provider call, sale mutation, source edit or physical-phone test was performed in
this review. Only this memo and own brain checkpoints were written.

Next: Mutungamiri packages the verified current APK and observes the proposal →
Yes → payment → authoritative receipt → stock/history flow on a phone. Re-review
if quantity, confirmation, pricing, commit or replay semantics change.
