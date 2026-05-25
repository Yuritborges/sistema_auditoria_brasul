"""Ícone na barra de título e tarefas do Windows (WM_SETICON + tamanhos 16/32)."""

from __future__ import annotations

import sys


def aplicar_icone_janela_win32(widget, ico_path: str) -> bool:
    if not sys.platform.startswith("win") or not ico_path:
        return False
    try:
        import ctypes

        hwnd = int(widget.winId())
        if not hwnd:
            return False
        WM_SETICON = 0x80
        ICON_SMALL = 0
        ICON_BIG = 1
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x10
        user32 = ctypes.windll.user32

        hicon_sm = user32.LoadImageW(
            None, ico_path, IMAGE_ICON, 16, 16, LR_LOADFROMFILE
        )
        hicon_lg = user32.LoadImageW(
            None, ico_path, IMAGE_ICON, 32, 32, LR_LOADFROMFILE
        )
        if not hicon_sm and not hicon_lg:
            hicon_lg = user32.LoadImageW(
                None, ico_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | 0x40
            )
            hicon_sm = hicon_lg
        if hicon_sm:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_sm)
        if hicon_lg:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_lg)
        return bool(hicon_sm or hicon_lg)
    except Exception:
        return False
