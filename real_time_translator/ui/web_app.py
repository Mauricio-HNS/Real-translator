from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)

    def refresh() -> tuple[str, str, str, str, int, float]:
        status, original, translated = controller.snapshot()
        mode, threshold, pause = controller.settings_snapshot()
        return status, original, translated, mode, threshold, pause

    def start() -> tuple[str, str, str, str, int, float]:
        controller.start()
        return refresh()

    def request_microphone() -> tuple[str, str, str, str, int, float]:
        controller.request_microphone_access()
        return refresh()

    def stop() -> tuple[str, str, str, str, int, float]:
        controller.stop()
        return refresh()

    def clear() -> tuple[str, str, str, str, int, float]:
        controller.clear()
        return refresh()

    def apply_sensitivity(mode: str, threshold: int, pause: float) -> tuple[str, str, str, str, int, float]:
        controller.apply_sensitivity(mode=mode, manual_threshold=threshold, pause_threshold=pause)
        return refresh()

    def recalibrate(seconds: float) -> tuple[str, str, str, str, int, float]:
        controller.recalibrate(seconds=seconds)
        return refresh()

    with gr.Blocks(title="Real-Time Translator") as app:
        gr.Markdown("# Real-Time Translator (EN -> PT)")
        gr.Markdown("Use os botões para iniciar/parar e ajuste sensibilidade para reduzir ruído de fundo.")

        status = gr.Textbox(label="Status", interactive=False)
        with gr.Row():
            mic_btn = gr.Button("Permitir Microfone")
            start_btn = gr.Button("Iniciar", variant="primary")
            stop_btn = gr.Button("Parar")
            clear_btn = gr.Button("Limpar")
            refresh_btn = gr.Button("Atualizar")

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

        app.load(
            fn=refresh,
            outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold],
        )
        auto_refresh_timer = gr.Timer(1.0)
        auto_refresh_timer.tick(
            fn=refresh,
            outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold],
        )
        mic_btn.click(fn=request_microphone, outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold])
        start_btn.click(fn=start, outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold])
        stop_btn.click(fn=stop, outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold])
        clear_btn.click(fn=clear, outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold])
        refresh_btn.click(fn=refresh, outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold])
        apply_btn.click(
            fn=apply_sensitivity,
            inputs=[sensitivity_mode, manual_threshold, pause_threshold],
            outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold],
        )
        recalibrate_btn.click(
            fn=recalibrate,
            inputs=[recalibrate_seconds],
            outputs=[status, original, translated, sensitivity_mode, manual_threshold, pause_threshold],
        )

    return app
