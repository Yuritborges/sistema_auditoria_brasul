"""Consolidação Iury+Thamyres fora da thread da UI."""

from PySide6.QtCore import QObject, Signal


class ConsolidarRedeWorker(QObject):
    finished = Signal(bool, str)

    def __init__(self, service):
        super().__init__()
        self._service = service

    def run(self):
        try:
            ok, err = self._service.sincronizar_consolidado_pedidos()
            self.finished.emit(ok, err or "")
        except Exception as e:
            self.finished.emit(False, str(e))
