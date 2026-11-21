# Copyright (c) 2026 Antonio Romeo <antonioromeo@ilve.it>
# Author: Antonio Romeo (with Claude Code et al.)
# SPDX-License-Identifier: MIT (see the LICENSE file for the full terms)

"""Disegna icons/myEasyMP3toIPhone.ico (16, 32, 48, 256 px, PNG dentro l'ICO). Si esegue a mano solo per cambiarla:
    .venv/Scripts/python tools/make_icon.py"""

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath, QPen

SIZES = (16, 32, 48, 256)
TARGET = Path(__file__).resolve().parent.parent / "icons" / "myEasyMP3toIPhone.ico"


def draw(size: int) -> bytes:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    scale = size / 256.0
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor(255, 94, 98))
    gradient.setColorAt(1.0, QColor(140, 60, 220))
    path = QPainterPath()
    path.addRoundedRect(QRectF(8 * scale, 8 * scale, 240 * scale, 240 * scale), 52 * scale, 52 * scale)
    painter.fillPath(path, gradient)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(255, 255, 255))
    # due note unite da una barra
    painter.drawEllipse(QPointF(84 * scale, 178 * scale), 30 * scale, 23 * scale)
    painter.drawEllipse(QPointF(172 * scale, 154 * scale), 30 * scale, 23 * scale)
    painter.drawRect(QRectF(104 * scale, 62 * scale, 14 * scale, 118 * scale))
    painter.drawRect(QRectF(192 * scale, 40 * scale, 14 * scale, 116 * scale))
    beam = QPainterPath()
    beam.moveTo(104 * scale, 62 * scale)
    beam.lineTo(206 * scale, 40 * scale)
    beam.lineTo(206 * scale, 72 * scale)
    beam.lineTo(104 * scale, 94 * scale)
    beam.closeSubpath()
    painter.drawPath(beam)
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    result = bytes(data)
    return result


def main() -> int:
    _app = QGuiApplication(sys.argv)
    images = [draw(size) for size in SIZES]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b""
    for size, png in zip(SIZES, images):
        side = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_bytes(header + entries + b"".join(images))
    print(f"Scritta {TARGET}")
    result = 0
    return result


if __name__ == "__main__":
    sys.exit(main())
