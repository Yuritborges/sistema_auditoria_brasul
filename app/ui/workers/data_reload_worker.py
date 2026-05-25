"""Carrega pedidos consolidados fora da thread da UI."""

from PySide6.QtCore import QObject, Signal


class DataReloadWorker(QObject):
    finished = Signal(object, str)
    error = Signal(str)

    def __init__(self, service, force=False):
        super().__init__()
        self._service = service
        self._force = force

    def run(self):
        try:
            dados, origem = self._service.carregar(force=self._force)
            self.finished.emit(dados, origem)
        except Exception as e:
            self.error.emit(str(e))
