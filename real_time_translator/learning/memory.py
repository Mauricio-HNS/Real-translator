from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MemoryEntry:
    source_text: str
    corrected_text: str
    preferred_translation: str


class LearningMemory:
    def __init__(self, db_path: str = "learning_memory.db") -> None:
        self._db_path = Path(db_path)
        self._lock = threading.Lock()
        self._entries: list[MemoryEntry] = []
        self._ensure_db()
        self._reload_cache()

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join((text or "").strip().lower().split())

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _ensure_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS corrections (
                    source_key TEXT PRIMARY KEY,
                    source_text TEXT NOT NULL,
                    corrected_text TEXT NOT NULL,
                    preferred_translation TEXT NOT NULL DEFAULT '',
                    hits INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def _reload_cache(self) -> None:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT source_text, corrected_text, preferred_translation FROM corrections ORDER BY LENGTH(source_text) DESC"
            ).fetchall()
        self._entries = [MemoryEntry(source_text=r[0], corrected_text=r[1], preferred_translation=r[2]) for r in rows]

    def remember(self, source_text: str, corrected_text: str, preferred_translation: str) -> None:
        source_clean = " ".join((source_text or "").strip().split())
        corrected_clean = " ".join((corrected_text or "").strip().split())
        translation_clean = " ".join((preferred_translation or "").strip().split())
        if not source_clean:
            return
        if not corrected_clean:
            corrected_clean = source_clean
        key = self._normalize(source_clean)
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO corrections (source_key, source_text, corrected_text, preferred_translation)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(source_key) DO UPDATE SET
                        source_text=excluded.source_text,
                        corrected_text=excluded.corrected_text,
                        preferred_translation=excluded.preferred_translation,
                        updated_at=CURRENT_TIMESTAMP
                    """,
                    (key, source_clean, corrected_clean, translation_clean),
                )
                conn.commit()
            self._reload_cache()

    def resolve(self, text: str) -> tuple[str, str]:
        original = " ".join((text or "").strip().split())
        if not original:
            return "", ""
        normalized = self._normalize(original)
        with self._lock:
            entries = list(self._entries)
        for entry in entries:
            source_key = self._normalize(entry.source_text)
            if normalized == source_key:
                return entry.corrected_text or original, entry.preferred_translation or ""
        lower_original = original.lower()
        for entry in entries:
            source = entry.source_text.strip()
            if len(source) < 8:
                continue
            if source.lower() in lower_original:
                replaced = original.replace(source, entry.corrected_text)
                return replaced, entry.preferred_translation or ""
        return original, ""

    def count(self) -> int:
        with self._lock:
            return len(self._entries)
