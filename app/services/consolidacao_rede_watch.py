"""Detecta cotacao_rede.db defasado e dispara consolidar_rede em segundo plano."""

from __future__ import annotations

import logging
import os
import threading

from app.config import BASE_REDE_PEDIDOS, resolve_consolidar_argv

DB_IURY = os.path.join(BASE_REDE_PEDIDOS, "Iury", "cotacao_iury.db")
DB_THAMYRES = os.path.join(BASE_REDE_PEDIDOS, "Thamyres", "cotacao_thamyres.db")
DB_REDE = os.path.join(BASE_REDE_PEDIDOS, "cotacao_rede.db")
LOCK_PATH = os.path.join(BASE_REDE_PEDIDOS, ".consolidar_rede.lock")


def _file_mtime(path: str) -> float:
    try:
        return os.path.getmtime(path) if os.path.isfile(path) else 0.0
    except OSError:
        return 0.0


def consolidado_precisa_atualizar() -> bool:
    if not os.path.isfile(DB_IURY) or not os.path.isfile(DB_THAMYRES):
        return False
    t_rede = _file_mtime(DB_REDE)
    t_compradores = max(_file_mtime(DB_IURY), _file_mtime(DB_THAMYRES))
    if t_compradores <= 0:
        return False
    if not os.path.isfile(DB_REDE):
        return True
    return t_compradores > t_rede + 1.0


class ConsolidacaoRedeWatch:
    def __init__(self, auditoria_service, on_success=None):
        self._service = auditoria_service
        self._on_success = on_success
        self._log = logging.getLogger(__name__)
        self._busy = False
        self._guard = threading.Lock()

    def tick(self) -> None:
        if not consolidado_precisa_atualizar():
            return
        if not resolve_consolidar_argv():
            return
        if os.path.isfile(LOCK_PATH):
            return
        with self._guard:
            if self._busy:
                return
            self._busy = True
        threading.Thread(target=self._run_consolidar, daemon=True).start()

    def _run_consolidar(self) -> None:
        try:
            ok, err = self._service.sincronizar_consolidado_pedidos()
            if ok:
                self._log.info("Consolidação automática concluída (cotacao_rede.db).")
                if self._on_success:
                    try:
                        self._on_success()
                    except Exception:
                        self._log.exception("Callback pós-consolidação")
            elif err:
                self._log.warning("Consolidação automática: %s", err[:500])
        except Exception:
            self._log.exception("Consolidação automática falhou")
        finally:
            with self._guard:
                self._busy = False
