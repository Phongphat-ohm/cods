"""
CODS Main Application Window - Python Standalone 100% Offline
Modern Official Judicial Theme with Wizard Steps and Personal Templates
"""

import sys
import os
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox, QDialog, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QKeyEvent

from constants import DEFAULT_CASE_TYPES, APP_NAME, APP_VERSION
from excel_service import read_excel_data, guess_column_mapping
import storage_service
from icon_service import get_app_logo_icon
from dialogs import (
    TemplateManagerDialog, BenchManagerDialog, SignatoryRoleManagerDialog,
    CourtSettingsDialog, ShortcutsGuideDialog, AboutDialog
)
from ui.dialogs.welcome_wizard_dialog import WelcomeWizardDialog
from ui.theme import load_application_fonts, get_application_stylesheet, get_default_font
from ui.components.sidebar import SidebarWidget
from ui.components.shortcut_bar import ShortcutTipBar
from ui.components.tutorial_overlay import TutorialOverlay, TutorialStep
from ui.pages.menu_page import MenuPage
from ui.pages.import_page import ImportPage
from ui.pages.table_page import TablePage
from ui.pages.doc_type_page import DocTypePage
from ui.pages.form_page import FormPage
from ui.pages.online_form_page import OnlineFormPage

class CODSMainWindow(QMainWindow):
    """Main Application Window orchestrating navigation, state, and pages."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ระบบสร้างรายงานกระบวนพิจารณาคดี ({APP_NAME} Offline v{APP_VERSION})")
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
        self.is_online_report: bool = False

        self.init_ui()
        self.apply_theme()
        self.update_step_ui()
        QTimer.singleShot(250, self.check_first_run_tutorial)

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
        self.sidebar.tutorial_requested.connect(self.open_tutorial_menu)
        self.sidebar.about_requested.connect(self.open_about_dialog)
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
        self.page_menu.signatory_roles_requested.connect(self.open_signatory_role_manager)
        self.page_menu.court_settings_requested.connect(self.open_court_settings)
        self.page_menu.about_requested.connect(self.open_about_dialog)
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

        # Page 4: 3-Section Form & Document Generator (ทำเอกสารปกติ / ตามยอม)
        self.page_form = FormPage(self)
        self.page_form.back_to_doc_type_requested.connect(lambda: self.go_to_step(3))
        self.page_form.back_to_table_requested.connect(lambda: self.go_to_step(2))
        self.page_form.bench_manager_requested.connect(self.open_bench_manager)
        self.page_form.court_saved_as_default.connect(self.handle_court_saved_as_default)
        self.stacked_widget.addWidget(self.page_form)

        # Page 4 (Online): Dedicated Form for Online Proceedings Report (รายงานออนไลน์)
        self.page_online_form = OnlineFormPage(self)
        self.page_online_form.back_to_doc_type_requested.connect(lambda: self.go_to_step(3))
        self.page_online_form.back_to_table_requested.connect(lambda: self.go_to_step(2))
        self.page_online_form.bench_manager_requested.connect(self.open_bench_manager)
        self.page_online_form.court_saved_as_default.connect(self.handle_court_saved_as_default)
        self.stacked_widget.addWidget(self.page_online_form)

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

    def closeEvent(self, event):
        """Prompt confirmation if user has unsaved changes in form."""
        if self.current_step == 4 and hasattr(self.page_form, 'has_unsaved_content') and self.page_form.has_unsaved_content():
            reply = QMessageBox.question(
                self,
                "ยืนยันการปิดโปรแกรม",
                "ท่านมีข้อมูลที่กำลังกรอกอยู่ในแบบฟอร์ม\nหากปิดโปรแกรม ข้อมูลที่ยังไม่ได้สร้างเป็นเอกสาร Word จะสูญหาย\n\nท่านต้องการปิดโปรแกรมจริงหรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    def go_to_step(self, step_idx: int):
        if self.current_step == 4 and step_idx < 4:
            if hasattr(self.page_form, 'has_unsaved_content') and self.page_form.has_unsaved_content():
                reply = QMessageBox.question(
                    self,
                    "ยืนยันการย้อนกลับ",
                    "ท่านมีข้อมูลหรือย่อหน้าที่กำลังกรอกอยู่\nการย้อนกลับจะทำให้ข้อมูลที่แก้ไขไว้สูญหาย\n\nท่านต้องการย้อนกลับหรือไม่?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

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
                self.page_doc_type.set_selected_type(self.current_doc_type, getattr(self, 'is_online_report', False))
        elif step_idx == 4:
            if not self.excel_rows or self.page_table.table_widget.rowCount() == 0:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกไฟล์ Excel ในขั้นตอนที่ 1 ก่อน")
                step_idx = 1
            elif not self.selected_row_data:
                QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกคดีจากตารางในขั้นตอนที่ 2 ก่อน")
                step_idx = 2

        self.current_step = step_idx
        if step_idx == 4 and getattr(self, 'is_online_report', False):
            self.stacked_widget.setCurrentWidget(self.page_online_form)
        else:
            step_widgets = [self.page_menu, self.page_import, self.page_table, self.page_doc_type, self.page_form]
            if 0 <= step_idx < len(step_widgets):
                self.stacked_widget.setCurrentWidget(step_widgets[step_idx])
        self.update_step_ui()

        # Smart Focus on transition
        if step_idx == 2:
            self.page_table.focus_search()
        elif step_idx == 4:
            if getattr(self, 'is_online_report', False):
                self.page_online_form.focus_first_field()
            else:
                self.page_form.focus_first_field()

        # Contextual feature onboarding / spotlight tutorial for this step
        if 0 <= step_idx <= 4:
            QTimer.singleShot(250, lambda s=step_idx: self.show_step_tutorial(s))

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

        # F12 or Ctrl+I: Open About System Dialog
        if key == Qt.Key.Key_F12 or (modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_I):
            self.open_about_dialog()
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

        # Ctrl+S or F5: Generate Word Document
        if (modifiers == Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_S) or key == Qt.Key.Key_F5:
            if self.current_step == 4:
                if getattr(self, 'is_online_report', False):
                    self.page_online_form.handle_generate_docx()
                else:
                    self.page_form.trigger_generate_document()
                event.accept()
                return
            elif self.current_step == 3:
                is_on = getattr(self.page_doc_type, 'is_online_report', False)
                self.handle_doc_type_selected(self.current_doc_type or "report", is_on)
                if getattr(self, 'is_online_report', False):
                    self.page_online_form.handle_generate_docx()
                else:
                    self.page_form.trigger_generate_document()
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

        # Step 3 (DocType Selection) keyboard navigation: Arrow Left/Right to choose, Enter to confirm
        if self.current_step == 3:
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                self.page_doc_type.select_doc_type("report")
                event.accept()
                return
            elif key in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                self.page_doc_type.select_doc_type("compromise")
                event.accept()
                return
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                is_on = getattr(self.page_doc_type, 'is_online_report', False)
                self.handle_doc_type_selected(self.current_doc_type or "report", is_on)
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
                is_on = getattr(self.page_doc_type, 'is_online_report', False)
                self.handle_doc_type_selected(self.current_doc_type or "report", is_on)
                event.accept()
                return
            elif self.current_step == 4:
                active_form = self.page_online_form if getattr(self, 'is_online_report', False) else self.page_form
                if active_form.form_section < 2:
                    if hasattr(active_form, 'handle_next_to_attendees') and active_form.form_section == 0:
                        active_form.handle_next_to_attendees()
                    else:
                        active_form.set_form_section(active_form.form_section + 1)
                    event.accept()
                    return
                elif active_form.form_section == 2:
                    if getattr(self, 'is_online_report', False):
                        active_form.handle_generate_docx()
                    else:
                        active_form.trigger_generate_document()
                    event.accept()
                    return

        # PageUp: Previous Step / Previous Section
        if key == Qt.Key.Key_PageUp:
            if self.current_step == 4:
                active_form = self.page_online_form if getattr(self, 'is_online_report', False) else self.page_form
                if active_form.form_section > 0:
                    active_form.set_form_section(active_form.form_section - 1)
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

            # Record in recent files history
            try:
                storage_service.add_recent_file(
                    file_path=file_path,
                    file_name=self.excel_filename,
                    file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                    case_count=len(rows)
                )
            except Exception:
                pass

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
            if hasattr(self, 'page_online_form'):
                self.page_online_form.load_case_row(row, self.mapping)
            if not self.page_form.txt_court_name.text().strip():
                default_court = storage_service.get_default_court_name()
                if default_court:
                    self.page_form.txt_court_name.setText(default_court)
                    if hasattr(self, 'page_online_form'):
                        self.page_online_form.txt_court_name.setText(default_court)

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
        self.page_doc_type.set_selected_type(self.current_doc_type, getattr(self, 'is_online_report', False))
        self.go_to_step(3)

    def handle_proceed_to_form(self):
        """Backwards compatibility proxy for proceed_to_form_requested."""
        self.handle_proceed_from_table()

    def handle_doc_type_selected(self, doc_type: str, is_online: bool = False):
        """From Step 3 (Doc Type Selection), proceed to Step 4 (Form Wizard)."""
        self.current_doc_type = doc_type
        self.is_online_report = is_online if doc_type == "report" else False
        self.page_table.set_doc_type(doc_type)

        if not self.selected_row_data:
            orig_idx = self.page_table.get_selected_original_index()
            if orig_idx is not None and 0 <= orig_idx < len(self.excel_rows):
                self.handle_row_selected(orig_idx)
            else:
                QMessageBox.warning(self, "แจ้งเตือน", "กรุณาคลิกเลือกคดีในตารางก่อน")
                self.go_to_step(2)
                return

        default_court = storage_service.get_default_court_name()

        if self.is_online_report:
            if self.selected_row_data and self.mapping:
                self.page_online_form.load_case_row(self.selected_row_data, self.mapping)
            if not self.page_online_form.txt_court_name.text().strip() and default_court:
                self.page_online_form.txt_court_name.setText(default_court)
            self.page_online_form.set_form_section(0)
        else:
            self.page_form.set_doc_type(doc_type)
            if self.selected_row_data and self.mapping:
                self.page_form.load_case_row(self.selected_row_data, self.mapping)
            if not self.page_form.txt_court_name.text().strip() and default_court:
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
        if hasattr(self, 'page_online_form'):
            self.page_online_form.refresh_judge1_completer()
        current_j1 = self.page_form.cmb_judge1.currentText().strip()
        if current_j1:
            self.page_form.handle_judge1_changed(current_j1)
            if hasattr(self, 'page_online_form'):
                self.page_online_form.handle_judge1_changed(current_j1)

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

    def open_about_dialog(self):
        """Open About dialog displaying system specs, version, changelog, and directories."""
        dlg = AboutDialog(self)
        dlg.exec()

    def check_first_run_tutorial(self):
        """Check if this is the user's first time launching CODS and prompt onboarding wizard."""
        if not storage_service.is_tutorial_completed("welcome_wizard"):
            self.open_welcome_wizard()
        elif not storage_service.is_tutorial_completed("step_menu"):
            self.show_step_tutorial(0)

    def open_welcome_wizard(self):
        """Launch the first-time welcome wizard dialog."""
        dlg = WelcomeWizardDialog(self)
        if dlg.exec():
            court_name = storage_service.get_default_court_name()
            if court_name:
                self.handle_court_saved_as_default(court_name)
            # After finishing welcome wizard, show menu spotlight tour if tutorials enabled
            QTimer.singleShot(350, lambda: self.show_step_tutorial(0))

    def show_step_tutorial(self, step_idx: int, force: bool = False):
        """Display interactive spotlight tutorial for the given step if not completed or forced."""
        key_map = {
            0: ("step_menu", self.page_menu),
            1: ("step_import", self.page_import),
            2: ("step_table", self.page_table),
            3: ("step_doctype", self.page_doc_type),
            4: ("step_form", self.page_form),
        }
        if step_idx not in key_map:
            return

        tut_key, page = key_map[step_idx]
        if step_idx == 4 and getattr(self, 'is_online_report', False):
            page = self.page_online_form
            tut_key = "step_online_form"

        if not force and storage_service.is_tutorial_completed(tut_key):
            return

        if hasattr(page, "get_tutorial_steps"):
            steps = list(page.get_tutorial_steps())
            if step_idx == 0 and hasattr(self, 'sidebar') and hasattr(self.sidebar, 'tools_title'):
                steps.append(TutorialStep(
                    target=self.sidebar.tools_title,
                    title="6. เมนูคลังข้อมูล & ตั้งค่าบน Sidebar (เข้าถึงได้ทุกหน้า)",
                    description="ไม่ว่าท่านจะกำลังทำเอกสารอยู่ในขั้นตอนใด สามารถเปิดคลัง Template, คู่องค์คณะ, จัดการบทบาทผู้มาศาล หรือตั้งค่าศาลเริ่มต้นได้จากแถบเมนูด้านข้างนี้ตลอดเวลา",
                    preferred_position="right"
                ))
            if steps:
                # Close any existing overlay
                for child in self.findChildren(TutorialOverlay):
                    child.close_and_cleanup()
                overlay = TutorialOverlay(self, tut_key, steps)
                overlay.show()

    def open_tutorial_menu(self):
        """Modal menu for launching tutorials, resetting tours, or viewing shortcuts."""
        dlg = QDialog(self)
        dlg.setWindowTitle("แนะนำการใช้งาน CODS")
        dlg.setFixedWidth(460)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(14)

        lbl_title = QLabel("ศูนย์แนะนำการใช้งาน (Tutorial & Help Center) - CODS", dlg)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e1b4b;")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel("เลือกรูปแบบการแนะนำการใช้งานที่ท่านต้องการ:", dlg)
        lbl_desc.setStyleSheet("font-size: 13px; color: #64748b;")
        layout.addWidget(lbl_desc)

        btn_wizard = QPushButton("🌟 เริ่มทัวร์แนะนำโปรแกรม (Welcome Wizard)", dlg)
        btn_wizard.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_wizard.setStyleSheet("""
            QPushButton {
                background-color: #faf5ff;
                border: 1.5px solid #d8b4fe;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
                color: #581c87;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
                border-color: #a855f7;
            }
        """)
        btn_wizard.clicked.connect(lambda: (dlg.accept(), self.open_welcome_wizard()))
        layout.addWidget(btn_wizard)

        btn_library_tour = QPushButton("📚 แนะนำเมนูคลังข้อมูลและการตั้งค่า (Settings & Library Tour)", dlg)
        btn_library_tour.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_library_tour.setStyleSheet("""
            QPushButton {
                background-color: #faf5ff;
                border: 1.5px solid #d8b4fe;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
                color: #581c87;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
                border-color: #a855f7;
            }
        """)
        btn_library_tour.clicked.connect(lambda: (dlg.accept(), self.go_to_step(0), self.show_step_tutorial(0, force=True)))
        layout.addWidget(btn_library_tour)

        btn_spotlight = QPushButton("💡 เริ่มแนะนำหน้าจอปัจจุบัน (Spotlight Tour)", dlg)
        btn_spotlight.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_spotlight.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }
        """)
        btn_spotlight.clicked.connect(lambda: (dlg.accept(), self.show_step_tutorial(self.current_step, force=True)))
        layout.addWidget(btn_spotlight)

        btn_shortcuts = QPushButton("⌨️ คู่มือปุ่มลัดคีย์บอร์ดทั้งหมด (Shortcuts Guide)", dlg)
        btn_shortcuts.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_shortcuts.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 600;
                color: #1e293b;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }
        """)
        btn_shortcuts.clicked.connect(lambda: (dlg.accept(), self.open_shortcuts_guide()))
        layout.addWidget(btn_shortcuts)

        btn_reset = QPushButton("🔄 รีเซ็ตการแนะนำทั้งหมด (เริ่มแสดงคำแนะนำใหม่ทุกหน้า)", dlg)
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #fff1f2;
                border: 1.5px solid #fecdd3;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 13.5px;
                font-weight: 600;
                color: #b91c1c;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #ffe4e6;
                border-color: #f87171;
            }
        """)

        def do_reset():
            storage_service.reset_all_tutorials()
            dlg.accept()
            QMessageBox.information(
                self,
                "รีเซ็ตคำแนะนำสำเร็จ",
                "ระบบได้รีเซ็ตสถานะคำแนะนำเรียบร้อยแล้ว\n"
                "ระบบจะแสดงการแนะนำแบบส่องไฟ (Spotlight) ให้ใหม่เมื่อท่านเข้าสู่แต่ละหน้าจอ"
            )

        btn_reset.clicked.connect(do_reset)
        layout.addWidget(btn_reset)

        btn_close = QPushButton("ปิด", dlg)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #e2e8f0;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                color: #475569;
            }
            QPushButton:hover {
                background-color: #cbd5e1;
            }
        """)
        btn_close.clicked.connect(dlg.reject)
        layout.addWidget(btn_close)

        dlg.exec()




JADSMainWindow = CODSMainWindow
