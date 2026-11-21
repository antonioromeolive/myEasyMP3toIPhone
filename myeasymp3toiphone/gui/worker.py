"""Esecuzione delle operazioni lunghe in un thread separato, con avanzamento e annullamento."""

import logging
import threading
from typing import Callable, Optional

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton, QStatusBar

from ..iphone import IPhoneError

log = logging.getLogger(__name__)


class _Signals(QObject):
    progress = Signal(int, int, str)
    finished = Signal(object)
    failed = Signal(str)


class _Task(QRunnable):
    """Esegue fn(progress, cancel) e ne restituisce il risultato tramite segnali."""

    def __init__(self, fn: Callable, cancel: threading.Event) -> None:
        super().__init__()
        self.fn = fn
        self.cancel = cancel
        self.signals = _Signals()

    def _progress(self, index: int, total: int, text: str) -> None:
        self.signals.progress.emit(index, total, text)

    @Slot()
    def run(self) -> None:
        try:
            value = self.fn(self._progress, self.cancel)
            self.signals.finished.emit(value)
        except IPhoneError as exc:
            self.signals.failed.emit(str(exc))
        except Exception as exc:  # noqa: BLE001 - qualsiasi errore va mostrato all'utente
            # nel log, non su una console: l'eseguibile a finestra non ne ha (sys.stderr è None)
            log.exception("Operazione non riuscita")
            self.signals.failed.emit(f"{type(exc).__name__}: {exc}")


class TaskRunner(QObject):
    """Gestisce un'operazione alla volta e ne mostra l'avanzamento nella barra di stato."""

    busy_changed = Signal(bool)
    error = Signal(str, str)  # titolo, messaggio

    def __init__(self, status_bar: QStatusBar) -> None:
        super().__init__()
        self._pool = QThreadPool.globalInstance()
        self._task: Optional[_Task] = None
        self._title = ""
        self._label = QLabel()
        self._bar = QProgressBar()
        self._bar.setMaximumWidth(260)
        self._cancel_button = QPushButton("Annulla")
        self._cancel_button.clicked.connect(self.cancel)
        status_bar.addPermanentWidget(self._label)
        status_bar.addPermanentWidget(self._bar)
        status_bar.addPermanentWidget(self._cancel_button)
        self._set_visible(False)

    def _set_visible(self, visible: bool) -> None:
        self._label.setVisible(visible)
        self._bar.setVisible(visible)
        self._cancel_button.setVisible(visible)

    @property
    def is_busy(self) -> bool:
        result = self._task is not None
        return result

    def run(self, title: str, fn: Callable, on_done: Callable,
            on_error: Optional[Callable] = None) -> bool:
        """Avvia fn(progress, cancel). Restituisce False se un'altra operazione è in corso."""
        if self._task is not None:
            self.error.emit("Operazione in corso", "Attendi la fine dell'operazione in corso.")
            started = False
        else:
            task = _Task(fn, threading.Event())
            task.setAutoDelete(False)
            task.signals.progress.connect(self._on_progress)
            task.signals.finished.connect(lambda value: self._finish(on_done, value))
            task.signals.failed.connect(lambda message: self._fail(on_error, message))
            self._task = task
            self._title = title
            self._label.setText(title + "…")
            self._bar.setRange(0, 0)
            self._cancel_button.setEnabled(True)
            self._set_visible(True)
            self.busy_changed.emit(True)
            self._pool.start(task)
            started = True
        return started

    def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel.set()
            self._cancel_button.setEnabled(False)
            self._label.setText(self._title + ": annullamento…")

    def _on_progress(self, index: int, total: int, text: str) -> None:
        if total > 0:
            self._bar.setRange(0, total)
            self._bar.setValue(index)
        self._label.setText(f"{self._title}: {text}")

    def _done(self) -> None:
        self._task = None
        self._set_visible(False)
        self.busy_changed.emit(False)

    def _finish(self, on_done: Callable, value) -> None:
        self._done()
        on_done(value)

    def _fail(self, on_error: Optional[Callable], message: str) -> None:
        title = self._title
        self._done()
        if on_error is not None:
            on_error(message)
        else:
            self.error.emit(title, message)
