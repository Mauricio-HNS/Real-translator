from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)
    auto_boot_done = {"value": False}

    def _power_visual() -> tuple[str, dict, dict]:
        running = controller.is_running()
        label = "ON" if running else "OFF"
        color = "#15803d" if running else "#b91c1c"
        badge = (
            "<div style='font-weight:700;font-size:18px;'>Estado do Tradutor: "
            f"<span style='color:{color}'>{label}</span></div>"
        )
        on_update = gr.update(interactive=not running, variant="primary" if not running else "secondary")
        off_update = gr.update(interactive=running, variant="primary" if running else "secondary")
        return badge, on_update, off_update

    def refresh() -> tuple[str, str, str, str, int, str, dict, dict]:
        status, original, translated, logs = controller.snapshot()
        _mode, threshold, _pause = controller.settings_snapshot()
        power_badge, on_update, off_update = _power_visual()
        return status, original, translated, logs, threshold, power_badge, on_update, off_update

    def bootstrap() -> tuple[str, str, str, str, int, str, dict, dict]:
        if not auto_boot_done["value"]:
            controller.prepare_default()
            auto_boot_done["value"] = True
        return refresh()

    def on_start() -> tuple[str, str, str, str, int, str, dict, dict]:
        controller.start()
        return refresh()

    def on_stop() -> tuple[str, str, str, str, int, str, dict, dict]:
        controller.stop()
        return refresh()

    def on_calibrate() -> tuple[str, str, str, str, int, str, dict, dict]:
        controller.recalibrate(seconds=1.2)
        return refresh()

    def on_sensitivity(threshold: int) -> tuple[str, str, str, str, int, str, dict, dict]:
        controller.apply_sensitivity(mode="manual", manual_threshold=threshold, pause_threshold=0.45)
        return refresh()

    with gr.Blocks(title="Real-Time Translator") as app:
        gr.Markdown("# Real-Time Translator")
        power_status = gr.HTML()

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
        logs = gr.Textbox(label="Logs do Programa", lines=7, interactive=False)

        app.load(
            fn=bootstrap,
            outputs=[status, original, translated, logs, sensitivity, power_status, on_btn, off_btn],
        )

        auto_refresh_timer = gr.Timer(1.0)
        auto_refresh_timer.tick(
            fn=refresh,
            outputs=[status, original, translated, logs, sensitivity, power_status, on_btn, off_btn],
        )

        on_btn.click(
            fn=on_start,
            outputs=[status, original, translated, logs, sensitivity, power_status, on_btn, off_btn],
        )
        off_btn.click(
            fn=on_stop,
            outputs=[status, original, translated, logs, sensitivity, power_status, on_btn, off_btn],
        )
        calibrate_btn.click(
            fn=on_calibrate,
            outputs=[status, original, translated, logs, sensitivity, power_status, on_btn, off_btn],
        )
        apply_sens_btn.click(
            fn=on_sensitivity,
            inputs=[sensitivity],
            outputs=[status, original, translated, logs, sensitivity, power_status, on_btn, off_btn],
        )

    return app
