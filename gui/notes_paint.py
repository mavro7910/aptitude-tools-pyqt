# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QFrame, QSizePolicy
)

# -------- Paint Canvas --------
class PaintCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pix = QPixmap(1200, 600)
        self._pix.fill(Qt.white)
        self._last_pos = None
        self._pen = QPen(Qt.black, 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

    def clear(self):
        self._pix.fill(Qt.white)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self._pix)

    def resizeEvent(self, event):
        if event.size().width() > self._pix.width() or event.size().height() > self._pix.height():
            new_w = max(event.size().width(), self._pix.width())
            new_h = max(event.size().height(), self._pix.height())
            new_pix = QPixmap(new_w, new_h)
            new_pix.fill(Qt.white)
            qp = QPainter(new_pix)
            qp.drawPixmap(0, 0, self._pix)
            qp.end()
            self._pix = new_pix
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._last_pos = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self._last_pos is not None:
            painter = QPainter(self._pix)
            painter.setPen(self._pen)
            painter.drawLine(self._last_pos, event.pos())
            painter.end()
            self._last_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._last_pos = None

# -------- Top Area (Notepad/Paint) --------
class TopArea(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Header: toggle + clear
        self.btn_note = QPushButton("메모장")
        self.btn_paint = QPushButton("그림판")
        for b in (self.btn_note, self.btn_paint):
            b.setCheckable(True)
            b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn_note.setChecked(True)

        self.btn_clear = QPushButton("전체 지우기")
        self.btn_clear.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        header.addWidget(self.btn_note)
        header.addWidget(self.btn_paint)
        header.addStretch(1)
        header.addWidget(self.btn_clear)

        header_frame = QFrame()
        header_frame.setLayout(header)
        header_frame.setFrameShape(QFrame.NoFrame)

        # Stack content
        self.stack = QStackedWidget()

        # Notepad
        self.text = QTextEdit()
        self.text.setPlaceholderText("여기에 메모하세요...")

        # Paint
        self.canvas = PaintCanvas()

        self.stack.addWidget(self.text)   # 0
        self.stack.addWidget(self.canvas) # 1

        # Main layout
        main = QVBoxLayout()
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)
        main.addWidget(header_frame)
        main.addWidget(self.stack)
        self.setLayout(main)

        # Signals
        self.btn_note.clicked.connect(self._switch_note)
        self.btn_paint.clicked.connect(self._switch_paint)
        self.btn_clear.clicked.connect(self._clear_active)

    def _switch_note(self):
        self.btn_note.setChecked(True)
        self.btn_paint.setChecked(False)
        self.stack.setCurrentIndex(0)

    def _switch_paint(self):
        self.btn_note.setChecked(False)
        self.btn_paint.setChecked(True)
        self.stack.setCurrentIndex(1)

    def _clear_active(self):
        if self.stack.currentIndex() == 0:
            self.text.clear()
        else:
            self.canvas.clear()
