"""Ícone do aplicativo (blocos Brasul) — barra de título e tarefas."""

from __future__ import annotations

import os

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon

from app.config import ASSETS_DIR, LOGOS_DIR, resolve_app_icon_path


def criar_icone_aplicativo() -> QIcon:
    path = resolve_app_icon_path()
    png_candidates = [
        os.path.join(ASSETS_DIR, "iconebrasul2.png"),
        os.path.join(LOGOS_DIR, "iconebrasul2.png"),
    ]
    png_path = next((p for p in png_candidates if os.path.isfile(p)), "")

    icon = QIcon()
    if path and os.path.isfile(path):
        icon = QIcon(path)
    if png_path:
        for sz in (16, 20, 24, 32, 48, 64, 128):
            icon.addFile(png_path, QSize(sz, sz))
    return icon if not icon.isNull() else QIcon()
