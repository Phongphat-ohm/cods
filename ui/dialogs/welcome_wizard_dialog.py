"""
CODS Welcome Wizard Dialog
First-launch onboarding wizard introducing users to CODS,
summarizing the 4-step workflow, and configuring initial court settings.
"""

from PySide6.QtWidgets import (
    QDialog, QStackedWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QFrame, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap

from services import storage_service, icon_service
from ui.components.judicial_card import JudicialAccentCard


class WelcomeWizardDialog(QDialog):
    """3-step welcome wizard displayed when CODS is launched for the first time."""
    wizard_finished = Signal(str, bool)  # (court_name, enable_tutorials)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ยินดีต้อนรับสู่ CODS")
        self.setFixedSize(680, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 24)
        main_layout.setSpacing(16)

        # 1. Top Header: Logo + App Title
        top_header = QHBoxLayout()
        top_header.setSpacing(14)

        lbl_logo = QLabel(self)
        logo_pm = icon_service.get_app_logo_pixmap(44)
        if logo_pm and not logo_pm.isNull():
            lbl_logo.setPixmap(logo_pm)
        else:
            lbl_logo.setPixmap(icon_service.get_pixmap("balance", "#7e22ce", 40))
        top_header.addWidget(lbl_logo)

        header_text_vbox = QVBoxLayout()
        header_text_vbox.setSpacing(2)

        lbl_title = QLabel("ยินดีต้อนรับสู่ CODS", self)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e1b4b;")
        header_text_vbox.addWidget(lbl_title)

        lbl_subtitle = QLabel("ระบบสนับสนุนการจัดทำเอกสารกระบวนพิจารณาและคำพิพากษาศาลยุติธรรม", self)
        lbl_subtitle.setStyleSheet("font-size: 12px; color: #64748b;")
        header_text_vbox.addWidget(lbl_subtitle)

        top_header.addLayout(header_text_vbox)
        top_header.addStretch()
        main_layout.addLayout(top_header)

        # Divider
        divider = QFrame(self)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #e2e8f0; max-height: 1px;")
        main_layout.addWidget(divider)

        # 2. Stacked Pages
        self.stack = QStackedWidget(self)
        self.stack.addWidget(self._create_intro_page())
        self.stack.addWidget(self._create_workflow_page())
        self.stack.addWidget(self._create_library_page())
        self.stack.addWidget(self._create_setup_page())
        main_layout.addWidget(self.stack, 1)

        # 3. Bottom Navigation & Indicators
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 10, 0, 0)
        bottom_bar.setSpacing(12)

        # Step indicator dots
        self.lbl_dots = QLabel("●  ○  ○  ○", self)
        self.lbl_dots.setStyleSheet("color: #7e22ce; font-size: 14px; font-weight: bold; letter-spacing: 4px;")
        bottom_bar.addWidget(self.lbl_dots)

        bottom_bar.addStretch()

        self.btn_skip = QPushButton("ข้ามการแนะนำ", self)
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 13px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                color: #0f172a;
                text-decoration: underline;
            }
        """)
        self.btn_skip.clicked.connect(self.skip_wizard)
        bottom_bar.addWidget(self.btn_skip)

        self.btn_back = QPushButton("ย้อนกลับ", self)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setFixedHeight(36)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 13px;
                color: #475569;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.btn_back.clicked.connect(self.prev_page)
        self.btn_back.setEnabled(False)
        bottom_bar.addWidget(self.btn_back)

        self.btn_next = QPushButton("ถัดไป →", self)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setFixedHeight(36)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #7e22ce;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
                font-size: 13px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6b21a8;
            }
        """)
        self.btn_next.clicked.connect(self.next_page)
        bottom_bar.addWidget(self.btn_next)

        main_layout.addLayout(bottom_bar)

    def _create_intro_page(self) -> QWidget:
        """Page 1: Introduction & Highlights."""
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(14)

        card = JudicialAccentCard(
            stripe_color="#9333ea",
            border_color="#e9d5ff",
            bg_color="#faf5ff",
            stripe_width=4,
            radius=10,
            parent=page
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(8)

        lbl_lead = QLabel("CODS ออกแบบมาเพื่อช่วยลดภาระงานศาลยุติธรรมโดยเฉพาะ", card)
        lbl_lead.setStyleSheet("font-size: 15px; font-weight: bold; color: #581c87;")
        card_layout.addWidget(lbl_lead)

        lbl_sub = QLabel(
            "ระบบช่วยดึงข้อมูลจากตารางนัดหมาย Excel มาสร้างเอกสารทางตุลาการอย่างเป็นทางการ "
            "โดยประมวลผลบนเครื่องของท่าน 100% ปลอดภัย ปราศจากการเชื่อมต่ออินเทอร์เน็ตภายนอก (Air-Gapped)",
            card
        )
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size: 13px; color: #4b5563; line-height: 1.5;")
        card_layout.addWidget(lbl_sub)
        layout.addWidget(card)

        # Highlight Features
        features = [
            ("⚡", "ออกรายงานกระบวนพิจารณา & คำพิพากษาตามยอม ได้ในคลิกเดียว"),
            ("⚖️", "ระบบจำคู่องค์คณะผู้พิพากษาอัตโนมัติ ไม่ต้องกรอกชื่อซ้ำ"),
            ("📝", "คลังแม่แบบย่อหน้า รองรับตัวแปร {{ชื่อตัวแปร}} สแกนสร้างช่องกรอกสด"),
            ("👥", "จัดการผู้มาศาล พร้อมปุ่มจัดลำดับตามแบบพิธีการศาลไทยอัตโนมัติ")
        ]

        feat_layout = QVBoxLayout()
        feat_layout.setSpacing(10)
        for icon, text in features:
            row = QHBoxLayout()
            row.setSpacing(12)
            lbl_ico = QLabel(icon, page)
            lbl_ico.setStyleSheet("font-size: 16px;")
            row.addWidget(lbl_ico)

            lbl_txt = QLabel(text, page)
            lbl_txt.setStyleSheet("font-size: 13px; color: #334155; font-weight: 500;")
            row.addWidget(lbl_txt, 1)
            feat_layout.addLayout(row)

        layout.addLayout(feat_layout)
        layout.addStretch()
        return page

    def _create_workflow_page(self) -> QWidget:
        """Page 2: 4-Step Workflow Overview."""
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(12)

        lbl_head = QLabel("ขั้นตอนการทำงาน 4 ขั้นตอนง่ายๆ ใน CODS", page)
        lbl_head.setStyleSheet("font-size: 15px; font-weight: bold; color: #1e1b4b;")
        layout.addWidget(lbl_head)

        steps = [
            ("1", "นำเข้าไฟล์บัญชีนัดความ", "ลากไฟล์ตารางนัด Excel (.xlsx, .xls) มาวาง หรือคลิกเลือกไฟล์ (Ctrl+O)"),
            ("2", "ค้นหาและเลือกคดี", "ตารางแสดงคดีทั้งหมด กรองค้นหาเลขคดีหรือชื่อคู่ความได้ทันที (Ctrl+F)"),
            ("3", "เลือกประเภทเอกสาร", "เลือกระหว่าง 'รายงานกระบวนพิจารณา' หรือ 'คำพิพากษาตามยอม'"),
            ("4", "ตรวจสอบและสร้างเอกสาร", "ตรวจชื่อองค์คณะ ผู้มาศาล ย่อหน้า แล้วกดสร้างไฟล์ Word (.docx)")
        ]

        for num, title, desc in steps:
            step_box = QFrame(page)
            step_box.setStyleSheet("""
                QFrame {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                }
            """)
            s_layout = QHBoxLayout(step_box)
            s_layout.setContentsMargins(14, 10, 14, 10)
            s_layout.setSpacing(14)

            badge = QLabel(num, step_box)
            badge.setFixedSize(26, 26)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet("""
                background-color: #7e22ce;
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border-radius: 13px;
            """)
            s_layout.addWidget(badge)

            info_vbox = QVBoxLayout()
            info_vbox.setSpacing(2)
            lbl_stitle = QLabel(title, step_box)
            lbl_stitle.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a;")
            info_vbox.addWidget(lbl_stitle)

            lbl_sdesc = QLabel(desc, step_box)
            lbl_sdesc.setStyleSheet("font-size: 12px; color: #64748b;")
            info_vbox.addWidget(lbl_sdesc)

            s_layout.addLayout(info_vbox, 1)
            layout.addWidget(step_box)

        layout.addStretch()
        return page

    def _create_library_page(self) -> QWidget:
        """Page 3: Data Library & Settings Tools Overview."""
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(10)

        lbl_head = QLabel("คลังข้อมูลและการตั้งค่าระบบ (Data Library & Settings)", page)
        lbl_head.setStyleSheet("font-size: 15px; font-weight: bold; color: #1e1b4b;")
        layout.addWidget(lbl_head)

        lbl_desc = QLabel(
            "CODS มีเครื่องมือคลังข้อมูลและการตั้งค่า ช่วยอำนวยความสะดวกและลดขั้นตอนการทำงานซ้ำซ้อน "
            "(เข้าถึงได้ตลอดเวลาจากทั้งหน้าแรกและแถบเมนูด้านข้าง Sidebar):",
            page
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 13px; color: #475569; line-height: 1.4;")
        layout.addWidget(lbl_desc)

        tools = [
            ("📝", "คลัง Template ย่อหน้า (Ctrl+T)", "จัดเก็บแบบข้อความกระบวนพิจารณาที่ท่านสร้างขึ้นเอง กำหนดตัวแปร {{ชื่อตัวแปร}} เพื่อให้ระบบสร้างช่องกรอกสด"),
            ("⚖️", "คู่องค์คณะผู้พิพากษา (Ctrl+B)", "จับคู่ผู้พิพากษาเจ้าของสำนวนและองค์คณะ เมื่อเลือกผู้พิพากษาคนที่ 1 ระบบจะเติมองค์คณะคนที่ 2 ให้อัตโนมัติ"),
            ("👥", "จัดการบทบาทผู้มาศาล (Quick-Add)", "กำหนดปุ่มลัดเลือกบทบาทผู้มาศาล เช่น โจทก์, จำเลย, ทนายความ เพื่อคลิกเลือกชื่อได้อย่างรวดเร็วในหน้าทำเอกสาร"),
            ("🏛️", "ตั้งค่าชื่อศาลเริ่มต้น", "กำหนดชื่อศาลประจำเครื่องที่จะแสดงบนหัวรายงานกระบวนพิจารณาและเอกสารทุกฉบับ ไม่ต้องพิมพ์ซ้ำ")
        ]

        for icon, title, desc in tools:
            tool_box = QFrame(page)
            tool_box.setStyleSheet("""
                QFrame {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 8px;
                }
            """)
            t_layout = QHBoxLayout(tool_box)
            t_layout.setContentsMargins(12, 8, 12, 8)
            t_layout.setSpacing(12)

            ico_lbl = QLabel(icon, tool_box)
            ico_lbl.setStyleSheet("font-size: 18px;")
            t_layout.addWidget(ico_lbl)

            info_vbox = QVBoxLayout()
            info_vbox.setSpacing(2)
            lbl_title = QLabel(title, tool_box)
            lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #0f172a;")
            info_vbox.addWidget(lbl_title)

            lbl_sub = QLabel(desc, tool_box)
            lbl_sub.setWordWrap(True)
            lbl_sub.setStyleSheet("font-size: 12px; color: #64748b;")
            info_vbox.addWidget(lbl_sub)

            t_layout.addLayout(info_vbox, 1)
            layout.addWidget(tool_box)

        layout.addStretch()
        return page

    def _create_setup_page(self) -> QWidget:
        """Page 3: Quick Initial Setup (Default Court Name)."""
        page = QWidget(self)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(16)

        lbl_head = QLabel("ตั้งค่าเริ่มต้นประจำเครื่องของคุณ", page)
        lbl_head.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e1b4b;")
        layout.addWidget(lbl_head)

        lbl_desc = QLabel(
            "โปรดระบุชื่อศาลของคุณ เช่น 'ศาลจังหวัดนนทบุรี' หรือ 'ศาลแขวงดุสิต' "
            "ระบบจะจำค่านี้ไว้ และนำไปเติมลงในเอกสารทุกฉบับโดยอัตโนมัติ (สามารถเปลี่ยนภายหลังได้)",
            page
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 13px; color: #475569; line-height: 1.5;")
        layout.addWidget(lbl_desc)

        # Court Name Input
        vbox_input = QVBoxLayout()
        vbox_input.setSpacing(6)

        lbl_court = QLabel("ชื่อศาลประจำเครื่อง:", page)
        lbl_court.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b;")
        vbox_input.addWidget(lbl_court)

        self.txt_court = QLineEdit(page)
        self.txt_court.setPlaceholderText("ตัวอย่าง: ศาลจังหวัดนนทบุรี")
        self.txt_court.setFixedHeight(40)
        self.txt_court.setText(storage_service.get_default_court_name())
        self.txt_court.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 14px;
                color: #0f172a;
            }
            QLineEdit:focus {
                border-color: #9333ea;
            }
        """)
        vbox_input.addWidget(self.txt_court)
        layout.addLayout(vbox_input)

        # Checkbox for Step-by-Step Interactive Tours
        self.chk_enable_tours = QCheckBox("เปิดระบบแนะนำการใช้งานแต่ละหน้าจอ (Interactive Spotlight)", page)
        self.chk_enable_tours.setChecked(True)
        self.chk_enable_tours.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_enable_tours.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #334155;
                font-weight: 500;
                margin-top: 10px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid #94a3b8;
            }
            QCheckBox::indicator:checked {
                background-color: #7e22ce;
                border-color: #7e22ce;
            }
        """)
        layout.addWidget(self.chk_enable_tours)

        layout.addStretch()
        return page

    def update_nav(self):
        idx = self.stack.currentIndex()
        self.btn_back.setEnabled(idx > 0)

        dots = ["○", "○", "○", "○"]
        dots[idx] = "●"
        self.lbl_dots.setText(f"{dots[0]}  {dots[1]}  {dots[2]}  {dots[3]}")

        if idx == self.stack.count() - 1:
            self.btn_next.setText("เริ่มต้นใช้งาน CODS  ✓")
            self.btn_next.setStyleSheet("""
                QPushButton {
                    background-color: #16a34a;
                    border: none;
                    border-radius: 6px;
                    padding: 0 20px;
                    font-size: 13px;
                    color: #ffffff;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #15803d;
                }
            """)
            self.txt_court.setFocus()
        else:
            self.btn_next.setText("ถัดไป →")
            self.btn_next.setStyleSheet("""
                QPushButton {
                    background-color: #7e22ce;
                    border: none;
                    border-radius: 6px;
                    padding: 0 20px;
                    font-size: 13px;
                    color: #ffffff;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #6b21a8;
                }
            """)

    def next_page(self):
        curr = self.stack.currentIndex()
        if curr < self.stack.count() - 1:
            self.stack.setCurrentIndex(curr + 1)
            self.update_nav()
        else:
            self.finish_wizard()

    def prev_page(self):
        curr = self.stack.currentIndex()
        if curr > 0:
            self.stack.setCurrentIndex(curr - 1)
            self.update_nav()

    def finish_wizard(self):
        court_name = self.txt_court.text().strip()
        if court_name:
            storage_service.set_default_court_name(court_name)

        storage_service.mark_tutorial_completed("welcome_wizard", True)

        enable_tours = self.chk_enable_tours.isChecked()
        if not enable_tours:
            # Mark all sub-tutorials completed too
            storage_service.mark_tutorial_completed("step_import", True)
            storage_service.mark_tutorial_completed("step_table", True)
            storage_service.mark_tutorial_completed("step_doctype", True)
            storage_service.mark_tutorial_completed("step_form", True)

        self.wizard_finished.emit(court_name, enable_tours)
        self.accept()

    def skip_wizard(self):
        storage_service.mark_tutorial_completed("welcome_wizard", True)
        self.reject()
