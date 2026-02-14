from __future__ import annotations

import gradio as gr

from real_time_translator.app_controller import AppController


def build_web_app(mic_index: int | None = None) -> gr.Blocks:
    controller = AppController(mic_index=mic_index)

    def refresh() -> tuple[str, str, str]:
        return controller.snapshot()

    def start() -> tuple[str, str, str]:
        controller.start()
        return controller.snapshot()

    def stop() -> tuple[str, str, str]:
        controller.stop()
        return controller.snapshot()

    def clear() -> tuple[str, str, str]:
        controller.clear()
        return controller.snapshot()

    with gr.Blocks(title="Real-Time Translator") as app:
        gr.Markdown("# Real-Time Translator (EN -> PT)")
        gr.Markdown("Use os botões para iniciar/parar a escuta e atualizar o texto.")

        status = gr.Textbox(label="Status", interactive=False)
        with gr.Row():
            start_btn = gr.Button("Iniciar", variant="primary")
            stop_btn = gr.Button("Parar")
            clear_btn = gr.Button("Limpar")
            refresh_btn = gr.Button("Atualizar")

        with gr.Row():
            original = gr.Textbox(label="Inglês (captado)", lines=14, interactive=False)
            translated = gr.Textbox(label="Português (traduzido)", lines=14, interactive=False)

        app.load(fn=refresh, outputs=[status, original, translated])
        start_btn.click(fn=start, outputs=[status, original, translated])
        stop_btn.click(fn=stop, outputs=[status, original, translated])
        clear_btn.click(fn=clear, outputs=[status, original, translated])
        refresh_btn.click(fn=refresh, outputs=[status, original, translated])

    return app
