"""
Time Variable Input Component
Court hearing time picker with quick presets (09.00 นาฬิกา, 13.30 นาฬิกา, etc.)
and manual typing support.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QMenu
from PySide6.QtCore import Signal, QPoint
from services.icon_service import get_icon


class TimeVariableInputWidget(QWidget):
    """
    Dedicated Time Variable Input Widget with court preset hours:
    09.00 นาฬิกา, 09.30 นาฬิกา, 10.00 นาฬิกา, 13.30 นาฬิกา, 14.00 นาฬิกา
    """

    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, initial_value: str = "", parent=None):
        super().__init__(parent)
        self.init_ui(initial_value)

    def init_ui(self, initial_value: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.txt_time = QLineEdit()
        self.txt_time.setObjectName("formInput")
        self.txt_time.setPlaceholderText("เช่น 09.00 นาฬิกา หรือ 09.30 น.")
        self.txt_time.setText(initial_value)
        self.txt_time.setStyleSheet("""
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
        self.txt_time.textChanged.connect(self.textChanged.emit)
        self.txt_time.returnPressed.connect(self.returnPressed.emit)
        layout.addWidget(self.txt_time, 1)

        self.btn_presets = QPushButton("เลือกเวลา")
        self.btn_presets.setIcon(get_icon("clock", color="#581c87", size=14))
        self.btn_presets.setStyleSheet("""
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
        self.btn_presets.clicked.connect(self.show_time_menu)
        layout.addWidget(self.btn_presets)

    def text(self) -> str:
        return self.txt_time.text().strip()

    def get_value(self) -> str:
        return self.text()

    def set_value(self, val: str):
        self.txt_time.setText(val)

    def setText(self, val: str):
        self.set_value(val)

    def show_time_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 18px;
                border-radius: 4px;
                color: #1e293b;
            }
            QMenu::item:selected {
                background-color: #f3e8ff;
                color: #4c1d95;
                font-weight: 600;
            }
        """)

        court_times = [
            "09.00 นาฬิกา",
            "09.30 นาฬิกา",
            "10.00 นาฬิกา",
            "10.30 นาฬิกา",
            "11.00 นาฬิกา",
            "13.30 นาฬิกา",
            "14.00 นาฬิกา",
            "14.30 นาฬิกา",
            "09.00 น.",
            "09.30 น.",
            "10.00 น.",
            "13.30 น.",
        ]

        for t in court_times:
            action = menu.addAction(t)
            action.triggered.connect(lambda checked=False, val=t: self.txt_time.setText(val))

        menu.exec(self.btn_presets.mapToGlobal(QPoint(0, self.btn_presets.height())))
