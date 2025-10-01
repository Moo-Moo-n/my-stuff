"""Module entry point so the app can be launched with ``python -m blackjack_counter``."""

from .ui import BlackjackCounterApp


def main() -> None:
    app = BlackjackCounterApp()
    app.run()


if __name__ == "__main__":
    main()
