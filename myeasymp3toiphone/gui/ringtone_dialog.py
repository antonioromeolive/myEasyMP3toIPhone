# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Crea una suoneria da un brano: la forma d'onda (ffmpeg), il pezzo da usare (al massimo ~40 s, trascinando sulla
forma d'onda o con i campi), dissolvenze facoltative, l'ascolto del pezzo (ffmpeg prepara un WAV temporaneo, lo suona
winsound: niente QtMultimedia, che porterebbe nella build altre DLL di FFmpeg). Il risultato è un .m4r nuovo nella
cartella delle suonerie: il brano non cambia."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from .. import ringtones
from ..i18n import tr
from .worker import BackgroundJob

log = logging.getLogger(__name__)

WAVE_COLOR = QColor(70, 130, 220)
SELECTION_COLOR = QColor(40, 110, 230, 60)
HANDLE_COLOR = QColor(40, 110, 230)
CURSOR_COLOR = QColor(220, 60, 60)
HANDLE_GRAB = 6          # pixel: quanto vicino a un bordo del pezzo si prende il bordo
TICK_MS = 40


def _format_seconds(value: float) -> str:
    whole = int(value)
    result = f"{whole // 60}:{whole % 60:02d}.{int(round((value - whole) * 10)) % 10}"
    return result


class Player:
    """L'ascolto: un WAV temporaneo (ringtones.make_preview, in sottofondo) suonato da winsound. on_started(secondi)
    quando parte, on_stopped() quando finisce o si ferma, on_error(messaggio)."""

    def __init__(self, on_started, on_stopped, on_error) -> None:
        self._on_started = on_started
        self._on_stopped = on_stopped
        self._on_error = on_error
        self._file = None
        self._job = None
        self._generation = 0         # cresce a ogni ascolto o Ferma: un WAV pronto troppo tardi non suona
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.stop)

    @staticmethod
    def available() -> bool:
        try:
            import winsound  # noqa: F401 - solo per sapere se c'è (Windows)
            result = True
        except ImportError:
            result = False
        return result

    def play(self, ffmpeg: Path, source: Path, start: float, end: float, fade_in: float, fade_out: float) -> None:
        self.stop()
        self._generation += 1
        generation = self._generation

        def work(_progress, _cancel, emit):
            emit(ringtones.make_preview(ffmpeg, source, start, end, fade_in, fade_out))

        job = BackgroundJob(work)
        job.item.connect(lambda path: self._ready(Path(path), end - start, generation))
        job.failed.connect(self._on_error)
        self._job = job
        job.start()

    def _ready(self, path: Path, seconds: float, generation: int) -> None:
        import winsound
        if generation != self._generation:
            path.unlink(missing_ok=True)         # fermato (o chiuso) mentre ffmpeg lo preparava
        else:
            self._cleanup()
            self._file = path
            try:
                winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                self._timer.start(int(seconds * 1000) + 200)
                self._on_started(seconds)
            except RuntimeError as exc:
                self._on_error(str(exc))

    def stop(self) -> None:
        self._generation += 1
        self._timer.stop()
        if self._file is not None:
            try:
                import winsound
                winsound.PlaySound(None, 0)
            except (ImportError, RuntimeError):
                pass
            self._cleanup()
            self._on_stopped()

    def _cleanup(self) -> None:
        if self._file is not None:
            try:
                self._file.unlink(missing_ok=True)
            except OSError:
                pass        # winsound lo tiene ancora aperto: resta nella cartella temporanea
            self._file = None


