"""Main entry point for the Video Compressor GUI application."""

from app.gui import CompressorApp


def main() -> None:
    """Start the GUI application."""
    app = CompressorApp()
    app.start()


if __name__ == "__main__":
    main()

