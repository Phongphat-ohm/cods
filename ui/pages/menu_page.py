"""
Page 0: Main Menu & Dashboard
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QFrame,
    QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from icon_service import get_icon, get_pixmap, get_app_logo_pixmap
import storage_service
from constants import APP_NAME, APP_VERSION


class ClickableDocCard(QFrame):
    """Clickable card container for document type selection."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("docTypeCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MenuPage(QWidget):
    """Main menu and dashboard landing page."""

    start_requested = Signal()
    template_manager_requested = Signal()
    bench_manager_requested = Signal()
    signatory_roles_requested = Signal()
    court_settings_requested = Signal()
    about_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Wrap main content with QScrollArea to prevent cards squeezing on small screens
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #ffffff; } QScrollArea > QWidget > QWidget { background-color: #ffffff; }")

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(18)

        # Welcome Header with App Logo
        header_layout = QHBoxLayout()
        header_layout.setSpacing(18)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        logo_label = QLabel()
        logo_label.setPixmap(get_app_logo_pixmap(size=64))
        logo_label.setFixedSize(64, 64)
        logo_label.setScaledContents(True)
        header_layout.addWidget(logo_label)

        v_title = QVBoxLayout()
        v_title.setSpacing(4)
        title = QLabel("ระบบงานศาล (CODS) - โปรแกรมสร้างรายงานกระบวนพิจารณาคดี")
        title.setObjectName("welcomeTitle")
        subtitle = QLabel("โปรแกรมช่วยเจ้าหน้าที่ธุรการศาลจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม จากตารางนัด Excel สู่ไฟล์ Word อย่างรวดเร็ว ปลอดภัยแบบออฟไลน์ 100%")
        subtitle.setObjectName("welcomeSubtitle")
        self.lbl_sub = subtitle
        v_title.addWidget(title)
        v_title.addWidget(subtitle)
        header_layout.addLayout(v_title)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        layout.addSpacing(6)

        # Section 1: เริ่มสร้างเอกสาร
        lbl_sec_docs = QLabel("ระบบจัดทำเอกสารคดี")
        lbl_sec_docs.setStyleSheet("font-size: 16px; font-weight: 600; color: #4c1d95;")
        layout.addWidget(lbl_sec_docs)

        docs_cards_layout = QVBoxLayout()
        docs_cards_layout.setSpacing(16)

        # Card: เริ่มสร้างเอกสาร
        card_report = ClickableDocCard()
        self.card_report = card_report
        card_report.setStyleSheet(
            "QFrame#docTypeCard { background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 12px; } "
            "QFrame#docTypeCard:hover { border: 1.5px solid #4c1d95; background-color: #faf5ff; }"
        )
        card_report.clicked.connect(self.start_requested.emit)
        c1_layout = QVBoxLayout(card_report)
        c1_layout.setContentsMargins(24, 20, 24, 20)
        c1_layout.setSpacing(12)

        c1_header = QHBoxLayout()
        c1_header.setSpacing(14)
        icon_box1 = QLabel()
        icon_box1.setPixmap(get_pixmap("file-text", color="#4c1d95", size=38))
        c1_header.addWidget(icon_box1)

        v_doc1_title = QVBoxLayout()
        v_doc1_title.setSpacing(3)
        h_tags1 = QHBoxLayout()
        h_tags1.setSpacing(8)
        lbl_badge_1 = QLabel("ระบบสร้างเอกสาร")
        lbl_badge_1.setObjectName("docTypeBadge")
        lbl_badge_1.setStyleSheet("background-color: #4c1d95; color: #ffffff; font-size: 13px; font-weight: 600; padding: 4px 12px; border-radius: 12px;")
        lbl_status_1 = QLabel("พร้อมใช้งาน")
        lbl_status_1.setObjectName("docTypeStatusBadge")
        h_tags1.addWidget(lbl_badge_1)
        h_tags1.addWidget(lbl_status_1)
        h_tags1.addStretch()
        v_doc1_title.addLayout(h_tags1)

        lbl_doc1_name = QLabel("สร้างเอกสารจากตารางนัด")
        lbl_doc1_name.setObjectName("docTypeTitle")
        v_doc1_title.addWidget(lbl_doc1_name)
        c1_header.addLayout(v_doc1_title, 1)

        btn_start_1 = QPushButton("สร้างเอกสารจากตารางนัด")
        btn_start_1.setObjectName("primaryButtonLarge")
        btn_start_1.setIcon(get_icon("arrow-right", color="#ffffff", size=16))
        btn_start_1.setToolTip("เริ่มต้นจัดทำเอกสารคดีจากตารางนัด Excel [PgDown]")
        btn_start_1.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; border: 1px solid #3b0764; border-radius: 8px; padding: 13px 26px; font-weight: 600; font-size: 16px; } "
            "QPushButton:hover { background-color: #5b21b6; } "
            "QPushButton:pressed { background-color: #3b0764; }"
        )
        btn_start_1.clicked.connect(self.start_requested.emit)
        self.btn_start_1 = btn_start_1
        c1_header.addWidget(btn_start_1)
        c1_layout.addLayout(c1_header)

        lbl_desc_1 = QLabel(
            "จัดทำและส่งออกเอกสารคดีศาลยุติธรรม ทั้งรายงานกระบวนพิจารณา และคำพิพากษาตามยอม โดยนำเข้าข้อมูลจากตารางนัด Excel (.xlsx) "
            "จัดการข้อมูลคดี องค์คณะผู้พิพากษา และจัดทำเนื้อหาเอกสาร แล้วส่งออกเป็นไฟล์ Word (.docx)"
        )
        lbl_desc_1.setObjectName("docTypeDesc")
        lbl_desc_1.setWordWrap(True)
        c1_layout.addWidget(lbl_desc_1)

        h_pills_1 = QHBoxLayout()
        h_pills_1.setSpacing(6)
        for p_text in ["นำเข้าตารางนัด Excel (.xlsx)", "รายงานกระบวนพิจารณา", "คำพิพากษาตามยอม", "ส่งออกไฟล์ Word (.docx)"]:
            lbl_p = QLabel(p_text)
            lbl_p.setObjectName("docTypeFeaturePill")
            h_pills_1.addWidget(lbl_p)
        h_pills_1.addStretch()
        c1_layout.addLayout(h_pills_1)
        docs_cards_layout.addWidget(card_report)

        layout.addLayout(docs_cards_layout)

        layout.addSpacing(6)

        # Section 2: คลังข้อมูลและการตั้งค่าระบบ
        self.lbl_sec_utils = QLabel("คลังข้อมูลและการตั้งค่าระบบ")
        self.lbl_sec_utils.setStyleSheet("font-size: 16px; font-weight: 600; color: #475569;")
        layout.addWidget(self.lbl_sec_utils)

        # 2x2 Sub Cards Container
        sub_cards_layout = QGridLayout()
        sub_cards_layout.setSpacing(16)

        # Card 2: จัดการ Template
        self.card_tpl = QFrame()
        self.card_tpl.setObjectName("menuSubCardFrame")
        self.card_tpl.setStyleSheet(
            "QFrame#menuSubCardFrame { background-color: #fcfaff; border: 1.5px solid #f3e8ff; border-radius: 10px; } "
            "QFrame#menuSubCardFrame:hover { border-color: #d8b4fe; background-color: #ffffff; }"
        )
        c2_layout = QVBoxLayout(self.card_tpl)
        c2_layout.setContentsMargins(20, 18, 20, 18)
        c2_layout.setSpacing(10)

        c2_header = QHBoxLayout()
        icon2 = QLabel()
        icon2.setPixmap(get_pixmap("clipboard-list", color="#4c1d95", size=26))
        title2 = QLabel("จัดการ Template ย่อหน้าส่วนตัว")
        title2.setObjectName("cardSubTitle")
        c2_header.addWidget(icon2)
        c2_header.addWidget(title2)
        c2_header.addStretch()
        c2_layout.addLayout(c2_header)

        desc2 = QLabel("จัดเก็บแบบข้อความกระบวนพิจารณาที่ท่านสร้างขึ้นเอง จัดหมวดหมู่ และนำไปแทรกลงในรายงานได้อย่างถูกต้องและรวดเร็ว")
        desc2.setObjectName("cardDesc")
        desc2.setWordWrap(True)
        c2_layout.addWidget(desc2)
        c2_layout.addStretch()

        self.btn_tpl = QPushButton("เปิดคลัง Template...")
        self.btn_tpl.setObjectName("secondaryButton")
        self.btn_tpl.setIcon(get_icon("clipboard-list", color="#4c1d95", size=15))
        self.btn_tpl.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 6px; padding: 8px 16px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; }"
        )
        self.btn_tpl.setToolTip("เปิดคลังจัดการ Template ย่อหน้าส่วนตัว [Ctrl+T]")
        self.btn_tpl.clicked.connect(self.template_manager_requested.emit)
        c2_layout.addWidget(self.btn_tpl, alignment=Qt.AlignmentFlag.AlignRight)
        sub_cards_layout.addWidget(self.card_tpl, 0, 0)

        # Card 3: คู่องค์คณะ
        self.card_bench = QFrame()
        self.card_bench.setObjectName("menuSubCardFrame")
        self.card_bench.setStyleSheet(
            "QFrame#menuSubCardFrame { background-color: #fcfaff; border: 1.5px solid #f3e8ff; border-radius: 10px; } "
            "QFrame#menuSubCardFrame:hover { border-color: #d8b4fe; background-color: #ffffff; }"
        )
        c3_layout = QVBoxLayout(self.card_bench)
        c3_layout.setContentsMargins(20, 18, 20, 18)
        c3_layout.setSpacing(10)

        c3_header = QHBoxLayout()
        icon3 = QLabel()
        icon3.setPixmap(get_pixmap("users", color="#4c1d95", size=26))
        title3 = QLabel("บันทึกคู่องค์คณะผู้พิพากษา")
        title3.setObjectName("cardSubTitle")
        c3_header.addWidget(icon3)
        c3_header.addWidget(title3)
        c3_header.addStretch()
        c3_layout.addLayout(c3_header)

        desc3 = QLabel("กำหนดคู่องค์คณะผู้พิพากษา (เจ้าของสำนวนและองค์คณะ) เพื่อให้ระบบนำเข้าข้อมูลโดยอัตโนมัติ")
        desc3.setObjectName("cardDesc")
        desc3.setWordWrap(True)
        c3_layout.addWidget(desc3)
        c3_layout.addStretch()

        self.btn_bench = QPushButton("จัดการคู่องค์คณะ...")
        self.btn_bench.setObjectName("secondaryButton")
        self.btn_bench.setIcon(get_icon("users", color="#4c1d95", size=15))
        self.btn_bench.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 6px; padding: 8px 16px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; }"
        )
        self.btn_bench.setToolTip("จัดการคู่องค์คณะผู้พิพากษา [Ctrl+B]")
        self.btn_bench.clicked.connect(self.bench_manager_requested.emit)
        c3_layout.addWidget(self.btn_bench, alignment=Qt.AlignmentFlag.AlignRight)
        sub_cards_layout.addWidget(self.card_bench, 0, 1)

        # Card 4: จัดการบทบาทผู้มาศาล (Quick-Add Chips)
        self.card_roles = QFrame()
        self.card_roles.setObjectName("menuSubCardFrame")
        self.card_roles.setStyleSheet(
            "QFrame#menuSubCardFrame { background-color: #fcfaff; border: 1.5px solid #f3e8ff; border-radius: 10px; } "
            "QFrame#menuSubCardFrame:hover { border-color: #d8b4fe; background-color: #ffffff; }"
        )
        c_roles_layout = QVBoxLayout(self.card_roles)
        c_roles_layout.setContentsMargins(20, 18, 20, 18)
        c_roles_layout.setSpacing(10)

        c_roles_header = QHBoxLayout()
        icon_roles = QLabel()
        icon_roles.setPixmap(get_pixmap("user", color="#4c1d95", size=26))
        title_roles = QLabel("จัดการบทบาทผู้มาศาล (Quick-Add)")
        title_roles.setObjectName("cardSubTitle")
        c_roles_header.addWidget(icon_roles)
        c_roles_header.addWidget(title_roles)
        c_roles_header.addStretch()
        c_roles_layout.addLayout(c_roles_header)

        desc_roles = QLabel("กำหนดปุ่มลัดเลือกบทบาทผู้มาศาล เช่น โจทก์, จำเลย, ทนายความ เพื่อคลิกเลือกชื่อได้อย่างรวดเร็วในหน้าทำเอกสาร")
        desc_roles.setObjectName("cardDesc")
        desc_roles.setWordWrap(True)
        c_roles_layout.addWidget(desc_roles)
        c_roles_layout.addStretch()

        self.btn_roles = QPushButton("จัดการบทบาท...")
        self.btn_roles.setObjectName("secondaryButton")
        self.btn_roles.setIcon(get_icon("user", color="#4c1d95", size=15))
        self.btn_roles.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 6px; padding: 8px 16px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; }"
        )
        self.btn_roles.setToolTip("จัดการปุ่มบทบาทผู้มาศาล (Quick Add Chips)")
        self.btn_roles.clicked.connect(self.signatory_roles_requested.emit)
        c_roles_layout.addWidget(self.btn_roles, alignment=Qt.AlignmentFlag.AlignRight)
        sub_cards_layout.addWidget(self.card_roles, 1, 0)

        # Card 5: ตั้งค่าชื่อศาลเริ่มต้น
        self.card_court = QFrame()
        self.card_court.setObjectName("menuSubCardFrame")
        self.card_court.setStyleSheet(
            "QFrame#menuSubCardFrame { background-color: #fcfaff; border: 1.5px solid #f3e8ff; border-radius: 10px; } "
            "QFrame#menuSubCardFrame:hover { border-color: #d8b4fe; background-color: #ffffff; }"
        )
        c4_layout = QVBoxLayout(self.card_court)
        c4_layout.setContentsMargins(20, 18, 20, 18)
        c4_layout.setSpacing(10)

        c4_header = QHBoxLayout()
        icon4 = QLabel()
        icon4.setPixmap(get_pixmap("scale", color="#4c1d95", size=26))
        title4 = QLabel("ตั้งค่าชื่อศาลเริ่มต้น")
        title4.setObjectName("cardSubTitle")
        c4_header.addWidget(icon4)
        c4_header.addWidget(title4)
        c4_header.addStretch()
        c4_layout.addLayout(c4_header)

        self.lbl_menu_court_desc = QLabel()
        self.lbl_menu_court_desc.setObjectName("cardDesc")
        self.lbl_menu_court_desc.setWordWrap(True)
        self.update_court_description()
        c4_layout.addWidget(self.lbl_menu_court_desc)
        c4_layout.addStretch()

        self.btn_court = QPushButton("ตั้งค่าชื่อศาล...")
        self.btn_court.setObjectName("secondaryButton")
        self.btn_court.setIcon(get_icon("scale", color="#4c1d95", size=15))
        self.btn_court.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 6px; padding: 8px 16px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; }"
        )
        self.btn_court.clicked.connect(self.court_settings_requested.emit)
        c4_layout.addWidget(self.btn_court, alignment=Qt.AlignmentFlag.AlignRight)
        sub_cards_layout.addWidget(self.card_court, 1, 1)

        # Card 6: เกี่ยวกับระบบ (About & System Information)
        self.card_about = QFrame()
        self.card_about.setObjectName("menuSubCardFrame")
        self.card_about.setStyleSheet(
            "QFrame#menuSubCardFrame { background-color: #fcfaff; border: 1.5px solid #f3e8ff; border-radius: 10px; } "
            "QFrame#menuSubCardFrame:hover { border-color: #d8b4fe; background-color: #ffffff; }"
        )
        c5_layout = QVBoxLayout(self.card_about)
        c5_layout.setContentsMargins(20, 18, 20, 18)
        c5_layout.setSpacing(10)

        c5_header = QHBoxLayout()
        icon5 = QLabel()
        icon5.setPixmap(get_pixmap("info", color="#4c1d95", size=26))
        title5 = QLabel(f"เกี่ยวกับระบบ ({APP_NAME} Offline v{APP_VERSION})")
        title5.setObjectName("cardSubTitle")
        c5_header.addWidget(icon5)
        c5_header.addWidget(title5)
        c5_header.addStretch()
        c5_layout.addLayout(c5_header)

        desc5 = QLabel("ตรวจสอบรายละเอียดเวอร์ชัน ประวัติการพัฒนา (Changelog) ความปลอดภัยข้อมูล และเปิดโฟลเดอร์ระบบ")
        desc5.setObjectName("cardDesc")
        desc5.setWordWrap(True)
        c5_layout.addWidget(desc5)
        c5_layout.addStretch()

        self.btn_about = QPushButton("เกี่ยวกับระบบ... [F12]")
        self.btn_about.setObjectName("secondaryButton")
        self.btn_about.setIcon(get_icon("info", color="#4c1d95", size=15))
        self.btn_about.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 6px; padding: 8px 16px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; }"
        )
        self.btn_about.setToolTip("แสดงข้อมูลเกี่ยวกับโปรแกรม ประวัติเวอร์ชัน และโฟลเดอร์ระบบ [F12]")
        self.btn_about.clicked.connect(self.about_requested.emit)
        c5_layout.addWidget(self.btn_about, alignment=Qt.AlignmentFlag.AlignRight)
        sub_cards_layout.addWidget(self.card_about, 2, 0, 1, 2)

        layout.addLayout(sub_cards_layout)
        layout.addStretch()

        scroll_area.setWidget(content_widget)
        root_layout.addWidget(scroll_area)

    def handle_compromise_clicked(self):
        QMessageBox.information(
            self,
            "แจ้งเตือน",
            "ฟังก์ชันสร้างคำพิพากษาตามยอมกำลังอยู่ระหว่างการพัฒนา"
        )

    def showEvent(self, event):
        super().showEvent(event)
        self.update_court_description()

    def update_court_description(self, court_name=None):
        c = court_name if court_name is not None else storage_service.get_default_court_name()
        if c:
            self.lbl_menu_court_desc.setText(f"กำหนดชื่อศาลเริ่มต้นไว้คือ: '{c}' (แสดงในแบบฟอร์มให้อัตโนมัติ)")
            self.lbl_menu_court_desc.setStyleSheet("font-size: 13px; color: #16a34a; font-weight: 500;")
        else:
            self.lbl_menu_court_desc.setText("ยังไม่ได้กำหนดชื่อศาลเริ่มต้น กดปุ่มเพื่อกำหนดชื่อศาลที่จะให้ระบบเติมให้อัตโนมัติ")
            self.lbl_menu_court_desc.setStyleSheet("font-size: 13px; color: #475569;")

    def get_tutorial_steps(self):
        """Spotlight tutorial steps introducing Menu page and the Data Library & Settings tools."""
        from ui.components.tutorial_overlay import TutorialStep
        steps = []
        if hasattr(self, 'card_report') and self.card_report:
            steps.append(TutorialStep(
                target=self.card_report,
                title="1. ระบบจัดทำเอกสารคดี (4 ขั้นตอน)",
                description="คลิกปุ่มนี้หรือกดปุ่ม PgDown เพื่อเริ่มต้นกระบวนการจัดทำเอกสาร โดยระบบจะพาผ่านขั้นตอนนำเข้า Excel -> เลือกคดี -> เลือกประเภทเอกสาร -> สร้างเอกสาร Word",
                preferred_position="bottom"
            ))
        if hasattr(self, 'card_tpl') and self.card_tpl:
            steps.append(TutorialStep(
                target=self.card_tpl,
                title="2. คลัง Template ย่อหน้าส่วนตัว",
                description="คลังเก็บแบบข้อความกระบวนพิจารณาที่ท่านสร้างขึ้นเอง สามารถใส่ตัวแปร {{ชื่อตัวแปร}} เพื่อให้ระบบสแกนสร้างช่องกรอกข้อมูลให้อัตโนมัติในหน้าทำเอกสาร",
                preferred_position="top"
            ))
        if hasattr(self, 'card_bench') and self.card_bench:
            steps.append(TutorialStep(
                target=self.card_bench,
                title="3. บันทึกคู่องค์คณะผู้พิพากษา",
                description="จับคู่ผู้พิพากษาเจ้าของสำนวนและองค์คณะ เมื่อพิมพ์หรือเลือกชื่อผู้พิพากษาคนที่ 1 ระบบจะเติมชื่อองค์คณะคนที่ 2 ให้อัตโนมัติ",
                preferred_position="top"
            ))
        if hasattr(self, 'card_roles') and self.card_roles:
            steps.append(TutorialStep(
                target=self.card_roles,
                title="4. จัดการบทบาทผู้มาศาล (Quick-Add)",
                description="กำหนดและจัดลำดับปุ่มลัดเลือกบทบาทผู้มาศาล เช่น โจทก์, จำเลย, ทนายความ เพื่อคลิกเลือกชื่อได้อย่างรวดเร็วในหน้าทำเอกสาร",
                preferred_position="top"
            ))
        if hasattr(self, 'card_court') and self.card_court:
            steps.append(TutorialStep(
                target=self.card_court,
                title="5. ตั้งค่าชื่อศาลเริ่มต้น",
                description="กำหนดชื่อศาลเริ่มต้นที่จะปรากฏบนหัวรายงานกระบวนพิจารณาและเอกสารทุกฉบับ ไม่ต้องพิมพ์ซ้ำทุกครั้ง",
                preferred_position="top"
            ))
        return steps

