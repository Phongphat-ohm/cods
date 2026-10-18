"""
Thai Date Picker Component
Interactive date selector with Buddhist Era calendar, quick delta presets (+7, +14, +30 days),
and dynamic format conversion (full, short, numeric, official court format).
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QCalendarWidget, QDialog, QMenu
)
from PySide6.QtCore import Qt, Signal, QDate, QPoint
from services.icon_service import get_icon
from services.template_variable_service import (
    DATE_FORMAT_STYLES,
    format_thai_date_by_style,
    parse_date_to_dmy,
    normalize_date_format_style,
)


class ThaiDatePickerWidget(QWidget):
    """
    Dedicated Thai Date Picker Widget with:
    - Text field showing formatted date
    - Calendar popup button with Buddhist Era year & Thai months
    - Quick shortcut buttons: 'วันนี้', '+7 วัน', '+14 วัน', '+30 วัน'
    - Date format dropdown allowing instant on-the-fly reformatting
    """

    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(self, initial_value: str = "", default_format: str = "full", parent=None):
        super().__init__(parent)
        self.current_format = normalize_date_format_style(default_format)
        self.selected_date: Optional[QDate] = None
        self._suppress_signal = False

        self.init_ui(initial_value)

    def init_ui(self, initial_value: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 1. Main Text Input for formatted date
        self.txt_date = QLineEdit()
        self.txt_date.setObjectName("formInput")
        self.txt_date.setPlaceholderText("เลือกหรือพิมพ์วันที่...")
        self.txt_date.setStyleSheet("""
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
        self.txt_date.textChanged.connect(self._on_text_edited)
        self.txt_date.returnPressed.connect(self.returnPressed.emit)
        layout.addWidget(self.txt_date, 1)

        # 2. Calendar Popup Button
        self.btn_cal = QPushButton()
        self.btn_cal.setIcon(get_icon("calendar", color="#581c87", size=15))
        self.btn_cal.setToolTip("เปิดปฏิทินเลือกวันนัด (พ.ศ.)")
        self.btn_cal.setStyleSheet("""
            QPushButton {
                background-color: #f5f3ff;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton:hover {
                background-color: #ede9fe;
                border-color: #7c3aed;
            }
            QPushButton:pressed {
                background-color: #ddd6fe;
            }
        """)
        self.btn_cal.clicked.connect(self.show_calendar_popup)
        layout.addWidget(self.btn_cal)

        # 3. Format Selector Dropdown
        self.cmb_format = QComboBox()
        self.cmb_format.setToolTip("เลือกรูปแบบการแสดงผลวันที่")
        self.cmb_format.setStyleSheet("""
            QComboBox {
                font-size: 12px;
                padding: 5px 8px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #f8fafc;
                color: #334155;
                font-weight: 500;
            }
            QComboBox:hover {
                border-color: #94a3b8;
                background: #ffffff;
            }
            QComboBox::drop-down {
                border: none;
                width: 18px;
            }
        """)

        # Populate format choices
        for style_id, meta in DATE_FORMAT_STYLES.items():
            self.cmb_format.addItem(f"{meta['label']} ({meta['example']})", style_id)

        # Set default selection
        idx = self.cmb_format.findData(self.current_format)
        if idx >= 0:
            self.cmb_format.setCurrentIndex(idx)

        self.cmb_format.currentIndexChanged.connect(self._on_format_changed)
        layout.addWidget(self.cmb_format)

        # 4. Quick Shortcuts Menu Button
        self.btn_quick = QPushButton("+ นัด")
        self.btn_quick.setToolTip("เลือกวันนัดด่วน (วันนี้, +7 วัน, +14 วัน, +30 วัน)")
        self.btn_quick.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #6b21a8;
                border: 1px solid #c4b5fd;
                border-radius: 6px;
                padding: 5px 9px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f5f3ff;
                border-color: #7c3aed;
            }
        """)
        self.btn_quick.clicked.connect(self.show_quick_menu)
        layout.addWidget(self.btn_quick)

        if initial_value:
            self.set_value(initial_value)

    def text(self) -> str:
        return self.txt_date.text().strip()

    def get_value(self) -> str:
        return self.text()

    def set_value(self, val: str):
        self._suppress_signal = True
        self.txt_date.setText(val)
        parsed = parse_date_to_dmy(val)
        if parsed:
            d, m, be_y, _ = parsed
            ce_y = be_y - 543 if be_y >= 2400 else be_y
            self.selected_date = QDate(ce_y, m, d)
        self._suppress_signal = False

    def setText(self, val: str):
        self.set_value(val)

    def set_format(self, format_style: str):
        clean_fmt = normalize_date_format_style(format_style)
        self.current_format = clean_fmt
        idx = self.cmb_format.findData(clean_fmt)
        if idx >= 0 and self.cmb_format.currentIndex() != idx:
            self.cmb_format.setCurrentIndex(idx)
        else:
            self._reformat_current_value()

    def _on_format_changed(self, index: int):
        fmt_id = self.cmb_format.itemData(index)
        if fmt_id:
            self.current_format = fmt_id
            self._reformat_current_value()

    def _reformat_current_value(self):
        curr_text = self.text()
        if not curr_text and not self.selected_date:
            return

        target_date = self.selected_date if self.selected_date else curr_text
        new_formatted = format_thai_date_by_style(target_date, self.current_format)
        if new_formatted and new_formatted != curr_text:
            self._suppress_signal = True
            self.txt_date.setText(new_formatted)
            self._suppress_signal = False
            self.textChanged.emit(new_formatted)

    def _on_text_edited(self, new_text: str):
        if not self._suppress_signal:
            parsed = parse_date_to_dmy(new_text)
            if parsed:
                d, m, be_y, _ = parsed
                ce_y = be_y - 543 if be_y >= 2400 else be_y
                self.selected_date = QDate(ce_y, m, d)
            self.textChanged.emit(new_text)

    def apply_date(self, qdate: QDate):
        self.selected_date = qdate
        formatted = format_thai_date_by_style(qdate, self.current_format)
        self.txt_date.setText(formatted)

    def show_calendar_popup(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("เลือกวันที่ (ปฏิทิน พ.ศ.)")
        dlg.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 2px solid #7c3aed;
                border-radius: 12px;
            }
        """)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        # Header title with close button
        head_layout = QHBoxLayout()
        lbl_head = QLabel("เลือกวันนัด / วันที่กระบวนพิจารณา")
        lbl_head.setStyleSheet("font-size: 14px; font-weight: 700; color: #4c1d95;")
        head_layout.addWidget(lbl_head)
        head_layout.addStretch()

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setToolTip("ปิดหน้าต่าง")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 13px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #b91c1c;
            }
        """)
        btn_close.clicked.connect(dlg.reject)
        head_layout.addWidget(btn_close)
        lay.addLayout(head_layout)

        # Calendar Widget with clean white styling & no week number confusion
        cal = QCalendarWidget()
        cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        cal.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        cal.setGridVisible(False)
        if self.selected_date and self.selected_date.isValid():
            cal.setSelectedDate(self.selected_date)
        else:
            cal.setSelectedDate(QDate.currentDate())

        # Set navigation chevron icons
        btn_prev = cal.findChild(QPushButton, "qt_calendar_prevmonth") or cal.findChildren(QPushButton)
        # Find QToolButton for navigation in QCalendarWidget
        from PySide6.QtWidgets import QToolButton
        tool_prev = cal.findChild(QToolButton, "qt_calendar_prevmonth")
        tool_next = cal.findChild(QToolButton, "qt_calendar_nextmonth")
        if tool_prev:
            tool_prev.setIcon(get_icon("arrow-left", color="#4c1d95", size=14))
        if tool_next:
            tool_next.setIcon(get_icon("arrow-right", color="#4c1d95", size=14))

        cal.setStyleSheet("""
            QCalendarWidget {
                background-color: #ffffff;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #f5f3ff;
                border-bottom: 1.5px solid #ddd6fe;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
                min-height: 38px;
            }
            QCalendarWidget QToolButton {
                color: #4c1d95;
                background-color: #ffffff;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 700;
                margin: 2px 3px;
                padding: 3px 8px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #ede9fe;
                border-color: #7c3aed;
            }
            QCalendarWidget QToolButton:pressed {
                background-color: #ddd6fe;
            }
            QCalendarWidget QHeaderView::section {
                background-color: #faf5ff;
                color: #4c1d95;
                font-weight: 700;
                font-size: 12px;
                padding: 5px 0px;
                border: none;
                border-bottom: 1.5px solid #e9d5ff;
            }
            QCalendarWidget QTableView {
                background-color: #ffffff;
                alternate-background-color: #faf5ff;
                color: #0f172a;
                font-size: 13px;
                font-weight: 500;
                selection-background-color: #7c3aed;
                selection-color: #ffffff;
                gridline-color: #f8fafc;
                border: none;
                outline: none;
            }
            QCalendarWidget QTableView:item:hover {
                background-color: #ede9fe;
                color: #4c1d95;
            }
            QCalendarWidget QTableView:item:selected {
                background-color: #7c3aed;
                color: #ffffff;
                font-weight: 700;
            }
            QCalendarWidget QSpinBox {
                background-color: #ffffff;
                color: #4c1d95;
                font-weight: 700;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 2px 4px;
            }
            QCalendarWidget QMenu {
                background-color: #ffffff;
                color: #0f172a;
                border: 1.5px solid #ddd6fe;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        lay.addWidget(cal)

        # Quick preset buttons row
        h_quick = QHBoxLayout()
        h_quick.setSpacing(6)

        presets = [
            ("วันนี้", 0),
            ("+7 วัน", 7),
            ("+14 วัน", 14),
            ("+30 วัน", 30),
        ]
        today = QDate.currentDate()
        for label, days in presets:
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f5f3ff;
                    color: #581c87;
                    border: 1.5px solid #c4b5fd;
                    border-radius: 6px;
                    padding: 5px 8px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #7c3aed;
                    color: #ffffff;
                    border-color: #6d28d9;
                }
            """)
            target_qdate = today.addDays(days)
            btn.clicked.connect(lambda checked=False, qd=target_qdate: (
                self.apply_date(qd),
                dlg.accept()
            ))
            h_quick.addWidget(btn)

        lay.addLayout(h_quick)

        # Action buttons row (Cancel & Confirm)
        h_actions = QHBoxLayout()
        h_actions.setSpacing(8)

        btn_cancel = QPushButton("ยกเลิก")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #475569;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
                color: #1e293b;
            }
        """)
        btn_cancel.clicked.connect(dlg.reject)
        h_actions.addWidget(btn_cancel)

        btn_confirm = QPushButton("ตกลงเลือกวันนี้")
        btn_confirm.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                border: 1.5px solid #3b0764;
                border-radius: 6px;
                padding: 7px 16px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5b21b6;
                border-color: #4c1d95;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
        """)
        btn_confirm.clicked.connect(lambda: (
            self.apply_date(cal.selectedDate()),
            dlg.accept()
        ))
        h_actions.addWidget(btn_confirm, 1)

        lay.addLayout(h_actions)

        cal.activated.connect(lambda qd: (
            self.apply_date(qd),
            dlg.accept()
        ))

        dlg.adjustSize()

        # Position popup near button
        btn_pos = self.btn_cal.mapToGlobal(QPoint(0, self.btn_cal.height()))
        dlg.move(btn_pos.x() - 100, btn_pos.y() + 4)
        dlg.exec()

    def show_quick_menu(self):
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

        today = QDate.currentDate()
        options = [
            ("วันนี้", 0),
            ("วันพรุ่งนี้", 1),
            ("อีก 7 วัน (1 สัปดาห์)", 7),
            ("อีก 14 วัน (2 สัปดาห์)", 14),
            ("อีก 30 วัน (1 เดือน)", 30),
            ("อีก 60 วัน (2 เดือน)", 60),
            ("อีก 90 วัน (3 เดือน)", 90),
        ]

        for label, days in options:
            target = today.addDays(days)
            fmt_sample = format_thai_date_by_style(target, self.current_format)
            action = menu.addAction(f"{label} ({fmt_sample})")
            action.triggered.connect(lambda checked=False, qd=target: self.apply_date(qd))

        menu.exec(self.btn_quick.mapToGlobal(QPoint(0, self.btn_quick.height())))
