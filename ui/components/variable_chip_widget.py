"""
Variable Chip Component Widget
A clean, official judicial chip component that represents a template variable
as a true interactive chip without any symbols, emoji, or braces.
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from services.icon_service import get_icon
from services.template_variable_service import parse_variable_tag
from ui.components.typed_variable_input import create_typed_variable_input


class VariableChipComponent(QFrame):
    """
    Interactive Chip Component for a template variable.
    Displays pure text inside a clean pill chip badge, along with a specialized
    input (Date Picker, Time Picker, Currency/Number, Select, or Text)
    for the user to type/select and apply the variable's value.
    """

    value_changed = Signal(str, str)  # (var_name, new_value)
    apply_requested = Signal(str, str)  # (var_name, value_to_apply)

    def __init__(self, var_name: str, initial_value: str = "", parent=None):
        super().__init__(parent)
        self.var_name = var_name.strip()
        self.meta = parse_variable_tag(self.var_name)
        self.base_name = self.meta['name'] or self.var_name
        self.setObjectName("variableChipComponent")
        self.setStyleSheet("""
            QFrame#variableChipComponent {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 4px 8px;
            }
            QFrame#variableChipComponent:hover {
                border-color: #c4b5fd;
                background-color: #fcfaff;
            }
        """)
        self.init_ui(initial_value)

    def init_ui(self, initial_value: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(10)

        # 1. Pure text Chip Badge with Type subtitle
        h_badge = QHBoxLayout()
        h_badge.setSpacing(4)

        self.lbl_chip = QLabel(self.base_name)
        self.lbl_chip.setObjectName("chipBadge")
        self.lbl_chip.setStyleSheet("""
            QLabel#chipBadge {
                background-color: #ede9fe;
                color: #4c1d95;
                border: 1.5px solid #c4b5fd;
                border-radius: 12px;
                padding: 4px 12px;
                font-weight: 600;
                font-size: 13px;
            }
        """)
        h_badge.addWidget(self.lbl_chip)
        layout.addLayout(h_badge)

        # 2. Specialized Typed Input field for value (Date picker, Time picker, Number, etc.)
        self.txt_value = create_typed_variable_input(self.meta, initial_value, parent=self)
        if hasattr(self.txt_value, 'textChanged'):
            self.txt_value.textChanged.connect(lambda txt: self.value_changed.emit(self.var_name, txt))
        if hasattr(self.txt_value, 'returnPressed'):
            self.txt_value.returnPressed.connect(self.handle_apply)
        layout.addWidget(self.txt_value, 1)

        # 3. Action button: Apply value into text
        self.btn_apply = QPushButton("แทนที่ในข้อความ")
        self.btn_apply.setIcon(get_icon("check", color="#581c87", size=13))
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #f5f3ff;
                color: #581c87;
                border: 1px solid #d8b4fe;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #6b21a8;
                color: #ffffff;
                border-color: #6b21a8;
            }
            QPushButton:pressed {
                background-color: #581c87;
            }
        """)
        self.btn_apply.setToolTip(f"นำค่าที่กรอกไปแทนที่ชิป {self.var_name} ในข้อความ [Enter]")
        self.btn_apply.clicked.connect(self.handle_apply)
        layout.addWidget(self.btn_apply)

    def get_value(self) -> str:
        return self.txt_value.text().strip()

    def set_value(self, val: str):
        if self.txt_value.text() != val:
            self.txt_value.setText(val)

    def handle_apply(self):
        val = self.get_value()
        self.apply_requested.emit(self.var_name, val)
        if val:
            self.btn_apply.setText("แทนที่แล้ว")
            self.btn_apply.setIcon(get_icon("check", color="#ffffff", size=13))
            self.btn_apply.setStyleSheet("""
                QPushButton {
                    background-color: #16a34a;
                    color: #ffffff;
                    border: 1px solid #16a34a;
                    border-radius: 6px;
                    padding: 5px 12px;
                    font-size: 12px;
                    font-weight: 600;
                }
            """)
            QTimer.singleShot(1500, self._restore_apply_btn)

    def _restore_apply_btn(self):
        self.btn_apply.setText("แทนที่ในข้อความ")
        self.btn_apply.setIcon(get_icon("check", color="#581c87", size=13))
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #f5f3ff;
                color: #581c87;
                border: 1px solid #d8b4fe;
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #6b21a8;
                color: #ffffff;
                border-color: #6b21a8;
            }
            QPushButton:pressed {
                background-color: #581c87;
            }
        """)
