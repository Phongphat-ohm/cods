"""
Number Variable Input Component
Currency and numeric variable input with quick "+ บาท" suffix helper.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Signal
from services.template_variable_service import format_number_comma


class NumberVariableInputWidget(QWidget):
    """
    Dedicated Number/Currency Widget with comma auto-formatting and Baht helpers.
    """

    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, initial_value: str = "", parent=None):
        super().__init__(parent)
        self._suppress_signal = False
        self.init_ui(initial_value)

    def init_ui(self, initial_value: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.txt_num = QLineEdit()
        self.txt_num.setObjectName("formInput")
        self.txt_num.setPlaceholderText("ระบุจำนวนเงินหรือตัวเลข...")
        formatted_initial = format_number_comma(initial_value) if initial_value else ""
        self.txt_num.setText(formatted_initial)
        self.txt_num.setStyleSheet("""
            QLineEdit {
                font-size: 13.5px;
                padding: 6px 10px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 1.5px solid #7c3aed;
                background: #faf5ff;
            }
        """)
        self.txt_num.textChanged.connect(self._on_text_changed)
        self.txt_num.editingFinished.connect(self._format_on_finish)
        self.txt_num.returnPressed.connect(self.returnPressed.emit)
        layout.addWidget(self.txt_num, 1)

        self.btn_baht = QPushButton("+ บาท")
        self.btn_baht.setToolTip("จัดรูปแบบใส่คอมม่า และเติมคำว่า 'บาท' ท้ายจำนวนเงิน")
        self.btn_baht.setStyleSheet("""
            QPushButton {
                background-color: #f5f3ff;
                color: #581c87;
                border: 1px solid #d8b4fe;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ede9fe;
                border-color: #7c3aed;
            }
        """)
        self.btn_baht.clicked.connect(self._append_baht)
        layout.addWidget(self.btn_baht)

    def _on_text_changed(self, text: str):
        if not self._suppress_signal:
            self.textChanged.emit(text)

    def _format_on_finish(self):
        curr = self.txt_num.text().strip()
        if curr:
            formatted = format_number_comma(curr)
            if formatted != curr:
                self._suppress_signal = True
                self.txt_num.setText(formatted)
                self._suppress_signal = False
                self.textChanged.emit(formatted)

    def _append_baht(self):
        curr = self.txt_num.text().strip()
        if curr:
            formatted = format_number_comma(curr)
            if not formatted.endswith("บาท"):
                formatted = f"{formatted} บาท"
            self._suppress_signal = True
            self.txt_num.setText(formatted)
            self._suppress_signal = False
            self.textChanged.emit(formatted)

    def text(self) -> str:
        curr = self.txt_num.text().strip()
        return format_number_comma(curr) if curr else ""

    def get_value(self) -> str:
        return self.text()

    def set_value(self, val: str):
        formatted = format_number_comma(val) if val else ""
        self._suppress_signal = True
        self.txt_num.setText(formatted)
        self._suppress_signal = False

    def setText(self, val: str):
        self.set_value(val)
