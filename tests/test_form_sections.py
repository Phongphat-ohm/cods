"""
Unit Tests for Modular Form Section Components.
Tests CaseInfoSectionWidget, BenchPairingWidget, CompromiseDetailsWidget,
ParagraphsSectionWidget, and DynamicVariablesPanel.
"""

import unittest
from PySide6.QtWidgets import QApplication

# Ensure QApplication instance exists
app = QApplication.instance()
if not app:
    app = QApplication([])

from ui.components.form_sections import (
    CaseInfoSectionWidget,
    BenchPairingWidget,
    CompromiseDetailsWidget,
    ParagraphsSectionWidget,
    DynamicVariablesPanel
)
from services import storage_service


class TestFormSections(unittest.TestCase):

    def test_case_info_section_get_and_load(self):
        widget = CaseInfoSectionWidget()
        sample_row = {
            "คดีดำ": "ผบE1/2569",
            "คดีแดง": "ผบE2/2569",
            "ศาล": "ศาลแพ่ง",
            "ความ": "แพ่ง",
            "เหตุ": "สืบพยานโจทก์",
            "วันที่": "18 ตุลาคม 2569",
            "เวลา": "09.00 น.",
            "โจทก์": "นาย ก.",
            "จำเลย": "นาย ข."
        }
        mapping = {
            "case_black": "คดีดำ",
            "case_red": "คดีแดง",
            "court": "ศาล",
            "case_type": "ความ",
            "hearing_purpose": "เหตุ",
            "date": "วันที่",
            "time": "เวลา",
            "plaintiff": "โจทก์",
            "defendant": "จำเลย"
        }
        widget.load_case_row(sample_row, mapping)
        data = widget.get_case_data()

        self.assertEqual(data["case_black_no"], "ผบE1/2569")
        self.assertEqual(data["case_red_no"], "ผบE2/2569")
        self.assertEqual(data["court_name"], "ศาลแพ่ง")
        self.assertEqual(data["case_type"], "แพ่ง")
        self.assertEqual(data["hearing_purpose"], "สืบพยานโจทก์")
        self.assertEqual(data["day"], "18")
        self.assertEqual(data["month"], "ตุลาคม")
        self.assertEqual(data["year"], "2569")
        self.assertEqual(data["hearing_time"], "09.00 น.")
        self.assertEqual(data["plaintiff_name"], "นาย ก.")
        self.assertEqual(data["defendant_name"], "นาย ข.")

    def test_bench_pairing_widget(self):
        widget = BenchPairingWidget()
        widget.set_judges("ผู้พิพากษา ก.", "ผู้พิพากษา ข.")
        j1, j2 = widget.get_judges()
        self.assertEqual(j1, "ผู้พิพากษา ก.")
        self.assertEqual(j2, "ผู้พิพากษา ข.")
        self.assertEqual(widget.cmb_judge1.text(), "ผู้พิพากษา ก.")

    def test_compromise_details_currency_and_data(self):
        widget = CompromiseDetailsWidget()
        # Test Thai currency formatting
        fmt1 = widget.format_thai_currency("2500")
        self.assertEqual(fmt1, "2,500")

        fmt2 = widget.format_thai_currency("1234567.89")
        self.assertEqual(fmt2, "1,234,567.89")

        widget.txt_compromise_subject.setText("กู้ยืม")
        widget.txt_compromise_date.setText("18 ตุลาคม 2569")
        widget.txt_refund_total.setText("2,500")

        comp_data = widget.get_compromise_data()
        self.assertEqual(comp_data["case_subject"], "กู้ยืม")
        self.assertEqual(comp_data["compromise_date"], "18 ตุลาคม 2569")
        self.assertEqual(comp_data["refund_total"], "2,500")

    def test_paragraphs_section_card_management(self):
        widget = ParagraphsSectionWidget()
        self.assertEqual(len(widget.paragraph_cards), 0)

        c1 = widget.add_paragraph_card("ย่อหน้าที่หนึ่ง")
        c2 = widget.add_paragraph_card("ย่อหน้าที่สอง")
        self.assertEqual(len(widget.paragraph_cards), 2)
        self.assertEqual(widget.get_paragraph_texts(), ["ย่อหน้าที่หนึ่ง", "ย่อหน้าที่สอง"])

        widget.move_paragraph_up(c2)
        self.assertEqual(widget.get_paragraph_texts(), ["ย่อหน้าที่สอง", "ย่อหน้าที่หนึ่ง"])

        widget.delete_paragraph_card(c1)
        self.assertEqual(len(widget.paragraph_cards), 1)
        self.assertEqual(widget.get_paragraph_texts(), ["ย่อหน้าที่สอง"])

        widget.clear_paragraphs()
        self.assertEqual(len(widget.paragraph_cards), 0)

    def test_dynamic_variables_panel_scan(self):
        panel = DynamicVariablesPanel()
        para_widget = ParagraphsSectionWidget()
        para_widget.add_paragraph_card("นัดสืบพยานวันที่ {{วันนัด:วันที่}} จำนวนเงิน {{ค่าเสียหาย:ตัวเลข}} บาท")

        panel.scan_and_update(para_widget.paragraph_cards, doc_type="report", tpl_path=None)
        # Should detect the 2 variables
        self.assertIn("วันนัด:วันที่", panel.dynamic_inputs)
        self.assertIn("ค่าเสียหาย:ตัวเลข", panel.dynamic_inputs)


if __name__ == "__main__":
    unittest.main()
