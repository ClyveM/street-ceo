# Apo/Napo voice setup

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
