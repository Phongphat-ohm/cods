"""
Theme and Styling Module for CODS (Court Official Document System)
Font: Kanit (Loaded natively for high legibility across all Windows displays)
Official Imperial Amethyst & Judicial Purple Theme (Enterprise Court of Justice Standard)
"""

import os
from PySide6.QtGui import QFont, QFontDatabase

# ==============================================================================
# Design Tokens: Imperial Amethyst & Judicial Purple Theme
# ==============================================================================
# Primary Brand
COLOR_PRIMARY = "#4c1d95"           # Amethyst Deep
COLOR_PRIMARY_HOVER = "#5b21b6"     # Amethyst Royal (Hover)
COLOR_PRIMARY_PRESSED = "#3b0764"   # Amethyst Night (Pressed)
COLOR_SURFACE_TINT = "#f5f3ff"      # Amethyst Tint (Surface / Background)
COLOR_FOCUS_RING = "#7c3aed"        # Violet Focus Ring (2px)
COLOR_LIGHT_BORDER = "#ddd6fe"      # Light Amethyst Border

# Neutral / Secondary (WCAG 2.1 AA Compliant)
COLOR_TEXT_MAIN = "#0f172a"         # Slate 900 (Main text, 16.1:1 AAA contrast)
COLOR_TEXT_MUTED = "#334155"        # Slate 700 (Muted text, 9.6:1 AAA contrast)
COLOR_TEXT_DISABLED = "#94a3b8"     # Slate 400 (Disabled controls)
COLOR_BORDER_STANDARD = "#cbd5e1"   # Slate 300 (Standard borders, gridlines)
COLOR_CARD_SURFACE = "#ffffff"      # Pure white surface
COLOR_SLATE_MUTED = "#f8fafc"       # Slate 50 (Sidebar, disabled backgrounds)
COLOR_BORDER_SUBTLE = "#e2e8f0"     # Slate 200 (Dividers, subtle borders)
COLOR_SLATE_HOVER = "#f1f5f9"       # Slate 100 (Secondary hover, table headers)

# Semantic Status
COLOR_SUCCESS = "#15803d"           # Forest Green (Success text/border)
COLOR_SUCCESS_BG = "#dcfce7"        # Green 100 (Success surface)
COLOR_DANGER = "#b91c1c"            # Crimson Red (Danger text/border)
COLOR_DANGER_BG = "#fee2e2"         # Red 100 (Danger surface)
COLOR_WARNING = "#92400e"           # Amber Brown (Warning text/border)
COLOR_WARNING_BG = "#fef3c7"        # Amber 100 (Warning surface)
COLOR_INFO = "#0369a1"              # Judicial Sky Blue (WCAG AA Compliant 4.7:1+)
COLOR_INFO_BG = "#e0f2fe"           # Blue 100 (Info surface)


def load_application_fonts() -> None:
    """Load bundled Kanit font files into Qt Font Database."""
    from services.storage_service import get_fonts_dir
    fonts_dir = get_fonts_dir()
    if fonts_dir and os.path.exists(fonts_dir):
        for f in os.listdir(fonts_dir):
            if f.lower().endswith((".ttf", ".otf")):
                QFontDatabase.addApplicationFont(os.path.join(fonts_dir, f))


def get_default_font(size: int = 11) -> QFont:
    """Return default application font with Kanit family and Thai fallback chain."""
    font = QFont()
    font.setFamilies(["Kanit", "Sarabun", "Segoe UI", "Tahoma", "sans-serif"])
    font.setPointSize(size)
    return font


