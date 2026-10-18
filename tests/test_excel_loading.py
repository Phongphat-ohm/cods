"""
Test Excel Data Loading and Propagation across all forms and widgets.
"""

import unittest
import os
from PySide6.QtWidgets import QApplication

app = QApplication.instance()
if not app:
    app = QApplication([])

from services import excel_service, storage_service
from ui.pages.form_page import FormPage
from ui.pages.online_form_page import OnlineFormPage
from ui.pages.doc_type_page import DocTypePage


class TestExcelLoading(unittest.TestCase):

    def test_full_excel_propagation(self):
        # Raw headers commonly found in court Excel schedules
        raw_headers = [
            'หมายเลขคดีดำ', 'หมายเลขคดีแดง', 'ประเภทความ', 'ข้อหานัด',
            'ชื่อศาล', 'ชื่อโจทก์', 'ชื่อจำเลย', 'วันนัดพิจารณา',
            'เวลานัด', 'เจ้าของสำนวน', 'เรื่อง'
        ]
        mapping = excel_service.guess_column_mapping(raw_headers)

        sample_row = {
            'หมายเลขคดีดำ': 'ผบE123/2569',
            'หมายเลขคดีแดง': 'ผบE456/2569',
            'ประเภทความ': 'ผู้บริโภค',
            'ข้อหานัด': 'สืบพยานโจทก์',
            'ชื่อศาล': 'ศาลจังหวัดมีนบุรี',
            'ชื่อโจทก์': 'ธนาคารไทยพาณิชย์ จำกัด (มหาชน)',
            'ชื่อจำเลย': 'นายสมศักดิ์ รักดี',
            'วันนัดพิจารณา': '19 ตุลาคม 2569',
            'เวลานัด': '09.30 น.',
            'เจ้าของสำนวน': 'นายผู้พิพากษา หนึ่ง',
            'เรื่อง': 'กู้ยืมเงิน บัตรเครดิต'
        }

        # 1. Test FormPage
        form_page = FormPage()
        form_page.load_case_row(sample_row, mapping)

        self.assertEqual(form_page.txt_case_black.text(), 'ผบE123/2569')
        self.assertEqual(form_page.txt_case_red.text(), 'ผบE456/2569')
        self.assertEqual(form_page.txt_court_name.text(), 'ศาลจังหวัดมีนบุรี')
        self.assertEqual(form_page.txt_case_type.text(), 'ผู้บริโภค')
        self.assertEqual(form_page.txt_hearing_purpose.text(), 'สืบพยานโจทก์')
        self.assertEqual(form_page.txt_plaintiff.text(), 'ธนาคารไทยพาณิชย์ จำกัด (มหาชน)')
        self.assertEqual(form_page.txt_defendant.text(), 'นายสมศักดิ์ รักดี')
        self.assertEqual(form_page.txt_time.text(), '09.30 น.')
        self.assertEqual(form_page.txt_day.text(), '19')
        self.assertEqual(form_page.txt_month.text(), 'ตุลาคม')
        self.assertEqual(form_page.txt_year.text(), '2569')
        self.assertEqual(form_page.cmb_judge1.text(), 'นายผู้พิพากษา หนึ่ง')
        self.assertEqual(form_page.txt_compromise_subject.text(), 'กู้ยืมเงิน บัตรเครดิต')
        self.assertEqual(form_page.txt_compromise_date.text(), '19 ตุลาคม 2569')

        # 2. Test OnlineFormPage
        online_page = OnlineFormPage()
        online_page.load_case_row(sample_row, mapping)

        self.assertEqual(online_page.txt_case_black.text(), 'ผบE123/2569')
        self.assertEqual(online_page.txt_court_name.text(), 'ศาลจังหวัดมีนบุรี')
        self.assertEqual(online_page.txt_plaintiff.text(), 'ธนาคารไทยพาณิชย์ จำกัด (มหาชน)')
        self.assertEqual(online_page.cmb_judge1.text(), 'นายผู้พิพากษา หนึ่ง')

        # 3. Test DocTypePage
        doc_page = DocTypePage()
        doc_page.set_case_info(sample_row, mapping)
        self.assertIn('ผบE123/2569', doc_page.lbl_case_summary.text())
        self.assertIn('ธนาคารไทยพาณิชย์', doc_page.lbl_parties_summary.text())
        self.assertIn('นายสมศักดิ์ รักดี', doc_page.lbl_parties_summary.text())

    def test_immediate_associate_judge_autofill(self):
        # Configure a paired associate judge in storage
        storage_service.save_or_update_pair("นายสมเกียรติ ปฏิบัติธรรม", "นางสาวกัลยา สุจริต")

        raw_headers = ['หมายเลขคดีดำ', 'เจ้าของสำนวน']
        mapping = excel_service.guess_column_mapping(raw_headers)
        row = {
            'หมายเลขคดีดำ': 'ม100/2569',
            'เจ้าของสำนวน': 'นายสมเกียรติ ปฏิบัติธรรม'
        }

        form_page = FormPage()
        form_page.load_case_row(row, mapping)

        # Judge 1 must be filled
        self.assertEqual(form_page.cmb_judge1.text(), "นายสมเกียรติ ปฏิบัติธรรม")
        # Judge 2 MUST BE AUTO-FILLED IMMEDIATELY without waiting or prompts!
        self.assertEqual(form_page.txt_judge2.text(), "นางสาวกัลยา สุจริต")

        # Test OnlineFormPage as well
        online_page = OnlineFormPage()
        online_page.load_case_row(row, mapping)
        self.assertEqual(online_page.cmb_judge1.text(), "นายสมเกียรติ ปฏิบัติธรรม")
        self.assertEqual(online_page.txt_judge2.text(), "นางสาวกัลยา สุจริต")

        # Test live typing / selection change
        form_page.handle_judge1_changed("นายสมเกียรติ ปฏิบัติธรรม")
        self.assertEqual(form_page.txt_judge2.text(), "นางสาวกัลยา สุจริต")


if __name__ == '__main__':
    unittest.main()
