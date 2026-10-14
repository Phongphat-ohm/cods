"""
Page 2: Case Selection Table
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QStackedLayout
)
from PySide6.QtCore import Qt, Signal
from icon_service import get_icon, get_pixmap
import storage_service


class TablePage(QWidget):
    """Step 2: Table view showing imported cases from Excel with real-time filtering."""

    change_file_requested = Signal()
    proceed_to_form_requested = Signal()
    doc_type_changed = Signal(str)
    row_selected = Signal(int)  # Emits original row index in dataset

    def __init__(self, parent=None):
        super().__init__(parent)
        self.excel_rows: List[Dict[str, Any]] = []
        self.doc_type: str = "report"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 22, 32, 22)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title = QLabel("ขั้นตอนที่ 2: เลือกคดีความที่ต้องการสร้างเอกสาร")
        title.setObjectName("stepPageTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_back = QPushButton("เปลี่ยนไฟล์ Excel")
        btn_back.setObjectName("secondaryButton")
        btn_back.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_back.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_back.setToolTip("เปลี่ยนไฟล์ Excel [PgUp]")
        btn_back.clicked.connect(self.change_file_requested.emit)
        header_layout.addWidget(btn_back)

        self.btn_next_to_form = QPushButton("ต่อไป: เลือกประเภทเอกสาร")
        self.btn_next_to_form.setObjectName("primaryButton")
        self.btn_next_to_form.setIcon(get_icon("arrow-right", color="#ffffff", size=16))
        self.btn_next_to_form.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; padding: 9px 20px; font-weight: 600; font-size: 15px; border-radius: 6px; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        self.btn_next_to_form.setToolTip("ไปยังขั้นตอนเลือกประเภทเอกสาร [PgDown หรือ Enter]")
        self.btn_next_to_form.clicked.connect(self.proceed_to_form_requested.emit)
        header_layout.addWidget(self.btn_next_to_form)

        # Retain attribute for backwards compatibility
        self.btn_compromise = QPushButton("สร้างคำพิพากษาตามยอม")
        layout.addLayout(header_layout)

        # Filter and status bar
        sub_bar = QHBoxLayout()
        self.lbl_table_status = QLabel("รายการคดีทั้งหมด")
        self.lbl_table_status.setObjectName("fieldLabel")
        sub_bar.addWidget(self.lbl_table_status)
        sub_bar.addStretch()

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("พิมพ์ค้นหาเลขคดีดำ/แดง, โจทก์, จำเลย...")
        self.filter_input.setStyleSheet(
            "QLineEdit:focus { border: 2px solid #7c3aed; background-color: #faf5ff; }"
        )
        self.filter_input.setToolTip("ค้นหาคดี [Ctrl+F]")
        self.filter_input.setFixedWidth(340)
        self.filter_input.textChanged.connect(self.handle_filter_table)
        sub_bar.addWidget(self.filter_input)
        layout.addLayout(sub_bar)

        # Table & Empty State Stack Container
        table_container = QWidget()
        self.table_stack = QStackedLayout(table_container)
        self.table_stack.setStackingMode(QStackedLayout.StackingMode.StackAll)

        self.table_widget = QTableWidget()
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setStyleSheet(
            "QTableWidget { selection-background-color: #ede9fe; selection-color: #4c1d95; } "
            "QTableWidget::item:selected { background-color: #ede9fe; color: #4c1d95; font-weight: 500; }"
        )
        self.table_widget.itemSelectionChanged.connect(self.handle_selection_changed)
        self.table_widget.cellDoubleClicked.connect(lambda r, c: self.proceed_to_form_requested.emit())
        self.table_stack.addWidget(self.table_widget)

        # Empty State Overlay when search finds 0 matches
        self.empty_state_widget = QWidget()
        self.empty_state_widget.setObjectName("emptyStateWidget")
        self.empty_state_widget.setStyleSheet(
            "#emptyStateWidget { background-color: rgba(255, 255, 255, 0.96); border: 1.5px solid #e2e8f0; border-radius: 6px; }"
        )
        empty_layout = QVBoxLayout(self.empty_state_widget)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(12)

        icon_empty = QLabel()
        icon_empty.setPixmap(get_pixmap("search", color="#4c1d95", size=48))
        icon_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_empty)

        lbl_empty_title = QLabel("ไม่พบคดีที่ตรงกับคำค้นหา")
        lbl_empty_title.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e293b;")
        lbl_empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(lbl_empty_title)

        lbl_empty_hint = QLabel("ลองตรวจสอบคำสะกด หรือกดปุ่มด้านล่างเพื่อแสดงรายการคดีทั้งหมด")
        lbl_empty_hint.setStyleSheet("font-size: 13px; color: #64748b;")
        lbl_empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(lbl_empty_hint)

        self.btn_clear_search = QPushButton("ล้างคำค้นหา")
        self.btn_clear_search.setObjectName("secondaryButton")
        self.btn_clear_search.setIcon(get_icon("rotate-ccw", color="#4c1d95", size=14))
        self.btn_clear_search.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 6px; padding: 7px 18px; font-weight: 600; font-size: 14px; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        self.btn_clear_search.clicked.connect(self.clear_search)
        empty_layout.addWidget(self.btn_clear_search, alignment=Qt.AlignmentFlag.AlignCenter)

        self.table_stack.addWidget(self.empty_state_widget)
        self.empty_state_widget.hide()

        layout.addWidget(table_container)

        lbl_hint = QLabel('คำแนะนำ: คลิกเลือกแถวคดีที่ต้องการ แล้วกดปุ่ม "ต่อไป: เลือกประเภทเอกสาร" หรือดับเบิลคลิกที่แถวคดีโดยตรง')
        lbl_hint.setObjectName("helperText")
        layout.addWidget(lbl_hint)

    def clear_search(self):
        """Clear filter search input and restore focus."""
        self.filter_input.clear()
        self.filter_input.setFocus()

    def set_table_data(self, headers: List[str], rows: List[Dict[str, Any]], filename: str, mapping: Dict[str, str]):
        self.excel_rows = rows
        self.table_widget.clear()
        if hasattr(self, 'empty_state_widget'):
            self.empty_state_widget.hide()
        if not rows:
            self.lbl_table_status.setText("ไม่พบข้อมูลคดีในไฟล์ Excel")
            return

        cols = list(rows[0].keys())
        self.table_widget.setColumnCount(len(cols))
        self.table_widget.setRowCount(len(rows))
        self.table_widget.setHorizontalHeaderLabels(cols)
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_widget.horizontalHeader().setStretchLastSection(True)

        for r_idx, r_data in enumerate(rows):
            for c_idx, col_name in enumerate(cols):
                val = r_data.get(col_name, "")
                item = QTableWidgetItem(str(val))
                item.setData(Qt.ItemDataRole.UserRole, r_idx)
                self.table_widget.setItem(r_idx, c_idx, item)

        self.table_widget.resizeColumnsToContents()
        for c in range(len(cols)):
            if self.table_widget.columnWidth(c) < 90:
                self.table_widget.setColumnWidth(c, 90)

        mapped_black = mapping.get('case_black_no')
        mapped_red = mapping.get('case_red_no')
        status_text = f"ไฟล์: {filename} (พบ {len(rows)} คดี, {len(headers)} คอลัมน์ที่มีข้อมูล)"
        default_court = storage_service.get_default_court_name()
        if default_court:
            status_text += f" | ศาล: {default_court}"
        if mapped_black:
            status_text += f" | คดีดำ: {mapped_black}"
        if mapped_red:
            status_text += f" | คดีแดง: {mapped_red}"
        self._base_status_text = status_text
        self.lbl_table_status.setText(status_text)

        self.table_widget.selectRow(0)

    def handle_filter_table(self, query: str):
        q = query.strip().lower()
        total_rows = self.table_widget.rowCount()
        if not q:
            for r in range(total_rows):
                self.table_widget.setRowHidden(r, False)
            if hasattr(self, '_base_status_text'):
                self.lbl_table_status.setText(self._base_status_text)
            if hasattr(self, 'empty_state_widget'):
                self.empty_state_widget.hide()
            return

        visible_count = 0
        first_visible_row = -1
        for r in range(total_rows):
            match = False
            for c in range(self.table_widget.columnCount()):
                item = self.table_widget.item(r, c)
                if item and q in item.text().lower():
                    match = True
                    break
            self.table_widget.setRowHidden(r, not match)
            if match:
                visible_count += 1
                if first_visible_row == -1:
                    first_visible_row = r

        if first_visible_row != -1:
            self.table_widget.selectRow(first_visible_row)
        else:
            self.table_widget.clearSelection()

        # Show empty state overlay if no cases match
        if hasattr(self, 'empty_state_widget'):
            if visible_count == 0:
                self.empty_state_widget.show()
            else:
                self.empty_state_widget.hide()

        self.lbl_table_status.setText(
            f"แสดงผล {visible_count} จากทั้งหมด {total_rows} คดี (คำค้นหา: '{query.strip()}')"
        )

    def handle_selection_changed(self):
        selected_indexes = self.table_widget.selectionModel().selectedRows()
        if not selected_indexes:
            return

        visual_row = selected_indexes[0].row()
        item0 = self.table_widget.item(visual_row, 0)
        orig_idx = item0.data(Qt.ItemDataRole.UserRole) if item0 else visual_row
        if orig_idx is None or orig_idx >= len(self.excel_rows):
            orig_idx = visual_row

        self.row_selected.emit(orig_idx)

    def get_selected_original_index(self) -> Optional[int]:
        selected_indexes = self.table_widget.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        visual_row = selected_indexes[0].row()
        item0 = self.table_widget.item(visual_row, 0)
        orig_idx = item0.data(Qt.ItemDataRole.UserRole) if item0 else visual_row
        return orig_idx

    def showEvent(self, event):
        super().showEvent(event)
        self.table_widget.setFocus()

    def focus_search(self):
        """Smart focus: focus the search input and select existing text."""
        self.filter_input.setFocus()
        self.filter_input.selectAll()

    def set_doc_type(self, doc_type: str):
        self.doc_type = doc_type
        self.btn_next_to_form.setText("ต่อไป: เลือกประเภทเอกสาร")
        self.btn_next_to_form.setToolTip("ไปยังขั้นตอนเลือกประเภทเอกสาร [PgDown หรือ Enter]")

    def handle_compromise_clicked(self):
        if getattr(self, 'doc_type', 'report') == 'compromise':
            self.set_doc_type('report')
            self.doc_type_changed.emit('report')
        else:
            self.set_doc_type('compromise')
            self.doc_type_changed.emit('compromise')
            self.proceed_to_form_requested.emit()

    def get_tutorial_steps(self):
        """Return tutorial steps for Step 2 (Table)."""
        from ui.components.tutorial_overlay import TutorialStep
        return [
            TutorialStep(
                target=self.filter_input,
                title="ค้นหากรองรายการคดี (Ctrl+F)",
                description="พิมพ์เลขคดีดำ, คดีแดง, ชื่อโจทก์ หรือจำเลย เพื่อกรองหาคดีที่ต้องการได้อย่างรวดเร็วแบบทันที",
                preferred_position="bottom"
            ),
            TutorialStep(
                target=self.table_widget,
                title="ตารางแสดงรายการคดี",
                description="คลิกเลือกคดีที่ต้องการจัดทำเอกสาร (หรือดับเบิลคลิกแถวคดีเพื่อไปขั้นตอนถัดไปทันที)",
                preferred_position="top"
            ),
            TutorialStep(
                target=self.btn_next_to_form,
                title="ปุ่มไปยังขั้นตอนถัดไป (Enter)",
                description="เมื่อเลือกแถวคดีเรียบร้อยแล้ว กดปุ่มนี้หรือกด Enter เพื่อไปสู่ขั้นตอนเลือกประเภทเอกสาร",
                preferred_position="bottom"
            )
        ]

