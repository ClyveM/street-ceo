# Apo/Napo voice setup

## Current app framing and retries — 2026-11-02

The Android APK uses native foreground recognition/TTS; the web app uses supported
browser speech APIs. Both normalize recognized control words before submitting
the product request. Apo (or leading Apple) starts capture; terminal Napo, Nabo
or Napple closes it. Saved personal phrases remain supported, with longest
matching phrases taking precedence. Ordinary/internal Apple stays product text.

Catalogue questions accept a bare quantity or a complete framed retry. A retry
such as recognized “Apple one bath soap napple” is buffered across speech chunks
and canonicalized; control words do not become unknown products. Incomplete
framed retries wait for the end word rather than submit a partial basket.
Match, payment and day-close replies remain on their existing paths. Generic
trailing Apple is not treated as an end word. Profile pronunciation setup is
personal phrase matching, not training the speech provider's model.

## Short conversations and five-sample Napo setup

The payment-choice screen keeps its full visible question, while Apo says only
“Cash or bank?” A confirmed saved sale says “Sale saved.” Totals, amount received
and change remain visible on the receipt; other clarification/error prompts stay
specific to the answer needed.

In Profile, use Napo pronunciation setup to capture five samples. Review what
the recognizer heard for each sample. Valid distinct phrases are retained as
personal end-word aliases on that device; repeated recognitions count as samples
without duplicating aliases. Existing saved pronunciation remains supported.
For example, a tester can review and save “nepal”, “nepo” or “nopple” when that
is what their recognizer produces. These are personal mappings, not global fuzzy
matching or changes to Meta's speech model. Aliases close a command only at its
end; ordinary product words inside the basket remain product text. Reset clears
the personal mappings. Testers should repeat setup on their own device/browser.

Street CEO uses Meta Llama for understanding the transcript of a short shop
command. The Apo/Napo state machine remains responsible for wake/end words,
confirmation, stock checks, and posting a sale. This prevents a model response
from directly mutating stock or the ledger.

## Where to put the Meta API settings

Create a local, uncommitted `.env` file in the repository root:

```text
LLAMA_API_KEY=put-your-meta-llama-key-here
LLAMA_MODEL=the-model-id-enabled-for-your-account
```

Never commit this file or place the key in `apps/web`. The browser must not see
the key; the FastAPI/voice service reads it on the server. The official Meta
Llama Python client also supports `LLAMA_API_KEY` from the environment and
recommends keeping it out of source control.

Install the backend requirements, then create the provider with
`build_meta_llama_interpreter()`. The adapter accepts the transcript and
requires strict JSON for the bounded sale-intent schema. Invalid, unsafe, or
unavailable model output fails closed and leaves the sale unposted.

Meta Llama is the language-understanding layer. Microphone capture,
speech-to-text, and text-to-speech are separate audio capabilities; they need
an audio provider or an on-device Meta-compatible speech model. The current
text fallback and push-to-talk paths remain available while that audio layer is
selected.
