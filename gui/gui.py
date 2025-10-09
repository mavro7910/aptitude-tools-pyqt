# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from gui.notes_paint import TopArea
from gui.calculator import Calculator

APP_TITLE = "Aptitude Tools (PyQt5)"

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(500, 840)

        main = QVBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        self.top_area = TopArea()
        self.calc = Calculator()

        main.addWidget(self.top_area, stretch=2)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main.addWidget(line)
        main.addWidget(self.calc, stretch=3)

        self.setLayout(main)
