from __future__ import annotations

import audioop
from array import array
import re
import threading
import traceback
from datetime import datetime

import speech_recognition as sr
import numpy as np

from real_time_translator.audio.capture import AudioCapture
from real_time_translator.config import DEFAULT_CONFIG
from real_time_translator.stt.provider import GoogleSTTProvider
from real_time_translator.translation.provider import GoogleTranslationProvider
from real_time_translator.translation.translator import Translator


class AppController:
    _PT_SELF_HARM_RE = re.compile(
        r"\b(se\s*mate|mate-?se|suic[ií]dio|suicidar|se\s*matar|tire\s+a\s+vida)\b",
        re.IGNORECASE,
    )
    _EN_SELF_HARM_RE = re.compile(
        r"\b(kill\s+yourself|suicide|end\s+your\s+life|harm\s+yourself|self-?harm)\b",
        re.IGNORECASE,
    )

    def __init__(self, mic_index: int | None = None) -> None:
        self._mic_index = mic_index
        self._capture = AudioCapture(DEFAULT_CONFIG, device_index=self._mic_index)
        self._stt = GoogleSTTProvider(language=DEFAULT_CONFIG.source_speech_language)
        self._translator = Translator(
            GoogleTranslationProvider(
                source=DEFAULT_CONFIG.source_translation_language,
                target=DEFAULT_CONFIG.target_translation_language,
            )
        )
        self._running = False
        self._starting = False
        self._status = "Ready"
        self._sensitivity_mode = "auto"
        self._manual_threshold = DEFAULT_CONFIG.energy_threshold
        self._pause_threshold = 0.6
        self._original_lines: list[str] = []
        self._translated_lines: list[str] = []
        self._events: list[str] = []
        self._unknown_counter = 0
        self._last_level = 0
        self._captured_count = 0
        self._error_count = 0
        self._last_original = ""
        self._auto_meter_samples = 0
        self._pending_phrase = ""
        self._pending_chunks = 0
        self._spectrum_bins: list[int] = [18] * 28
        self._last_sensitivity_signature: tuple[str, int, float] = ("", -1, -1.0)
        self._lock = threading.Lock()
        self._capture.set_sensitivity(
            mode=self._sensitivity_mode,
            manual_threshold=self._manual_threshold,
            pause_threshold=self._pause_threshold,
        )

    @staticmethod
    def list_microphones() -> list[str]:
        return AudioCapture.list_microphones()

    @property
    def mic_index(self) -> int | None:
        return self._mic_index

    def set_microphone(self, mic_index: int | None) -> str:
        with self._lock:
            if self._running:
                return "Stop listening before changing microphone."
            names = self.list_microphones()
            if mic_index is not None and 0 <= mic_index < len(names):
                if self._is_blocked_remote_mic(names[mic_index]):
                    self._status = "Blocked remote microphone. Use the Mac built-in microphone."
                    self._events.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Blocked mic {mic_index} ({names[mic_index]})"
                    )
                    self._events = self._events[-120:]
                    return self._status
            self._mic_index = mic_index
            self._capture = AudioCapture(DEFAULT_CONFIG, device_index=self._mic_index)
            self._capture.set_sensitivity(
                mode=self._sensitivity_mode,
                manual_threshold=self._manual_threshold,
                pause_threshold=self._pause_threshold,
            )
            mic_label = "default"
            if self._mic_index is not None and 0 <= self._mic_index < len(names):
                mic_label = f"{self._mic_index} ({names[self._mic_index]})"
            self._status = f"Microphone set: {mic_label}"
            return self._status

    def auto_select_microphone(self) -> str:
        names = self.list_microphones()
        if not names:
            with self._lock:
                self._status = "No microphone detected."
                return self._status

        candidates = self._local_mic_candidates(names)
        for index in candidates:
            try:
                probe = AudioCapture(DEFAULT_CONFIG, device_index=index)
                probe.probe_microphone_permission()
                return self.set_microphone(index)
            except Exception:  # noqa: BLE001
                continue

        with self._lock:
            self._status = "Could not open a local microphone input."
            return self._status

    def auto_scan_microphone(self, seconds: float = 0.9) -> str:
        names = self.list_microphones()
        if not names:
            with self._lock:
                self._status = "No microphone detected."
                return self._status

        best_idx = None
        best_score = -10_000
        best_level = -1
        candidates = self._local_mic_candidates(names)
        if not candidates:
            with self._lock:
                self._status = "No local microphone available (remote devices blocked)."
                return self._status

        for index in candidates:
            try:
                probe = AudioCapture(DEFAULT_CONFIG, device_index=index)
                probe.probe_microphone_permission()
                level = probe.capture_level(seconds=seconds)
                score = self._mic_name_score(names[index]) + min(level, 2000)
                if score > best_score:
                    best_score = score
                    best_level = level
                    best_idx = index
            except Exception:  # noqa: BLE001
                continue

        if best_idx is None:
            with self._lock:
                self._status = "Auto scan failed: no readable local microphone."
                return self._status

        self.set_microphone(best_idx)
        with self._lock:
            self._last_level = max(0, best_level)
            self._status = f"Auto scan selected mic {best_idx} with level {best_level}"
            self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Auto scan selected mic={best_idx}, level={best_level}")
            self._events = self._events[-120:]
            return self._status

    @staticmethod
    def _mic_name_score(name: str) -> int:
        text = (name or "").strip().lower()
        score = 0
        if any(k in text for k in ["macbook", "built-in", "builtin", "internal"]):
            score += 1200
        if "microphone" in text:
            score += 150
        if any(k in text for k in ["iphone", "ios", "continuity", "phone"]):
            score -= 2000
        if any(k in text for k in ["airpods", "bluetooth", "headset"]):
            score -= 250
        return score

    @staticmethod
    def _is_blocked_remote_mic(name: str) -> bool:
        text = (name or "").strip().lower()
        blocked_tokens = [
            "iphone",
            "ios",
            "continuity",
            "airpods",
            "bluetooth",
            "headset",
            "hands-free",
            "earbuds",
        ]
        return any(token in text for token in blocked_tokens)

    @staticmethod
    def _is_preferred_local_mic(name: str) -> bool:
        text = (name or "").strip().lower()
        return any(token in text for token in ["macbook", "built-in", "builtin", "internal"])

    def _local_mic_candidates(self, names: list[str]) -> list[int]:
        preferred: list[int] = []
        others: list[int] = []
        blocked: list[int] = []

        for index, name in enumerate(names):
            if self._is_blocked_remote_mic(name):
                blocked.append(index)
                continue
            if self._is_preferred_local_mic(name):
                preferred.append(index)
            else:
                others.append(index)

        if blocked:
            with self._lock:
                for idx in blocked:
                    self._events.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Ignored remote mic {idx} ({names[idx]})."
                    )
                self._events = self._events[-120:]

        return preferred + others

    def prepare_default(self) -> str:
        self.request_microphone_access()
        self.auto_scan_microphone(seconds=0.8)
        self.apply_auto_distance_profile(target_meters=1.0)
        self.recalibrate(seconds=1.2)
        with self._lock:
            self._status = "Ready (auto-configured)"
            self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Auto setup completed.")
            self._events = self._events[-120:]
            return self._status

    def test_microphone_level(self, seconds: float = 1.0) -> str:
        try:
            level = self._capture.capture_level(seconds=seconds)
            with self._lock:
                self._last_level = level
                self._status = f"Mic level={level} (good speech usually > 250)"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Mic level sample: {level}")
                self._events = self._events[-120:]
                return self._status
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status = f"Mic test failed: {exc}"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Mic test failed: {exc}")
                self._events = self._events[-120:]
                return self._status

    def request_microphone_access(self) -> str:
        try:
            self._capture.probe_microphone_permission()
            with self._lock:
                self._status = "Microphone access ok"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Microphone access granted.")
                self._events = self._events[-120:]
                return self._status
        except sr.WaitTimeoutError:
            with self._lock:
                self._status = "Microphone access ok (silence)"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Microphone reachable (silence).")
                self._events = self._events[-120:]
                return self._status
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status = f"Microphone permission error: {exc}"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Microphone error: {exc}")
                self._events = self._events[-120:]
                return self._status

    def diagnose_once(self) -> str:
        try:
            self.request_microphone_access()
            level = self._capture.capture_level(seconds=1.2)
            audio = self._capture.listen_once(seconds=2.5)
            text = self._stt.transcribe(self._capture.recognizer, audio)
            with self._lock:
                self._last_level = level
                self._status = f"Diagnostic OK. Level={level}. Heard: {text[:80]}"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Diagnostic transcription: {text}")
                self._events = self._events[-120:]
                return self._status
        except sr.UnknownValueError:
            with self._lock:
                self._status = "Diagnostic: audio received but no speech recognized."
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Diagnostic failed: no speech recognized.")
                self._events = self._events[-120:]
                return self._status
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status = f"Diagnostic failed: {exc}"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Diagnostic exception: {exc}")
                self._events = self._events[-120:]
                return self._status

    def _audio_callback(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        if not self._running:
            return

        try:
            level = self._audio_level(audio)
            if level > 0:
                with self._lock:
                    self._last_level = level
                self._auto_adjust_for_distance(level)
            self._update_spectrum(audio)

            original = self._transcribe_far_field(recognizer, audio, level)
            stable_original = self._accumulate_phrase(original)
            if not stable_original:
                return
            translated = self._safe_translate(stable_original)
            stamp = datetime.now().strftime("%H:%M:%S")

            with self._lock:
                self._original_lines.append(f"[{stamp}] {stable_original}")
                self._translated_lines.append(f"[{stamp}] {translated}")
                self._original_lines = self._original_lines[-300:]
                self._translated_lines = self._translated_lines[-300:]
                self._unknown_counter = 0
                self._captured_count += 1
                self._last_original = stable_original
                self._events.append(f"[{stamp}] Captured and translated successfully.")
                self._events = self._events[-120:]
        except sr.UnknownValueError:
            with self._lock:
                self._unknown_counter += 1
                if self._sensitivity_mode == "auto":
                    current = int(self._capture.recognizer.energy_threshold)
                    lowered = max(85, current - 18)
                    if lowered != current:
                        self._capture.recognizer.energy_threshold = lowered
                if self._unknown_counter % 4 == 0:
                    self._status = "Audio detected but speech not recognized yet."
                    self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Speech not recognized (noise/low volume).")
                    self._events = self._events[-120:]
                if self._unknown_counter % 6 == 0:
                    stamp = datetime.now().strftime("%H:%M:%S")
                    self._original_lines.append(f"[{stamp}] xxxxx")
                    self._translated_lines.append(f"[{stamp}] -----")
                    self._original_lines = self._original_lines[-300:]
                    self._translated_lines = self._translated_lines[-300:]
                    self._pending_phrase = ""
                    self._pending_chunks = 0
            return
        except sr.RequestError as exc:
            with self._lock:
                self._status = f"STT error: {exc}"
                self._error_count += 1
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] STT request error: {exc}")
                self._events = self._events[-120:]
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status = f"Translation error: {exc}"
                self._error_count += 1
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Translation error: {exc}")
                self._events = self._events[-120:]

    def apply_preset(self, preset: str) -> str:
        normalized = (preset or "").strip().lower()
        if normalized == "tv_noise":
            return self.apply_sensitivity(mode="manual", manual_threshold=1200, pause_threshold=0.35)
        if normalized == "quiet_room":
            return self.apply_sensitivity(mode="auto", manual_threshold=500, pause_threshold=0.55)
        if normalized == "street_noise":
            return self.apply_sensitivity(mode="manual", manual_threshold=1500, pause_threshold=0.3)
        return self.apply_sensitivity(mode="auto", manual_threshold=900, pause_threshold=0.5)

    def start_smart(self) -> str:
        self.request_microphone_access()
        self.auto_scan_microphone(seconds=0.9)
        self.apply_auto_distance_profile(target_meters=1.0)
        self.recalibrate(seconds=1.4)
        return self.start()

    def apply_auto_distance_profile(self, target_meters: float = 1.0) -> str:
        meters = max(0.6, min(1.5, float(target_meters)))
        # For phone speaker at ~1m, start with a lower threshold and adapt upward if noise rises.
        base_threshold = int(70 + (meters - 1.0) * 90)
        pause = 0.55 if meters <= 1.0 else 0.62
        status = self.apply_sensitivity(mode="auto", manual_threshold=base_threshold, pause_threshold=pause)
        with self._lock:
            self._events.append(
                f"[{datetime.now().strftime('%H:%M:%S')}] Auto distance profile enabled (~{meters:.1f}m)."
            )
            self._events = self._events[-120:]
        return status

    def _audio_level(self, audio: sr.AudioData) -> int:
        try:
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            return int(audioop.rms(raw, 2))
        except Exception:  # noqa: BLE001
            return 0

    def _update_spectrum(self, audio: sr.AudioData) -> None:
        try:
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
            if samples.size < 256:
                return

            window = np.hanning(samples.size).astype(np.float32)
            weighted = samples * window
            fft = np.abs(np.fft.rfft(weighted))
            freqs = np.fft.rfftfreq(samples.size, d=1.0 / 16000.0)

            low_hz = 60.0
            high_hz = 4200.0
            bins = len(self._spectrum_bins)
            edges = np.geomspace(low_hz, high_hz, num=bins + 1)

            values: list[float] = []
            for i in range(bins):
                mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
                if not np.any(mask):
                    values.append(0.0)
                    continue
                band = fft[mask]
                values.append(float(np.log1p(float(np.mean(band)))))

            max_value = max(values) if values else 1.0
            if max_value <= 0.0:
                return

            normalized = [int(8 + (v / max_value) * 92) for v in values]
            with self._lock:
                self._spectrum_bins = normalized
        except Exception:  # noqa: BLE001
            return

    def _transcribe_far_field(self, recognizer: sr.Recognizer, audio: sr.AudioData, level: int) -> str:
        attempts = self._prepare_audio_attempts(audio, level)
        last_unknown: Exception | None = None
        for candidate in attempts:
            try:
                text = self._stt.transcribe(recognizer, candidate)
                if text:
                    return text
            except sr.UnknownValueError as exc:
                last_unknown = exc
                continue
        if last_unknown is not None:
            raise last_unknown
        return ""

    def _accumulate_phrase(self, original: str) -> str:
        text = (original or "").strip()
        if not text:
            return ""

        with self._lock:
            if self._pending_phrase:
                combined = f"{self._pending_phrase} {text}".strip()
            else:
                combined = text

            self._pending_phrase = combined
            self._pending_chunks += 1

            words = combined.split()
            ends_sentence = combined.endswith((".", "?", "!"))
            long_enough = len(words) >= 6
            too_many_chunks = self._pending_chunks >= 3

            if not (ends_sentence or long_enough or too_many_chunks):
                return ""

            finalized = self._pending_phrase
            self._pending_phrase = ""
            self._pending_chunks = 0
            return finalized

    def _safe_translate(self, original: str) -> str:
        translated = self._translator.translate(original)
        if self._looks_like_harm_hallucination(original, translated):
            stamp = datetime.now().strftime("%H:%M:%S")
            with self._lock:
                self._events.append(
                    f"[{stamp}] Safety filter blocked unsafe translation; marked as uncertain."
                )
                self._events = self._events[-120:]
            return "[Tradução incerta - repita a frase]"
        return translated

    def _looks_like_harm_hallucination(self, original: str, translated: str) -> bool:
        if not translated:
            return False
        pt_harm = bool(self._PT_SELF_HARM_RE.search(translated))
        if not pt_harm:
            return False
        en_harm = bool(self._EN_SELF_HARM_RE.search(original))
        return not en_harm

    def _prepare_audio_attempts(self, audio: sr.AudioData, level: int) -> list[sr.AudioData]:
        attempts: list[sr.AudioData] = []
        gains = self._gain_candidates(level)
        if gains:
            boosted = self._boost_audio(audio, gains[0], denoise=False)
            if boosted is not None:
                attempts.append(boosted)
        # Keep raw as final fallback.
        attempts.append(audio)
        return attempts

    @staticmethod
    def _gain_candidates(level: int) -> list[float]:
        if level < 80:
            return [5.2, 4.1, 3.0]
        if level < 130:
            return [4.1, 3.1, 2.3]
        if level < 220:
            return [3.0, 2.2, 1.7]
        if level < 340:
            return [2.0, 1.6]
        return [1.3]

    def _boost_audio(self, audio: sr.AudioData, gain: float, denoise: bool = False) -> sr.AudioData | None:
        try:
            raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
            if gain <= 1.0:
                return None
            boosted = audioop.mul(raw, 2, gain)
            if denoise:
                boosted = self._speech_denoise_and_normalize(boosted)
            return sr.AudioData(boosted, 16000, 2)
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _speech_denoise_and_normalize(raw: bytes) -> bytes:
        # Light noise gate + peak normalization focused on speech band dynamics.
        samples = array("h")
        samples.frombytes(raw)
        if not samples:
            return raw

        avg_abs = max(1, int(sum(abs(s) for s in samples) / len(samples)))
        gate = max(180, min(900, int(avg_abs * 0.75)))

        max_abs = 1
        for i, sample in enumerate(samples):
            if -gate < sample < gate:
                samples[i] = 0
                continue
            if abs(sample) > max_abs:
                max_abs = abs(sample)

        target_peak = 11000
        norm_gain = min(2.8, max(1.0, target_peak / max_abs))
        if norm_gain > 1.0:
            normalized = audioop.mul(samples.tobytes(), 2, norm_gain)
            return normalized
        return samples.tobytes()

    def _auto_adjust_for_distance(self, level: int) -> None:
        with self._lock:
            if self._sensitivity_mode != "auto":
                return
        recognizer = self._capture.recognizer
        current = int(recognizer.energy_threshold)
        updated = current
        if level < 100:
            updated = max(55, current - 34)
        elif level < 170:
            updated = max(55, current - 20)
        elif level > 1400:
            updated = min(1400, current + 30)
        elif level > 950:
            updated = min(1400, current + 14)
        if updated != current:
            recognizer.energy_threshold = updated
        with self._lock:
            self._auto_meter_samples += 1
            if self._auto_meter_samples % 12 == 0:
                self._events.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Auto sensitivity: level={level}, threshold={int(recognizer.energy_threshold)}"
                )
                self._events = self._events[-120:]

    def start(self) -> str:
        with self._lock:
            if self._running or self._starting:
                return self._status
            self._starting = True
            self._running = True
            self._status = "Calibrating microphone..."

        try:
            self._start_listening_sequence()
            with self._lock:
                self._status = "Listening..."
                self._starting = False
                return self._status
        except Exception as exc:  # noqa: BLE001
            # Recovery path: rebuild capture and retry once.
            try:
                self._capture.stop()
            except Exception:  # noqa: BLE001
                pass
            try:
                self._capture = AudioCapture(DEFAULT_CONFIG, device_index=self._mic_index)
                self._capture.set_sensitivity(
                    mode=self._sensitivity_mode,
                    manual_threshold=self._manual_threshold,
                    pause_threshold=self._pause_threshold,
                )
                self._start_listening_sequence()
                with self._lock:
                    self._status = "Listening... (recovered)"
                    self._starting = False
                    self._events.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Start recovered after {type(exc).__name__}: {exc!r}"
                    )
                    self._events = self._events[-120:]
                    return self._status
            except Exception as exc2:  # noqa: BLE001
                err = f"{type(exc2).__name__}: {exc2!r}"
                first = f"{type(exc).__name__}: {exc!r}"
                trace = traceback.format_exc(limit=2).strip().replace("\n", " | ")
                with self._lock:
                    self._running = False
                    self._starting = False
                    self._status = f"Start failed ({err})"
                    self._events.append(
                        f"[{datetime.now().strftime('%H:%M:%S')}] Start failed. first={first} second={err}"
                    )
                    self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Start traceback: {trace}")
                    self._events = self._events[-120:]
                    return self._status

            # Defensive fallback (should not reach here)
            with self._lock:
                self._running = False
                self._starting = False
                err = f"{type(exc).__name__}: {exc!r}"
                self._status = f"Start failed ({err})"
                self._events.append(f"[{datetime.now().strftime('%H:%M:%S')}] Start failed: {err}")
                self._events = self._events[-120:]
                return self._status

    def _start_listening_sequence(self) -> None:
        # Low-latency start: avoid blocking calibration on start; use explicit "Calibrar" button when needed.
        self._capture.start(self._audio_callback)

    def apply_sensitivity(self, mode: str, manual_threshold: int, pause_threshold: float) -> str:
        clamped_threshold = max(60, min(3200, int(manual_threshold)))
        clamped_pause = max(0.2, min(1.2, float(pause_threshold)))
        with self._lock:
            self._sensitivity_mode = "manual" if (mode or "").lower() == "manual" else "auto"
            self._manual_threshold = clamped_threshold
            self._pause_threshold = clamped_pause

        self._capture.set_sensitivity(
            mode=self._sensitivity_mode,
            manual_threshold=self._manual_threshold,
            pause_threshold=self._pause_threshold,
        )

        effective_threshold = int(self._capture.recognizer.energy_threshold)
        with self._lock:
            if self._sensitivity_mode == "manual":
                self._manual_threshold = effective_threshold
            effective = (
                f"manual={effective_threshold}"
                if self._sensitivity_mode == "manual"
                else "auto"
            )
            self._status = (
                f"Sensitivity applied ({effective}, pause={self._pause_threshold:.2f}, "
                f"threshold={effective_threshold})"
            )
            signature = (self._sensitivity_mode, effective_threshold, round(self._pause_threshold, 2))
            if signature != self._last_sensitivity_signature:
                self._last_sensitivity_signature = signature
                self._events.append(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Sensitivity set: mode={self._sensitivity_mode}, "
                    f"threshold={effective_threshold}, pause={self._pause_threshold:.2f}"
                )
                self._events = self._events[-120:]
            return self._status

    def recalibrate(self, seconds: float = 1.0) -> str:
        with self._lock:
            was_running = self._running
            if was_running:
                self._running = False
        if was_running:
            self._capture.stop()

        self._capture.recalibrate(seconds=seconds)
        self._capture.set_sensitivity(
            mode=self._sensitivity_mode,
            manual_threshold=self._manual_threshold,
            pause_threshold=self._pause_threshold,
        )

        if was_running:
            self._capture.start(self._audio_callback)
            with self._lock:
                self._running = True

        with self._lock:
            self._status = f"Environment recalibrated ({seconds:.1f}s)"
            return self._status

    def stop(self) -> str:
        with self._lock:
            if not self._running:
                return self._status
            self._running = False
            self._starting = False
            self._pending_phrase = ""
            self._pending_chunks = 0

        self._capture.stop()

        with self._lock:
            self._status = "Stopped"
            return self._status

    def clear(self) -> str:
        with self._lock:
            self._original_lines.clear()
            self._translated_lines.clear()
            self._events.clear()
            self._pending_phrase = ""
            self._pending_chunks = 0
            return self._status

    def snapshot(self) -> tuple[str, str, str, str]:
        with self._lock:
            return (
                self._status,
                "\n".join(self._original_lines),
                "\n".join(self._translated_lines),
                "\n".join(self._events[-25:]),
            )

    def settings_snapshot(self) -> tuple[str, int, float]:
        with self._lock:
            return self._sensitivity_mode, self._manual_threshold, self._pause_threshold

    def metrics_snapshot(self) -> str:
        with self._lock:
            mic = "default" if self._mic_index is None else str(self._mic_index)
            return (
                f"mic={mic} | level={self._last_level} | captured={self._captured_count} "
                f"| errors={self._error_count} | mode={self._sensitivity_mode}"
            )

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def spectrum_snapshot(self) -> list[int]:
        with self._lock:
            return list(self._spectrum_bins)
