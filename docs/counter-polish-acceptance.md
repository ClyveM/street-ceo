# Counter polish — Owner brief, 2026-11-01

The Owner reported the phone sale working and supplied a saved-receipt screenshot.
Preserve the working catalogue, Muse matching, payment, stock, history, retry and
server contracts. This assignment changes presentation and voice session continuity.

- Busy-shop hierarchy: short saved state, products/quantities, Total, Tendered and
  Change. Change is easy to read at a glance. Do not expose debug prose by default.
- Receipt identifiers, timestamps, transcripts, connection/build diagnostics and
  stock/settlement/undo explanation remain available on demand or in Profile.
  An Undo action keeps its existing limitations next to the action.
- Use the existing logo and restrained navy/green/teal with a warm accent and
  friendly short copy. Do not add new characters, image assets or frameworks.
- An Apo/Apple wake closes only a completed receipt, returns to the sale screen
  and preserves any following words in that same utterance for the next basket.
- A wake never abandons pending tender, match clarification or an uncertain paid
  request. It cannot create a sale merely by closing a receipt.
- One hands-free preference covers wake framing, match replies, quantity replies,
  Cash/Bank/amount, question retry and repeated sales. Explicit pause remains
  available; successful completion/modal close does not turn listening off.
- Typing is available without losing the hands-free preference. Recognition stays
  quiet during its own spoken output and while the app is in the background.

Gate: targeted session/wake regressions, full frontend tests/build, independent QA,
APK asset/signature/download checks, then phone layout and two-sale voice rehearsal.
No backend restart or live sale mutation is needed for this presentation patch.
