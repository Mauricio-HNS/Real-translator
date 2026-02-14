from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from real_time_translator.app_controller import AppController


class DesktopTranslatorApp:
    def __init__(self) -> None:
        self.controller = AppController()

        self.root = tk.Tk()
        self.root.title("Real Translator")
        self.root.geometry("1100x720")

        container = ttk.Frame(self.root, padding=14)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Real Translator", font=("Helvetica", 20, "bold")).pack(anchor=tk.W)
        ttk.Label(container, text="Flow: Permitir microfone -> Auto detectar/Testar -> Iniciar", foreground="#555").pack(anchor=tk.W, pady=(0, 8))

        self.status = tk.StringVar(value="Ready")
        ttk.Label(container, textvariable=self.status, foreground="#0a7").pack(anchor=tk.W, pady=(0, 10))

        top = ttk.Frame(container)
        top.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(top, text="Microfone:").pack(side=tk.LEFT)
        self.mic_combo = ttk.Combobox(top, width=60, state="readonly")
        self.mic_combo.pack(side=tk.LEFT, padx=8)

        ttk.Button(top, text="Atualizar Lista", command=self._refresh_mics).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Usar Selecionado", command=self._apply_selected_mic).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Auto Detectar", command=self._auto_detect_mic).pack(side=tk.LEFT, padx=4)

        controls = ttk.Frame(container)
        controls.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(controls, text="Permitir Microfone", command=self._request_mic).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Testar Microfone", command=self._test_mic).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Recalibrar Ambiente", command=self._recalibrate).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Iniciar", command=self._start).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Parar", command=self._stop).pack(side=tk.LEFT, padx=4)
        ttk.Button(controls, text="Limpar", command=self._clear).pack(side=tk.LEFT, padx=4)

        sensitivity = ttk.Frame(container)
        sensitivity.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(sensitivity, text="Sensibilidade:").pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="auto")
        ttk.Radiobutton(sensitivity, text="Auto", variable=self.mode_var, value="auto").pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(sensitivity, text="Manual", variable=self.mode_var, value="manual").pack(side=tk.LEFT, padx=6)

        ttk.Label(sensitivity, text="Threshold manual:").pack(side=tk.LEFT, padx=(12, 4))
        self.threshold_var = tk.IntVar(value=900)
        self.threshold_scale = ttk.Scale(
            sensitivity,
            from_=100,
            to=2500,
            orient=tk.HORIZONTAL,
            command=self._on_threshold_scale,
            length=220,
        )
        self.threshold_scale.set(900)
        self.threshold_scale.pack(side=tk.LEFT)
        self.threshold_label = ttk.Label(sensitivity, text="900")
        self.threshold_label.pack(side=tk.LEFT, padx=(6, 10))

        ttk.Label(sensitivity, text="Pausa:").pack(side=tk.LEFT)
        self.pause_var = tk.DoubleVar(value=0.6)
        self.pause_scale = ttk.Scale(
            sensitivity,
            from_=0.2,
            to=1.2,
            orient=tk.HORIZONTAL,
            command=self._on_pause_scale,
            length=140,
        )
        self.pause_scale.set(0.6)
        self.pause_scale.pack(side=tk.LEFT)
        self.pause_label = ttk.Label(sensitivity, text="0.60")
        self.pause_label.pack(side=tk.LEFT, padx=(6, 10))

        ttk.Button(sensitivity, text="Aplicar Sensibilidade", command=self._apply_sensitivity).pack(side=tk.LEFT)

        panes = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        panes.pack(fill=tk.BOTH, expand=True)

        left = ttk.Labelframe(panes, text="Inglês", padding=8)
        right = ttk.Labelframe(panes, text="Português", padding=8)
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        self.original = tk.Text(left, wrap=tk.WORD)
        self.original.pack(fill=tk.BOTH, expand=True)
        self.translated = tk.Text(right, wrap=tk.WORD)
        self.translated.pack(fill=tk.BOTH, expand=True)

        self._refresh_mics()
        self.root.after(500, self._tick)

    def _on_threshold_scale(self, value: str) -> None:
        ivalue = int(float(value))
        self.threshold_var.set(ivalue)
        self.threshold_label.configure(text=str(ivalue))

    def _on_pause_scale(self, value: str) -> None:
        fvalue = float(value)
        self.pause_var.set(fvalue)
        self.pause_label.configure(text=f"{fvalue:.2f}")

    def _refresh_mics(self) -> None:
        names = self.controller.list_microphones()
        if not names:
            self.mic_combo["values"] = ["(sem microfone detectado)"]
            self.mic_combo.current(0)
            return
        labels = [f"{idx}: {name}" for idx, name in enumerate(names)]
        self.mic_combo["values"] = labels
        self.mic_combo.current(0)

    def _apply_selected_mic(self) -> None:
        selected = self.mic_combo.get()
        if ":" not in selected:
            return
        idx = int(selected.split(":", 1)[0])
        self.status.set(self.controller.set_microphone(idx))

    def _auto_detect_mic(self) -> None:
        self.status.set(self.controller.auto_select_microphone())

    def _request_mic(self) -> None:
        self.status.set(self.controller.request_microphone_access())

    def _test_mic(self) -> None:
        self.status.set(self.controller.test_microphone_level(seconds=1.0))

    def _recalibrate(self) -> None:
        self.status.set(self.controller.recalibrate(seconds=1.2))

    def _start(self) -> None:
        self.status.set(self.controller.start())

    def _stop(self) -> None:
        self.status.set(self.controller.stop())

    def _clear(self) -> None:
        self.status.set(self.controller.clear())

    def _apply_sensitivity(self) -> None:
        self.status.set(
            self.controller.apply_sensitivity(
                mode=self.mode_var.get(),
                manual_threshold=self.threshold_var.get(),
                pause_threshold=self.pause_var.get(),
            )
        )

    def _tick(self) -> None:
        status, original, translated, _logs = self.controller.snapshot()
        self.status.set(status)

        self.original.delete("1.0", tk.END)
        self.original.insert(tk.END, original)
        self.original.see(tk.END)

        self.translated.delete("1.0", tk.END)
        self.translated.insert(tk.END, translated)
        self.translated.see(tk.END)

        self.root.after(700, self._tick)

    def run(self) -> None:
        self.root.mainloop()