class WaveformView(QWidget):
    """La forma d'onda con il pezzo scelto: un clic e un trascinamento scelgono il pezzo, i bordi si spostano."""

    selection_changed = Signal(float, float)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        self.peaks = []
        self.total = 0.0
        self.start = 0.0
        self.end = 0.0
        self.cursor = -1.0           # la posizione dell'ascolto (secondi), -1 = niente
        self._drag = ""              # "start", "end" o "new"
        self._anchor = 0.0
        self.message = tr("Lettura del brano…")

    def set_audio(self, total: float, peaks: list) -> None:
        self.total = total
        self.peaks = list(peaks)
        self.message = ""
        self.update()

    def set_selection(self, start: float, end: float) -> None:
        self.start = start
        self.end = end
        self.update()

    def _x(self, seconds: float) -> float:
        result = seconds / self.total * self.width() if self.total else 0.0
        return result

    def _seconds(self, x: float) -> float:
        result = min(max(0.0, x / max(1, self.width()) * self.total), self.total)
        return result

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().base())
        if self.message:
            painter.drawText(self.rect(), Qt.AlignCenter, self.message)
        elif self.peaks:
            painter.fillRect(QRectF(self._x(self.start), 0, self._x(self.end) - self._x(self.start), self.height()),
                             SELECTION_COLOR)
            middle = self.height() / 2
            painter.setPen(QPen(WAVE_COLOR, 1))
            width = self.width()
            count = len(self.peaks)
            column = 0
            while column < width:
                peak = self.peaks[min(count - 1, column * count // max(1, width))]
                half = peak * (middle - 2)
                painter.drawLine(column, int(middle - half), column, int(middle + half))
                column += 1
            painter.setPen(QPen(HANDLE_COLOR, 2))
            for seconds in (self.start, self.end):
                x = int(self._x(seconds))
                painter.drawLine(x, 0, x, self.height())
            if self.cursor >= 0:
                painter.setPen(QPen(CURSOR_COLOR, 2))
                x = int(self._x(self.cursor))
                painter.drawLine(x, 0, x, self.height())
        painter.end()

    def mousePressEvent(self, event) -> None:
        if self.peaks and event.button() == Qt.LeftButton:
            x = event.position().x()
            if abs(x - self._x(self.start)) <= HANDLE_GRAB:
                self._drag = "start"
            elif abs(x - self._x(self.end)) <= HANDLE_GRAB:
                self._drag = "end"
            else:
                self._drag = "new"
                self._anchor = self._seconds(x)

    def mouseMoveEvent(self, event) -> None:
        x = event.position().x()
        near = self.peaks and (abs(x - self._x(self.start)) <= HANDLE_GRAB or abs(x - self._x(self.end)) <= HANDLE_GRAB)
        self.setCursor(Qt.SizeHorCursor if near or self._drag in ("start", "end") else Qt.ArrowCursor)
        if self._drag:
            seconds = self._seconds(x)
            if self._drag == "start":
                start, end = seconds, self.end
            elif self._drag == "end":
                start, end = self.start, seconds
            else:
                start, end = min(self._anchor, seconds), max(self._anchor, seconds)
            if end - start >= 0.1:
                self.selection_changed.emit(start, end)

    def mouseReleaseEvent(self, event) -> None:
        if self._drag == "new" and abs(self._seconds(event.position().x()) - self._anchor) < 0.1:
            # un clic senza trascinare: il pezzo parte da qui, con la stessa lunghezza
            length = self.end - self.start
            self.selection_changed.emit(self._anchor, self._anchor + length)
        self._drag = ""


class RingtoneDialog(QDialog):
    """source: il file del brano (del PC, o una copia temporanea di quello dell'iPhone); title: il nome proposto;
    folder: la cartella delle suonerie. Dopo exec(), created è il file creato (o None) e send dice se metterlo in
    attesa per l'iPhone."""

    def __init__(self, parent, ffmpeg: Path, source: Path, title: str, folder: Path, label: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("Crea una suoneria"))
        self.resize(860, 480)
        self._ffmpeg = ffmpeg
        self._source = source
        self._folder = folder
        self.created = None
        self.send = False
        self._updating = False
        self._clock = QElapsedTimer()
        self._play_start = 0.0
        self._tick = QTimer(self)
        self._tick.setInterval(TICK_MS)
        self._tick.timeout.connect(self._advance)
        self._player = Player(self._playing, self._stopped, self._play_failed)

        heading = QLabel(f"<b>{label or source.name}</b>")
        heading.setWordWrap(True)
        intro = QLabel(tr(f"Scegli il pezzo (al massimo {ringtones.MAX_SECONDS:g} secondi): trascina sulla forma "
                          "d'onda, sposta i bordi o scrivi inizio e fine. Il brano non cambia: la suoneria è un file "
                          "nuovo nella cartella delle suonerie."))
        intro.setWordWrap(True)
        self._wave = WaveformView()
        self._wave.selection_changed.connect(self._dragged)
        self._start = self._spin()
        self._end = self._spin()
        self._start.valueChanged.connect(lambda _value: self._typed(True))
        self._end.valueChanged.connect(lambda _value: self._typed(False))
        self._length = QLabel()
        self._fade_in = QCheckBox("Dissolvenza all'inizio")
        self._fade_in_seconds = self._fade_spin(0.5)
        self._fade_out = QCheckBox("Dissolvenza alla fine")
        self._fade_out.setChecked(True)
        self._fade_out_seconds = self._fade_spin(2.0)
        self._name = QLineEdit(title)
        self._name.setToolTip(tr("Il nome che vedrai nell'elenco delle suonerie dell'iPhone (e del file sul PC)"))
        self._send = QCheckBox("Mettila anche in attesa per l'iPhone (Invia come suoneria, parte con Applica)")
        self._play = QPushButton("Ascolta il pezzo")
        self._play.clicked.connect(self._toggle_play)
        self._play.setEnabled(False)
        if not Player.available():
            self._play.setToolTip(tr("L'ascolto c'è solo su Windows"))
        where = QLabel(tr(f"Cartella delle suonerie: {folder}"))
        where.setStyleSheet("color: gray")
        where.setWordWrap(True)

        times = QHBoxLayout()
        times.addWidget(QLabel("Inizio"))
        times.addWidget(self._start)
        times.addWidget(QLabel("Fine"))
        times.addWidget(self._end)
        times.addWidget(self._length, 1)
        times.addWidget(self._play)
        fades = QHBoxLayout()
        fades.addWidget(self._fade_in)
        fades.addWidget(self._fade_in_seconds)
        fades.addSpacing(20)
        fades.addWidget(self._fade_out)
        fades.addWidget(self._fade_out_seconds)
        fades.addStretch(1)
        form = QFormLayout()
        form.addRow("Nome della suoneria", self._name)
        self._buttons = QDialogButtonBox()
        self._create = self._buttons.addButton("Crea la suoneria", QDialogButtonBox.AcceptRole)
        self._create.setProperty("role", "go")
        self._create.setEnabled(False)
        self._buttons.addButton("Annulla", QDialogButtonBox.RejectRole)
        self._buttons.accepted.connect(self._make)
        self._buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(heading)
        layout.addWidget(intro)
        layout.addWidget(self._wave, 1)
        layout.addLayout(times)
        layout.addLayout(fades)
        layout.addLayout(form)
        layout.addWidget(self._send)
        layout.addWidget(where)
        layout.addWidget(self._buttons)
        self._load()

    @staticmethod
    def _spin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setDecimals(1)
        spin.setSingleStep(0.5)
        spin.setSuffix(" s")
        spin.setRange(0.0, 0.0)
        return spin

    @staticmethod
    def _fade_spin(value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setDecimals(1)
        spin.setSingleStep(0.5)
        spin.setRange(0.1, 10.0)
        spin.setSuffix(" s")
        spin.setValue(value)
        return spin

    def _load(self) -> None:
        ffmpeg = self._ffmpeg
        source = self._source

        def work(_progress, _cancel, emit):
            emit(ringtones.waveform(ffmpeg, source))

        self._job = BackgroundJob(work)
        self._job.item.connect(self._loaded)
        self._job.failed.connect(self._load_failed)
        self._job.start()

    def _loaded(self, value) -> None:
        total, peaks = value
        self._wave.set_audio(total, peaks)
        for spin in (self._start, self._end):
            spin.setRange(0.0, round(total, 1))
        start, end = ringtones.clamp_selection(0.0, ringtones.DEFAULT_SECONDS, total)
        self._set_selection(start, end)
        self._create.setEnabled(True)
        self._play.setEnabled(Player.available())

    def _load_failed(self, message: str) -> None:
        self._wave.message = tr("Il brano non si legge")
        self._wave.update()
        QMessageBox.warning(self, tr("Crea una suoneria"), message)

    def _set_selection(self, start: float, end: float) -> None:
        start, end = ringtones.clamp_selection(start, end, self._wave.total)
        self._updating = True
        self._start.setValue(start)
        self._end.setValue(end)
        self._updating = False
        self._wave.set_selection(start, end)
        self._length.setText(tr(f"Durata: {end - start:.1f} s (da {_format_seconds(start)} a "
                                f"{_format_seconds(end)})"))

    def _dragged(self, start: float, end: float) -> None:
        self._player.stop()
        self._set_selection(start, end)

    def _typed(self, start_changed: bool) -> None:
        if not self._updating and self._wave.total:
            start = self._start.value()
            end = self._end.value()
            if start_changed and end - start > ringtones.MAX_SECONDS:
                end = start + ringtones.MAX_SECONDS       # si sposta la fine: l'inizio è quello scritto
            elif not start_changed and end - start > ringtones.MAX_SECONDS:
                start = end - ringtones.MAX_SECONDS
            self._set_selection(start, end)

    def _fades(self) -> tuple:
        fade_in = self._fade_in_seconds.value() if self._fade_in.isChecked() else 0.0
        fade_out = self._fade_out_seconds.value() if self._fade_out.isChecked() else 0.0
        result = (fade_in, fade_out)
        return result

    def _toggle_play(self) -> None:
        if self._tick.isActive():
            self._player.stop()
        else:
            fade_in, fade_out = self._fades()
            self._play.setEnabled(False)
            self._player.play(self._ffmpeg, self._source, self._start.value(), self._end.value(), fade_in, fade_out)

    def _playing(self, _seconds: float) -> None:
        self._play_start = self._start.value()
        self._clock.start()
        self._tick.start()
        self._play.setText(tr("Ferma"))
        self._play.setEnabled(True)

    def _advance(self) -> None:
        position = self._play_start + self._clock.elapsed() / 1000
        self._wave.cursor = position if position <= self._end.value() else -1.0
        self._wave.update()

    def _stopped(self) -> None:
        self._tick.stop()
        self._wave.cursor = -1.0
        self._wave.update()
        self._play.setText(tr("Ascolta il pezzo"))
        self._play.setEnabled(True)

    def _play_failed(self, message: str) -> None:
        self._stopped()
        QMessageBox.warning(self, tr("Ascolta il pezzo"), message)

    def _make(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.information(self, tr("Crea una suoneria"), tr("Scrivi il nome della suoneria."))
        else:
            self._player.stop()
            fade_in, fade_out = self._fades()
            try:
                self.created = ringtones.create_ringtone(self._ffmpeg, self._source, self._folder,
                                                         self._start.value(), self._end.value(), fade_in, fade_out,
                                                         name)
                self.send = self._send.isChecked()
                self.accept()
            except (ringtones.RingtoneError, OSError) as exc:
                QMessageBox.warning(self, tr("Crea una suoneria"), str(exc))

    def done(self, code: int) -> None:
        self._player.stop()
        if getattr(self, "_job", None) is not None:
            self._job.cancel()
        super().done(code)
