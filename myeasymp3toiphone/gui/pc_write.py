# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Scrivere i tag nei file ORIGINALI del PC: solo dopo che l'utente ha visto e approvato l'elenco dei file e dei campi
che cambiano (PcWriteDialog: ora → diventa, non si può annullare), con tags.write_tags_approved. Lo usano Usa i tag da
iPhone a PC e la scelta "Anche nei file del PC" delle correzioni (Correggi tag di Verifica album online, Applica la
correzione di Controlla la musica). Ogni altra modifica dei tag resta in sospeso e va solo sulle copie."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem, QVBoxLayout,
)

from ..i18n import tr
from ..tags import READ_ONLY_EXTENSIONS, TAG_FIELDS

ALIGN_TITLE = "Usa i tag da iPhone a PC: modifica dei file del PC"
ALIGN_WHAT = "si scrivono nel file i tag dell'iPhone dei campi scelti"
PHONE_ONLY = "solo_iphone"
ALSO_PC = "anche_pc"


def shown_value(name: str, value) -> str:
    """Un valore come si mostra: "" per un tag vuoto, sì/no per la compilation."""
    if name == "compilation":
        result = "sì" if value else "no"
    elif value is None:
        result = ""
    else:
        result = str(value)
    return result


class PcWriteDialog(QDialog):
    """L'elenco dei file del PC che verranno modificati, con ogni campo (ora → diventa). Una casella per campo, con
    quanti file cambia: si scrivono solo i campi scelti (chosen_plan). Si scrive solo con Modifica i file.
    plan: [(brano, tag nuovi, campi)]. pending=False (Usa i tag da iPhone a PC): "ora" e la base dei tag scritti sono
    i tag del brano con le modifiche in sospeso, che entrano nel file insieme. pending=True (le correzioni): "ora" e la
    base sono i tag del file; i campi non scelti restano in sospeso."""

    def __init__(self, parent, plan: list, title: str = ALIGN_TITLE, what: str = ALIGN_WHAT,
                 pending: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(1000, 520)
        self._plan = plan
        self._what = what
        self._pending = pending
        self._labels = dict(TAG_FIELDS)
        counts = {}
        for _track, _new_tags, fields in plan:
            for name in fields:
                counts[name] = counts.get(name, 0) + 1
        self._header = QLabel()
        self._header.setWordWrap(True)
        self._boxes = {}
        choices = QHBoxLayout()
        choices.addWidget(QLabel("Campi da scrivere:"))
        for name, _label in TAG_FIELDS:
            if name in counts:
                box = QCheckBox(f"{tr(self._labels[name])} ({counts[name]} file)")
                box.setChecked(True)
                box.toggled.connect(lambda _checked: self._refresh())
                self._boxes[name] = box
                choices.addWidget(box)
        choices.addStretch(1)
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["File", "Campo", "Ora sul PC", "Diventa"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        for column, width in enumerate((420, 110, 200)):
            self._tree.setColumnWidth(column, width)
        self._buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._buttons.button(QDialogButtonBox.Ok).setProperty("role", "danger")
        self._buttons.button(QDialogButtonBox.Cancel).setText("Annulla")
        self._buttons.button(QDialogButtonBox.Cancel).setDefault(True)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self._header)
        layout.addLayout(choices)
        layout.addWidget(self._tree, 1)
        layout.addWidget(self._buttons)
        self._refresh()

    def _base(self, track):
        """I tag di partenza: quelli del file (pending) o quelli del brano con le modifiche in sospeso."""
        if self._pending:
            result = track.original_tags or track.tags
        else:
            result = track.tags
        return result

    def chosen_plan(self) -> list:
        """Il piano con i soli campi scelti: (brano, tag da scrivere, campi); i file senza campi scelti non ci sono."""
        result = []
        for track, new_tags, fields in self._plan:
            kept = []
            for name in fields:
                if self._boxes[name].isChecked():
                    kept.append(name)
            if kept:
                tags = self._base(track).copy()
                for name in kept:
                    setattr(tags, name, getattr(new_tags, name))
                result.append((track, tags, kept))
        return result

    def _refresh(self) -> None:
        plan = self.chosen_plan()
        self._header.setText(f"<b>Questi {len(plan)} file del PC verranno modificati</b>: {tr(self._what)}. Non si "
                             "può annullare.")
        self._tree.clear()
        rows = []
        for track, new_tags, fields in plan:
            first = True
            base = self._base(track)
            for name in fields:
                row = QTreeWidgetItem([str(track.path) if first else "", tr(self._labels.get(name, name)),
                                       shown_value(name, getattr(base, name)), shown_value(name, getattr(new_tags, name))])
                row.setToolTip(0, str(track.path))
                rows.append(row)
                first = False
        self._tree.addTopLevelItems(rows)
        accept = self._buttons.button(QDialogButtonBox.Ok)
        accept.setText(f"Modifica {len(plan)} file")
        accept.setEnabled(bool(plan))


def ask_where(parent, title: str, text: str) -> str:
    """Dove va una correzione: PHONE_ONLY (solo le copie per l'iPhone, in sospeso), ALSO_PC (anche i file del PC,
    dopo l'elenco da approvare) o "" (annullata)."""
    box = QMessageBox(QMessageBox.Question, title, text, parent=parent)
    box.setInformativeText("Solo per l'iPhone: i file del PC non cambiano e la differenza resta da allineare. Anche "
                           "nei file del PC: prima vedi l'elenco di ogni file e campo che cambia, e decidi.")
    phone = box.addButton("Solo per l'iPhone", QMessageBox.AcceptRole)
    both = box.addButton("Anche nei file del PC…", QMessageBox.AcceptRole)
    box.addButton("Annulla", QMessageBox.RejectRole)
    box.setDefaultButton(phone)
    box.exec()
    clicked = box.clickedButton()
    if clicked is phone:
        result = PHONE_ONLY
    elif clicked is both:
        result = ALSO_PC
    else:
        result = ""
    return result


def pending_plan(tracks: list) -> list:
    """Le modifiche in sospeso dei brani come piano da scrivere nei file del PC: (brano, tag in sospeso, campi diversi
    dal file). Senza i file che non si possono scrivere (WMA, WAV, AIFF): restano in sospeso."""
    result = []
    seen = set()
    for track in tracks:
        original = track.original_tags
        fresh = id(track) not in seen
        seen.add(id(track))
        if fresh and original is not None and track.path.suffix.lower() not in READ_ONLY_EXTENSIONS:
            fields = []
            for name, _label in TAG_FIELDS:
                if getattr(track.tags, name) != getattr(original, name):
                    fields.append(name)
            if fields:
                result.append((track, track.tags.copy(), fields))
    return result


def offer_pc_write(window, parent, tracks: list, title: str, what: str) -> None:
    """Dopo una correzione salvata in sospeso: l'elenco delle modifiche da scrivere anche nei file del PC; con Modifica
    i file si scrivono, con Annulla restano solo per l'iPhone."""
    plan = pending_plan(tracks)
    if not plan:
        QMessageBox.information(parent, title, "Nei file del PC non c'è niente da cambiare.")
    else:
        dialog = PcWriteDialog(parent, plan, title=f"{title}: modifica dei file del PC", what=what, pending=True)
        if dialog.exec():
            write_pc_tags(window, parent, dialog.chosen_plan(), title)
        else:
            window.statusBar().showMessage("File del PC non modificati: le correzioni valgono solo per l'iPhone", 8000)


def write_pc_tags(window, parent, plan: list, title: str) -> None:
    """Scrive i tag approvati nei file del PC (tags.write_tags_approved) e li rilegge. I campi scritti non sono più in
    sospeso; quelli non scelti restano in sospeso (solo per le copie)."""
    from ..library import load_track
    from ..tags import TagError, write_tags_approved

    def work(progress, _cancel):
        done = []
        errors = []
        for index, (track, new_tags, _fields) in enumerate(plan):
            progress(index, len(plan), track.path.name)
            try:
                write_tags_approved(track.path, new_tags)
                done.append((track, new_tags, load_track(track.path)))
            except (TagError, OSError) as exc:
                errors.append(f"{track.path.name}: {exc}")
        value = (done, errors)
        return value

    def finished(value):
        done, errors = value
        for track, new_tags, fresh in done:
            wanted = track.tags.copy()                       # i tag voluti: quelli in sospeso, con i campi scritti
            for name, _label in TAG_FIELDS:
                if getattr(new_tags, name) != getattr(track.original_tags or track.tags, name):
                    setattr(wanted, name, getattr(new_tags, name))
            track.original_tags = fresh.tags.copy()
            track.length = fresh.length or track.length
            window.overlay.set_tags(track, wanted)          # in sospeso resta solo quello che il file non ha
            window.tag_cache.store(track)
        try:
            window.overlay.save()
        except OSError:
            pass  # resta come prima: al prossimo avvio le modifiche in sospeso coincidono con il file
        window.tag_cache.save()
        window.refresh_after_tag_change()
        message = f"Tag scritti in {len(done)} file del PC"
        if errors:
            QMessageBox.warning(parent, title, message + ". Non riusciti:\n" + "\n".join(errors[:10]))
        else:
            window.statusBar().showMessage(message, 8000)

    window.runner.run(title, work, finished)
