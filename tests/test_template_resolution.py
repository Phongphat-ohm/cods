"""
Unit tests for template resolution and UI layout without redundant top template input.
"""

import unittest
import os
from PySide6.QtWidgets import QApplication

app = QApplication.instance()
if not app:
    app = QApplication([])

from services import storage_service
from ui.pages.form_page import FormPage
from ui.pages.online_form_page import OnlineFormPage


class TestTemplateResolutionAndLayout(unittest.TestCase):

    def test_normal_report_uses_correct_template(self):
        page = FormPage()
        page.set_doc_type("report")
        tpl_path = page.get_active_template_path()
        self.assertIsNotNone(tpl_path)
        base = os.path.basename(tpl_path)
        self.assertEqual(base, "รายงานกระบวนพิจารณา.docx")
        self.assertNotIn("ออนใลน์", base)
        self.assertNotIn("ออนไลน์", base)

    def test_compromise_uses_correct_template(self):
        page = FormPage()
        page.set_doc_type("compromise")
        tpl_path = page.get_active_template_path()
        self.assertIsNotNone(tpl_path)
        base = os.path.basename(tpl_path)
        self.assertEqual(base, "คำพิพากษาตามยอม.docx")

    def test_online_report_uses_correct_template(self):
        page = OnlineFormPage()
        tpl_path = page.get_active_template_path()
        self.assertIsNotNone(tpl_path)
        base = os.path.basename(tpl_path)
        self.assertTrue(
            base in ("รายงานกระบวนพิจารณาออนใลน์.docx", "รายงานกระบวนพิจารณาออนไลน์.docx"),
            f"Expected online template but got: {base}"
        )
        self.assertNotEqual(base, "รายงานกระบวนพิจารณา.docx")

    def test_top_template_input_panel_not_visible(self):
        # FormPage Section 3
        form_page = FormPage()
        form_page.set_doc_type("report")
        form_page.set_form_section(2)
        # Verify dynamic_variables_panel is not visible
        self.assertFalse(form_page.dynamic_variables_panel.isVisible())

        # OnlineFormPage Section 3
        online_page = OnlineFormPage()
        online_page.set_form_section(2)
        self.assertFalse(online_page.dynamic_variables_panel.isVisible())

    def test_compromise_summary_placement(self):
        page = FormPage()
        page.set_doc_type("compromise")

        # In Section 2, summary_card is NOT in compromise_widget's layout
        page.set_form_section(1)
        comp_widget_children = [
            page.compromise_widget.layout().itemAt(i).widget()
            for i in range(page.compromise_widget.layout().count())
            if page.compromise_widget.layout().itemAt(i).widget()
        ]
        self.assertNotIn(page.compromise_widget.summary_card, comp_widget_children)

        # In Section 3, summary_card is in page_sec3_compromise layout
        page.set_form_section(2)
        sec3_children = page.page_sec3_compromise.findChildren(type(page.compromise_widget.summary_card))
        self.assertIn(page.compromise_widget.summary_card, sec3_children)


if __name__ == '__main__':
    unittest.main()
