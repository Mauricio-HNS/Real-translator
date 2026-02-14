from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)
    auto_boot_done = {"value": False}
    ui_css = """
    :root {
      --bg: #23242b;
      --bg-soft: #2b2d36;
      --card: #2d2f39;
      --card-2: #262832;
      --text: #dde3ef;
      --muted: #9da7bc;
      --green: #27c87a;
      --green-glow: rgba(39, 200, 122, 0.65);
      --shadow-dark: #1a1c24;
      --shadow-light: #3b3e4d;
      --cyan: #5bd5ff;
      --magenta: #d05bff;
      --orange: #ff9f66;
    }
    .gradio-container {
      background: radial-gradient(circle at 30% -10%, #3a3d4c, #24262f 45%, #1f2028 100%);
      color: var(--text);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      max-width: 1140px !important;
    }
    .gradio-container h1, .gradio-container h2, .gradio-container h3, .gradio-container label {
      color: var(--text) !important;
      letter-spacing: 0.5px;
    }
    .gradio-container .block {
      background: var(--card);
      border: none !important;
      border-radius: 18px !important;
      box-shadow: 8px 8px 18px var(--shadow-dark), -8px -8px 18px var(--shadow-light) !important;
    }
    .gradio-container textarea, .gradio-container input {
      background: var(--card-2) !important;
      border: none !important;
      border-radius: 14px !important;
      box-shadow: inset 5px 5px 10px #1f2129, inset -5px -5px 10px #373b48 !important;
      color: #eff4ff !important;
    }
    .gradio-container button {
      border: none !important;
      border-radius: 14px !important;
      font-weight: 700 !important;
      box-shadow: 7px 7px 14px var(--shadow-dark), -7px -7px 14px var(--shadow-light) !important;
      background: linear-gradient(160deg, #363948, #252833) !important;
      color: #d6deef !important;
    }
    .gradio-container button.primary {
      background: linear-gradient(160deg, #23b95f, #13874a) !important;
      color: #f6fff9 !important;
      box-shadow: 0 0 20px var(--green-glow), 7px 7px 14px #183225 !important;
    }
    .gradio-container button:hover {
      transform: translateY(-1px);
      transition: all 0.15s ease;
    }
    #theme-shell {
      padding: 20px;
      border-radius: 24px;
      background: linear-gradient(165deg, #2f313d, #252732);
      box-shadow: inset 1px 1px 0 #4a4e61, inset -1px -1px 0 #1d2029, 12px 12px 30px #191b23;
      border: 1px solid #383b4a;
    }
    #eq-strip {
      margin: 4px 0 14px 0;
      padding: 16px 18px;
      background: linear-gradient(180deg, #2a2c35, #20222b);
      border-radius: 16px;
      box-shadow: inset 4px 4px 10px #1a1c23, inset -4px -4px 10px #333644;
    }
    .eq-bars {
      display: grid;
      grid-template-columns: repeat(28, 1fr);
      gap: 3px;
      align-items: end;
      height: 112px;
    }
    .eq-bar {
      width: 100%;
      border-radius: 4px 4px 2px 2px;
      background: linear-gradient(180deg, var(--orange), #ff5e86, var(--magenta), #6fa8ff);
      animation: pulse 1.9s ease-in-out infinite;
      opacity: 0.92;
    }
    .eq-bar:nth-child(odd) { animation-duration: 1.4s; }
    .eq-bar:nth-child(3n) { animation-duration: 2.2s; }
    @keyframes pulse {
      0%, 100% { transform: scaleY(0.55); filter: brightness(0.8); }
      50% { transform: scaleY(1.0); filter: brightness(1.15); }
    }
    @keyframes ledspin {
      0% { box-shadow: 0 0 0 rgba(39,200,122,0.0); }
      50% { box-shadow: 0 0 18px rgba(39,200,122,0.7); }
      100% { box-shadow: 0 0 0 rgba(39,200,122,0.0); }
    }
    #bottom-deco {
      margin-top: 12px;
      display: flex;
      justify-content: center;
      gap: 38px;
      padding: 10px 0 4px;
    }
    .neo-knob {
      width: 112px;
      height: 112px;
      border-radius: 999px;
      background: radial-gradient(circle at 30% 25%, #3c4050, #252933 65%);
      box-shadow: 9px 9px 20px #171922, -7px -7px 15px #3a3e4e, inset 1px 1px 0 #4b4f62;
      position: relative;
      transition: transform 0.2s ease;
      animation: pulse 2.0s ease-in-out infinite;
    }
    .neo-knob::after {
      content: "";
      position: absolute;
      width: 8px;
      height: 28px;
      left: 52px;
      top: 14px;
      border-radius: 999px;
      background: linear-gradient(180deg, var(--cyan), #4a9dff);
      box-shadow: 0 0 12px rgba(91, 213, 255, 0.8);
    }
    .neo-label {
      margin-top: 9px;
      color: var(--muted);
      font-size: 13px;
      text-align: center;
      letter-spacing: 0.6px;
    }
    #status-box textarea { min-height: 62px !important; }
    #logs-box textarea { min-height: 130px !important; }
    #power-led { margin: 6px 0 4px; }
    #title-main h1 {
      text-shadow: 0 0 18px rgba(150, 170, 255, 0.25);
      font-weight: 700;
    }
    """

    def _power_visual() -> tuple[str, dict, dict, dict]:
        running = controller.is_running()
        label = "ON" if running else "OFF"
        color = "#18a55a" if running else "#5e6a63"
        glow = "0 0 6px rgba(24,165,90,0.75), 0 0 22px rgba(24,165,90,0.65)" if running else "none"
        badge = (
            "<div style='display:flex;align-items:center;gap:12px;font-weight:700;font-size:18px;'>"
            f"<span style='width:15px;height:15px;border-radius:999px;background:{color};box-shadow:{glow};display:inline-block;animation:ledspin 1.2s infinite;'></span>"
            f"<span>Estado do Tradutor: <strong style='color:{color}'>{label}</strong></span>"
            "</div>"
        )
        on_update = gr.update(interactive=not running, variant="primary" if not running else "secondary")
        off_update = gr.update(interactive=running, variant="primary" if running else "secondary")
        calibrate_update = gr.update(variant="secondary" if running else "primary")
        return badge, on_update, off_update, calibrate_update

    def _spectrum_visual() -> str:
        bins = controller.spectrum_snapshot()
        bars: list[str] = []
        total = max(1, len(bins) - 1)
        for idx, value in enumerate(bins):
            t = idx / total
            hue = 130 + int(t * 150)  # green -> blue -> purple
            sat = 90
            light = 58
            bars.append(
                f"<span class='eq-bar' style='height:{max(8, min(100, value))}px;"
                f"background:linear-gradient(180deg, hsl({hue}, {sat}%, {light + 8}%), hsl({hue + 8}, {sat}%, {light - 12}%));'></span>"
            )
        return "<div id='eq-strip'><div class='eq-bars'>" + "".join(bars) + "</div></div>"

    def refresh() -> tuple[str, str, str, str, int, str, str, dict, dict, dict]:
        status, original, translated, logs = controller.snapshot()
        _mode, threshold, _pause = controller.settings_snapshot()
        power_badge, on_update, off_update, calibrate_update = _power_visual()
        spectrum_html = _spectrum_visual()
        return (
            status,
            original,
            translated,
            logs,
            threshold,
            power_badge,
            spectrum_html,
            on_update,
            off_update,
            calibrate_update,
        )

    def bootstrap() -> tuple[str, str, str, str, int, str, str, dict, dict, dict]:
        if not auto_boot_done["value"]:
            controller.prepare_default()
            auto_boot_done["value"] = True
        return refresh()

    def on_start() -> tuple[str, str, str, str, int, str, str, dict, dict, dict]:
        controller.start_smart()
        return refresh()

    def on_stop() -> tuple[str, str, str, str, int, str, str, dict, dict, dict]:
        controller.stop()
        return refresh()

    def on_calibrate() -> tuple[str, str, str, str, int, str, str, dict, dict, dict]:
        controller.recalibrate(seconds=1.6)
        return refresh()

    def on_sensitivity(threshold: int) -> tuple[str, str, str, str, int, str, str, dict, dict, dict]:
        controller.apply_sensitivity(mode="manual", manual_threshold=threshold, pause_threshold=0.45)
        return refresh()

    with gr.Blocks(title="Real-Time Translator", css=ui_css) as app:
        with gr.Column(elem_id="theme-shell"):
            gr.Markdown("# Real-Time Translator", elem_id="title-main")
            spectrum_top = gr.HTML(value="<div id='eq-strip'><div class='eq-bars'></div></div>")

            power_status = gr.HTML(elem_id="power-led")
            status = gr.Textbox(label="Status", interactive=False, elem_id="status-box")
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
        logs = gr.Textbox(label="Logs do Programa", lines=7, interactive=False, elem_id="logs-box")

        gr.HTML(
            "<div id='bottom-deco'>"
            "<div><div class='neo-knob'></div><div class='neo-label'>INPUT</div></div>"
            "<div><div class='neo-knob'></div><div class='neo-label'>FILTER</div></div>"
            "<div><div class='neo-knob'></div><div class='neo-label'>OUTPUT</div></div>"
            "</div>"
        )

        app.load(
            fn=bootstrap,
            outputs=[status, original, translated, logs, sensitivity, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )

        auto_refresh_timer = gr.Timer(1.0)
        auto_refresh_timer.tick(
            fn=refresh,
            outputs=[status, original, translated, logs, sensitivity, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )

        on_btn.click(
            fn=on_start,
            outputs=[status, original, translated, logs, sensitivity, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )
        off_btn.click(
            fn=on_stop,
            outputs=[status, original, translated, logs, sensitivity, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )
        calibrate_btn.click(
            fn=on_calibrate,
            outputs=[status, original, translated, logs, sensitivity, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )
        apply_sens_btn.click(
            fn=on_sensitivity,
            inputs=[sensitivity],
            outputs=[status, original, translated, logs, sensitivity, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )

    return app
