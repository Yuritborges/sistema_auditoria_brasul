"""Descoberta da pasta brasul_pedidos na rede (Z:, Y:, BRASUL_REDE_DIR, etc.)."""

from __future__ import annotations

import os

DEFAULT_BASE_REDE_SUFFIX = os.path.join("0 OBRAS", "brasul_pedidos")
# Mapeamento novo (2026-07): unidade pode apontar direto para "0 obras",
# ficando a pasta em {letra}:\brasul_pedidos.
DEFAULT_BASE_REDE_NOME = "brasul_pedidos"
# Fallback no layout NOVO — nunca recriar a estrutura antiga em 0 OBRAS.
DEFAULT_BASE_REDE_DIR = r"Z:\brasul_pedidos"
DEFAULT_BASE_REDE_UNC = r"\\192.168.15.250\arquivos brasul\0 obras\brasul_pedidos"
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


def _pasta_rede_com_dados_reais(caminho: str) -> bool:
    """True se a pasta contém dados de produção (não apenas estrutura recriada).

    Programas antigos recriavam a árvore vazia em {letra}:\\0 OBRAS\\brasul_pedidos
    quando não achavam a rede — essa cópia "fantasma" não pode ser escolhida.
    """
    if not _pasta_rede_brasul_valida(caminho):
        return False
    pontos = 0
    if os.path.isfile(os.path.join(caminho, "cotacao_rede.db")):
        pontos += 1
    obras_json = os.path.join(caminho, "cadastros_compartilhados", "obras.json")
    fornecedores_json = os.path.join(caminho, "cadastros_compartilhados", "fornecedores.json")
    for arq in (obras_json, fornecedores_json):
        try:
            if os.path.getsize(arq) > 1024:
                pontos += 1
        except OSError:
            pass
    usuarios = 0
    for pasta in ("Iury", "Thamyres", "SuaPasta", "CI"):
        if os.path.isdir(os.path.join(caminho, pasta)):
            usuarios += 1
    if usuarios >= 2:
        pontos += 1
    return pontos >= 2


def _candidatos_base_rede() -> list[str]:
    """Candidatos em ordem de prioridade: layout novo antes do antigo."""
    env = (
        (os.environ.get("BRASUL_REDE_DIR") or "").strip()
        or (os.environ.get("AUDITORIA_REDE_DIR") or "").strip()
    )
    candidatos: list[str] = []
    if env:
        candidatos.append(env)
    # Layout novo primeiro: unidade aponta direto para a pasta "0 obras"
    for letra in "ZYXWVUTSRQPONMLKJIHGFED":
        candidatos.append(os.path.join(f"{letra}:\\", DEFAULT_BASE_REDE_NOME))
    candidatos.append(DEFAULT_BASE_REDE_UNC)
    # Layout antigo por último (pode existir uma cópia vazia recriada por engano)
    for letra in "ZYXWVUTSRQPONMLKJIHGFED":
        candidatos.append(os.path.join(f"{letra}:\\", DEFAULT_BASE_REDE_SUFFIX))
    candidatos.append(DEFAULT_BASE_REDE_DIR)
    return candidatos


def resolver_base_rede_dir() -> str:
    """
    Descobre a pasta brasul_pedidos na rede.

    Ordem: BRASUL_REDE_DIR ou AUDITORIA_REDE_DIR → layout novo
    ({letra}:\\brasul_pedidos) → UNC → layout antigo
    ({letra}:\\0 OBRAS\\brasul_pedidos) → DEFAULT_BASE_REDE_DIR.
    Passa 1 exige dados reais (bancos/cadastros preenchidos); passa 2 aceita
    qualquer pasta com a estrutura. Mesma lógica do sistema de pedidos.
    """
    candidatos = _candidatos_base_rede()

    for validador in (_pasta_rede_com_dados_reais, _pasta_rede_brasul_valida):
        vistos: set[str] = set()
        for bruto in candidatos:
            caminho = os.path.normpath(bruto)
            chave = caminho.lower()
            if chave in vistos:
                continue
            vistos.add(chave)
            if validador(caminho):
                return caminho
    return DEFAULT_BASE_REDE_DIR
