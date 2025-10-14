# gui/timer.py
# -*- coding: utf-8 -*-
from __future__ import annotations

import sys, os
from pathlib import Path

import re
MMSS_RE = re.compile(r"^\s*(\d{1,3})(?::([0-5]?\d))?\s*$")

from PyQt5.QtCore import QTimer, Qt, QUrl
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton
)

from PyQt5.QtMultimedia import QSoundEffect

def _fmt(sec: int) -> str:
    sec = max(0, sec)
    m, s = divmod(sec, 60)
    return f"{m:02d}:{s:02d}"


def _parse_mmss(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    m = MMSS_RE.match(text)
    if not m:
        raise ValueError("시간 형식은 MM:SS 또는 초(정수)입니다.")
    mm = int(m.group(1))
    ss = int(m.group(2) or 0)
    return mm * 60 + ss

def resource_path(rel: str) -> str:
    # PyInstaller(onefile)로 돌 때는 _MEIPASS 사용, 개발 환경은 소스 기준
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return str((base / rel).resolve())

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
        
        # 비프 사운드
        wav_path = resource_path("assets/beep.wav")   # 프로젝트루트/assets/beep.wav
        self._beep = QSoundEffect(self)
        self._beep.setSource(QUrl.fromLocalFile(wav_path))
        self._beep.setVolume(0.8)
        self._beep.setLoopCount(1) 

    # --- 동작 로직 ---
    def start(self):
        if self._running:
            return

        try:
            # 남은 시간이 0이면 입력값 파싱
            if self._remaining <= 0:
                self._remaining = _parse_mmss(self.edit.text())

            # 0초면 시작 안 함
            if self._remaining <= 0:
                return

        except ValueError:
            # 형식 오류: 테두리 빨강 + 포커스/선택
            self.edit.setStyleSheet("QLineEdit { border:1px solid #d9534f; }")
            self.edit.setToolTip("시간 형식은 MM:SS 또는 초(정수)입니다.")
            self.edit.setFocus()
            self.edit.selectAll()
            return
        else:
            # 정상: 테두리 원복
            self.edit.setStyleSheet("")
            self.edit.setToolTip("")

        # 타이머 시작
        self._running = True
        self.edit.setEnabled(False)
        self.timer.start()
        self._render()

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
            self._beep.play()
        self._render()

    def _render(self):
        self.lbl_show.setText(_fmt(self._remaining))
        color = "#222"
        if self._running:
            color = "#d9534f" if self._remaining <= 10 else "#222"
        self.lbl_show.setStyleSheet(f"font-size:18px; font-weight:600; color:{color};")

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