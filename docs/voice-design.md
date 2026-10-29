# Street CEO — Voice Design (v0, 2026-10-29)

Status: interaction contract. No pipeline implemented yet. Owner: Inzwi.

## The interaction

- "Apo" — wake word. Device starts listening.
- Command — one short utterance (a sale, a stock check, a cash query).
- "Napo" — ends the command. Device stops listening and acts.
- Confirmation — audible and visible; the vendor confirms before anything posts.

## Grammar (initial, kept small deliberately)

1. Record sale: item + quantity (+ price override if needed).
2. Check stock: item → quantity on hand.
3. Check cash: today's sales / cash position.
4. Cancel: abort the current command with no side effects.

Exact phrasings to be fixed by Inzwi with test utterances, including
noisy-market samples.

## Design rules

- Short, fast commands only; no open-ended dictation.
- Never posts an unconfirmed sale; misheard commands fail safe.
- Latency budget favors completion in seconds on low-cost devices.
- Every voice action maps to an existing API endpoint (no voice-only side paths).
- Error recovery is spoken and shown: repeat, correct, or cancel.
