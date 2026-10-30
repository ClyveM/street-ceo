"""Evidence register for the Meta/Llama route (checked 2026-10-30).

This is deliberately a capability register, not a claim that Street CEO has
live access. ``verified`` means supported by the cited official material;
``available_here`` is false until credentials and a successful smoke test exist.
"""

CAPABILITY_MATRIX = (
    {
        "capability": "Structured tool/function-style output",
        "route": "Llama 3.1 / Llama 4 prompt formats",
        "verified": True,
        "available_here": False,
        "evidence": "https://github.com/meta-llama/llama-models/blob/main/models/llama4/prompt_format.md",
        "notes": "Model output is structured to facilitate calling; an executor must validate and act.",
    },
    {
        "capability": "Hosted inference client",
        "route": "Official Llama API Python client",
        "verified": True,
        "available_here": False,
        "evidence": "https://github.com/meta-llama/llama-api-python",
        "notes": "Official client documents API errors, timeouts, retries, and API-key configuration.",
    },
    {
        "capability": "Text reasoning for business insight",
        "route": "Llama 3.3 70B or Llama 4 Scout/Maverick via a configured provider",
        "verified": True,
        "available_here": False,
        "evidence": "https://ai.meta.com/resources/models-and-libraries/llama-downloads/",
        "notes": "Model family and text capability are documented; Street CEO fit, cost, and latency are unmeasured.",
    },
    {
        "capability": "Multimodal input",
        "route": "Llama 4 Scout/Maverick",
        "verified": True,
        "available_here": False,
        "evidence": "https://ai.meta.com/blog/llama-4-multimodal-intelligence/",
        "notes": "Not required for Wave 1 sale-intent or insight MVP.",
    },
    {
        "capability": "Street CEO live model access, credentials, latency, cost",
        "route": "Repository/runtime",
        "verified": False,
        "available_here": False,
        "evidence": None,
        "notes": "No key, installed provider SDK, deployment target, or successful live request was observed.",
    },
)
