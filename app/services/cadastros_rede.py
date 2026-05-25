"""Cadastros JSON compartilhados na rede (mesma pasta do sistema de pedidos)."""

from __future__ import annotations

import json
import os

from app.config import OBRAS_JSON_PATH


def nomes_obras_cadastro() -> list[str]:
    if not os.path.isfile(OBRAS_JSON_PATH):
        return []
    try:
        with open(OBRAS_JSON_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError, TypeError):
        return []
    if isinstance(data, dict):
        return sorted({str(k).strip() for k in data if str(k).strip()}, key=lambda s: s.upper())
    if isinstance(data, list):
        return sorted({str(x).strip() for x in data if str(x).strip()}, key=lambda s: s.upper())
    return []
