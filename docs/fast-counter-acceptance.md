# Fast counter acceptance — 2026-11-02

## Later Owner-approved demo override — 2026-11-02

The Owner accepts a longer wait for imperfect product phrases for this demo.
Catalogue Muse resolution now has a 24-second application budget, with a
25-second catalogue HTTP timeout and the existing 30-second voice client timeout.
This replaces the six-second target below. Local matches stay immediate, no
automatic retries are added, and uncertain results still require confirmation.
Provider speed and successful product interpretation are not guaranteed by a
longer timeout. The earlier performance target remains historical context.

Owner: 24 seconds is too long during selling. Preserve the entire hands-free
catalogue → confirmation → Cash/Bank/amount → durable receipt → next Apo cycle,
with typing available. Exact catalogue interpretation already has a parser.

- Immediate conservative proposals may handle exact unique catalogue aliases plus
  narrowly observed speech-noise tails. Every quantity and item must be preserved.
  Words that may name another catalogue product cannot be discarded. Unknown or
  ambiguous baskets never partially post. No Apple/fruit stripping.
- These proposals identify their local source honestly and always require spoken
  product confirmation before payment. Existing server approval enforcement,
  idempotency, price, stock and historical cost snapshots remain authoritative.
- Harder phrases use one real Muse call with a short bounded wait (target six
  seconds), bounded two-call capacity and no automatic retry. Reuse connections
  and reduce prompt overhead; do not promise external provider latency.
- Keep persistent request/response investigations and honest fallback messages.
- Android app buttons must sit clear of the system navigation/gesture area.
  Hide navigation controls using supported transient swipe reveal; reserve safe
  stable space so revealed controls do not cover shop navigation. Keep status,
  permission prompts, IME, background/resume and native speech working.

Gate: specialist tests and independent QA, API confirmation/no-mutation smoke,
frontend build, offline native compile, APK signature/assets/download checks.
Physical Samsung three-button/gesture/swipe/keyboard and consecutive speech sale
acceptance remains separate. Root ADB inventory found no connected device.
