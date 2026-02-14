import argparse

from real_time_translator.app_controller import AppController
from real_time_translator.ui.web_app import build_web_app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real-Time Translator Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="Host for web server")
    parser.add_argument("--port", type=int, default=7860, help="Port for web server")
    parser.add_argument("--mic-index", type=int, default=None, help="Microphone index")
    parser.add_argument("--list-mics", action="store_true", help="List microphones and exit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_mics:
        for idx, name in enumerate(AppController.list_microphones()):
            print(f"{idx}: {name}")
        return

    app = build_web_app(mic_index=args.mic_index)
    app.launch(server_name=args.host, server_port=args.port, share=False)


if __name__ == "__main__":
    main()
