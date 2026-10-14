"""
Document Type Selection Dialog Component
Modal dialog for choosing document generation type:
1. รายงานกระบวนพิจารณา
2. คำพิพากษาตามยอม
Equal visual weight, interactive cards, unified judicial aesthetics.
"""
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PySide6.QtCore import Qt, Signal
from services.icon_service import get_icon, get_pixmap, get_app_logo_icon


class SelectableDocTypeCard(QFrame):
    """Interactive selectable card for document type in modal with balanced design."""
    chosen = Signal()

    def __init__(self, title: str, badge_text: str, icon_name: str,
                 desc: str, features: List[str], btn_text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            SelectableDocTypeCard {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 12px;
            }
            SelectableDocTypeCard:hover {
                border: 2px solid #5b21b6;
                background-color: #faf5ff;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        # Header with icon & title + badge
        header_lay = QHBoxLayout()
        header_lay.setSpacing(12)

        icon_box = QFrame()
        icon_box.setFixedSize(48, 48)
        icon_box.setStyleSheet("""
            background-color: #f5f3ff;
            border: 1px solid #ddd6fe;
            border-radius: 8px;
        """)
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(get_pixmap(icon_name, color="#4c1d95", size=26))
        ib_lay.addWidget(lbl_icon)
        header_lay.addWidget(icon_box)

        v_titles = QVBoxLayout()
        v_titles.setSpacing(4)
        h_badge = QHBoxLayout()
        h_badge.setSpacing(6)
        lbl_badge = QLabel(badge_text)
        lbl_badge.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #4c1d95;
            background-color: #ede9fe;
            border-radius: 4px;
            padding: 2px 8px;
        """)
        h_badge.addWidget(lbl_badge)
        h_badge.addStretch()
        v_titles.addLayout(h_badge)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 17px; font-weight: 700; color: #0f172a;")
        v_titles.addWidget(lbl_t)
        header_lay.addLayout(v_titles, 1)
        lay.addLayout(header_lay)

        # Description
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet("font-size: 13.5px; color: #475569; line-height: 1.45;")
        lbl_desc.setWordWrap(True)
        lay.addWidget(lbl_desc)

        # Features List
        v_feats = QVBoxLayout()
        v_feats.setSpacing(6)
        for feat in features:
            h_f = QHBoxLayout()
            h_f.setSpacing(8)
            f_icon = QLabel()
            f_icon.setPixmap(get_pixmap("check", color="#16a34a", size=14))
            f_lbl = QLabel(feat)
            f_lbl.setStyleSheet("font-size: 13px; color: #334155; font-weight: 500;")
            h_f.addWidget(f_icon)
            h_f.addWidget(f_lbl, 1)
            v_feats.addLayout(h_f)
        lay.addLayout(v_feats)

        lay.addStretch()

        # Selection Action Button
        btn = QPushButton(btn_text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIcon(get_icon("arrow-right", color="#ffffff", size=15))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 14.5px;
                font-weight: 600;
                padding: 11px 18px;
                border-radius: 7px;
                border: 1px solid #3b0764;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                color: #e2e8f0;
            }
        """)
        btn.clicked.connect(self.chosen.emit)
        lay.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.chosen.emit()
        super().mousePressEvent(event)


class DocTypeSelectDialog(QDialog):
    """
    Step 2: Modal dialog for choosing document generation type:
    1. รายงานกระบวนพิจารณา
    2. คำพิพากษาตามยอม
    Equal visual weight, interactive cards, unified judicial aesthetics.
    """
    def __init__(self, filename: str = "", count: int = 0, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("เลือกประเภทเอกสารที่ต้องการจัดทำ - CODS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(760, 520)
        self.selected_type: Optional[str] = None
        self.filename = filename
        self.count = count
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)

        # Title
        lbl_title = QLabel("เลือกประเภทเอกสารที่ต้องการจัดทำ")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a;")
        layout.addWidget(lbl_title)

        # File Info Banner
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1.5px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        info_lay = QHBoxLayout(info_frame)
        info_lay.setContentsMargins(16, 12, 16, 12)
        info_lay.setSpacing(12)

        icon_file = QLabel()
        icon_file.setPixmap(get_pixmap("file-spreadsheet", color="#4c1d95", size=24))
        info_lay.addWidget(icon_file)

        v_info_text = QVBoxLayout()
        v_info_text.setSpacing(2)
        txt_header = f"ไฟล์ตารางนัด: <b>{self.filename}</b> &nbsp;•&nbsp; พบข้อมูลคดีทั้งหมด <b>{self.count}</b> รายการ" if self.filename else "นำเข้าข้อมูลคดีเรียบร้อยแล้ว"
        lbl_file_info = QLabel(txt_header)
        lbl_file_info.setStyleSheet("font-size: 13.5px; color: #1e293b;")
        v_info_text.addWidget(lbl_file_info)

        lbl_instruct = QLabel("ท่านสามารถนำข้อมูลคดีไปจัดทำเอกสารได้ตามรูปแบบที่ต้องการ กรุณาเลือกประเภทเอกสาร:")
        lbl_instruct.setStyleSheet("font-size: 13px; color: #64748b;")
        v_info_text.addWidget(lbl_instruct)
        info_lay.addLayout(v_info_text, 1)

        layout.addWidget(info_frame)

        # 2 Options Cards (Equal Prominence)
        opts_layout = QHBoxLayout()
        opts_layout.setSpacing(18)

        # Option 1: รายงานกระบวนพิจารณา
        card_rep = SelectableDocTypeCard(
            title="รายงานกระบวนพิจารณา",
            badge_text="แบบพิมพ์รายงาน",
            icon_name="file-text",
            desc="จัดทำรายงานกระบวนพิจารณาคดีศาลยุติธรรม บันทึกเหตุที่นัด รายชื่อผู้มาศาล องค์คณะ และกระบวนพิจารณา",
            features=[
                "จัดการรายชื่อผู้มาศาล (โจทก์ จำเลย ทนาย ฯลฯ)",
                "คลัง Template ย่อหน้ากระบวนพิจารณาส่วนตัว",
                "ส่งออกไฟล์ Word (.docx) ตามแบบพิมพ์มาตรฐาน"
            ],
            btn_text="สร้างรายงานกระบวนพิจารณา"
        )
        card_rep.chosen.connect(self.select_report)
        opts_layout.addWidget(card_rep, 1)

        # Option 2: คำพิพากษาตามยอม
        card_comp = SelectableDocTypeCard(
            title="คำพิพากษาตามยอม",
            badge_text="สัญญาประนีประนอม",
            icon_name="scale",
            desc="จัดทำคำพิพากษาตามสัญญาประนีประนอมยอมความ ระบุข้อหาแห่งคดี สัญญาฉบับลงวันที่ และคืนค่าขึ้นศาล",
            features=[
                "ระบุข้อหาแห่งคดี (เรื่อง) และสัญญาฉบับลงวันที่",
                "บันทึกคำสั่งคืนค่าขึ้นศาลเป็นกรณีพิเศษ (บาท)",
                "ส่งออกคำพิพากษาตามยอม (.docx) พร้อมเลขไทย"
            ],
            btn_text="สร้างคำพิพากษาตามยอม"
        )
        card_comp.chosen.connect(self.select_compromise)
        opts_layout.addWidget(card_comp, 1)

        layout.addLayout(opts_layout, 1)

        # Bottom Bar: Cancel Button
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        btn_cancel = QPushButton("ยกเลิก [Esc]")
        btn_cancel.setObjectName("secondaryButton")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #475569;
                font-size: 14px;
                padding: 8px 20px;
                border-radius: 6px;
                border: 1.5px solid #cbd5e1;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_bar.addWidget(btn_cancel)
        layout.addLayout(btn_bar)

    def select_report(self):
        self.selected_type = "report"
        self.accept()

    def select_compromise(self):
        self.selected_type = "compromise"
        self.accept()
