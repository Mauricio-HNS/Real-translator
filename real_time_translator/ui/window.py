from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class MainWindow:
    def __init__(self, on_start: Callable[[], None], on_stop: Callable[[], None]) -> None:
        self.root = tk.Tk()
        self.root.title("Real-Time Translator (EN -> PT)")
        self.root.geometry("980x620")

        self._on_start = on_start
        self._on_stop = on_stop

        container = ttk.Frame(self.root, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        header = ttk.Label(container, text="Real-Time Translator", font=("Helvetica", 20, "bold"))
        header.pack(anchor=tk.W)

        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(container, textvariable=self.status_var, foreground="#2f6")
        status.pack(anchor=tk.W, pady=(4, 12))

        controls = ttk.Frame(container)
        controls.pack(fill=tk.X, pady=(0, 12))

        self.start_btn = ttk.Button(controls, text="Start", command=self._start)
        self.start_btn.pack(side=tk.LEFT)

        self.stop_btn = ttk.Button(controls, text="Stop", command=self._stop, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.clear_btn = ttk.Button(controls, text="Clear", command=self.clear)
        self.clear_btn.pack(side=tk.LEFT, padx=(8, 0))

        panes = ttk.Panedwindow(container, orient=tk.VERTICAL)
        panes.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Labelframe(panes, text="English (recognized)", padding=8)
        bottom_frame = ttk.Labelframe(panes, text="Portuguese (translated)", padding=8)
        panes.add(top_frame, weight=1)
        panes.add(bottom_frame, weight=1)

        self.original_text = tk.Text(top_frame, wrap=tk.WORD, height=10)
        self.original_text.pack(fill=tk.BOTH, expand=True)

        self.translated_text = tk.Text(bottom_frame, wrap=tk.WORD, height=10)
        self.translated_text.pack(fill=tk.BOTH, expand=True)

    def _start(self) -> None:
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status_var.set("Listening...")
        self._on_start()

    def _stop(self) -> None:
        self.stop_btn.configure(state=tk.DISABLED)
        self.start_btn.configure(state=tk.NORMAL)
        self.status_var.set("Stopped")
        self._on_stop()

    def clear(self) -> None:
        self.original_text.delete("1.0", tk.END)
        self.translated_text.delete("1.0", tk.END)

    def append(self, original: str, translated: str) -> None:
        self.original_text.insert(tk.END, original + "\n")
        self.original_text.see(tk.END)

        self.translated_text.insert(tk.END, translated + "\n")
        self.translated_text.see(tk.END)

    def set_status(self, value: str) -> None:
        self.status_var.set(value)

    def run(self) -> None:
        self.root.mainloop()
