"""
Page 1: Excel File Import with Real Drag & Drop Support
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from icon_service import get_icon, get_pixmap


class DragDropUploadFrame(QFrame):
    """Interactive upload frame supporting visual drag and drop of Excel files."""

    file_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("uploadCardFrame")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                fn = url.toLocalFile()
                if fn.lower().endswith(('.xlsx', '.xls')):
                    self.setProperty("dragOver", True)
                    self.style().unpolish(self)
                    self.style().polish(self)
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)
        event.accept()

    def dropEvent(self, event: QDropEvent):
        self.setProperty("dragOver", False)
        self.style().unpolish(self)
        self.style().polish(self)
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                fn = url.toLocalFile()
                if fn.lower().endswith(('.xlsx', '.xls')) and os.path.exists(fn):
                    event.acceptProposedAction()
                    self.file_dropped.emit(fn)
                    return
        event.ignore()


class ImportPage(QWidget):
    """Step 1: Excel file selection and upload view with Drag & Drop."""

    back_requested = Signal()
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("ขั้นตอนที่ 1: เลือกไฟล์ตารางนัดพิจารณาคดี (Excel)")
        title.setObjectName("stepPageTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_back = QPushButton("กลับหน้าหลัก")
        btn_back.setObjectName("secondaryButton")
        btn_back.setIcon(get_icon("arrow-left", color="#1e3a8a", size=16))
        btn_back.setToolTip("กลับหน้าหลัก [PgUp]")
        btn_back.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(btn_back)
        layout.addLayout(header_layout)

        self.upload_box = DragDropUploadFrame(self)
        self.upload_box.file_dropped.connect(self.file_selected.emit)
        box_layout = QVBoxLayout(self.upload_box)
        box_layout.setContentsMargins(40, 56, 40, 56)
        box_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.setSpacing(18)

        icon = QLabel()
        icon.setPixmap(get_pixmap("file-spreadsheet", color="#1e3a8a", size=60))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(icon)

        lbl_instruct = QLabel("นำเข้าไฟล์ตารางนัดพิจารณาของศาล")
        lbl_instruct.setObjectName("uploadInstructTitle")
        lbl_instruct.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(lbl_instruct)

        lbl_sub = QLabel("ลากไฟล์มาวางที่นี่ หรือกดปุ่มด้านล่างเพื่อเลือกไฟล์ Microsoft Excel (.xlsx)\n(ประมวลผลภายในเครื่อง 100% ปลอดภัยตามมาตรฐานศาลยุติธรรม)")
        lbl_sub.setObjectName("helperText")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_layout.addWidget(lbl_sub)

        self.btn_browse = QPushButton("เลือกไฟล์ Excel จากคอมพิวเตอร์ (.xlsx)...")
        self.btn_browse.setObjectName("primaryButtonLarge")
        self.btn_browse.setIcon(get_icon("folder-open", color="#ffffff", size=20))
        self.btn_browse.setToolTip("เลือกไฟล์จากคอมพิวเตอร์ [Ctrl+O]")
        self.btn_browse.clicked.connect(self.handle_browse_file)
        box_layout.addWidget(self.btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.upload_box)
        layout.addStretch()

    def get_tutorial_steps(self):
        """Return tutorial steps for Step 1."""
        from ui.components.tutorial_overlay import TutorialStep
        return [
            TutorialStep(
                target=self.upload_box,
                title="พื้นที่ลากวางไฟล์บัญชีนัด (Drag & Drop)",
                description="ท่านสามารถลากไฟล์ตารางนัด Excel (.xlsx หรือ .xls) จากหน้าต่างคอมพิวเตอร์มาปล่อยลงในกรอบนี้ได้ทันที",
                preferred_position="bottom"
            ),
            TutorialStep(
                target=self.btn_browse,
                title="ปุ่มเลือกไฟล์จากเครื่อง (Ctrl+O)",
                description="หรือคลิกปุ่มนี้เพื่อค้นหาและเลือกไฟล์ Excel จากโฟลเดอร์ในเครื่อง ระบบจะประมวลผลภายในเครื่อง 100% ปลอดภัยตามมาตรฐานศาลยุติธรรม",
                preferred_position="bottom"
            )
        ]

    def trigger_file_dialog(self):
        """Programmatically trigger file browse dialog via keyboard shortcut."""
        self.handle_browse_file()

    def handle_browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "เลือกไฟล์ตารางนัดพิจารณา", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_selected.emit(file_path)
