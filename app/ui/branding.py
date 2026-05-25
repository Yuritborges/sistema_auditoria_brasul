"""Logo horizontal BRASUL na interface (login, menu, topo)."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import QLabel

from app.config import resolve_logo_path


def _carregar_logo_ui() -> QPixmap:
    path = resolve_logo_path()
    if not path:
        return QPixmap()
    try:
        from PIL import Image

        img = Image.open(path).convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGBA8888)
        pix = QPixmap.fromImage(qimg.copy())
        # Remove fundo branco (mesma regra do sistema de pedidos).
        qimg2 = pix.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        for y in range(qimg2.height()):
            for x in range(qimg2.width()):
                c = qimg2.pixelColor(x, y)
                if c.alpha() and c.red() >= 248 and c.green() >= 248 and c.blue() >= 248:
                    qimg2.setPixelColor(x, y, QColor(0, 0, 0, 0))
        return QPixmap.fromImage(qimg2)
    except Exception:
        pix = QPixmap(path)
        return pix if not pix.isNull() else QPixmap()


def scaled_logo_pixmap(max_width: int, max_height: int) -> Optional[QPixmap]:
    pix = _carregar_logo_ui()
    if pix.isNull():
        return None
    return pix.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def _configurar_label_logo(lb: QLabel) -> None:
    lb.setStyleSheet("background: transparent; border: none;")
    lb.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)


def logo_label_sidebar(parent, max_width: int = 252, max_height: int = 78) -> Optional[QLabel]:
    pix = scaled_logo_pixmap(max_width, max_height)
    if pix is None:
        return None
    lb = QLabel(parent)
    lb.setObjectName("sidebarLogo")
    _configurar_label_logo(lb)
    lb.setPixmap(pix)
    lb.setAlignment(Qt.AlignCenter)
    lb.setScaledContents(False)
    return lb


def logo_label_compact(parent, max_width: int = 220, max_height: int = 56) -> Optional[QLabel]:
    pix = scaled_logo_pixmap(max_width, max_height)
    if pix is None:
        return None
    lb = QLabel(parent)
    lb.setObjectName("topbarLogo")
    _configurar_label_logo(lb)
    lb.setPixmap(pix)
    lb.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    lb.setScaledContents(False)
    return lb
