from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)

    auto_boot_done = {"value": False}

    def refresh() -> tuple[str, str, str, str, str, str, int, float]:
        status, original, translated, logs = controller.snapshot()
        metrics = controller.metrics_snapshot()
        mode, threshold, pause = controller.settings_snapshot()
        return status, metrics, original, translated, logs, mode, threshold, pause

    def bootstrap() -> tuple[str, str, str, str, str, str, int, float]:
        if not auto_boot_done["value"]:
            controller.prepare_default()
            auto_boot_done["value"] = True
        return refresh()

    def start() -> tuple[str, str, str, str, str, str, int, float]:
        controller.start()
        return refresh()

    def request_microphone() -> tuple[str, str, str, str, str, str, int, float]:
        controller.request_microphone_access()
        return refresh()

    def stop() -> tuple[str, str, str, str, str, str, int, float]:
        controller.stop()
        return refresh()

    def clear() -> tuple[str, str, str, str, str, str, int, float]:
        controller.clear()
        return refresh()

    def apply_sensitivity(mode: str, threshold: int, pause: float) -> tuple[str, str, str, str, str, str, int, float]:
        controller.apply_sensitivity(mode=mode, manual_threshold=threshold, pause_threshold=pause)
        return refresh()

    def recalibrate(seconds: float) -> tuple[str, str, str, str, str, str, int, float]:
        controller.recalibrate(seconds=seconds)
        return refresh()

    def diagnose() -> tuple[str, str, str, str, str, str, int, float]:
        controller.diagnose_once()
        return refresh()

    def auto_scan() -> tuple[str, str, str, str, str, str, int, float]:
        controller.auto_scan_microphone(seconds=0.9)
        return refresh()

    def start_smart() -> tuple[str, str, str, str, str, str, int, float]:
        controller.start_smart()
        return refresh()

    def apply_preset(preset: str) -> tuple[str, str, str, str, str, str, int, float]:
        controller.apply_preset(preset)
        return refresh()

    with gr.Blocks(title="Real-Time Translator") as app:
        gr.Markdown("# Real-Time Translator (EN -> PT)")
        gr.Markdown("Auto setup na abertura: escolhe microfone, aplica preset e calibra automaticamente.")

        status = gr.Textbox(label="Status", interactive=False)
        metrics = gr.Textbox(label="Health", interactive=False)
        with gr.Row():
            mic_btn = gr.Button("Permitir Microfone")
            smart_btn = gr.Button("Start Smart", variant="primary")
            autoscan_btn = gr.Button("Auto Scan Mic")
            start_btn = gr.Button("Iniciar", variant="primary")
            stop_btn = gr.Button("Parar")
            clear_btn = gr.Button("Limpar")
            refresh_btn = gr.Button("Atualizar")

        preset = gr.Radio(
            choices=["tv_noise", "quiet_room", "street_noise"],
            value="tv_noise",
            label="Preset de ambiente",
        )
        preset_btn = gr.Button("Aplicar Preset", variant="secondary")

        with gr.Row():
            sensitivity_mode = gr.Radio(
                choices=["auto", "manual"],
                value="auto",
                label="Sensibilidade",
                info="Auto adapta sozinho. Manual bloqueia melhor ruído com threshold alto.",
            )
            manual_threshold = gr.Slider(
                minimum=100,
                maximum=2500,
                step=50,
                value=300,
                label="Threshold manual",
            )
            pause_threshold = gr.Slider(
                minimum=0.2,
                maximum=1.2,
                step=0.05,
                value=0.6,
                label="Pausa entre frases",
            )

        with gr.Row():
            recalibrate_seconds = gr.Slider(
                minimum=0.5,
                maximum=3.0,
                step=0.1,
                value=1.0,
                label="Tempo de recalibragem (s)",
            )
            apply_btn = gr.Button("Aplicar Sensibilidade", variant="secondary")
            recalibrate_btn = gr.Button("Recalibrar Ambiente", variant="secondary")

        with gr.Row():
            original = gr.Textbox(label="Inglês (captado)", lines=14, interactive=False)
            translated = gr.Textbox(label="Português (traduzido)", lines=14, interactive=False)
        logs = gr.Textbox(label="Logs de diagnóstico", lines=8, interactive=False)
        diagnose_btn = gr.Button("Diagnóstico Rápido", variant="secondary")

        app.load(
            fn=bootstrap,
            outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold],
        )
        auto_refresh_timer = gr.Timer(1.0)
        auto_refresh_timer.tick(
            fn=refresh,
            outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold],
        )
        mic_btn.click(fn=request_microphone, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        smart_btn.click(fn=start_smart, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        autoscan_btn.click(fn=auto_scan, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        preset_btn.click(fn=apply_preset, inputs=[preset], outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        start_btn.click(fn=start, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        stop_btn.click(fn=stop, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        clear_btn.click(fn=clear, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        refresh_btn.click(fn=refresh, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])
        apply_btn.click(
            fn=apply_sensitivity,
            inputs=[sensitivity_mode, manual_threshold, pause_threshold],
            outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold],
        )
        recalibrate_btn.click(
            fn=recalibrate,
            inputs=[recalibrate_seconds],
            outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold],
        )
        diagnose_btn.click(fn=diagnose, outputs=[status, metrics, original, translated, logs, sensitivity_mode, manual_threshold, pause_threshold])

    return app