def get_application_stylesheet() -> str:
    """
    Return official Imperial Amethyst & Judicial Purple Theme stylesheet (QSS)
    with high contrast, dignified judicial styling, and WCAG 2.1 AA compliance.
    """
    return """
        QWidget {
            font-family: 'Kanit', 'Sarabun', 'Segoe UI', 'Tahoma', sans-serif;
            font-size: 15px;
            color: #0f172a;
        }

        QMainWindow, #contentArea, QDialog {
            background-color: #ffffff;
        }

        /* Clean transparent label background */
        QLabel {
            background-color: transparent;
        }

        /* Sidebar Navigation */
        #sidebarFrame {
            background-color: #f8fafc;
            border-right: 1.5px solid #cbd5e1;
        }
        #brandLabel {
            font-size: 18px;
            font-weight: 600;
            color: #0f172a;
            padding-bottom: 2px;
        }
        #brandSubLabel {
            font-size: 12px;
            color: #475569;
            font-weight: 400;
        }
        #menuSectionTitle {
            font-size: 13px;
            font-weight: 600;
            color: #334155;
            padding-top: 12px;
            padding-bottom: 6px;
            letter-spacing: 0.5px;
        }
        #sidebarButton {
            background-color: transparent;
            color: #1e293b;
            text-align: left;
            padding: 10px 16px;
            border: 1px solid transparent;
            border-radius: 6px;
            font-weight: 500;
            font-size: 15px;
        }
        #sidebarButton:hover {
            background-color: #f1f5f9;
            color: #0f172a;
        }
        #sidebarButton:pressed {
            background-color: #e2e8f0;
        }
        #sidebarButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #sidebarButton[active="true"] {
            background-color: #f5f3ff;
            color: #4c1d95;
            border: 1.5px solid #ddd6fe;
            border-radius: 6px;
            font-weight: 600;
        }

        /* Step Indicators in Sidebar */
        #stepIndicator {
            font-size: 14px;
            color: #334155;
            padding: 7px 12px;
            border-radius: 5px;
        }
        #stepIndicator[current="true"] {
            color: #4c1d95;
            font-weight: 600;
            background-color: #f5f3ff;
            border: 1px solid #ddd6fe;
        }

        /* Status Box */
        #statusBox {
            background-color: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 6px;
        }
        #statusDot {
            font-size: 13px;
            font-weight: 600;
            color: #15803d;
        }
        #statusDesc {
            font-size: 12px;
            color: #334155;
            line-height: 1.4;
        }

        /* Sidebar Court Badge */
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

        /* Page Titles */
        #welcomeTitle {
            font-size: 24px;
            font-weight: 600;
            color: #0f172a;
        }
        #welcomeSubtitle {
            font-size: 15px;
            color: #334155;
            line-height: 1.5;
        }
        #stepPageTitle {
            font-size: 20px;
            font-weight: 600;
            color: #0f172a;
        }
        #sectionHeaderTitle {
            font-size: 17px;
            font-weight: 600;
            color: #4c1d95;
        }

        /* Cards */
        #menuCardFrame {
            background-color: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 10px;
        }
        #menuCardFrame:hover {
            border-color: #94a3b8;
        }
        #menuSubCardFrame {
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
            border-radius: 10px;
        }
        #menuSubCardFrame:hover {
            border-color: #cbd5e1;
            background-color: #ffffff;
        }
        #cardTitle {
            font-size: 18px;
            font-weight: 600;
            color: #0f172a;
        }
        #cardSubTitle {
            font-size: 16px;
            font-weight: 600;
            color: #0f172a;
        }
        #cardDesc {
            font-size: 14px;
            color: #334155;
            line-height: 1.5;
        }

        /* Upload Box (Drag and Drop Target) */
        #uploadCardFrame {
            background-color: #f8fafc;
            border: 2px dashed #94a3b8;
            border-radius: 12px;
        }
        #uploadCardFrame[dragOver="true"] {
            border: 2.5px dashed #4c1d95;
            background-color: #f5f3ff;
        }
        #uploadInstructTitle {
            font-size: 20px;
            font-weight: 600;
            color: #0f172a;
        }

        /* Form Groups & Containers (Imperial Amethyst Judicial Palette) */
        #innerGroupFrame, #signatoriesBox {
            background-color: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 8px;
        }
        #benchContainer {
            background-color: transparent;
            border: none;
        }
        #paragraphCard {
            background-color: #f8fafc;
            border: 1.5px solid #cbd5e1;
            border-radius: 8px;
        }
        #paragraphCard[dropTarget="true"] {
            border: 2px dashed #4c1d95;
            background-color: #f5f3ff;
        }
        #dragGripHandle {
            color: #334155;
            background-color: #e2e8f0;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
        }
        #dragGripHandle:hover {
            background-color: #cbd5e1;
            color: #0f172a;
        }
        #paragraphBadge {
            font-size: 14px;
            font-weight: 600;
            color: #4c1d95;
            background-color: #f5f3ff;
            border: 1px solid #ddd6fe;
            padding: 4px 10px;
            border-radius: 4px;
        }
        #fieldLabel {
            font-size: 14px;
            font-weight: 600;
            color: #1e293b;
        }
        #helperText {
            font-size: 13px;
            color: #334155;
        }

        /* Inputs & Text Editing */
        QLineEdit, QTextEdit, QComboBox, QListWidget {
            background-color: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 6px;
            padding: 8px 12px;
            color: #0f172a;
            font-size: 15px;
        }
        QLineEdit:hover, QTextEdit:hover, QComboBox:hover {
            border: 1.5px solid #94a3b8;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border: 2px solid #7c3aed;
            background-color: #ffffff;
            outline: none;
        }
        QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        /* Signatories List Specific High-Readability Styling */
        #signatoriesList {
            background-color: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px;
            font-size: 15px;
        }
        #signatoriesList::item {
            padding: 10px 14px;
            margin: 3px 2px;
            border-radius: 6px;
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #0f172a;
            font-size: 15px;
        }
        #signatoriesList::item:hover {
            background-color: #f1f5f9;
            border: 1px solid #94a3b8;
        }
        #signatoriesList::item:selected {
            background-color: #f5f3ff;
            border: 1.5px solid #7c3aed;
            color: #4c1d95;
            font-weight: 600;
        }

        /* Tables */
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f8fafc;
            border: 1.5px solid #cbd5e1;
            border-radius: 6px;
            gridline-color: #cbd5e1;
            selection-background-color: #f5f3ff;
            selection-color: #4c1d95;
            font-size: 14px;
        }
        QHeaderView::section {
            background-color: #f1f5f9;
            color: #1e293b;
            padding: 9px 12px;
            border: 1px solid #cbd5e1;
            font-weight: 600;
            font-size: 14px;
        }
        QTableCornerButton::section {
            background-color: #f1f5f9;
            border: 1px solid #cbd5e1;
        }

        /* Generic QPushButton Focus and Disabled Base States */
        QPushButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        QPushButton:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        /* Action Buttons: Primary */
        #primaryButton {
            background-color: #4c1d95;
            color: #ffffff;
            padding: 9px 20px;
            font-weight: 500;
            font-size: 15px;
            border-radius: 6px;
            border: 1px solid #3b0764;
        }
        #primaryButton:hover {
            background-color: #5b21b6;
        }
        #primaryButton:pressed {
            background-color: #3b0764;
        }
        #primaryButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #primaryButton:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        #primaryButtonSmall {
            background-color: #4c1d95;
            color: #ffffff;
            padding: 6px 14px;
            font-size: 13px;
            font-weight: 500;
            border-radius: 5px;
            border: 1px solid #3b0764;
        }
        #primaryButtonSmall:hover {
            background-color: #5b21b6;
        }
        #primaryButtonSmall:pressed {
            background-color: #3b0764;
        }
        #primaryButtonSmall:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #primaryButtonSmall:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        #primaryButtonLarge {
            background-color: #4c1d95;
            color: #ffffff;
            padding: 13px 30px;
            font-size: 16px;
            font-weight: 600;
            border-radius: 8px;
            border: 1px solid #3b0764;
        }
        #primaryButtonLarge:hover {
            background-color: #5b21b6;
        }
        #primaryButtonLarge:pressed {
            background-color: #3b0764;
        }
        #primaryButtonLarge:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #primaryButtonLarge:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        /* Action Buttons: Secondary */
        #secondaryButton {
            background-color: #ffffff;
            color: #1e293b;
            border: 1.5px solid #cbd5e1;
            border-radius: 6px;
            padding: 9px 16px;
            font-weight: 500;
            font-size: 14px;
        }
        #secondaryButton:hover {
            background-color: #f1f5f9;
            color: #0f172a;
            border-color: #94a3b8;
        }
        #secondaryButton:pressed {
            background-color: #e2e8f0;
        }
        #secondaryButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #secondaryButton:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        #secondaryButtonSmall {
            background-color: #ffffff;
            color: #1e293b;
            border: 1.5px solid #cbd5e1;
            border-radius: 5px;
            padding: 5px 12px;
            font-size: 13px;
            font-weight: 500;
        }
        #secondaryButtonSmall:hover {
            background-color: #f1f5f9;
            color: #0f172a;
            border-color: #94a3b8;
        }
        #secondaryButtonSmall:pressed {
            background-color: #e2e8f0;
        }
        #secondaryButtonSmall:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #secondaryButtonSmall:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        /* Action Buttons: Mini & Contextual */
        #cardMiniButton {
            background-color: #ffffff;
            color: #1e293b;
            border: 1.5px solid #cbd5e1;
            border-radius: 5px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 500;
        }
        #cardMiniButton:hover {
            background-color: #f1f5f9;
            color: #0f172a;
        }
        #cardMiniButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #cardMiniButton:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        #cardMiniButtonDanger {
            background-color: #ffffff;
            color: #b91c1c;
            border: 1.5px solid #fca5a5;
            border-radius: 5px;
            padding: 4px 10px;
            font-size: 13px;
            font-weight: 500;
        }
        #cardMiniButtonDanger:hover {
            background-color: #fee2e2;
            color: #991b1b;
        }
        #cardMiniButtonDanger:focus {
            border: 2px solid #b91c1c;
            outline: none;
        }
        #cardMiniButtonDanger:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        /* Sovereign Judicial Purple Report Generation Button */
        #generateButton {
            background-color: #4c1d95;
            color: #ffffff;
            padding: 11px 26px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 6px;
            border: 1px solid #3b0764;
        }
        #generateButton:hover {
            background-color: #5b21b6;
        }
        #generateButton:pressed {
            background-color: #3b0764;
        }
        #generateButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #generateButton:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        #tagButton {
            background-color: #f8fafc;
            color: #1e293b;
            border: 1.5px solid #cbd5e1;
            border-radius: 5px;
            padding: 4px 9px;
            font-size: 12.5px;
            font-weight: 500;
        }
        #tagButton:hover {
            background-color: #e2e8f0;
            color: #0f172a;
        }
        #tagButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #tagButton:disabled {
            color: #94a3b8;
            background-color: #f8fafc;
            border: 1.5px solid #e2e8f0;
        }

        /* Document Types Selection Cards on Main Menu */
        #docTypeCard {
            background-color: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 12px;
        }
        #docTypeCard:hover {
            border: 1.5px solid #4c1d95;
            background-color: #f8fafc;
        }
        #docTypeTitle {
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
        }
        #docTypeBadge {
            background-color: #4c1d95;
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            padding: 4px 12px;
            border-radius: 12px;
        }
        #docTypeStatusBadge {
            background-color: #dcfce7;
            color: #15803d;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid #bbf7d0;
        }
        #docTypeStatusBadgePending {
            background-color: #fef3c7;
            color: #92400e;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid #fde68a;
        }
        #docTypeStatusBadgeInfo {
            background-color: #e0f2fe;
            color: #0369a1;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid #bae6fd;
        }
        #docTypeStatusBadgeDanger {
            background-color: #fee2e2;
            color: #b91c1c;
            font-size: 12px;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 12px;
            border: 1px solid #fca5a5;
        }
        #docTypeFeaturePill {
            background-color: #f1f5f9;
            color: #334155;
            font-size: 12px;
            font-weight: 500;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #e2e8f0;
        }

        #previewCalloutBox {
            background-color: #f5f3ff;
            border: 1.5px solid #ddd6fe;
            border-radius: 6px;
        }
        #previewCalloutBoxInfo {
            background-color: #e0f2fe;
            border: 1.5px solid #bae6fd;
            border-radius: 6px;
        }

        /* Sub-stepper tabs in Section 3 */
        #stepperTabButton {
            background-color: #f8fafc;
            color: #334155;
            border: 1.5px solid #cbd5e1;
            border-radius: 6px;
            padding: 9px 18px;
            font-size: 14px;
            font-weight: 500;
        }
        #stepperTabButton:hover {
            background-color: #f1f5f9;
            color: #0f172a;
        }
        #stepperTabButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
        #stepperTabButton[active="true"] {
            background-color: #f5f3ff;
            color: #4c1d95;
            border: 2px solid #4c1d95;
            font-weight: 600;
        }

        /* Paragraph Empty Placeholder */
        #paraPlaceholderBox {
            background-color: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 8px;
        }

        /* Modern Slim Scrollbar (WCAG 2.1 AA Compliant Judicial Theme) */
        QScrollBar:vertical {
            border: none;
            background: #f1f5f9;
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #64748b;
            min-height: 24px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #334155;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            border: none;
            background: none;
            height: 0px;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }

        QScrollBar:horizontal {
            border: none;
            background: #f1f5f9;
            height: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal {
            background: #64748b;
            min-width: 24px;
            border-radius: 5px;
        }
        QScrollBar::handle:horizontal:hover {
            background: #334155;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            border: none;
            background: none;
            width: 0px;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: none;
        }

        /* Scroll Area */
        QScrollArea {
            border: 1.5px solid #cbd5e1;
            border-radius: 8px;
            background-color: #ffffff;
        }
        QScrollArea > QWidget > QWidget {
            background-color: #ffffff;
        }

        /* Custom Judicial Autocomplete Popup */
        #autocompletePopup {
            background-color: #ffffff;
            border: 1.5px solid #4c1d95;
            border-radius: 6px;
        }
        #autocompleteList {
            background-color: #ffffff;
            border: none;
            outline: none;
            padding: 4px;
        }
        #autocompleteList::item {
            padding: 7px 12px;
            border-radius: 4px;
            color: #0f172a;
            font-size: 14px;
        }
        #autocompleteList::item:hover {
            background-color: #f5f3ff;
            color: #4c1d95;
        }
        #autocompleteList::item:selected {
            background-color: #4c1d95;
            color: #ffffff;
            font-weight: 500;
        }

        /* Shortcut Tip Bar */
        #shortcutTipBar {
            background-color: #f8fafc;
            border-top: 1.5px solid #e2e8f0;
        }
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
            padding: 1px 5px;
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
            padding: 3px 10px;
            border-radius: 4px;
        }
        #shortcutHelpButton:hover {
            background-color: #f5f3ff;
            border-color: #4c1d95;
        }
        #shortcutHelpButton:focus {
            border: 2px solid #7c3aed;
            outline: none;
        }
    """
