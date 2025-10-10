# gui/gui.py
# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from .timer import TimerWidget
from .notes_paint import TopArea
from .calculator import Calculator

APP_TITLE = "Aptitude Tools (PyQt5)"

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(400, 900)

        main = QVBoxLayout(self)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(8)

        # 순서: 타이머 → 메모장/그림판 → 계산기
        self.timer = TimerWidget()
        self.top_area = TopArea()
        self.calc = Calculator()

        # 구성
        main.addWidget(self.timer)  # 맨 위
        line1 = QFrame(); line1.setFrameShape(QFrame.HLine); line1.setFrameShadow(QFrame.Sunken)
        main.addWidget(line1)

        main.addWidget(self.top_area, stretch=2)
        line2 = QFrame(); line2.setFrameShape(QFrame.HLine); line2.setFrameShadow(QFrame.Sunken)
        main.addWidget(line2)

        main.addWidget(self.calc, stretch=3)