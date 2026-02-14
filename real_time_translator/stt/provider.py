from __future__ import annotations

import os
from typing import Protocol

import speech_recognition as sr


class STTProvider(Protocol):
    def transcribe(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> str:
        ...


class GoogleSTTProvider:
    def __init__(self, language: str = "en-US") -> None:
        self._language = language

    def transcribe(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> str:
        candidates = [self._language, "en-GB"] if self._language != "en-GB" else [self._language, "en-US"]
        for lang in candidates:
            try:
                detailed = recognizer.recognize_google(audio, language=lang, show_all=True)
                if isinstance(detailed, dict):
                    alternatives = detailed.get("alternative", []) or []
                    valid = [alt for alt in alternatives if str(alt.get("transcript", "")).strip()]
                    if valid:
                        best = max(
                            valid,
                            key=lambda alt: (
                                float(alt.get("confidence", -1.0)),
                                len(str(alt.get("transcript", ""))),
                            ),
                        )
                        text = str(best.get("transcript", "")).strip()
                        if text and len(text) >= 2:
                            return text
                fallback = recognizer.recognize_google(audio, language=lang).strip()
                if fallback and len(fallback) >= 2:
                    return fallback
            except sr.UnknownValueError:
                continue
        raise sr.UnknownValueError()


class HybridSTTProvider:
    def __init__(self, language: str = "en-US") -> None:
        self._language = language
        self._google = GoogleSTTProvider(language=language)
        self._whisper = None
        self._backend = "google"
        self._whisper_language = "en"

        model_name = os.getenv("RT_STT_MODEL", "small.en")
        try:
            from faster_whisper import WhisperModel  # type: ignore

            self._whisper = WhisperModel(model_name, device="auto", compute_type="int8")
            self._backend = f"whisper:{model_name}+google"
        except Exception:
            self._whisper = None
            self._backend = "google"

    def backend_name(self) -> str:
        return self._backend

    def transcribe(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> str:
        if self._whisper is not None:
            try:
                text = self._transcribe_with_whisper(audio)
                if text:
                    return text
            except sr.UnknownValueError:
                pass
            except Exception:
                # If Whisper fails for any reason, keep app working via Google fallback.
                pass
        return self._google.transcribe(recognizer, audio)

    def _transcribe_with_whisper(self, audio: sr.AudioData) -> str:
        import numpy as np

        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if pcm.size == 0:
            raise sr.UnknownValueError()

        segments, _info = self._whisper.transcribe(  # type: ignore[union-attr]
            pcm,
            language=self._whisper_language,
            task="transcribe",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            vad_filter=True,
            condition_on_previous_text=False,
            word_timestamps=False,
            no_speech_threshold=0.45,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
        )

        merged = " ".join((seg.text or "").strip() for seg in segments).strip()
        if len(merged) < 2:
            raise sr.UnknownValueError()
        return merged
