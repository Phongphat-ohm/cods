"""
Sidebar Navigation Component for CODS
Official, clean, and responsive navigation panel adhering to Court of Justice standards.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
import storage_service
import constants
from icon_service import get_icon, get_pixmap, get_app_logo_pixmap


class SidebarWidget(QFrame):
    """Left navigation panel with brand, navigation buttons, and step indicators."""

    step_navigation_requested = Signal(int)
    template_manager_requested = Signal()
    bench_manager_requested = Signal()
    signatory_roles_requested = Signal()
    court_settings_requested = Signal()
    tutorial_requested = Signal()
    about_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarFrame")
        self.setFixedWidth(280)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
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
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ---------------------------------------------------------------------
        # 1. FIXED TOP HEADER: Brand Logo, Title & Court Name Badge
        # ---------------------------------------------------------------------
        top_fixed_widget = QWidget()
        top_fixed_widget.setObjectName("sidebarTopFixedWidget")
        top_layout = QVBoxLayout(top_fixed_widget)
        top_layout.setContentsMargins(14, 18, 14, 10)
        top_layout.setSpacing(10)

        # Brand Header with App Logo
        h_brand = QHBoxLayout()
        h_brand.setSpacing(10)
        h_brand.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        brand_logo = QLabel()
        brand_logo.setObjectName("sidebarBrandLogo")
        brand_logo.setPixmap(get_app_logo_pixmap(size=40))
        brand_logo.setFixedSize(40, 40)
        brand_logo.setScaledContents(False)
        brand_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_logo.setStyleSheet("QLabel#sidebarBrandLogo { background: transparent; padding: 0px; border: none; }")
        h_brand.addWidget(brand_logo)

        v_brand_text = QVBoxLayout()
        v_brand_text.setSpacing(2)
        brand_label = QLabel("ระบบงานศาล (CODS)")
        brand_label.setObjectName("brandLabel")
        brand_sub = QLabel("เครื่องมือช่วยงานธุรการศาลยุติธรรม")
        brand_sub.setObjectName("brandSubLabel")
        brand_sub.setToolTip("เครื่องมือช่วยงานธุรการศาลยุติธรรม")
        v_brand_text.addWidget(brand_label)
        v_brand_text.addWidget(brand_sub)
        h_brand.addLayout(v_brand_text, 1)

        top_layout.addLayout(h_brand)

        # Court Badge Indicator (Fixed under brand)
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

        top_layout.addWidget(self.court_badge)
        self.refresh_court_badge()

        # Separator line under fixed header
        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.Shape.HLine)
        sep_line.setFrameShadow(QFrame.Shadow.Plain)
        sep_line.setStyleSheet("QFrame { border: none; border-bottom: 1px solid #e2e8f0; min-height: 1px; max-height: 1px; }")
        top_layout.addWidget(sep_line)

        root_layout.addWidget(top_fixed_widget)

        # ---------------------------------------------------------------------
        # 2. SCROLLABLE NAVIGATION & SETTINGS AREA
        # ---------------------------------------------------------------------
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setObjectName("sidebarScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea#sidebarScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea#sidebarScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollArea#sidebarScrollArea QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollArea#sidebarScrollArea QScrollBar::handle:vertical {
                background: #cbd5e1;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollArea#sidebarScrollArea QScrollBar::handle:vertical:hover {
                background: #94a3b8;
            }
            QScrollArea#sidebarScrollArea QScrollBar::add-line:vertical,
            QScrollArea#sidebarScrollArea QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: none;
            }
            QScrollArea#sidebarScrollArea QScrollBar::add-page:vertical,
            QScrollArea#sidebarScrollArea QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Container widget holding scrollable items
        content_widget = QWidget()
        content_widget.setObjectName("sidebarContentWidget")
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(14, 10, 14, 16)
        layout.setSpacing(10)

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
        self.tools_title = QLabel("คลังข้อมูล & ตั้งค่า")
        self.tools_title.setObjectName("menuSectionTitle")
        layout.addWidget(self.tools_title)

        self.btn_nav_templates = QPushButton("คลัง Template ย่อหน้า")
        self.btn_nav_templates.setObjectName("sidebarButton")
        self.btn_nav_templates.setIcon(get_icon("clipboard-list", color="#4c1d95", size=18))
        self.btn_nav_templates.clicked.connect(self.template_manager_requested.emit)
        layout.addWidget(self.btn_nav_templates)

        self.btn_nav_bench = QPushButton("คู่องค์คณะผู้พิพากษา")
        self.btn_nav_bench.setObjectName("sidebarButton")
        self.btn_nav_bench.setIcon(get_icon("users", color="#4c1d95", size=18))
        self.btn_nav_bench.clicked.connect(self.bench_manager_requested.emit)
        layout.addWidget(self.btn_nav_bench)

        self.btn_nav_roles = QPushButton("จัดการบทบาทผู้มาศาล")
        self.btn_nav_roles.setObjectName("sidebarButton")
        self.btn_nav_roles.setIcon(get_icon("user", color="#4c1d95", size=18))
        self.btn_nav_roles.clicked.connect(self.signatory_roles_requested.emit)
        layout.addWidget(self.btn_nav_roles)

        self.btn_nav_court = QPushButton("ตั้งค่าชื่อศาลเริ่มต้น")
        self.btn_nav_court.setObjectName("sidebarButton")
        self.btn_nav_court.setIcon(get_icon("scale", color="#4c1d95", size=18))
        self.btn_nav_court.clicked.connect(self.court_settings_requested.emit)
        layout.addWidget(self.btn_nav_court)

        self.btn_nav_tutorial = QPushButton("แนะนำการใช้งาน")
        self.btn_nav_tutorial.setObjectName("sidebarButton")
        self.btn_nav_tutorial.setIcon(get_icon("help-circle", color="#4c1d95", size=18))
        self.btn_nav_tutorial.clicked.connect(self.tutorial_requested.emit)
        layout.addWidget(self.btn_nav_tutorial)

        self.btn_nav_about = QPushButton("เกี่ยวกับระบบ (About)")
        self.btn_nav_about.setObjectName("sidebarButton")
        self.btn_nav_about.setIcon(get_icon("info", color="#4c1d95", size=18))
        self.btn_nav_about.clicked.connect(self.about_requested.emit)
        layout.addWidget(self.btn_nav_about)

        layout.addStretch()

        self.scroll_area.setWidget(content_widget)
        root_layout.addWidget(self.scroll_area, 1)

        # ---------------------------------------------------------------------
        # 3. FIXED BOTTOM FOOTER: Green Offline Status Box & Version Footer
        # ---------------------------------------------------------------------
        bottom_fixed_widget = QWidget()
        bottom_fixed_widget.setObjectName("sidebarBottomFixedWidget")
        bottom_layout = QVBoxLayout(bottom_fixed_widget)
        bottom_layout.setContentsMargins(14, 8, 14, 12)
        bottom_layout.setSpacing(6)

        # Separator line above bottom fixed area
        sep_bottom = QFrame()
        sep_bottom.setFrameShape(QFrame.Shape.HLine)
        sep_bottom.setFrameShadow(QFrame.Shadow.Plain)
        sep_bottom.setStyleSheet("QFrame { border: none; border-top: 1px solid #e2e8f0; min-height: 1px; max-height: 1px; margin-bottom: 4px; }")
        bottom_layout.addWidget(sep_bottom)

        # Offline Status Indicator (Green box)
        status_box = QFrame()
        status_box.setObjectName("statusBox")
        status_box.setMinimumHeight(60)
        status_box_layout = QVBoxLayout(status_box)
        status_box_layout.setContentsMargins(12, 9, 12, 9)
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

        lbl_status_desc = QLabel("รักษาความมั่นคงปลอดภัย\nตามมาตรฐานศาลยุติธรรม (Air-Gapped)")
        lbl_status_desc.setObjectName("statusDesc")
        lbl_status_desc.setWordWrap(True)
        status_box_layout.addWidget(lbl_status_desc)

        bottom_layout.addWidget(status_box)

        # Version & About Clickable Footer
        btn_ver_footer = QPushButton(f"{constants.APP_NAME} v{constants.APP_VERSION} • เกี่ยวกับระบบ")
        btn_ver_footer.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ver_footer.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 11.5px;
                font-weight: 500;
                padding: 4px 6px;
                text-align: center;
            }
            QPushButton:hover {
                color: #4c1d95;
                font-weight: 600;
                text-decoration: underline;
            }
        """)
        btn_ver_footer.clicked.connect(self.about_requested.emit)
        bottom_layout.addWidget(btn_ver_footer)

        root_layout.addWidget(bottom_fixed_widget)

    def set_current_step(self, step_idx: int):
        """Update active states on sidebar buttons."""
        self.btn_nav_menu.setProperty("active", step_idx == 0)
        self.btn_nav_generator.setProperty("active", step_idx > 0)
        for btn in [self.btn_nav_menu, self.btn_nav_generator]:
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def refresh_court_badge(self, court_name=None):
        """Update court name badge from parameter or configuration."""
        c = court_name if court_name is not None else storage_service.get_default_court_name()
        if c:
            self.lbl_court_name.setText(c)
        else:
            self.lbl_court_name.setText("ยังไม่ได้กำหนดชื่อศาล")
