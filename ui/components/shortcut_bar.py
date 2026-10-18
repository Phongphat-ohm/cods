"""
Shortcut Tip Bar Component for CODS
Displays keyboard shortcuts cheatsheet at the bottom of the workspace.
Assists court officers and clerks in operating the application rapidly via keyboard.
100% Offline, Native PySide6 implementation. Zero emojis.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from services.icon_service import get_icon


class ShortcutBadge(QFrame):
    """Badge pill displaying a key shortcut and its function."""

    def __init__(self, key_text: str, desc_text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("shortcutBadgePill")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 3, 6, 3)
        layout.setSpacing(5)

        self.lbl_key = QLabel(key_text)
        self.lbl_key.setObjectName("shortcutKeyBadge")

        self.lbl_desc = QLabel(desc_text)
        self.lbl_desc.setObjectName("shortcutDescText")

        layout.addWidget(self.lbl_key)
        layout.addWidget(self.lbl_desc)


class ShortcutTipBar(QFrame):
    """Bottom persistent status bar presenting workflow keyboard shortcut tips."""

    shortcuts_dialog_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("shortcutTipBar")
        self.setMinimumHeight(38)
        self.setStyleSheet("""
            #shortcutLeadLabel {
                font-size: 12px;
                font-weight: 600;
                color: #4c1d95;
            }
            #shortcutBadgePill {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
            }
            #shortcutKeyBadge {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 6px;
                border-radius: 3px;
            }
            #shortcutDescText {
                font-size: 12px;
                color: #334155;
                font-weight: 500;
            }
            #shortcutHelpButton {
                background-color: #ffffff;
                border: 1px solid #ddd6fe;
                color: #4c1d95;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 4px;
            }
            #shortcutHelpButton:hover {
                background-color: #f5f3ff;
                border-color: #4c1d95;
            }
            #shortcutHelpButton:pressed {
                background-color: #ede9fe;
            }
            #shortcutHelpButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(7)

        # Leading Tip Label
        lbl_tip = QLabel("TIP คีย์ลัด:")
        lbl_tip.setObjectName("shortcutLeadLabel")
        layout.addWidget(lbl_tip)

        # Shortcut Pills
        self.badge_pgup = ShortcutBadge("PgUp", "ก่อนหน้า")
        layout.addWidget(self.badge_pgup)

        self.badge_pgdn = ShortcutBadge("PgDn", "ถัดไป")
        layout.addWidget(self.badge_pgdn)

        self.badge_open = ShortcutBadge("Ctrl+O", "เปิด Excel")
        layout.addWidget(self.badge_open)

        self.badge_find = ShortcutBadge("Ctrl+F", "ค้นหาคดี")
        layout.addWidget(self.badge_find)

        self.badge_save = ShortcutBadge("Ctrl+S", "สร้าง Word")
        layout.addWidget(self.badge_save)

        self.badge_tpl = ShortcutBadge("Ctrl+T", "Template")
        layout.addWidget(self.badge_tpl)

        self.badge_bench = ShortcutBadge("Ctrl+B", "คู่องค์คณะ")
        layout.addWidget(self.badge_bench)

        layout.addStretch()

        # Help / All shortcuts button
        btn_all = QPushButton("คีย์ลัดทั้งหมด [F1]")
        btn_all.setObjectName("shortcutHelpButton")
        btn_all.setIcon(get_icon("help-circle", color="#4c1d95", size=13))
        btn_all.setToolTip("แสดงคู่มือสรุปคีย์ลัดการทำงานทั้งหมดในระบบ (กด F1)")
        btn_all.clicked.connect(self.shortcuts_dialog_requested.emit)
        layout.addWidget(btn_all)
