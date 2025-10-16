# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from decimal import Decimal, getcontext, InvalidOperation

from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QPlainTextEdit, QVBoxLayout, QLineEdit,
    QGridLayout, QSizePolicy, QFrame
)

# 원하는 정밀도(표시 자리수 아님)
getcontext().prec = 10


def D(x) -> Decimal:
    # float을 바로 Decimal로 넣지 말고 문자열 경유
    return x if isinstance(x, Decimal) else Decimal(str(x))


def fmt(d: Decimal) -> str:
    """지수표기 없이, 쓸모없는 0 제거해서 문자열화"""
    if d.is_nan():
        return "NaN"
    nd = d.normalize()
    # 정수인 경우 소수점 제거
    if nd == nd.to_integral():
        return format(nd.quantize(Decimal(1)), 'f')
    return format(nd, 'f')


# -------- Safe Evaluator (numbers & basic ops only) --------
class _SafeEval(ast.NodeVisitor):
    ALLOWED_BINOPS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b,
        ast.FloorDiv: lambda a, b: a // b,
        ast.Mod: lambda a, b: a % b,
        # 거듭제곱은 지수 정수만 허용 (Decimal은 비정수 지수 미지원)
        ast.Pow: lambda a, b: a ** int(b) if b == b.to_integral() else (_ for _ in ()).throw(ValueError("지수는 정수만 허용")),
    }
    ALLOWED_UNARY = {
        ast.UAdd: lambda a: +a,
        ast.USub: lambda a: -a,
    }
    ALLOWED_CONSTS = (int, float, Decimal)

    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        elif isinstance(node, ast.Num):  # Py<3.8
            return D(node.n)
        elif isinstance(node, ast.Constant):  # Py3.8+
            if isinstance(node.value, self.ALLOWED_CONSTS):
                return D(node.value)
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


def safe_eval_expr(expr: str) -> Decimal:
    expr = (expr or "").replace("^", "**")
    tree = ast.parse(expr, mode="eval")
    return _SafeEval().visit(tree)


# -------- Calculator Widget --------
class Calculator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_result: Decimal | None = None  # 직전 결과
        self._history = []  # 최근 3줄 저장

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        # ====== IO 카드 컨테이너 ======
        card = QFrame()
        card.setObjectName("ioCard")

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(4, 1, 4, 1) #(left, top, right, bottom)
        card_lay.setSpacing(0)

        # Output (read-only)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("계산 결과가 출력됩니다.")
        self.output.setFixedHeight(80) # 출력 칸 공간 크기

        # 오른쪽 정렬 설정
        opt = self.output.document().defaultTextOption()
        opt.setAlignment(Qt.AlignRight)
        self.output.document().setDefaultTextOption(opt)

        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("수식을 입력하세요.")
        self.input.setAlignment(Qt.AlignRight)
        self.input.setFixedHeight(32) # 입력 칸 공간 크기

        card_lay.addWidget(self.output)
        card_lay.addWidget(self.input)
        layout.addWidget(card)

        # ====== Keypad ======
        grid = QGridLayout()
        grid.setSpacing(6)
        buttons = [
            ("C", 0, 0), ("⌫", 0, 1), ("/", 0, 2), ("√", 0, 3),
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("*", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("-", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("+", 3, 3),
            ("0", 4, 0), ("00", 4, 1), (".", 4, 2), ("=", 4, 3),
        ]
        for text, r, c in buttons:
            btn = QPushButton(text)
            btn.setMinimumHeight(40)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            grid.addWidget(btn, r, c)
            if text == "C":
                btn.clicked.connect(self._clear_all)
            elif text == "⌫":
                btn.clicked.connect(self._backspace)
            elif text == "√":
                btn.clicked.connect(self._square_root)
            elif text == "=":
                btn.clicked.connect(self._equals)
            else:
                btn.clicked.connect(lambda checked, t=text: self._insert(t))

        layout.addLayout(grid)

        self.setLayout(layout)
        self.installEventFilter(self)  # click anywhere -> focus input
        self.input.returnPressed.connect(self._equals)

        # Styling
        for i in range(grid.rowCount()):
            grid.setRowMinimumHeight(i, 40)

        self.setStyleSheet("""
            QPushButton {
                font-size: 14px;
            }

            /* ✅ IO 카드: 흰색 네모 + 라운드 */
            QFrame#ioCard {
                background: #ffffff;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
            }

            /* ✅ 내부 위젯은 투명 + 경계 없음 */
            QFrame#ioCard QLineEdit,
            QFrame#ioCard QPlainTextEdit {
                border: none;
                background: transparent;
                padding: 6px 8px;
                font-size: 16px;
            }

            QFrame#ioCard:focus-within {
                border: 1px solid #3B82F6; /* 포커스시 파란 라인 */
            }

            QPlainTextEdit QScrollBar:vertical {
                width: 8px;
                background: transparent;
            }
            QPlainTextEdit QScrollBar::handle:vertical {
                background: #E5E7EB;
                border-radius: 4px;
                min-height: 24px;
            }
        """)

    # -------- 헬퍼: 출력 3줄 유지 --------
    def _push_line(self, line: str):
        self._history.append(line)
        if len(self._history) > 3:
            self._history.pop(0)
        self.output.setPlainText("\n".join(self._history))

        # 오른쪽 정렬 유지
        opt = self.output.document().defaultTextOption()
        opt.setAlignment(Qt.AlignRight)
        self.output.document().setDefaultTextOption(opt)

        sb = self.output.verticalScrollBar()
        sb.setValue(sb.maximum())

    # -------- Events --------
    def eventFilter(self, obj: QObject, event: QEvent):
        if obj is self and event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick):
            self.input.setFocus()
            return True
        return super().eventFilter(obj, event)

    # -------- Button helpers --------
    def _insert(self, t: str):
        if t == ".":
            cur = self.input.text()
            if not cur or cur[-1] in "+-*/":
                self.input.insert("0.")
                self.input.setFocus()
                return
        self.input.insert(t)
        self.input.setFocus()

    def _clear_all(self):
        self.input.clear()
        self.output.clear()
        self._last_result = None
        self._history = []
        self.input.setFocus()

    def _backspace(self):
        cur = self.input.text()
        if cur:
            self.input.setText(cur[:-1])
        self.input.setFocus()

    def _square_root(self):
        expr = self.input.text().strip()
        if not expr and self._last_result is not None:
            value = self._last_result
        else:
            try:
                value = D(safe_eval_expr(expr))
            except Exception:
                return  # 오류 무시

        if value < 0:
            return  # 음수 루트 무시

        try:
            result = value.sqrt()  # Decimal sqrt
        except InvalidOperation:
            return

        self._push_line(f"√({fmt(value)}) = {fmt(result)}")
        self._last_result = result
        self.input.clear()
        self.input.setFocus()

    def _equals(self):
        raw = self.input.text().strip()
        expr = self._prepare_expr(raw)
        if not expr:
            return
        try:
            result = safe_eval_expr(expr)
        except Exception:
            return

        self._push_line(f"{expr} = {fmt(result)}")
        self._last_result = result
        self.input.clear()
        self.input.setFocus()

    def _prepare_expr(self, expr: str | None):
        """연속 계산을 위해, 연산자로 시작하면 ans를 앞에 붙인다."""
        if not expr:
            return None
        first = expr[0]
        if first in "+-*/":
            if self._last_result is None:
                if first in "+-" and len(expr) > 1 and expr[1].isdigit():
                    return expr
                return None
            return f"{fmt(self._last_result)}{expr}"
        return expr
