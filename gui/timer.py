# gui/timer.py
# -*- coding: utf-8 -*-
from __future__ import annotations

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton
)

import winsound

def _fmt(sec: int) -> str:
    sec = max(0, sec)
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


def _parse_mmss(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    if ":" in text:
        m, s = text.split(":", 1)
        return int(m) * 60 + int(s)
    return int(text)


class TimerWidget(QWidget):
    """
    심플 카운트다운 타이머
    - 시간 입력: MM:SS 또는 숫자(초)
    - Start / Pause / Reset 버튼
    - 단축키: Space(시작/일시정지), R(리셋)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._remaining = 0
        self._running = False

        # 제목
        self.lbl_title = QLabel("⏱ Timer")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet("font-weight:600; font-size:14px;")

        # 시간 입력 및 표시
        self.edit = QLineEdit("20:00")
        self.edit.setFixedWidth(90)
        self.edit.setAlignment(Qt.AlignCenter)
        self.edit.setPlaceholderText("MM:SS 또는 초")

        self.lbl_show = QLabel("20:00")
        self.lbl_show.setFixedWidth(90)
        self.lbl_show.setAlignment(Qt.AlignCenter)
        self.lbl_show.setStyleSheet("font-size:18px; font-weight:600;")

        # 버튼
        self.btn_start = QPushButton("Start")
        self.btn_pause = QPushButton("Pause")
        self.btn_reset = QPushButton("Reset")

        for btn in (self.btn_start, self.btn_pause, self.btn_reset):
            btn.setFixedWidth(70)

        # --- 상단 (입력 + 남은 시간) ---
        input_row = QHBoxLayout()
        input_row.setSpacing(10)
        input_row.setAlignment(Qt.AlignCenter)
        input_row.addWidget(QLabel("입력:"))
        input_row.addWidget(self.edit)
        input_row.addSpacing(10)
        input_row.addWidget(QLabel("남은 시간:"))
        input_row.addWidget(self.lbl_show)

        # --- 하단 (버튼) ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_pause)
        btn_row.addWidget(self.btn_reset)

        # --- 전체 구성 ---
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.lbl_title)
        layout.addLayout(input_row)
        layout.addLayout(btn_row)

        # 타이머 설정
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)

        # 시그널 연결
        self.btn_start.clicked.connect(self.start)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_reset.clicked.connect(self.reset)

    # --- 동작 로직 ---
    def start(self):
        try:
            if not self._running:
                if self._remaining <= 0:
                    self._remaining = _parse_mmss(self.edit.text())
                if self._remaining <= 0:
                    return
                self._running = True
                self.edit.setEnabled(False)
                self.timer.start()
                self._render()
        except Exception:
            pass

    def pause(self):
        if self._running:
            self._running = False
            self.timer.stop()
            self.edit.setEnabled(True)

    def reset(self):
        self.timer.stop()
        self._running = False
        try:
            self._remaining = _parse_mmss(self.edit.text())
        except Exception:
            self._remaining = 0
        self.edit.setEnabled(True)
        self._render()

    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._remaining = 0
            self.timer.stop()
            self._running = False
            self.edit.setEnabled(True)
            winsound.Beep(1000, 400)
        self._render()

    def _render(self):
        self.lbl_show.setText(_fmt(self._remaining))
        self.lbl_show.setStyleSheet(
            "font-size:18px; font-weight:600; color:{};".format(
                "#d9534f" if self._running else "#222"
            )
        )

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space:
            if self._running:
                self.pause()
            else:
                self.start()
            e.accept()
            return
        if e.key() == Qt.Key_R:
            self.reset()
            e.accept()
            return
        super().keyPressEvent(e)