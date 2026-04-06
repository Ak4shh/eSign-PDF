import sys
import os

import fitz
fitz.TOOLS.mupdf_display_errors(False)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFontDatabase

from app.main_window import MainWindow
from app.settings import SIGNATURE_FONTS

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")


def register_fonts() -> None:
    for font_meta in SIGNATURE_FONTS:
        path = os.path.join(FONTS_DIR, font_meta["file"])
        if os.path.isfile(path):
            QFontDatabase.addApplicationFont(path)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("PDF eSign")
    app.setOrganizationName("PDF eSign")

    register_fonts()

    window = MainWindow(fonts_dir=FONTS_DIR)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
