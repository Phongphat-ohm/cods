"""
Page 3: Document Type Selection Page
Allows user to select document type (รายงานกระบวนพิจารณา vs คำพิพากษาตามยอม) for the selected case.
"""

from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from icon_service import get_icon, get_pixmap


class SelectableDocTypeCard(QFrame):
    """Interactive selectable card for document type selection with judicial styling."""
    chosen = Signal()

    def __init__(self, title: str, badge_text: str, icon_name: str,
                 desc: str, features: List[str], btn_text: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("selectableDocCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame#selectableDocCard {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 12px;
            }
            QFrame#selectableDocCard:hover {
                border: 2px solid #5b21b6;
                background-color: #faf5ff;
            }
            QFrame#selectableDocCard[active="true"] {
                border: 2.5px solid #4c1d95;
                background-color: #f5f3ff;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(14)

        # Header with icon & title + badge
        header_lay = QHBoxLayout()
        header_lay.setSpacing(14)

        icon_box = QFrame()
        icon_box.setFixedSize(52, 52)
        icon_box.setStyleSheet("""
            background-color: #f5f3ff;
            border: 1px solid #ddd6fe;
            border-radius: 10px;
        """)
        ib_lay = QVBoxLayout(icon_box)
        ib_lay.setContentsMargins(0, 0, 0, 0)
        ib_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon = QLabel()
        lbl_icon.setPixmap(get_pixmap(icon_name, color="#4c1d95", size=30))
        ib_lay.addWidget(lbl_icon)
        header_lay.addWidget(icon_box)

        v_titles = QVBoxLayout()
        v_titles.setSpacing(4)
        h_badge = QHBoxLayout()
        h_badge.setSpacing(6)
        lbl_badge = QLabel(badge_text)
        lbl_badge.setStyleSheet("""
            font-size: 11.5px;
            font-weight: 600;
            color: #4c1d95;
            background-color: #ede9fe;
            border-radius: 4px;
            padding: 3px 9px;
        """)
        h_badge.addWidget(lbl_badge)
        h_badge.addStretch()
        v_titles.addLayout(h_badge)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a;")
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
        v_feats.setSpacing(8)
        for feat in features:
            h_f = QHBoxLayout()
            h_f.setSpacing(8)
            f_icon = QLabel()
            f_icon.setPixmap(get_pixmap("check", color="#16a34a", size=15))
            f_lbl = QLabel(feat)
            f_lbl.setStyleSheet("font-size: 13px; color: #334155; font-weight: 500;")
            h_f.addWidget(f_icon)
            h_f.addWidget(f_lbl, 1)
            v_feats.addLayout(h_f)
        lay.addLayout(v_feats)

        lay.addStretch()

        self.chk_online = None

        # Selection Action Button
        btn = QPushButton(btn_text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIcon(get_icon("arrow-right", color="#ffffff", size=16))
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 15px;
                font-weight: 600;
                padding: 12px 20px;
                border-radius: 8px;
                border: 1px solid #3b0764;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
        """)
        btn.clicked.connect(self.chosen.emit)
        lay.addWidget(btn)

    def add_online_checkbox(self, text: str = "ออนไลน์ (ดำเนินกระบวนพิจารณาผ่านจอภาพ)") -> QCheckBox:
        """Add an online checkbox right above the action button."""
        chk = QCheckBox(text)
        chk.setCursor(Qt.CursorShape.PointingHandCursor)
        chk.setStyleSheet("""
            QCheckBox {
                font-size: 13.5px;
                font-weight: 600;
                color: #4c1d95;
                spacing: 8px;
                padding: 7px 12px;
                background-color: #f5f3ff;
                border: 1.5px solid #ddd6fe;
                border-radius: 7px;
            }
            QCheckBox:hover {
                background-color: #ede9fe;
                border-color: #c4b5fd;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        # Insert right before action button
        self.layout().insertWidget(self.layout().count() - 1, chk)
        self.chk_online = chk
        return chk

    def set_active(self, is_active: bool):
        self.setProperty("active", is_active)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.chosen.emit()
        super().mousePressEvent(event)


class DocTypePage(QWidget):
    """Step 3: Choose document type for the selected case."""

    back_requested = Signal()
    doc_type_selected = Signal(str, bool)  # (doc_type: "report"|"compromise", is_online: bool)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.selected_type: str = "report"
        self.is_online_report: bool = False
        self.init_ui()


    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #ffffff; }")

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 26, 40, 26)
        layout.setSpacing(18)

        # Header Bar
        header_layout = QHBoxLayout()
        title = QLabel("ขั้นตอนที่ 3: เลือกประเภทเอกสารที่ต้องการจัดทำ")
        title.setObjectName("stepPageTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        btn_back = QPushButton("ย้อนกลับ: เลือกคดี (ตาราง)")
        btn_back.setObjectName("secondaryButton")
        btn_back.setIcon(get_icon("arrow-left", color="#4c1d95", size=16))
        btn_back.setStyleSheet(
            "QPushButton { border: 1.5px solid #cbd5e1; border-radius: 6px; padding: 9px 16px; font-weight: 500; font-size: 14px; background: #ffffff; color: #1e293b; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; color: #4c1d95; }"
        )
        btn_back.setToolTip("ย้อนกลับไปยังตารางเลือกคดี [PgUp]")
        btn_back.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(btn_back)
        layout.addLayout(header_layout)

        # Selected Case Info Banner
        self.info_banner = QFrame()
        self.info_banner.setObjectName("selectedCaseBanner")
        self.info_banner.setStyleSheet("""
            QFrame#selectedCaseBanner {
                background-color: #faf5ff;
                border: 1.5px solid #ddd6fe;
                border-radius: 10px;
            }
        """)
        banner_layout = QVBoxLayout(self.info_banner)
        banner_layout.setContentsMargins(20, 16, 20, 16)
        banner_layout.setSpacing(8)

        b_top = QHBoxLayout()
        b_top.setSpacing(10)
        icon_case = QLabel()
        icon_case.setPixmap(get_pixmap("folder", color="#4c1d95", size=22))
        b_top.addWidget(icon_case)

        lbl_lead = QLabel("ข้อมูลคดีที่เลือกสำหรับจัดทำเอกสาร:")
        lbl_lead.setStyleSheet("font-size: 14px; font-weight: 700; color: #4c1d95;")
        b_top.addWidget(lbl_lead)
        b_top.addStretch()
        banner_layout.addLayout(b_top)

        # Case details row
        self.lbl_case_summary = QLabel("ยังไม่ได้เลือกคดี")
        self.lbl_case_summary.setStyleSheet("font-size: 14px; color: #1e293b; font-weight: 500; line-height: 1.5;")
        self.lbl_case_summary.setWordWrap(True)
        banner_layout.addWidget(self.lbl_case_summary)

        self.lbl_parties_summary = QLabel("")
        self.lbl_parties_summary.setStyleSheet("font-size: 13.5px; color: #475569;")
        self.lbl_parties_summary.setWordWrap(True)
        banner_layout.addWidget(self.lbl_parties_summary)

        layout.addWidget(self.info_banner)

        lbl_instruction = QLabel("กรุณาเลือกประเภทเอกสารที่ต้องการสร้าง:")
        lbl_instruction.setStyleSheet("font-size: 15px; font-weight: 600; color: #334155; margin-top: 4px;")
        layout.addWidget(lbl_instruction)

        # Document Option Cards Container
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(24)

        # Card 1: รายงานกระบวนพิจารณา
        self.card_report = SelectableDocTypeCard(
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
        self.chk_online = self.card_report.add_online_checkbox("ออนไลน์ (ดำเนินกระบวนพิจารณาผ่านจอภาพ)")
        self.chk_online.toggled.connect(self._on_online_toggled)
        self.card_report.chosen.connect(lambda: self.select_doc_type("report"))
        cards_layout.addWidget(self.card_report, 1)

        # Card 2: คำพิพากษาตามยอม
        self.card_comp = SelectableDocTypeCard(
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
        self.card_comp.chosen.connect(lambda: self.select_doc_type("compromise"))
        cards_layout.addWidget(self.card_comp, 1)

        layout.addLayout(cards_layout, 1)
        layout.addStretch()

        scroll_area.setWidget(content)
        root_layout.addWidget(scroll_area)

    def _on_online_toggled(self, checked: bool):
        self.is_online_report = checked

    def set_case_info(self, case_data: Dict[str, Any], mapping: Dict[str, str]):
        """Populate case summary details in banner."""
        if not case_data:
            self.lbl_case_summary.setText("ยังไม่ได้เลือกคดี")
            self.lbl_parties_summary.setText("")
            return

        black_col = mapping.get('case_black_no', '')
        red_col = mapping.get('case_red_no', '')
        plaintiff_col = mapping.get('plaintiff', '')
        defendant_col = mapping.get('defendant', '')
        case_type_col = mapping.get('case_type', '')
        hearing_col = mapping.get('hearing_purpose', '')

        black_no = str(case_data.get(black_col, '')).strip() if black_col else ''
        red_no = str(case_data.get(red_col, '')).strip() if red_col else ''
        plaintiff = str(case_data.get(plaintiff_col, '')).strip() if plaintiff_col else ''
        defendant = str(case_data.get(defendant_col, '')).strip() if defendant_col else ''
        case_type = str(case_data.get(case_type_col, '')).strip() if case_type_col else ''
        hearing = str(case_data.get(hearing_col, '')).strip() if hearing_col else ''

        # Fallbacks if columns weren't in mapping
        if not black_no:
            for k, v in case_data.items():
                if 'ดำ' in k and v:
                    black_no = str(v).strip()
                    break

        case_parts = []
        if black_no:
            case_parts.append(f"<b>คดีหมายเลขดำที่:</b> {black_no}")
        if red_no:
            case_parts.append(f"<b>คดีหมายเลขแดงที่:</b> {red_no}")
        if case_type:
            case_parts.append(f"<b>ประเภทคดี:</b> {case_type}")
        if hearing:
            case_parts.append(f"<b>เหตุที่นัด:</b> {hearing}")

        self.lbl_case_summary.setText(" &nbsp;&nbsp;|&nbsp;&nbsp; ".join(case_parts) if case_parts else "คดีความที่เลือก")

        parties = []
        if plaintiff:
            parties.append(f"<b>โจทก์:</b> {plaintiff}")
        if defendant:
            parties.append(f"<b>จำเลย:</b> {defendant}")
        self.lbl_parties_summary.setText(" &nbsp;&nbsp;|&nbsp;&nbsp; ".join(parties))

    def set_selected_type(self, doc_type: str, is_online: Optional[bool] = None):
        self.selected_type = doc_type
        if is_online is not None and hasattr(self, 'chk_online'):
            self.chk_online.blockSignals(True)
            self.chk_online.setChecked(is_online)
            self.chk_online.blockSignals(False)
            self.is_online_report = is_online

        if doc_type == "compromise":
            self.card_comp.set_active(True)
            self.card_report.set_active(False)
        else:
            self.card_report.set_active(True)
            self.card_comp.set_active(False)

    def select_doc_type(self, doc_type: str):
        self.set_selected_type(doc_type)
        is_online = self.is_online_report if doc_type == "report" else False
        self.doc_type_selected.emit(doc_type, is_online)


    def get_tutorial_steps(self):
        """Return tutorial steps for Step 3 (Doc Type Selection)."""
        from ui.components.tutorial_overlay import TutorialStep
        return [
            TutorialStep(
                target=self.card_report,
                title="รายงานกระบวนพิจารณา",
                description="สำหรับบันทึกกระบวนพิจารณาคดีทั่วไปประจำวัน เช่น นัดพร้อม, สืบพยาน, เลื่อนคดี, ฟังคำสั่ง/คำพิพากษา พร้อมผู้มาศาลและองค์คณะ",
                preferred_position="bottom"
            ),
            TutorialStep(
                target=self.card_comp,
                title="คำพิพากษาตามยอม",
                description="สำหรับคดีที่มีการทำสัญญาประนีประนอมยอมความ รองรับการระบุข้อหาแห่งคดี สัญญาฉบับลงวันที่ และคำสั่งคืนเงินค่าขึ้นศาล",
                preferred_position="bottom"
            )
        ]
