from __future__ import annotations

import math
import random

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)
    auto_boot_done = {"value": False}
    wave_phase = {"value": 0.0}
    ui_css = """
    :root {
      --bg: #0c0f0d;
      --bg-soft: #1a1f1b;
      --card: #121612;
      --card-2: #0e120f;
      --text: #edf3ec;
      --muted: #9fb29e;
      --green: #8cff00;
      --green-glow: rgba(140, 255, 0, 0.65);
      --shadow-dark: #040604;
      --shadow-light: #2a3029;
      --steel: #dfe4de;
      --graphite: #171b17;
    }
    .gradio-container {
      background:
        radial-gradient(circle at 8% 12%, rgba(139, 255, 0, 0.12), transparent 32%),
        radial-gradient(circle at 88% 78%, rgba(139, 255, 0, 0.08), transparent 30%),
        linear-gradient(160deg, #0b0f0c 0%, #111611 42%, #0c100d 100%);
      color: var(--text);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      max-width: 100vw !important;
      width: 100vw !important;
      padding: 0 !important;
      min-height: 100dvh;
      overflow-x: hidden;
      overflow-y: auto;
      box-sizing: border-box;
      scrollbar-width: thin;
      scrollbar-color: #4c5470 #242732;
    }
    .gradio-container ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    .gradio-container ::-webkit-scrollbar-track {
      background: #242732;
    }
    .gradio-container ::-webkit-scrollbar-thumb {
      background: #4c5470;
      border-radius: 999px;
    }
    .gradio-container h1, .gradio-container h2, .gradio-container h3, .gradio-container label {
      color: var(--text) !important;
      letter-spacing: 0.5px;
    }
    .gradio-container .block {
      background: linear-gradient(160deg, #141914, #0e120f);
      border: none !important;
      border-radius: 10px !important;
      box-shadow: 0 6px 18px rgba(0, 0, 0, 0.34) !important;
      border: 1px solid rgba(223, 228, 222, 0.08) !important;
      overflow: visible !important;
    }
    .gradio-container textarea, .gradio-container input {
      background: linear-gradient(180deg, #0d110e, #101510) !important;
      border: none !important;
      border-radius: 8px !important;
      box-shadow: inset 0 0 0 1px rgba(223, 228, 222, 0.12), inset 0 0 18px rgba(140, 255, 0, 0.06) !important;
      color: #f1f6ef !important;
      font-size: 14px !important;
      line-height: 1.4 !important;
    }
    .gradio-container button {
      border: none !important;
      border-radius: 8px !important;
      font-weight: 700 !important;
      box-shadow: 0 1px 0 rgba(223, 228, 222, 0.12), 0 8px 18px rgba(0, 0, 0, 0.3) !important;
      background: linear-gradient(160deg, #161b17, #0f130f) !important;
      color: #e5ece3 !important;
      min-height: 42px !important;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .gradio-container button.primary {
      background: linear-gradient(165deg, #98ff1a, #62c900) !important;
      color: #091007 !important;
      box-shadow: 0 0 16px rgba(140, 255, 0, 0.38), 0 8px 18px rgba(0, 0, 0, 0.26) !important;
    }
    .gradio-container button:hover {
      transform: translateY(-1px);
      transition: all 0.15s ease;
    }
    #theme-shell {
      padding: 12px;
      border-radius: 0;
      background: linear-gradient(180deg, #101510, #0b0e0b);
      box-shadow: inset 0 0 0 1px rgba(223, 228, 222, 0.08);
      border: none;
      width: 100%;
      max-width: 100%;
      margin: 0;
      min-height: 100dvh;
      display: flex;
      flex-direction: column;
      gap: 8px;
      overflow: visible;
      box-sizing: border-box;
      position: relative;
    }
    #main-readouts {
      flex: 0 0 auto;
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
      background: linear-gradient(180deg, #0d110e, #111611);
      border-radius: 8px;
      box-shadow: inset 0 0 0 1px rgba(223, 228, 222, 0.08);
      border: 1px solid rgba(223, 228, 222, 0.08);
    }
    .eq-bars {
      width: 100%;
      height: 62px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .eq-canvas {
      position: relative;
      width: 100%;
      height: 62px;
      border-radius: 6px;
      background: linear-gradient(180deg, rgba(140,255,0,0.04), rgba(140,255,0,0.01));
      overflow: hidden;
    }
    .eq-base {
      position: absolute;
      left: 0;
      right: 0;
      top: 31px;
      height: 1px;
      background: rgba(140,255,0,0.16);
    }
    .eq-seg {
      position: absolute;
      height: 2px;
      border-radius: 2px;
      background: #8cff00;
      box-shadow: 0 0 6px rgba(140,255,0,0.52);
      transform-origin: 0 50%;
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
      background: radial-gradient(circle at 28% 24%, #2b312b, #0e130f 65%);
      box-shadow: 0 0 0 1px rgba(223, 228, 222, 0.2), 0 8px 22px rgba(0, 0, 0, 0.55), 0 0 18px rgba(140, 255, 0, 0.12);
      position: relative;
      transition: transform 0.2s ease;
      animation: knob-spin 14s linear infinite;
    }
    .neo-knob::after {
      content: "";
      position: absolute;
      width: 6px;
      height: 22px;
      left: 40px;
      top: 10px;
      border-radius: 999px;
      background: linear-gradient(180deg, #e8efe8, #b8c4b6);
      box-shadow: 0 0 10px rgba(232, 239, 232, 0.35);
    }
    .knob-two { animation-duration: 16s; }
    .knob-three { animation-duration: 12s; animation-direction: reverse; }
    .neo-label {
      margin-top: 9px;
      color: #c6d2c4;
      font-size: 13px;
      text-align: center;
      letter-spacing: 0.6px;
    }
    #status-box textarea {
      min-height: 46px !important;
      max-height: 56px !important;
      overflow: hidden !important;
    }
    #logs-box textarea {
      min-height: 104px !important;
      max-height: 130px !important;
      overflow-y: auto !important;
    }
    #orig-box textarea, #trans-box textarea { min-height: 220px !important; max-height: 40dvh !important; overflow-y: auto !important; }
    #power-led { margin: 6px 0 4px; }
    #title-main h1 {
      text-shadow: 0 0 10px rgba(140, 255, 0, 0.2);
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
        min-height: 160px !important;
        max-height: 30dvh !important;
      }
      #logs-box textarea { min-height: 82px !important; max-height: 94px !important; }
    }
    @media (max-width: 1000px) {
      .gradio-container { padding: 0 !important; }
      #theme-shell { border-radius: 0; }
      #title-main h1 { font-size: 22px !important; }
      #main-readouts {
        flex-direction: column;
      }
      #orig-box textarea, #trans-box textarea {
        min-height: 180px !important;
        max-height: 32dvh !important;
      }
    }
    """

    def _power_visual() -> tuple[str, dict, dict, dict]:
        running = controller.is_running()
        label = "LIGADO" if running else "DESLIGADO"
        color = "#8cff00" if running else "#5e6a63"
        glow = "0 0 10px rgba(140,255,0,0.9), 0 0 28px rgba(140,255,0,0.7)" if running else "none"
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

        avg_level = sum(bins) / max(1, len(bins))
        amp = max(3.0, min(22.0, 4.0 + (avg_level * 0.15)))
        width = 560.0
        height = 62.0
        base = height / 2.0
        n = 54
        dx = width / (n - 1)
        phase = wave_phase["value"]
        wave_phase["value"] = (phase + 0.35) % (2.0 * math.pi)

        points: list[tuple[float, float]] = []
        for i in range(n):
            x = i * dx
            b = bins[i % max(1, len(bins))]
            bin_factor = min(1.35, max(0.15, b / 80.0))
            wobble = (random.uniform(-0.35, 0.35) * amp * 0.35)
            y = base + (amp * 0.55 * bin_factor) * math.sin((i * 0.55) + phase) + wobble
            y = max(4.0, min(height - 4.0, y))
            points.append((x, y))

        segments: list[str] = ["<div class='eq-base'></div>"]
        for i in range(n - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            ddx = x2 - x1
            ddy = y2 - y1
            dist = (ddx * ddx + ddy * ddy) ** 0.5
            angle = math.degrees(math.atan2(ddy, ddx))
            segments.append(
                f"<span class='eq-seg' style='left:{x1:.2f}px;top:{y1:.2f}px;width:{dist:.2f}px;transform:rotate({angle:.2f}deg)'></span>"
            )
        return "<div id='eq-strip'><div class='eq-bars'><div class='eq-canvas'>" + "".join(segments) + "</div></div></div>"

    def refresh() -> tuple[str, str, str, str, str, str, dict, dict, dict]:
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

    def bootstrap() -> tuple[str, str, str, str, str, str, dict, dict, dict]:
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

    def on_learn(correct_en: str, correct_pt: str) -> tuple[str, str, str, str, str, str, dict, dict, dict, dict, dict]:
        controller.learn_from_feedback(correct_en, correct_pt)
        status, original, translated, logs, power, spectrum, on_u, off_u, cal_u = refresh_live()
        return (
            status,
            original,
            translated,
            logs,
            power,
            spectrum,
            on_u,
            off_u,
            cal_u,
            gr.update(value=""),
            gr.update(value=""),
        )

    with gr.Blocks(title="Real-Time Translator", css=ui_css) as app:
        with gr.Column(elem_id="theme-shell"):
            gr.Markdown("# Tradutor em Tempo Real", elem_id="title-main")
            gr.HTML("<div style='color:#9fb0cc;font-size:13px;margin:-6px 0 6px 2px;letter-spacing:0.5px;'>Console de Tradução de Chamadas ao Vivo</div>")
            spectrum_top = gr.HTML(value="<div id='eq-strip'><div class='eq-bars'></div></div>")

            power_status = gr.HTML(elem_id="power-led")
            status = gr.Textbox(label="Status", interactive=False, elem_id="status-box")
            with gr.Row():
                on_btn = gr.Button("LIGAR", variant="primary")
                off_btn = gr.Button("DESLIGAR")
                calibrate_btn = gr.Button("CALIBRAR")

            with gr.Row():
                learn_en = gr.Textbox(
                    label="Aprender Inglês (opcional)",
                    placeholder="Deixe vazio para usar a última frase capturada",
                )
                learn_pt = gr.Textbox(
                    label="Tradução PT preferida (opcional)",
                    placeholder="Deixe vazio para auto-gerar",
                )
            learn_btn = gr.Button("Aprender correção")

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
            outputs=[status, original, translated, logs, power_status, spectrum_top, on_btn, off_btn, calibrate_btn],
        )

        auto_refresh_timer = gr.Timer(0.2)
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
        learn_btn.click(
            fn=on_learn,
            inputs=[learn_en, learn_pt],
            outputs=[status, original, translated, logs, power_status, spectrum_top, on_btn, off_btn, calibrate_btn, learn_en, learn_pt],
        )

    return app
