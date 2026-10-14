"""
JADS (Judicial Automated Document System) - Python Standalone 100% Offline
Modern Official Judicial Theme with Wizard Steps & Personal Templates
Font: Kanit (Loaded natively for high legibility across all Windows displays)
Pure Native Desktop GUI powered by PySide6 (Zero External Web Dependencies)
"""

import sys
import os
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox, QDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeyEvent

from constants import DEFAULT_CASE_TYPES
from excel_service import read_excel_data, guess_column_mapping
import storage_service
from icon_service import get_app_logo_icon
from dialogs import (
    TemplateManagerDialog, BenchManagerDialog, SignatoryRoleManagerDialog,
    CourtSettingsDialog, ShortcutsGuideDialog
)
from ui.theme import load_application_fonts, get_application_stylesheet, get_default_font
from ui.components.sidebar import SidebarWidget
from ui.components.shortcut_bar import ShortcutTipBar
from ui.pages.menu_page import MenuPage
from ui.pages.import_page import ImportPage
from ui.pages.table_page import TablePage
from ui.pages.doc_type_page import DocTypePage
from ui.pages.form_page import FormPage


class JADSMainWindow(QMainWindow):
    """Main Application Window orchestrating navigation, state, and pages."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ระบบสร้างรายงานกระบวนพิจารณาคดี (JADS Offline)")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(1200, 840)
        self.setMinimumSize(960, 600)

        # Application state
        self.current_step = 0  # 0: Menu, 1: Import, 2: Select Case (Table), 3: Select DocType, 4: Form Wizard
        self.excel_headers: List[str] = []
        self.excel_rows: List[Dict[str, Any]] = []
        self.excel_filename: str = ""
        self.mapping: Dict[str, str] = {}
        self.selected_row_data: Dict[str, Any] = {}
        self.case_types_list: List[str] = list(DEFAULT_CASE_TYPES)

        self.current_doc_type: str = "report"

        self.init_ui()
        self.apply_theme()
        self.update_step_ui()
        self.showMaximized()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar Navigation
        self.sidebar = SidebarWidget(self)
        self.sidebar.step_navigation_requested.connect(self.handle_sidebar_step_nav)
        self.sidebar.template_manager_requested.connect(self.open_template_manager)
        self.sidebar.bench_manager_requested.connect(self.open_bench_manager)
        self.sidebar.signatory_roles_requested.connect(self.open_signatory_role_manager)
        self.sidebar.court_settings_requested.connect(self.open_court_settings)
        main_layout.addWidget(self.sidebar)

        # 2. Central Content Area (Stacked Pages & Bottom Shortcut Bar)
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("contentArea")

        # Page 0: Main Menu
        self.page_menu = MenuPage(self)
        self.page_menu.start_requested.connect(lambda: self.go_to_step(1))
        self.page_menu.template_manager_requested.connect(self.open_template_manager)
        self.page_menu.bench_manager_requested.connect(self.open_bench_manager)
        self.page_menu.court_settings_requested.connect(self.open_court_settings)
        self.stacked_widget.addWidget(self.page_menu)

        # Page 1: Excel Import
        self.page_import = ImportPage(self)
        self.page_import.back_requested.connect(lambda: self.go_to_step(0))
        self.page_import.file_selected.connect(self.load_excel_file)
        self.stacked_widget.addWidget(self.page_import)

        # Page 2: Case Table Selection (เลือกคดี)
        self.page_table = TablePage(self)
        self.page_table.change_file_requested.connect(lambda: self.go_to_step(1))
        self.page_table.proceed_to_form_requested.connect(self.handle_proceed_from_table)
        self.page_table.doc_type_changed.connect(self.handle_doc_type_changed)
        self.page_table.row_selected.connect(self.handle_row_selected)
        self.stacked_widget.addWidget(self.page_table)

        # Page 3: Document Type Selection (เลือกประเภทเอกสาร)
        self.page_doc_type = DocTypePage(self)
        self.page_doc_type.back_requested.connect(lambda: self.go_to_step(2))
        self.page_doc_type.doc_type_selected.connect(self.handle_doc_type_selected)
        self.stacked_widget.addWidget(self.page_doc_type)

        # Page 4: 3-Section Form & Document Generator (ทำเอกสาร)
        self.page_form = FormPage(self)
        self.page_form.back_to_doc_type_requested.connect(lambda: self.go_to_step(3))
        self.page_form.back_to_table_requested.connect(lambda: self.go_to_step(2))
        self.page_form.bench_manager_requested.connect(self.open_bench_manager)
        self.page_form.court_saved_as_default.connect(self.handle_court_saved_as_default)
        self.stacked_widget.addWidget(self.page_form)

        content_layout.addWidget(self.stacked_widget, 1)

        # Bottom Shortcut Tip Bar
        self.shortcut_bar = ShortcutTipBar(self)
        self.shortcut_bar.shortcuts_dialog_requested.connect(self.open_shortcuts_guide)
        content_layout.addWidget(self.shortcut_bar)

        main_layout.addWidget(content_container, 1)

    def apply_theme(self):
        self.setStyleSheet(get_application_stylesheet())

    def update_step_ui(self):
        self.sidebar.set_current_step(self.current_step)

    def handle_sidebar_step_nav(self, step_idx: int):
        if step_idx == -1 or step_idx == 1:
            # "สร้างรายงานคดี": Always go to Step 1 to select file first
            self.go_to_step(1)
        else:
            self.go_to_step(step_idx)

    def go_to_step(self, step_idx: int):
        if step_idx == 2:
            if not self.excel_rows or self.page_table.table_widget.rowCount() == 0:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกไฟล์ Excel ที่มีข้อมูลคดีก่อนเข้าสู่ขั้นตอนที่ 2")
                step_idx = 1
        elif step_idx == 3:
            if not self.excel_rows or self.page_table.table_widget.rowCount() == 0:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกไฟล์ Excel ในขั้นตอนที่ 1 ก่อน")
                step_idx = 1
            elif not self.selected_row_data:
                orig_idx = self.page_table.get_selected_original_index()
                if orig_idx is not None and 0 <= orig_idx < len(self.excel_rows):
                    self.handle_row_selected(orig_idx)
                else:
                    QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกคดีจากตารางในขั้นตอนที่ 2 ก่อน")
                    step_idx = 2
            if self.selected_row_data:
                self.page_doc_type.set_case_info(self.selected_row_data, self.mapping)
                self.page_doc_type.set_selected_type(self.current_doc_type)
        elif step_idx == 4:
            if not self.excel_rows or self.page_table.table_widget.rowCount() == 0:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกไฟล์ Excel ในขั้นตอนที่ 1 ก่อน")
                step_idx = 1
            elif not self.selected_row_data:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกคดีจากตารางในขั้นตอนที่ 2 ก่อน")
                step_idx = 2

        self.current_step = step_idx
        self.stacked_widget.setCurrentIndex(step_idx)
        self.update_step_ui()

        # Smart Focus on transition
        if step_idx == 2:
            self.page_table.focus_search()
        elif step_idx == 4:
            self.page_form.focus_first_field()

    def open_shortcuts_guide(self):
        """Open keyboard shortcuts reference dialog."""
        dlg = ShortcutsGuideDialog(self)
        dlg.exec()

    def keyPressEvent(self, event: QKeyEvent):
        """Global keyboard shortcut routing."""
        key = event.key()
        modifiers = event.modifiers()

        # F1: Open shortcuts guide modal
        if key == Qt.Key.Key_F1:
            self.open_shortcuts_guide()
            event.accept()
            return

        # Ctrl+F: Smart focus search in Step 2 Table
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_F:
            if self.current_step != 2 and self.excel_rows:
                self.go_to_step(2)
            if self.current_step == 2:
                self.page_table.focus_search()
                event.accept()
                return

        # Ctrl+O: Open Excel file
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_O:
            if self.current_step != 1:
                self.go_to_step(1)
            self.page_import.trigger_file_dialog()
            event.accept()
            return

        # Ctrl+S or F5: Generate Word Document (in Step 4)
        if (modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S) or key == Qt.Key.Key_F5:
            if self.current_step == 4:
                self.page_form.handle_generate_docx()
                event.accept()
                return

        # Ctrl+T: Open Paragraph Template Manager Dialog
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_T:
            self.open_template_manager()
            event.accept()
            return

        # Ctrl+B: Open Bench Pairing Manager Dialog
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_B:
            self.open_bench_manager()
            event.accept()
            return

        # Ctrl+H: Return to Main Menu / Dashboard
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_H:
            self.go_to_step(0)
            event.accept()
            return

        # Ctrl+1 / 2 / 3 / 4: Jump between Wizard Steps
        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_1:
            self.go_to_step(1)
            event.accept()
            return

        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_2:
            if self.excel_rows and self.page_table.table_widget.rowCount() > 0:
                self.go_to_step(2)
                event.accept()
                return
            else:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกไฟล์ Excel ที่มีข้อมูลคดีก่อน")
                self.go_to_step(1)
                event.accept()
                return

        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_3:
            if self.selected_row_data:
                self.go_to_step(3)
                event.accept()
                return
            else:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกคดีจากตารางในขั้นตอนที่ 2 ก่อน")
                event.accept()
                return

        if modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_4:
            if self.selected_row_data:
                self.go_to_step(4)
                event.accept()
                return
            else:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกคดีจากตารางในขั้นตอนที่ 2 ก่อน")
                event.accept()
                return

        # PageDown: Next Step / Next Section
        if key == Qt.Key.Key_PageDown:
            if self.current_step == 0:
                self.go_to_step(1)
                event.accept()
                return
            elif self.current_step == 1:
                if self.excel_rows and self.page_table.table_widget.rowCount() > 0:
                    self.go_to_step(2)
                    event.accept()
                    return
                else:
                    QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกไฟล์ Excel ที่มีข้อมูลคดีก่อน")
                    event.accept()
                    return
            elif self.current_step == 2:
                self.handle_proceed_from_table()
                event.accept()
                return
            elif self.current_step == 3:
                self.handle_doc_type_selected(self.current_doc_type or "report")
                event.accept()
                return
            elif self.current_step == 4:
                if self.page_form.form_section < 2:
                    if self.page_form.form_section == 0:
                        self.page_form.handle_next_to_attendees()
                    else:
                        self.page_form.set_form_section(self.page_form.form_section + 1)
                    event.accept()
                    return
                elif self.page_form.form_section == 2:
                    self.page_form.handle_generate_docx()
                    event.accept()
                    return

        # PageUp: Previous Step / Previous Section
        if key == Qt.Key.Key_PageUp:
            if self.current_step == 4:
                if self.page_form.form_section > 0:
                    self.page_form.set_form_section(self.page_form.form_section - 1)
                    event.accept()
                    return
                else:
                    self.go_to_step(3)
                    event.accept()
                    return
            elif self.current_step == 3:
                self.go_to_step(2)
                event.accept()
                return
            elif self.current_step == 2:
                self.go_to_step(1)
                event.accept()
                return
            elif self.current_step == 1:
                self.go_to_step(0)
                event.accept()
                return

        super().keyPressEvent(event)

    # -------------------------------------------------------------------------
    # Backward Compatibility Proxies for Tests and Direct Access
    # -------------------------------------------------------------------------
    @property
    def paragraph_cards(self):
        return self.page_form.paragraph_cards

    @property
    def para_placeholder(self):
        return self.page_form.para_placeholder

    @property
    def btn_bottom_add_para(self):
        return self.page_form.btn_bottom_add_para

    @property
    def txt_case_type(self):
        return self.page_form.txt_case_type

    @property
    def case_type_model(self):
        return self.page_form.case_type_model

    @property
    def form_sub_stack(self):
        return self.page_form.form_sub_stack

    @property
    def table_widget(self):
        return self.page_table.table_widget

    @property
    def filter_input(self):
        return self.page_table.filter_input

    def set_form_section(self, idx: int):
        self.page_form.set_form_section(idx)

    def add_paragraph_card(self, initial_text: str = ""):
        return self.page_form.add_paragraph_card(initial_text)

    def delete_paragraph_card(self, card):
        return self.page_form.delete_paragraph_card(card)

    # -------------------------------------------------------------------------
    # Event Handlers: Excel Import & Selection
    # -------------------------------------------------------------------------
    def load_excel_file(self, file_path: str):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            headers, rows = read_excel_data(file_path)
            if not rows:
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(self, "แจ้งเตือน", "ไม่พบข้อมูลแถวในไฟล์ Excel ที่เลือก")
                return

            self.excel_headers = headers
            self.excel_rows = rows
            self.excel_filename = os.path.basename(file_path)
            self.mapping = guess_column_mapping(headers, rows)

            # Harvest unique case types from excel and update completer
            excel_case_types = set()
            type_col = self.mapping.get('case_type')
            if type_col:
                for r in rows:
                    v = str(r.get(type_col, '')).strip()
                    if v:
                        excel_case_types.add(v)
            else:
                for col in (rows[0].keys() if rows else []):
                    if any(kw in col for kw in ['ประเภท', 'ความ', 'คดี']):
                        for r in rows:
                            v = str(r.get(col, '')).strip()
                            if v and len(v) < 40:
                                excel_case_types.add(v)

            combined = list(DEFAULT_CASE_TYPES)
            for ct in sorted(excel_case_types):
                if ct not in combined:
                    combined.append(ct)
            self.case_types_list = combined
            self.page_form.update_case_types(self.case_types_list)

            # Update table widget
            self.page_table.set_table_data(headers, rows, self.excel_filename, self.mapping)

            # ตรวจสอบว่าตารางมีข้อมูลคดีหรือไม่
            if not self.excel_rows or self.page_table.table_widget.rowCount() == 0:
                QApplication.restoreOverrideCursor()
                QMessageBox.warning(self, "แจ้งเตือน", "ไม่พบข้อมูลคดีในตาราง กรุณาเลือกไฟล์ Excel อื่น")
                self.go_to_step(1)
                return

            # Set first row as initially selected
            if self.excel_rows:
                self.handle_row_selected(0)

            QApplication.restoreOverrideCursor()
            # Step 1 -> Step 2: ตรงไปยังขั้นตอนเลือกคดีทันที
            self.go_to_step(2)
        except Exception as e:
            while QApplication.overrideCursor():
                QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "เกิดข้อผิดพลาด", f"ไม่สามารถอ่านไฟล์ Excel ได้:\n{str(e)}")
        finally:
            while QApplication.overrideCursor():
                QApplication.restoreOverrideCursor()

    def handle_doc_type_changed(self, doc_type: str):
        self.current_doc_type = doc_type
        self.page_form.set_doc_type(doc_type)

    def handle_row_selected(self, orig_idx: int):
        if 0 <= orig_idx < len(self.excel_rows):
            row = self.excel_rows[orig_idx]
            self.selected_row_data = row
            self.page_form.load_case_row(row, self.mapping)
            if not self.page_form.txt_court_name.text().strip():
                default_court = storage_service.get_default_court_name()
                if default_court:
                    self.page_form.txt_court_name.setText(default_court)

    def handle_proceed_from_table(self):
        """From Step 2 (Table), proceed to Step 3 (Select Doc Type)."""
        if not self.selected_row_data:
            orig_idx = self.page_table.get_selected_original_index()
            if orig_idx is not None and 0 <= orig_idx < len(self.excel_rows):
                self.handle_row_selected(orig_idx)
            else:
                QMessageBox.warning(self, "แจ้งเตือน", "กรุณาคลิกเลือกคดีในตารางก่อน")
                return

        self.page_doc_type.set_case_info(self.selected_row_data, self.mapping)
        self.page_doc_type.set_selected_type(self.current_doc_type)
        self.go_to_step(3)

    def handle_proceed_to_form(self):
        """Backwards compatibility proxy for proceed_to_form_requested."""
        self.handle_proceed_from_table()

    def handle_doc_type_selected(self, doc_type: str):
        """From Step 3 (Doc Type Selection), proceed to Step 4 (Form Wizard)."""
        self.current_doc_type = doc_type
        self.page_table.set_doc_type(doc_type)
        self.page_form.set_doc_type(doc_type)

        if not self.selected_row_data:
            orig_idx = self.page_table.get_selected_original_index()
            if orig_idx is not None and 0 <= orig_idx < len(self.excel_rows):
                self.handle_row_selected(orig_idx)
            else:
                QMessageBox.warning(self, "แจ้งเตือน", "กรุณาคลิกเลือกคดีในตารางก่อน")
                self.go_to_step(2)
                return

        if not self.page_form.txt_court_name.text().strip():
            default_court = storage_service.get_default_court_name()
            if default_court:
                self.page_form.txt_court_name.setText(default_court)

        self.page_form.set_form_section(0)
        self.go_to_step(4)

    # -------------------------------------------------------------------------
    # Dialog Openers
    # -------------------------------------------------------------------------
    def open_bench_manager(self):
        dlg = BenchManagerDialog(self)
        dlg.exec()
        self.page_form.refresh_judge1_completer()
        current_j1 = self.page_form.cmb_judge1.currentText().strip()
        if current_j1:
            self.page_form.handle_judge1_changed(current_j1)

    def open_template_manager(self):
        dlg = TemplateManagerDialog(self)
        dlg.exec()

    def open_signatory_role_manager(self):
        dlg = SignatoryRoleManagerDialog(self)
        dlg.exec()
        if hasattr(self.page_form, 'signatories_widget'):
            self.page_form.signatories_widget.refresh_chips()

    def handle_court_saved_as_default(self, court_name: str):
        """React to court name saved from form page."""
        self.page_menu.update_court_description(court_name)
        if hasattr(self.sidebar, 'refresh_court_badge'):
            self.sidebar.refresh_court_badge(court_name)

    def open_court_settings(self):
        dlg = CourtSettingsDialog(self)
        if dlg.exec():
            default_court = storage_service.get_default_court_name()
            self.page_menu.update_court_description(default_court)
            self.page_form.txt_court_name.setText(default_court)
            if hasattr(self.sidebar, 'refresh_court_badge'):
                self.sidebar.refresh_court_badge(default_court)


def main():
    # Set Windows Taskbar AppUserModelID so taskbar displays the custom logo
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("coj.jads.desktop.app")
        except Exception:
            pass

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setWindowIcon(get_app_logo_icon())

    load_application_fonts()
    app.setFont(get_default_font(11))

    window = JADSMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
