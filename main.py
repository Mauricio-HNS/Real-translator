from real_time_translator.app_controller import AppController
from real_time_translator.ui.window import MainWindow


def main() -> None:
    controller = AppController()

    window = MainWindow(on_start=controller.start, on_stop=controller.stop)

    def tick() -> None:
        status, original, translated, _logs = controller.snapshot()
        window.set_status(status)
        if original:
            window.original_text.delete("1.0", "end")
            window.original_text.insert("end", original)
            window.original_text.see("end")
        if translated:
            window.translated_text.delete("1.0", "end")
            window.translated_text.insert("end", translated)
            window.translated_text.see("end")
        window.root.after(300, tick)

    window.root.after(300, tick)
    window.run()


if __name__ == "__main__":
    main()
