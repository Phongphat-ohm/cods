"""
CODSSplashScreen - Modern Judicial Splash & Startup Loading Screen
Displays instantaneous visual feedback, branding, and initialization progress
when launching the 100% offline desktop application.
"""

import os
import sys

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QFrame, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPixmap

from constants import APP_NAME, APP_VERSION


def _get_splash_logo_pixmap(size: int = 64) -> QPixmap:
    """Fast direct PNG loader without initializing vector SVG rendering engines."""
    bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    candidates = [
        os.path.join(bundle_dir, "logo.png"),
        os.path.join(os.getcwd(), "logo.png"),
        os.path.join(os.path.dirname(__file__), "..", "..", "logo.png"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            pix = QPixmap(p)
            if not pix.isNull():
                return pix.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
    return QPixmap()


class CODSSplashScreen(QWidget):
    """
    Frameless, rounded, elegant splash screen styled with the
    CODS Imperial Amethyst judicial theme.
    """

    def __init__(self):
        super().__init__()
        # Set window flags for splash screen: Frameless, stay on top, tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)

        self.setFixedSize(540, 310)
        self.init_ui()
        self.center_on_screen()

    def center_on_screen(self):
        """Center the splash window on the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            x = (screen_geom.width() - self.width()) // 2 + screen_geom.x()
            y = (screen_geom.height() - self.height()) // 2 + screen_geom.y()
            self.move(x, y)

    def init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)

        # Card Container (Light Judicial Theme)
        self.card = QFrame()
        self.card.setObjectName("SplashCard")
        self.card.setStyleSheet("""
            QFrame#SplashCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #fbf9ff);
                border: 1px solid #e9d5ff;
                border-radius: 18px;
            }
        """)

        # Drop Shadow for soft elevation
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(76, 29, 149, 45))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(28, 24, 28, 22)
        card_layout.setSpacing(10)

        # Top Section: Logo & Identity
        top_row = QHBoxLayout()
        top_row.setSpacing(18)

        # Court Logo
        logo_lbl = QLabel()
        logo_pix = _get_splash_logo_pixmap(64)
        if not logo_pix.isNull():
            logo_lbl.setPixmap(logo_pix)
        logo_lbl.setFixedSize(64, 64)
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(logo_lbl)

        # Text Branding
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_lbl = QLabel(APP_NAME)
        title_lbl.setStyleSheet("""
            font-size: 24pt;
            font-weight: 800;
            color: #4c1d95;
            letter-spacing: 1.5px;
        """)

        subtitle_en = QLabel("Court Official Document System")
        subtitle_en.setStyleSheet("""
            font-size: 10.5pt;
            font-weight: 600;
            color: #7c3aed;
            letter-spacing: 0.5px;
        """)

        subtitle_th = QLabel("ระบบจัดทำรายงานกระบวนพิจารณาและคำพิพากษาตามยอม")
        subtitle_th.setStyleSheet("""
            font-size: 10pt;
            color: #334155;
        """)

        text_layout.addWidget(title_lbl)
        text_layout.addWidget(subtitle_en)
        text_layout.addWidget(subtitle_th)
        top_row.addLayout(text_layout)
        top_row.addStretch()

        card_layout.addLayout(top_row)

        # Badge & Version Row
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 4, 0, 4)

        offline_badge = QLabel("100% Offline & Air-Gapped Judicial Assistant")
        offline_badge.setStyleSheet("""
            background-color: #f5f3ff;
            color: #6d28d9;
            border: 1px solid #ddd6fe;
            border-radius: 10px;
            padding: 3px 10px;
            font-size: 8.5pt;
            font-weight: 600;
        """)
        badge_row.addWidget(offline_badge)

        badge_row.addStretch()

        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet("""
            color: #64748b;
            font-size: 9pt;
            font-weight: 600;
        """)
        badge_row.addWidget(ver_lbl)

        card_layout.addLayout(badge_row)
        card_layout.addSpacing(6)

        # Progress Status Row
        status_row = QHBoxLayout()
        self.status_lbl = QLabel("กำลังเตรียมความพร้อมของระบบ...")
        self.status_lbl.setStyleSheet("""
            color: #475569;
            font-size: 9.5pt;
            font-weight: 500;
        """)

        self.percent_lbl = QLabel("0%")
        self.percent_lbl.setStyleSheet("""
            color: #7c3aed;
            font-size: 9.5pt;
            font-weight: 700;
        """)

        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        status_row.addWidget(self.percent_lbl)
        card_layout.addLayout(status_row)

        # Progress Bar (Light Theme with Purple Gradient)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(7)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #ede9fe;
                border: 1px solid #e2e8f0;
                border-radius: 3.5px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6d28d9, stop:0.6 #8b5cf6, stop:1 #a855f7);
                border-radius: 3.5px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        # Footer Notice
        footer_lbl = QLabel("ระบบสารสนเทศเพื่อสนับสนุนงานห้องพิจารณาคดี ศาลยุติธรรม")
        footer_lbl.setStyleSheet("""
            color: #94a3b8;
            font-size: 8pt;
        """)
        footer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(footer_lbl)

        outer_layout.addWidget(self.card)


    def set_progress(self, percent: int, message: str = ""):
        """
        Update progress percentage (0-100) and status message.
        Flushes Qt event loop to ensure immediate visual update.
        """
        clamped = max(0, min(100, int(percent)))
        self.progress_bar.setValue(clamped)
        self.percent_lbl.setText(f"{clamped}%")
        if message:
            self.status_lbl.setText(message)
        self.repaint()
        QApplication.processEvents()

    def finish(self, main_window=None):
        """
        Close splash screen and ensure the main window is focused.
        """
        self.close()
        if main_window is not None:
            main_window.raise_()
            main_window.activateWindow()
