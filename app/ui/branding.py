"""Logo e identidade visual na interface."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel

from app.config import resolve_logo_path


def scaled_logo_pixmap(max_width: int, max_height: int) -> Optional[QPixmap]:
    path = resolve_logo_path()
    if not path:
        return None
    pix = QPixmap(path)
    if pix.isNull():
        return None
    return pix.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def logo_label_sidebar(parent, max_width: int = 232, max_height: int = 78) -> Optional[QLabel]:
    pix = scaled_logo_pixmap(max_width, max_height)
    if pix is None:
        return None
    lb = QLabel(parent)
    lb.setObjectName("sidebarLogo")
    lb.setPixmap(pix)
    lb.setAlignment(Qt.AlignCenter)
    lb.setScaledContents(False)
    return lb


def logo_label_compact(parent, max_width: int = 148, max_height: int = 42) -> Optional[QLabel]:
    pix = scaled_logo_pixmap(max_width, max_height)
    if pix is None:
        return None
    lb = QLabel(parent)
    lb.setObjectName("topbarLogo")
    lb.setPixmap(pix)
    lb.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    lb.setScaledContents(False)
    return lb
