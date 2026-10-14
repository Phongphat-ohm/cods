"""
Sidebar Navigation Component for JADS
Official, clean, and responsive navigation panel adhering to Court of Justice standards.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal
import storage_service
from icon_service import get_icon, get_pixmap, get_app_logo_pixmap


class SidebarWidget(QFrame):
    """Left navigation panel with brand, navigation buttons, and step indicators."""

    step_navigation_requested = Signal(int)
    template_manager_requested = Signal()
    bench_manager_requested = Signal()
    signatory_roles_requested = Signal()
    court_settings_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setFixedWidth(270)
        self.setStyleSheet("""
            #sidebarButton[active="true"] {
                background-color: #f5f3ff;
                color: #4c1d95;
                border: 1.5px solid #ddd6fe;
                border-radius: 6px;
                font-weight: 600;
            }
            #stepIndicator[current="true"] {
                color: #4c1d95;
                font-weight: 600;
                background-color: #f5f3ff;
                border: 1px solid #ddd6fe;
            }
            #sidebarCourtBadge {
                background-color: #f5f3ff;
                border: 1px solid #ddd6fe;
                border-radius: 6px;
            }
            #sidebarCourtName {
                font-size: 13px;
                font-weight: 600;
                color: #4c1d95;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 24, 18, 22)
        layout.setSpacing(10)

        # Brand Header with App Logo
        h_brand = QHBoxLayout()
        h_brand.setSpacing(12)
        h_brand.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        brand_logo = QLabel()
        brand_logo.setPixmap(get_app_logo_pixmap(size=44))
        brand_logo.setFixedSize(44, 44)
        brand_logo.setScaledContents(True)
        h_brand.addWidget(brand_logo)

        v_brand_text = QVBoxLayout()
        v_brand_text.setSpacing(2)
        brand_label = QLabel("ระบบงานศาล (JADS)")
        brand_label.setObjectName("brandLabel")
        brand_sub = QLabel("เครื่องมือช่วยงานธุรการศาลยุติธรรม")
        brand_sub.setObjectName("brandSubLabel")
        v_brand_text.addWidget(brand_label)
        v_brand_text.addWidget(brand_sub)
        h_brand.addLayout(v_brand_text)
        h_brand.addStretch()

        layout.addLayout(h_brand)

        # Court Badge Indicator
        self.court_badge = QFrame()
        self.court_badge.setObjectName("sidebarCourtBadge")
        cb_layout = QHBoxLayout(self.court_badge)
        cb_layout.setContentsMargins(10, 8, 10, 8)
        cb_layout.setSpacing(8)

        icon_court = QLabel()
        icon_court.setPixmap(get_pixmap("landmark", color="#4c1d95", size=15))
        cb_layout.addWidget(icon_court)

        self.lbl_court_name = QLabel()
        self.lbl_court_name.setObjectName("sidebarCourtName")
        self.lbl_court_name.setWordWrap(True)
        cb_layout.addWidget(self.lbl_court_name)
        cb_layout.addStretch()

        layout.addWidget(self.court_badge)
        self.refresh_court_badge()
        layout.addSpacing(10)

        # Section 1: เมนูหลัก
        menu_title = QLabel("เมนูหลัก")
        menu_title.setObjectName("menuSectionTitle")
        layout.addWidget(menu_title)

        self.btn_nav_menu = QPushButton("หน้าหลัก")
        self.btn_nav_menu.setObjectName("sidebarButton")
        self.btn_nav_menu.setIcon(get_icon("landmark", color="#4c1d95", size=18))
        self.btn_nav_menu.clicked.connect(lambda: self.step_navigation_requested.emit(0))
        layout.addWidget(self.btn_nav_menu)

        self.btn_nav_generator = QPushButton("สร้างเอกสารคดี")
        self.btn_nav_generator.setObjectName("sidebarButton")
        self.btn_nav_generator.setIcon(get_icon("file-text", color="#4c1d95", size=18))
        self.btn_nav_generator.clicked.connect(lambda: self.step_navigation_requested.emit(1))
        layout.addWidget(self.btn_nav_generator)

        layout.addSpacing(10)

        # Section 2: คลังข้อมูล & ตั้งค่า
        tools_title = QLabel("คลังข้อมูล & ตั้งค่า")
        tools_title.setObjectName("menuSectionTitle")
        layout.addWidget(tools_title)

        btn_nav_templates = QPushButton("คลัง Template ย่อหน้า")
        btn_nav_templates.setObjectName("sidebarButton")
        btn_nav_templates.setIcon(get_icon("clipboard-list", color="#4c1d95", size=18))
        btn_nav_templates.clicked.connect(self.template_manager_requested.emit)
        layout.addWidget(btn_nav_templates)

        btn_nav_bench = QPushButton("คู่องค์คณะผู้พิพากษา")
        btn_nav_bench.setObjectName("sidebarButton")
        btn_nav_bench.setIcon(get_icon("users", color="#4c1d95", size=18))
        btn_nav_bench.clicked.connect(self.bench_manager_requested.emit)
        layout.addWidget(btn_nav_bench)

        btn_nav_roles = QPushButton("จัดการบทบาทผู้มาศาล")
        btn_nav_roles.setObjectName("sidebarButton")
        btn_nav_roles.setIcon(get_icon("user", color="#4c1d95", size=18))
        btn_nav_roles.clicked.connect(self.signatory_roles_requested.emit)
        layout.addWidget(btn_nav_roles)

        btn_nav_court = QPushButton("ตั้งค่าชื่อศาลเริ่มต้น")
        btn_nav_court.setObjectName("sidebarButton")
        btn_nav_court.setIcon(get_icon("scale", color="#4c1d95", size=18))
        btn_nav_court.clicked.connect(self.court_settings_requested.emit)
        layout.addWidget(btn_nav_court)

        layout.addSpacing(18)

        # Section 3: ขั้นตอนการทำเอกสาร (Step Indicators)
        lbl_steps_title = QLabel("ขั้นตอนการทำเอกสาร")
        lbl_steps_title.setObjectName("menuSectionTitle")
        layout.addWidget(lbl_steps_title)

        self.lbl_step1 = QLabel("1. เลือกไฟล์ตารางนัด (Excel)")
        self.lbl_step1.setObjectName("stepIndicator")
        self.lbl_step2 = QLabel("2. เลือกคดีความ (ตารางนัด)")
        self.lbl_step2.setObjectName("stepIndicator")
        self.lbl_step3 = QLabel("3. เลือกประเภทเอกสาร")
        self.lbl_step3.setObjectName("stepIndicator")
        self.lbl_step4 = QLabel("4. ทำเอกสาร / สร้างไฟล์ Word")
        self.lbl_step4.setObjectName("stepIndicator")

        layout.addWidget(self.lbl_step1)
        layout.addWidget(self.lbl_step2)
        layout.addWidget(self.lbl_step3)
        layout.addWidget(self.lbl_step4)

        layout.addStretch()

        # Offline Status Indicator
        status_box = QFrame()
        status_box.setObjectName("statusBox")
        status_box.setMinimumHeight(64)
        status_box_layout = QVBoxLayout(status_box)
        status_box_layout.setContentsMargins(12, 10, 12, 10)
        status_box_layout.setSpacing(4)

        status_head = QHBoxLayout()
        status_head.setSpacing(6)
        lbl_status_icon = QLabel()
        lbl_status_icon.setPixmap(get_pixmap("status-dot", color="#16a34a", size=10))
        lbl_status_dot = QLabel("ระบบประมวลผลภายในเครื่อง")
        lbl_status_dot.setObjectName("statusDot")
        status_head.addWidget(lbl_status_icon)
        status_head.addWidget(lbl_status_dot)
        status_head.addStretch()
        status_box_layout.addLayout(status_head)

        lbl_status_desc = QLabel("รักษาความมั่นคงปลอดภัยตามมาตรฐานศาลยุติธรรม (Air-Gapped)")
        lbl_status_desc.setObjectName("statusDesc")
        lbl_status_desc.setWordWrap(True)
        status_box_layout.addWidget(lbl_status_desc)

        layout.addWidget(status_box)

    def set_current_step(self, step_idx: int):
        """Update active states on sidebar buttons and step labels."""
        self.btn_nav_menu.setProperty("active", step_idx == 0)
        self.btn_nav_generator.setProperty("active", step_idx > 0)
        for btn in [self.btn_nav_menu, self.btn_nav_generator]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self.lbl_step1.setProperty("current", step_idx == 1)
        self.lbl_step2.setProperty("current", step_idx == 2)
        self.lbl_step3.setProperty("current", step_idx == 3)
        self.lbl_step4.setProperty("current", step_idx == 4)
        for lbl in [self.lbl_step1, self.lbl_step2, self.lbl_step3, self.lbl_step4]:
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

    def refresh_court_badge(self, court_name=None):
        """Update court name badge from parameter or configuration."""
        c = court_name if court_name is not None else storage_service.get_default_court_name()
        if c:
            self.lbl_court_name.setText(c)
        else:
            self.lbl_court_name.setText("ยังไม่ได้กำหนดชื่อศาล")
