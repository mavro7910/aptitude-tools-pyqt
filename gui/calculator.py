# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import ast
import operator as op

from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QPlainTextEdit, QVBoxLayout,
    QLineEdit, QGridLayout, QSpacerItem, QSizePolicy
)

# -------- Safe Evaluator (numbers & basic ops only) --------
class _SafeEval(ast.NodeVisitor):
    ALLOWED_BINOPS = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.FloorDiv: op.floordiv,
        ast.Mod: op.mod,
        ast.Pow: op.pow,
    }
    ALLOWED_UNARY = {ast.UAdd: op.pos, ast.USub: op.neg}
    ALLOWED_CONSTS = (int, float)

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, self.ALLOWED_CONSTS):
                return node.value
            raise ValueError("숫자만 사용")
        elif isinstance(node, ast.BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            fn = self.ALLOWED_BINOPS.get(type(node.op))
            if not fn:
                raise ValueError("연산자 불가")
            return fn(left, right)
        elif isinstance(node, ast.UnaryOp):
            fn = self.ALLOWED_UNARY.get(type(node.op))
            if not fn:
                raise ValueError("단항 연산자 불가")
            return fn(self.visit(node.operand))
        elif isinstance(node, ast.Expr):
            return self.visit(node.value)
        else:
            raise ValueError("표현식 불가")

def safe_eval_expr(expr: str):
    expr = (expr or "").replace("^", "**")
    tree = ast.parse(expr, mode="eval")
    return _SafeEval().visit(tree)

# -------- Calculator Widget --------
class Calculator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_result = None  # 직전 결과

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Output (read-only)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("계산 결과가 출력됩니다.")
        self.output.setFixedHeight(70)
        layout.addWidget(self.output)

        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("수식을 입력하세요.")
        self.input.setAlignment(Qt.AlignRight)
        self.input.setFixedHeight(36)
        layout.addWidget(self.input)

        # Keypad (aptitude-like)
        grid = QGridLayout()
        grid.setSpacing(6)
        buttons = [
            ("CE", 0, 0), ("C", 0, 1), ("⌫", 0, 2), ("√", 0, 3),
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("/", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("*", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("-", 3, 3),
            ("±", 4, 0), ("0", 4, 1), ("00", 4, 2), ("+", 4, 3),
        ]
        for text, r, c in buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            grid.addWidget(btn, r, c)
            if text == "C":
                btn.clicked.connect(self._clear_all)
            elif text == "CE":
                btn.clicked.connect(self._clear_entry)
            elif text == "⌫":
                btn.clicked.connect(self._backspace)
            elif text == "√":
                btn.clicked.connect(self._square_root)
            elif text == "±":
                btn.clicked.connect(self._toggle_sign)
            else:
                btn.clicked.connect(lambda checked, t=text: self._insert(t))

        # Big "="
        self.btn_eq = QPushButton("=")
        self.btn_eq.setMinimumHeight(44)
        self.btn_eq.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_eq.clicked.connect(self._equals)

        layout.addLayout(grid)
        layout.addWidget(self.btn_eq)

        self.setLayout(layout)
        self.installEventFilter(self)  # click anywhere -> focus input
        self.input.returnPressed.connect(self._equals)

        # Styling
        for i in range(grid.rowCount()):
            grid.setRowMinimumHeight(i, 40)
        self.setStyleSheet("""
            QPushButton { font-size: 14px; }
            QLineEdit { font-size: 16px; }
            QPlainTextEdit { font-size: 14px; }
        """)

    # -------- Events --------
    def eventFilter(self, obj: QObject, event: QEvent):
        if obj is self and event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick):
            self.input.setFocus()
            return True
        return super().eventFilter(obj, event)

    # -------- Button helpers --------
    def _insert(self, t: str):
        self.input.insert(t)
        self.input.setFocus()

    def _clear_all(self):
        self.input.clear()
        self.output.clear()
        self._last_result = None
        self.input.setFocus()

    def _clear_entry(self):
        self.input.clear()
        self.input.setFocus()

    def _backspace(self):
        cur = self.input.text()
        if cur:
            self.input.setText(cur[:-1])
        self.input.setFocus()

    def _toggle_sign(self):
        txt = self.input.text().strip()
        if not txt:
            self.input.setText("-")
            return
        if txt.startswith("-"):
            self.input.setText(txt[1:])
        else:
            self.input.setText("-" + txt)

    def _square_root(self):
        expr = self.input.text().strip()
        # 입력이 없고 직전 결과가 있으면 ans 사용
        if not expr and self._last_result is not None:
            value = self._last_result
        else:
            try:
                value = float(safe_eval_expr(expr))
            except Exception:
                return  # 오류 무시
        if value < 0:
            return  # 음수 루트는 무시
        result = math.sqrt(value)
        if self._last_result is None:
            self.output.setPlainText(str(result))
        else:
            self.output.setPlainText(f"ans = {self._last_result}\n√({value})={result}")
        self._last_result = result
        self.input.clear()
        self.input.setFocus()

    def _equals(self):
        expr = self.input.text().strip()
        if not expr:
            return
        try:
            result = safe_eval_expr(expr)
        except Exception:
            # 오류는 무시
            return
        if self._last_result is None:
            self.output.setPlainText(str(result))
        else:
            self.output.setPlainText(f"ans = {self._last_result}\n{expr}={result}")
        self._last_result = result
        self.input.clear()
        self.input.setFocus()
