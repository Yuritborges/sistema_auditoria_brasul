# Marca o servidor Brasul como Intranet local no Windows (HKCU, sem admin).

from __future__ import annotations

import os
import sys
from typing import Optional

if sys.platform == "win32":
    import winreg

_ZONEBASE = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMapKey"
_INTRANET = 1


def _host_de_unc(caminho: str) -> Optional[str]:
    if not caminho.startswith("\\\\"):
        return None
    partes = caminho.strip("\\").split("\\")
    return partes[0] if partes else None


def _host_de_unidade_mapeada(caminho: str) -> Optional[str]:
    if len(caminho) < 2 or caminho[1] != ":":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        buf = ctypes.create_unicode_buffer(1024)
        tamanho = wintypes.DWORD(len(buf))
        if ctypes.windll.mpr.WNetGetConnectionW(caminho[:2], buf, ctypes.byref(tamanho)) != 0:
            return None
        return _host_de_unc(buf.value)
    except Exception:
        return None


def _host_de_caminho(caminho: Optional[str]) -> Optional[str]:
    if not caminho:
        return None
    return _host_de_unc(caminho) or _host_de_unidade_mapeada(caminho)


def resolver_host_servidor(*caminhos_rede: Optional[str]) -> str:
    from app.rede_paths import DEFAULT_SERVIDOR_REDE_HOST

    for candidato in caminhos_rede:
        host = _host_de_caminho(candidato)
        if host:
            return host
    for env in ("BRASUL_REDE_DIR", "AUDITORIA_REDE_DIR"):
        host = _host_de_caminho((os.environ.get(env) or "").strip())
        if host:
            return host
    return DEFAULT_SERVIDOR_REDE_HOST


def _definir_zona(root: int, subcaminho: str, nome_valor: str, valor) -> None:
    chave = winreg.CreateKey(root, subcaminho)
    try:
        if isinstance(valor, int):
            winreg.SetValueEx(chave, nome_valor, 0, winreg.REG_DWORD, valor)
        else:
            winreg.SetValueEx(chave, nome_valor, 0, winreg.REG_STRING, str(valor))
    finally:
        winreg.CloseKey(chave)


def _intranet_ja_configurada(host: str) -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, f"{_ZONEBASE}\\UNC\\{host}"
        ) as chave:
            valor, _ = winreg.QueryValueEx(chave, "file")
            return int(valor) == _INTRANET
    except OSError:
        return False


def configurar_zona_intranet(host: str) -> bool:
    if sys.platform != "win32" or not host:
        return False
    if _intranet_ja_configurada(host):
        return True

    base = _ZONEBASE
    _definir_zona(winreg.HKEY_CURRENT_USER, f"{base}\\UNC\\{host}", "file", _INTRANET)
    _definir_zona(winreg.HKEY_CURRENT_USER, f"{base}\\Domains\\{host}", "file", _INTRANET)

    if host.replace(".", "").isdigit():
        prefixo = ".".join(host.split(".")[:3])
        nome_range = "BrasulLAN"
        _definir_zona(
            winreg.HKEY_CURRENT_USER,
            f"{base}\\Range\\{nome_range}",
            ":Range",
            f"{prefixo}.*",
        )
        _definir_zona(
            winreg.HKEY_CURRENT_USER,
            f"{base}\\Range\\{nome_range}",
            "file",
            _INTRANET,
        )

    return True


def aplicar_se_necessario(*caminhos_rede: Optional[str]) -> None:
    if sys.platform != "win32":
        return
    try:
        from app.rede_paths import DEFAULT_CONFIGURAR_INTRANET_WINDOWS

        if not DEFAULT_CONFIGURAR_INTRANET_WINDOWS:
            return
        host = resolver_host_servidor(*caminhos_rede)
        configurar_zona_intranet(host)
    except Exception:
        pass
