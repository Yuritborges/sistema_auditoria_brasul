"""Descoberta da pasta brasul_pedidos na rede (Z:, Y:, BRASUL_REDE_DIR, etc.)."""

from __future__ import annotations

import os

DEFAULT_BASE_REDE_SUFFIX = os.path.join("0 OBRAS", "brasul_pedidos")
DEFAULT_BASE_REDE_DIR = r"Z:\0 OBRAS\brasul_pedidos"
DEFAULT_SERVIDOR_REDE_HOST = "192.168.15.250"
DEFAULT_CONFIGURAR_INTRANET_WINDOWS = True


def _pasta_rede_brasul_valida(caminho: str) -> bool:
    """True se a pasta parece ser a raiz brasul_pedidos na rede."""
    if not caminho or not os.path.isdir(caminho):
        return False
    marcadores = (
        os.path.join(caminho, "cotacao_rede.db"),
        os.path.join(caminho, "cadastros_compartilhados"),
        os.path.join(caminho, "Iury"),
        os.path.join(caminho, "Thamyres"),
    )
    return any(os.path.exists(m) for m in marcadores)


def resolver_base_rede_dir() -> str:
    """
    Descobre a pasta brasul_pedidos na rede.

    Ordem: BRASUL_REDE_DIR ou AUDITORIA_REDE_DIR → letras Z..A → DEFAULT_BASE_REDE_DIR.
    Mesma lógica do sistema de pedidos — funciona com Z: (Iury) ou Y: (Thamyres).
    """
    env = (
        (os.environ.get("BRASUL_REDE_DIR") or "").strip()
        or (os.environ.get("AUDITORIA_REDE_DIR") or "").strip()
    )
    candidatos: list[str] = []
    if env:
        candidatos.append(env)
    for letra in "ZYXWVUTSRQPONMLKJIHGFED":
        candidatos.append(os.path.join(f"{letra}:\\", DEFAULT_BASE_REDE_SUFFIX))
    candidatos.append(DEFAULT_BASE_REDE_DIR)

    vistos: set[str] = set()
    for bruto in candidatos:
        caminho = os.path.normpath(bruto)
        chave = caminho.lower()
        if chave in vistos:
            continue
        vistos.add(chave)
        if _pasta_rede_brasul_valida(caminho):
            return caminho
    return DEFAULT_BASE_REDE_DIR
