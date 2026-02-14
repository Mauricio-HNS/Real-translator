from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)
    auto_boot_done = {"value": False}
    ui_css = """
    :root {
      --bg: #f4f9f4;
      --card: #eef6ee;
      --text: #13321f;
      --green: #1d9b52;
      --green-soft: #8ef0b8;
      --shadow-dark: #c8d7c8;
      --shadow-light: #ffffff;
    }
    .gradio-container {
      background: linear-gradient(155deg, var(--bg), #f8fcf8);
      color: var(--text);
      font-family: "Avenir Next", "Trebuchet MS", sans-serif;
    }
    .gradio-container h1, .gradio-container h2, .gradio-container h3, .gradio-container label {
      color: var(--text) !important;
      letter-spacing: 0.2px;
    }
    .gradio-container .block {
      background: var(--card);
      border: none !important;
      border-radius: 18px !important;
      box-shadow: 9px 9px 18px var(--shadow-dark), -9px -9px 18px var(--shadow-light) !important;
    }
    .gradio-container textarea, .gradio-container input {
      background: #f3faf3 !important;
      border: none !important;
      border-radius: 14px !important;
      box-shadow: inset 5px 5px 10px #d2dfd2, inset -5px -5px 10px #ffffff !important;
      color: #10301d !important;
    }
    .gradio-container button {
      border: none !important;
      border-radius: 14px !important;
      font-weight: 700 !important;
      box-shadow: 7px 7px 14px var(--shadow-dark), -7px -7px 14px var(--shadow-light) !important;
    }
    .gradio-container button.primary {
      background: linear-gradient(160deg, #23b95f, #15803d) !important;
      color: #f6fff9 !important;
      box-shadow: 0 0 0 rgba(0,0,0,0), 0 0 16px rgba(22, 163, 74, 0.45) !important;
    }
    """

    def _power_visual() -> tuple[str, dict, dict]:
        running = controller.is_running()
        label = "ON" if running else "OFF"
        color = "#18a55a" if running else "#5e6a63"
        glow = "0 0 6px rgba(24,165,90,0.75), 0 0 18px rgba(24,165,90,0.55)" if running else "none"
        badge = (
            "<div style='display:flex;align-items:center;gap:12px;font-weight:700;font-size:18px;'>"
            f"<span style='width:15px;height:15px;border-radius:999px;background:{color};box-shadow:{glow};display:inline-block;'></span>"
            f"<span>Estado do Tradutor: <strong style='color:{color}'>{label}</strong></span>"
            "</div>"
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

    with gr.Blocks(title="Real-Time Translator", css=ui_css) as app:
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
