"""
Select Variable Input Component
True interactive autocomplete dropdown select with substring filtering (MatchContains),
click-to-open interaction, and freeform text fallback.
"""

from typing import List
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QCompleter
from PySide6.QtCore import Qt, Signal, QEvent, QTimer


class SelectVariableInputWidget(QWidget):
    """
    True interactive Autocomplete Select Widget matching modern web/system selects:
    - Search-as-you-type autocomplete with MatchContains (finds keyword anywhere in choice)
    - Clicking anywhere on the input box opens the dropdown list immediately
    - Allows picking from options OR typing custom input freely
    - Clear button to quickly reset
    - Modern styled popup with clean judicial theme
    """

    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, options: List[str] = None, initial_value: str = "", parent=None):
        super().__init__(parent)
        self.options = [opt.strip() for opt in (options or []) if opt.strip()]
        self.init_ui(initial_value)

    def init_ui(self, initial_value: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.cmb_select = QComboBox()
        self.cmb_select.setObjectName("formInput")
        self.cmb_select.setEditable(True)
        self.cmb_select.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        # Populate items
        for opt in self.options:
            self.cmb_select.addItem(opt)

        line_edit = self.cmb_select.lineEdit()
        line_edit.setPlaceholderText("พิมพ์ค้นหา หรือคลิกเพื่อเลือกจากรายการ...")
        line_edit.setClearButtonEnabled(True)

        # Autocomplete Completer with MatchContains
        self.completer = QCompleter(self.options, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.cmb_select.setCompleter(self.completer)

        # Modern Judicial Select Styling
        self.cmb_select.setStyleSheet("""
            QComboBox {
                font-size: 13.5px;
                padding: 6px 10px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                color: #0f172a;
            }
            QComboBox:focus, QComboBox:on {
                border: 1.5px solid #7c3aed;
                background: #faf5ff;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid #e2e8f0;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                background: #f8fafc;
            }
            QComboBox::drop-down:hover {
                background: #f1f5f9;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #f3e8ff;
                selection-color: #4c1d95;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 32px;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 13.5px;
                color: #1e293b;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #f8fafc;
                color: #0f172a;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #f3e8ff;
                color: #4c1d95;
                font-weight: 600;
            }
        """)

        # Install click-to-open event filter on lineEdit so clicking anywhere opens popup
        line_edit.installEventFilter(self)

        if initial_value:
            self.set_value(initial_value)

        self.cmb_select.currentTextChanged.connect(self.textChanged.emit)
        line_edit.returnPressed.connect(self.returnPressed.emit)

        layout.addWidget(self.cmb_select, 1)

    def eventFilter(self, watched, event):
        if hasattr(self, 'cmb_select') and watched == self.cmb_select.lineEdit():
            if event.type() == QEvent.Type.MouseButtonPress:
                if not self.cmb_select.view().isVisible():
                    QTimer.singleShot(10, self.cmb_select.showPopup)
        return super().eventFilter(watched, event)

    def text(self) -> str:
        return self.cmb_select.currentText().strip()

    def get_value(self) -> str:
        return self.text()

    def set_value(self, val: str):
        idx = self.cmb_select.findText(val)
        if idx >= 0:
            self.cmb_select.setCurrentIndex(idx)
        else:
            self.cmb_select.setEditText(val)

    def setText(self, val: str):
        self.set_value(val)
