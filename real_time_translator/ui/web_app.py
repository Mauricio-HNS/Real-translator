from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)
    auto_boot_done = {"value": False}

    def refresh() -> tuple[str, str, str, int]:
        status, original, translated, _logs = controller.snapshot()
        _mode, threshold, _pause = controller.settings_snapshot()
        return status, original, translated, threshold

    def bootstrap() -> tuple[str, str, str, int]:
        if not auto_boot_done["value"]:
            controller.prepare_default()
            auto_boot_done["value"] = True
        return refresh()

    def on_start() -> tuple[str, str, str, int]:
        controller.start()
        return refresh()

    def on_stop() -> tuple[str, str, str, int]:
        controller.stop()
        return refresh()

    def on_calibrate() -> tuple[str, str, str, int]:
        controller.recalibrate(seconds=1.2)
        return refresh()

    def on_sensitivity(threshold: int) -> tuple[str, str, str, int]:
        controller.apply_sensitivity(mode="manual", manual_threshold=threshold, pause_threshold=0.45)
        return refresh()

    with gr.Blocks(title="Real-Time Translator") as app:
        gr.Markdown("# Real-Time Translator")

        status = gr.Textbox(label="Status", interactive=False)
        with gr.Row():
            on_btn = gr.Button("ON", variant="primary")
            off_btn = gr.Button("OFF")
            calibrate_btn = gr.Button("Calibrar")

        sensitivity = gr.Slider(
            minimum=200,
            maximum=2200,
            step=50,
            value=900,
            label="Sensibilidade",
        )
        apply_sens_btn = gr.Button("Aplicar Sensibilidade")

        with gr.Row():
            original = gr.Textbox(label="Inglês", lines=14, interactive=False)
            translated = gr.Textbox(label="Português", lines=14, interactive=False)

        app.load(fn=bootstrap, outputs=[status, original, translated, sensitivity])

        auto_refresh_timer = gr.Timer(1.0)
        auto_refresh_timer.tick(fn=refresh, outputs=[status, original, translated, sensitivity])

        on_btn.click(fn=on_start, outputs=[status, original, translated, sensitivity])
        off_btn.click(fn=on_stop, outputs=[status, original, translated, sensitivity])
        calibrate_btn.click(fn=on_calibrate, outputs=[status, original, translated, sensitivity])
        apply_sens_btn.click(fn=on_sensitivity, inputs=[sensitivity], outputs=[status, original, translated, sensitivity])

    return app
