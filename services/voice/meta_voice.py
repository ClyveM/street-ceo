"""Meta Muse Voice Transcribe adapter for browser recordings."""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any, Mapping

from services.ai.tracing import traced_call


class MetaVoiceTranscriber:
    """Convert browser audio to WAV and transcribe it through Meta Model API."""

    def __init__(self, api_key: str, http_client: Any, ffmpeg: str = "ffmpeg") -> None:
        self.api_key = api_key
        self.http_client = http_client
        self.ffmpeg = ffmpeg

    def transcribe(self, audio: bytes, media_type: str) -> str:
        wav = self._to_wav(audio, media_type)
        model = "muse-voice-transcribe-1.0"

        def send() -> Mapping[str, Any]:
            response = self.http_client.post(
                "https://api.meta.ai/v1/asr/transcribe",
                headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"},
                files={
                    "request": (None, json.dumps({"model": model, "audioEncoding": "WAV", "mode": "PUSH_TO_TALK"}), "application/json"),
                    "audio": ("recording.wav", wav, "audio/wav"),
                },
            )
            response.raise_for_status()
            return response.json()

        # Investigation retains transport metadata and provider JSON, never audio.
        payload = traced_call(operation="voice_transcription", model=model,
                              request={"model": model, "media_type": media_type,
                                       "size_bytes": len(audio), "wav_size_bytes": len(wav)},
                              call=send, secret_values=(self.api_key,))
        transcript = payload.get("transcript") if isinstance(payload, Mapping) else None
        if not isinstance(transcript, str) or not transcript.strip():
            raise ValueError("Meta Voice Transcribe returned no transcript")
        return transcript.strip()

    def _to_wav(self, audio: bytes, media_type: str) -> bytes:
        container = media_type.split(";", 1)[0].removeprefix("audio/").strip().lower() or "webm"
        if container == "x-m4a":
            container = "mp4"
        result = subprocess.run(
            [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-f", container, "-i", "pipe:0", "-ac", "1", "-ar", "24000", "-c:a", "pcm_s16le", "-f", "wav", "pipe:1"],
            input=audio,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0 or not result.stdout:
            raise ValueError("Could not convert the browser recording to WAV")
        return result.stdout


def build_meta_voice_transcriber() -> MetaVoiceTranscriber:
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("LLAMA_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("LLAMA_API_KEY is not configured")
    try:
        import httpx
        import truststore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Install HTTP and certificate dependencies for Meta voice") from exc
    return MetaVoiceTranscriber(api_key, httpx.Client(verify=truststore.SSLContext()))
