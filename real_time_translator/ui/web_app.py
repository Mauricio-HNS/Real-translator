from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)
    auto_boot_done = {"value": False}
    ui_css = """
    :root {
      --bg: #1f2129;
      --bg-soft: #2a2d37;
      --card: #2b2e39;
      --card-2: #242733;
      --text: #e6ecf8;
      --muted: #a9b4ca;
      --green: #27c87a;
      --green-glow: rgba(39, 200, 122, 0.65);
      --shadow-dark: #1a1c24;
      --shadow-light: #3b3e4d;
      --cyan: #5bd5ff;
      --magenta: #d05bff;
      --orange: #ff9f66;
    }
    .gradio-container {
      background: radial-gradient(circle at 20% -8%, #383c4c, #242732 42%, #1d1f28 100%);
      color: var(--text);
      font-family: "SF Pro Display", "Avenir Next", "Segoe UI", sans-serif;
      max-width: 100vw !important;
      width: 100vw !important;
      padding: 0 !important;
      height: 100dvh;
      overflow: auto;
      box-sizing: border-box;
    }
    .gradio-container h1, .gradio-container h2, .gradio-container h3, .gradio-container label {
      color: var(--text) !important;
      letter-spacing: 0.5px;
    }
    .gradio-container .block {
      background: var(--card);
      border: none !important;
      border-radius: 16px !important;
      box-shadow: 6px 6px 14px var(--shadow-dark), -6px -6px 14px #343845 !important;
      border: 1px solid rgba(175, 190, 220, 0.08) !important;
    }
    .gradio-container textarea, .gradio-container input {
      background: var(--card-2) !important;
      border: none !important;
      border-radius: 12px !important;
      box-shadow: inset 5px 5px 10px #1f2129, inset -5px -5px 10px #373b48 !important;
      color: #eff4ff !important;
      font-size: 14px !important;
      line-height: 1.4 !important;
    }
    .gradio-container button {
      border: none !important;
      border-radius: 12px !important;
      font-weight: 700 !important;
      box-shadow: 7px 7px 14px var(--shadow-dark), -7px -7px 14px var(--shadow-light) !important;
      background: linear-gradient(160deg, #363948, #252833) !important;
      color: #d6deef !important;
      min-height: 42px !important;
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
      padding: 12px;
      border-radius: 0;
      background: linear-gradient(165deg, #2d303c, #242733);
      box-shadow: inset 1px 1px 0 #4a4e61, inset -1px -1px 0 #1d2029;
      border: none;
      width: 100%;
      max-width: 100%;
      margin: 0;
      height: 100dvh;
      display: flex;
      flex-direction: column;
      gap: 8px;
      overflow: auto;
      box-sizing: border-box;
    }
    #main-readouts {
      flex: 1 1 auto;
      min-height: 0;
      display: flex;
      gap: 10px;
    }
    #main-readouts > * {
      flex: 1 1 0;
      min-width: 0;
    }
    #eq-strip {
      margin: 2px 0 10px 0;
      padding: 10px 12px;
      background: linear-gradient(180deg, #2a2c37, #1f222c);
      border-radius: 16px;
      box-shadow: inset 3px 3px 8px #1a1c23, inset -3px -3px 8px #333644;
      border: 1px solid rgba(170, 190, 235, 0.08);
    }
    .eq-bars {
      display: grid;
      grid-template-columns: repeat(14, 1fr);
      gap: 5px;
      align-items: end;
      height: 58px;
    }
    .eq-bar {
      width: 100%;
      border-radius: 4px 4px 2px 2px;
      background: linear-gradient(180deg, var(--orange), #ff5e86, var(--magenta), #6fa8ff);
      opacity: 0.82;
      transition: height 0.22s ease-out, filter 0.22s ease-out;
    }
    @keyframes knob-spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    @keyframes ledspin {
      0% { box-shadow: 0 0 0 rgba(39,200,122,0.0); }
      50% { box-shadow: 0 0 18px rgba(39,200,122,0.7); }
      100% { box-shadow: 0 0 0 rgba(39,200,122,0.0); }
    }
    #bottom-deco {
      margin-top: 8px;
      display: flex;
      justify-content: center;
      gap: 26px;
      padding: 6px 0 2px;
    }
    .neo-knob {
      width: 86px;
      height: 86px;
      border-radius: 999px;
      background: radial-gradient(circle at 30% 25%, #3c4050, #252933 65%);
      box-shadow: 9px 9px 20px #171922, -7px -7px 15px #3a3e4e, inset 1px 1px 0 #4b4f62;
      position: relative;
      transition: transform 0.2s ease;
      animation: knob-spin 6.5s linear infinite;
    }
    .neo-knob::after {
      content: "";
      position: absolute;
      width: 6px;
      height: 22px;
      left: 40px;
      top: 10px;
      border-radius: 999px;
      background: linear-gradient(180deg, var(--cyan), #4a9dff);
      box-shadow: 0 0 12px rgba(91, 213, 255, 0.8);
    }
    .knob-two { animation-duration: 7.2s; }
    .knob-three { animation-duration: 5.4s; animation-direction: reverse; }
    .neo-label {
      margin-top: 9px;
      color: var(--muted);
      font-size: 13px;
      text-align: center;
      letter-spacing: 0.6px;
    }
    .slider-ruler {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      margin: 4px 8px 0 8px;
      color: #9fb0cb;
      font-size: 11px;
      letter-spacing: 0.4px;
    }
    .slider-ruler span::before {
      content: "";
      display: block;
      width: 1px;
      height: 8px;
      margin: 0 auto 3px auto;
      background: #7d89a0;
      opacity: 0.8;
    }
    #status-box textarea { min-height: 46px !important; max-height: 56px !important; }
    #logs-box textarea { min-height: 74px !important; max-height: 82px !important; }
    #orig-box textarea, #trans-box textarea {
      height: clamp(210px, 36dvh, 410px) !important;
      min-height: 180px !important;
    }
    #power-led { margin: 6px 0 4px; }
    #title-main h1 {
      text-shadow: 0 0 18px rgba(150, 170, 255, 0.25);
      font-weight: 700;
      font-size: 30px !important;
      margin-bottom: 4px !important;
      letter-spacing: 0.8px !important;
    }
    @media (max-height: 860px) {
      #bottom-deco { display: none; }
      .eq-bars { height: 68px; }
      #theme-shell { padding: 10px; }
      #orig-box textarea, #trans-box textarea {
        height: clamp(150px, 30dvh, 250px) !important;
      }
    }
    @media (max-width: 1000px) {
      .gradio-container { padding: 0 !important; }
      #theme-shell { border-radius: 0; }
      #title-main h1 { font-size: 22px !important; }
      #main-readouts {
        flex-direction: column;
      }
      #orig-box textarea, #trans-box textarea {
        height: clamp(120px, 20dvh, 200px) !important;
      }
    }
    """

    def _power_visual() -> tuple[str, dict, dict, dict]:
        running = controller.is_running()
        label = "LIGADO" if running else "DESLIGADO"
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
        raw_bins = controller.spectrum_snapshot()
        bins: list[int] = []
        for i in range(0, len(raw_bins), 2):
            segment = raw_bins[i : i + 2]
            bins.append(int(sum(segment) / max(1, len(segment))))
        bars: list[str] = []
        total = max(1, len(bins) - 1)
        for idx, value in enumerate(bins):
            t = idx / total
            hue = 130 + int(t * 150)  # green -> blue -> purple
            sat = 90
            light = 58
            bars.append(
                f"<span class='eq-bar' style='height:{max(6, min(66, value))}px;"
                f"background:linear-gradient(180deg, hsl({hue}, {sat}%, {light + 8}%), hsl({hue + 8}, {sat}%, {light - 12}%));'></span>"
            )
        return "<div id='eq-strip'><div class='eq-bars'>" + "".join(bars) + "</div></div>"

    def refresh() -> tuple[str, str, str, str, int, str, str, str, dict, dict, dict]:
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
            f"Régua atual: {threshold}",
            power_badge,
            spectrum_html,
            on_update,
            off_update,
            calibrate_update,
        )

    def refresh_live() -> tuple[str, str, str, str, str, str, dict, dict, dict]:
        status, original, translated, logs = controller.snapshot()
        power_badge, on_update, off_update, calibrate_update = _power_visual()
        spectrum_html = _spectrum_visual()
        return (
            status,
            original,
            translated,
            logs,
            power_badge,
            spectrum_html,
            on_update,
            off_update,
            calibrate_update,
        )

    def bootstrap() -> tuple[str, str, str, str, int, str, str, str, dict, dict, dict]:
        if not auto_boot_done["value"]:
            controller.prepare_default()
            auto_boot_done["value"] = True
        return refresh()

    def on_start() -> tuple[str, str, str, str, str, str, dict, dict, dict]:
        controller.start()
        return refresh_live()

    def on_stop() -> tuple[str, str, str, str, str, str, dict, dict, dict]:
        controller.stop()
        return refresh_live()

    def on_calibrate() -> tuple[str, str, str, str, str, str, dict, dict, dict]:
        controller.recalibrate(seconds=1.6)
        return refresh_live()

    def on_sensitivity(threshold: int) -> tuple[str, str, str, str, int, str, str, str, dict, dict, dict]:
        controller.apply_sensitivity(mode="manual", manual_threshold=threshold, pause_threshold=0.60)
        return refresh()

    with gr.Blocks(title="Real-Time Translator", css=ui_css) as app:
        with gr.Column(elem_id="theme-shell"):
            gr.Markdown("# Real-Time Translator", elem_id="title-main")
            gr.HTML("<div style='color:#9fb0cc;font-size:13px;margin:-6px 0 6px 2px;letter-spacing:0.5px;'>Live Call Translation Console</div>")
            spectrum_top = gr.HTML(value="<div id='eq-strip'><div class='eq-bars'></div></div>")

            power_status = gr.HTML(elem_id="power-led")
            status = gr.Textbox(label="Status", interactive=False, elem_id="status-box")
            with gr.Row():
                on_btn = gr.Button("LIGAR", variant="primary")
                off_btn = gr.Button("DESLIGAR")
                calibrate_btn = gr.Button("Calibrar")

            sensitivity = gr.Slider(
                minimum=60,
                maximum=3200,
                step=5,
                value=900,
                label="Sensibilidade (baixo = mais sensível)",
            )
            gr.HTML(
                "<div class='slider-ruler'>"
                "<span>60</span><span>400</span><span>800</span><span>1200</span>"
                "<span>1800</span><span>2400</span><span>3200</span>"
                "</div>"
            )
            sensitivity_value = gr.Textbox(label="Régua de Sensibilidade", interactive=False, value="Régua atual: 900")
            apply_sens_btn = gr.Button("Aplicar Sensibilidade")

            with gr.Row(elem_id="main-readouts"):
                original = gr.Textbox(label="Inglês", lines=8, interactive=False, elem_id="orig-box")
                translated = gr.Textbox(label="Português", lines=8, interactive=False, elem_id="trans-box")
            logs = gr.Textbox(label="Logs do Programa", lines=4, interactive=False, elem_id="logs-box")

            gr.HTML(
                "<div id='bottom-deco'>"
                "<div><div class='neo-knob'></div><div class='neo-label'>INPUT</div></div>"
                "<div><div class='neo-knob knob-two'></div><div class='neo-label'>FILTER</div></div>"
                "<div><div class='neo-knob knob-three'></div><div class='neo-label'>OUTPUT</div></div>"
                "</div>"
            )

        app.load(
            fn=bootstrap,
            outputs=[status, original, translated, logs, sensitivity, sensitivity_value, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )

        auto_refresh_timer = gr.Timer(1.35)
        auto_refresh_timer.tick(
            fn=refresh_live,
            outputs=[status, original, translated, logs, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )

        on_btn.click(
            fn=on_start,
            outputs=[status, original, translated, logs, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )
        off_btn.click(
            fn=on_stop,
            outputs=[status, original, translated, logs, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )
        calibrate_btn.click(
            fn=on_calibrate,
            outputs=[status, original, translated, logs, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )
        apply_sens_btn.click(
            fn=on_sensitivity,
            inputs=[sensitivity],
            outputs=[status, original, translated, logs, sensitivity, sensitivity_value, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )

    return app
