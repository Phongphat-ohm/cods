"""
Unit and Integration Tests for CODS Template Variable System
Tests input types, multiple Thai date format styles, tag parsing, validation, and docx replacement.
"""

import unittest
import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QDate, QEvent, Qt
from PySide6.QtGui import QTextCursor, QKeyEvent

# Ensure QApplication exists for widget testing
app = QApplication.instance()
if not app:
    app = QApplication([])

from services.template_variable_service import (
    parse_variable_tag,
    format_thai_date_by_style,
    parse_date_to_dmy,
    get_variable_replace_pattern,
    normalize_input_type,
    normalize_date_format_style,
    DATE_FORMAT_STYLES
)
from services.docx_service import (
    validate_template_variable,
    replace_in_nodes
)
from ui.components.typed_variable_input import (
    ThaiDatePickerWidget,
    TimeVariableInputWidget,
    NumberVariableInputWidget,
    SelectVariableInputWidget,
    create_typed_variable_input
)
from ui.components.variable_chip_widget import VariableChipComponent
from lxml import etree


class TestTemplateVariableService(unittest.TestCase):

    def test_parse_variable_tag(self):
        # 1. Plain date (inferred)
        meta = parse_variable_tag("วันนัด")
        self.assertEqual(meta['name'], "วันนัด")
        self.assertEqual(meta['type'], "date")
        self.assertEqual(meta['format_style'], "full")

        # 2. Explicit Thai date with full format
        meta = parse_variable_tag("วันนัด:วันที่:เต็ม")
        self.assertEqual(meta['name'], "วันนัด")
        self.assertEqual(meta['type'], "date")
        self.assertEqual(meta['format_style'], "full")

        # 3. Explicit English date with short format
        meta = parse_variable_tag("วันนัดสืบพยาน:date:short")
        self.assertEqual(meta['name'], "วันนัดสืบพยาน")
        self.assertEqual(meta['type'], "date")
        self.assertEqual(meta['format_style'], "short")

        # 4. Numeric date format
        meta = parse_variable_tag("วันนัด:date:numeric")
        self.assertEqual(meta['name'], "วันนัด")
        self.assertEqual(meta['type'], "date")
        self.assertEqual(meta['format_style'], "numeric")

        # 5. Court official format
        meta = parse_variable_tag("วันนัด:วันที่:ทางการ")
        self.assertEqual(meta['name'], "วันนัด")
        self.assertEqual(meta['type'], "date")
        self.assertEqual(meta['format_style'], "court")

        # 6. Time variable
        meta = parse_variable_tag("เวลานัด:เวลา")
        self.assertEqual(meta['name'], "เวลานัด")
        self.assertEqual(meta['type'], "time")

        # 7. Number / Currency variable
        meta = parse_variable_tag("จำนวนเงิน:ตัวเลข")
        self.assertEqual(meta['name'], "จำนวนเงิน")
        self.assertEqual(meta['type'], "number")

        # 8. Select dropdown variable with choices
        meta = parse_variable_tag("ผลการพิจารณา:select:เลื่อนนัด,ไกล่เกลี่ย,สืบพยาน")
        self.assertEqual(meta['name'], "ผลการพิจารณา")
        self.assertEqual(meta['type'], "select")
        self.assertEqual(meta['options'], ["เลื่อนนัด", "ไกล่เกลี่ย", "สืบพยาน"])

    def test_format_thai_date_styles(self):
        # Target date: 18 October 2026 (BE 2569) - Sunday
        d = datetime.date(2026, 10, 18)

        full_d = format_thai_date_by_style(d, "full")
        self.assertEqual(full_d, "18 ตุลาคม 2569")

        short_d = format_thai_date_by_style(d, "short")
        self.assertEqual(short_d, "18 ต.ค. 2569")

        numeric_d = format_thai_date_by_style(d, "numeric")
        self.assertEqual(numeric_d, "18/10/2569")

        court_d = format_thai_date_by_style(d, "court")
        self.assertEqual(court_d, "วันที่ 18 เดือน ตุลาคม พ.ศ. 2569")

        court_short_d = format_thai_date_by_style(d, "court_short")
        self.assertEqual(court_short_d, "วันที่ 18 ต.ค. 2569")

        dm_d = format_thai_date_by_style(d, "day_month")
        self.assertEqual(dm_d, "18 ตุลาคม")

        dm_short_d = format_thai_date_by_style(d, "day_month_short")
        self.assertEqual(dm_short_d, "18 ต.ค.")

        weekday_d = format_thai_date_by_style(d, "weekday_full")
        self.assertEqual(weekday_d, "วันอาทิตย์ที่ 18 ตุลาคม 2569")

        sy_d = format_thai_date_by_style(d, "short_year")
        self.assertEqual(sy_d, "18 ต.ค. 69")

    def test_parse_date_string_and_reformat(self):
        # Parse from short Thai string and reformat to court official
        parsed = format_thai_date_by_style("18 ต.ค. 2569", "court")
        self.assertEqual(parsed, "วันที่ 18 เดือน ตุลาคม พ.ศ. 2569")

        # Parse from slash date and reformat to full
        parsed = format_thai_date_by_style("18/10/2569", "full")
        self.assertEqual(parsed, "18 ตุลาคม 2569")

        # Parse from ISO date and reformat to short
        parsed = format_thai_date_by_style("2026-10-18", "short")
        self.assertEqual(parsed, "18 ต.ค. 2569")

    def test_variable_replace_pattern(self):
        pat = get_variable_replace_pattern("วันนัด")

        # Should match [วันนัด]
        self.assertTrue(pat.search("นัดพร้อมใน [วันนัด] เวลา 09.00 นาฬิกา"))
        # Should match [วันนัด:date:full]
        self.assertTrue(pat.search("นัดพร้อมใน [วันนัด:date:full] เวลา 09.00 นาฬิกา"))
        # Should match [วันนัด:วันที่:ย่อ]
        self.assertTrue(pat.search("นัดพร้อมใน [วันนัด:วันที่:ย่อ] เวลา 09.00 นาฬิกา"))
        # Should match {{วันนัด}}
        self.assertTrue(pat.search("นัดพร้อมใน {{วันนัด}} เวลา 09.00 นาฬิกา"))

        # Replaces cleanly
        replaced = pat.sub("18 ตุลาคม 2569", "นัดพร้อมใน [วันนัด:วันที่:เต็ม] เวลา 09.00 นาฬิกา")
        self.assertEqual(replaced, "นัดพร้อมใน 18 ตุลาคม 2569 เวลา 09.00 นาฬิกา")

    def test_validate_template_variable(self):
        # Valid plain variable
        valid, _ = validate_template_variable("วันนัด")
        self.assertTrue(valid)

        # Valid typed variable
        valid, _ = validate_template_variable("วันนัด:วันที่:เต็ม")
        self.assertTrue(valid)

        valid, _ = validate_template_variable("จำนวนเงิน:number")
        self.assertTrue(valid)

        valid, _ = validate_template_variable("ผลการเจรจา:select:ตกลงได้,ตกลงไม่ได้")
        self.assertTrue(valid)

        # Invalid forbidden keyword
        valid, msg = validate_template_variable("paragraphs")
        self.assertFalse(valid)
        self.assertIn("คำสั่งสงวน", msg)

        # Invalid chars
        valid, msg = validate_template_variable("ชื่อ<ตัวแปร>")
        self.assertFalse(valid)

    def test_docx_replace_in_nodes(self):
        # XML node replacement simulation
        xml_src = "<w:p xmlns:w='http://purl.oclc.org/ooxml/wordprocessingml/main'><w:r><w:t>นัดพร้อมใน [วันนัด:วันที่:เต็ม] เวลา 09.00 นาฬิกา</w:t></w:r></w:p>"
        root = etree.fromstring(xml_src.encode('utf-8'))
        t_nodes = [t for t in root.iter() if t.tag.endswith('}t')]

        replacements = {"วันนัด": "18 ตุลาคม 2569"}
        replace_in_nodes(t_nodes, replacements)

        result_text = "".join(t.text or "" for t in t_nodes)
        self.assertEqual(result_text, "นัดพร้อมใน 18 ตุลาคม 2569 เวลา 09.00 นาฬิกา")


class TestTypedVariableUIWidgets(unittest.TestCase):

    def test_thai_date_picker_widget(self):
        widget = ThaiDatePickerWidget(initial_value="18/10/2569", default_format="full")
        self.assertEqual(widget.get_value(), "18/10/2569")

        # Reformat to short
        widget.set_format("short")
        self.assertEqual(widget.get_value(), "18 ต.ค. 2569")

        # Reformat to court
        widget.set_format("court")
        self.assertEqual(widget.get_value(), "วันที่ 18 เดือน ตุลาคม พ.ศ. 2569")

        # Test apply date
        qd = QDate(2026, 10, 25)
        widget.apply_date(qd)
        self.assertEqual(widget.get_value(), "วันที่ 25 เดือน ตุลาคม พ.ศ. 2569")

    def test_time_variable_widget(self):
        widget = TimeVariableInputWidget(initial_value="09.00 นาฬิกา")
        self.assertEqual(widget.get_value(), "09.00 นาฬิกา")
        widget.set_value("09.30 น.")
        self.assertEqual(widget.get_value(), "09.30 น.")

    def test_number_variable_widget(self):
        widget = NumberVariableInputWidget(initial_value="50,000")
        self.assertEqual(widget.get_value(), "50,000")
        widget._append_baht()
        self.assertEqual(widget.get_value(), "50,000 บาท")

    def test_select_variable_widget(self):
        options = ["เลื่อนนัด", "สืบพยาน", "ไกล่เกลี่ยสำเร็จ"]
        widget = SelectVariableInputWidget(options=options, initial_value="สืบพยาน")
        self.assertEqual(widget.get_value(), "สืบพยาน")
        self.assertEqual(widget.cmb_select.count(), 3)

    def test_variable_chip_component_typed(self):
        # Date chip component
        comp = VariableChipComponent("วันนัด:วันที่:ย่อ", initial_value="18 ต.ค. 2569")
        self.assertEqual(comp.base_name, "วันนัด")
        self.assertEqual(comp.get_value(), "18 ต.ค. 2569")
        self.assertIsInstance(comp.txt_value, ThaiDatePickerWidget)

        # Number chip component
        comp_num = VariableChipComponent("จำนวนเงิน:ตัวเลข", initial_value="100,000")
        self.assertEqual(comp_num.base_name, "จำนวนเงิน")
        self.assertIsInstance(comp_num.txt_value, NumberVariableInputWidget)


class TestTemplateChipKeyFilter(unittest.TestCase):
    """
    Tests for TemplateChipKeyFilter ensuring:
    - Backspace right after a chip enters inside before ']' to edit the variable name
    - Deleting the last remaining character inside removes the variable completely
    - Empty brackets are deleted completely
    - Selected variable content deletion removes delimiters
    """

    def setUp(self):
        from ui.components.template_chip_highlighter import TemplateChipHighlighter, TemplateChipKeyFilter
        from PySide6.QtWidgets import QTextEdit
        self.editor = QTextEdit()
        self.highlighter = TemplateChipHighlighter(self.editor)
        self.ev_bk = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
        self.ev_del = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)

    def test_backspace_enters_variable_for_editing(self):
        # Cursor right after ']'
        self.editor.setPlainText("ศาล [วันนัด] เวลา")
        after_bracket_pos = self.editor.toPlainText().find(']') + 1
        self.assertEqual(after_bracket_pos, 12)
        cur = self.editor.textCursor()
        cur.setPosition(after_bracket_pos)  # after ']'
        self.editor.setTextCursor(cur)

        # Press Backspace
        QApplication.sendEvent(self.editor, self.ev_bk)

        # Cursor should now be inside before ']' (pos 11)
        self.assertEqual(self.editor.textCursor().position(), 11)
        # Content remains unchanged (']' is NOT deleted)
        self.assertEqual(self.editor.toPlainText(), "ศาล [วันนัด] เวลา")

    def test_deleting_last_char_removes_variable_completely(self):
        # Variable has only 1 character left
        self.editor.setPlainText("ศาล [ว] เวลา")
        cur = self.editor.textCursor()
        cur.setPosition(6)  # right after 'ว', before ']'
        self.editor.setTextCursor(cur)

        # Press Backspace to delete 'ว'
        QApplication.sendEvent(self.editor, self.ev_bk)

        # The entire variable [ว] must disappear completely (no leftover brackets)
        self.assertEqual(self.editor.toPlainText(), "ศาล  เวลา")
        self.assertNotIn("[", self.editor.toPlainText())
        self.assertNotIn("]", self.editor.toPlainText())

    def test_empty_brackets_removed_on_backspace(self):
        # Backspace inside empty []
        self.editor.setPlainText("ศาล [] เวลา")
        cur = self.editor.textCursor()
        cur.setPosition(5)  # inside []
        self.editor.setTextCursor(cur)

        QApplication.sendEvent(self.editor, self.ev_bk)
        self.assertEqual(self.editor.toPlainText(), "ศาล  เวลา")

        # Backspace right after empty []
        self.editor.setPlainText("ศาล [] เวลา")
        cur = self.editor.textCursor()
        cur.setPosition(6)  # after []
        self.editor.setTextCursor(cur)

        QApplication.sendEvent(self.editor, self.ev_bk)
        self.assertEqual(self.editor.toPlainText(), "ศาล  เวลา")

    def test_selection_deletion_removes_variable_completely(self):
        self.editor.setPlainText("ศาล [วันนัด] เวลา")
        cur = self.editor.textCursor()
        cur.setPosition(5)  # start of 'วันนัด'
        cur.setPosition(11, QTextCursor.MoveMode.KeepAnchor)  # select 'วันนัด'
        self.editor.setTextCursor(cur)

        # Press Backspace with all inner content selected
        QApplication.sendEvent(self.editor, self.ev_bk)
        self.assertEqual(self.editor.toPlainText(), "ศาล  เวลา")
        self.assertNotIn("[", self.editor.toPlainText())

    def test_select_all_backspace_removes_everything_in_one_keystroke(self):
        # Text containing text and multiple typed variables
        self.editor.setPlainText("ศาลนัด [วันนัด:วันที่:เต็ม] เวลา [เวลานัด:เวลา] นัดสืบพยาน")
        self.editor.selectAll()
        self.assertTrue(self.editor.textCursor().hasSelection())

        # Press Backspace once (like Ctrl+A followed by Backspace)
        QApplication.sendEvent(self.editor, self.ev_bk)
        # Everything must be completely cleared in one shot
        self.assertEqual(self.editor.toPlainText(), "")

    def test_boundary_protection(self):
        # 1. Text after variable: deleting normal text works normally
        self.editor.setPlainText("ศาล [วันนัด] เวลา")
        cur = self.editor.textCursor()
        cur.setPosition(len(self.editor.toPlainText()))  # at the end after 'เวลา'
        self.editor.setTextCursor(cur)

        # Normal backspace deletes characters of 'เวลา' normally
        QApplication.sendEvent(self.editor, self.ev_bk)
        self.assertEqual(self.editor.toPlainText(), "ศาล [วันนัด] เวล")

        # 2. Backspace right at start of inner variable content deletes preceding character outside bracket
        self.editor.setPlainText("ศาล [วันนัด] เวลา")
        cur = self.editor.textCursor()
        cur.setPosition(5)  # right after '['
        self.editor.setTextCursor(cur)

        QApplication.sendEvent(self.editor, self.ev_bk)
        # Should delete space before '['
        self.assertEqual(self.editor.toPlainText(), "ศาล[วันนัด] เวลา")
        # Token intact
        self.assertIn("[วันนัด]", self.editor.toPlainText())

    def test_backspace_on_typed_variable_enters_name_directly(self):
        # Text with typed variable [วันนัด:วันที่:เต็ม]
        self.editor.setPlainText("ศาล [วันนัด:วันที่:เต็ม] เวลา")
        text = self.editor.toPlainText()
        after_pos = text.find(']') + 1
        cur = self.editor.textCursor()
        cur.setPosition(after_pos)
        self.editor.setTextCursor(cur)

        # Press Backspace: should jump to right after 'วันนัด' (pos 11, before hidden ':')
        QApplication.sendEvent(self.editor, self.ev_bk)
        self.assertEqual(self.editor.textCursor().position(), 11)
        # Token remains intact
        self.assertEqual(self.editor.toPlainText(), text)

    def test_deleting_typed_variable_removes_completely(self):
        self.editor.setPlainText("ศาล [ว:วันที่:เต็ม] เวลา")
        text = self.editor.toPlainText()
        after_pos = text.find(']') + 1
        cur = self.editor.textCursor()
        cur.setPosition(after_pos)
        self.editor.setTextCursor(cur)

        # 1st Backspace: moves cursor inside to after 'ว'
        QApplication.sendEvent(self.editor, self.ev_bk)
        self.assertEqual(self.editor.textCursor().position(), 6)

        # 2nd Backspace: deletes the only character 'ว', so the entire typed variable disappears!
        QApplication.sendEvent(self.editor, self.ev_bk)
        self.assertEqual(self.editor.toPlainText(), "ศาล  เวลา")
        self.assertNotIn("[", self.editor.toPlainText())
        self.assertNotIn(":", self.editor.toPlainText())

    def test_autocomplete_select_widget(self):
        options = ["เลื่อนนัดเพื่อเจรจา", "สืบพยานโจทก์", "ไกล่เกลี่ยสำเร็จ"]
        widget = SelectVariableInputWidget(options=options, initial_value="สืบพยานโจทก์")
        self.assertEqual(widget.get_value(), "สืบพยานโจทก์")
        self.assertTrue(widget.cmb_select.isEditable())
        self.assertIsNotNone(widget.cmb_select.completer())
        self.assertEqual(widget.cmb_select.completer().filterMode(), Qt.MatchFlag.MatchContains)
        self.assertTrue(widget.cmb_select.lineEdit().isClearButtonEnabled())
        
        # Test custom value typing
        widget.set_value("นัดฟังคำพิพากษา")
        self.assertEqual(widget.get_value(), "นัดฟังคำพิพากษา")

    def test_format_chips_html_clean_name_only(self):
        from ui.components.template_chip_highlighter import format_text_as_chips_html
        html = format_text_as_chips_html("ศาลนัด [วันนัด:วันที่:เต็ม] เวลา [เวลานัด:เวลา]")
        self.assertIn("วันนัด", html)
        self.assertIn("เวลานัด", html)
        self.assertNotIn("วันที่:เต็ม", html)
        self.assertNotIn("display_type_label", html)


    def test_modular_components_architecture(self):
        # 1. Direct modular imports from variable_inputs
        from ui.components.variable_inputs import (
            ThaiDatePickerWidget as DP1,
            TimeVariableInputWidget as TI1,
            NumberVariableInputWidget as NI1,
            SelectVariableInputWidget as SI1,
            create_typed_variable_input as factory1
        )
        # 2. Re-exported imports from ui.components
        from ui.components import (
            ThaiDatePickerWidget as DP2,
            TimeVariableInputWidget as TI2,
            NumberVariableInputWidget as NI2,
            SelectVariableInputWidget as SI2,
            create_typed_variable_input as factory2,
            show_date_chip_menu,
            show_combined_chip_menu,
        )
        self.assertIs(DP1, DP2)
        self.assertIs(TI1, TI2)
        self.assertIs(NI1, NI2)
        self.assertIs(SI1, SI2)
        self.assertIs(factory1, factory2)

        # 3. Test factory creation for all 5 types
        date_w = factory1({"type": "date", "name": "วันนัด", "format_style": "full"})
        self.assertIsInstance(date_w, DP1)

        time_w = factory1({"type": "time", "name": "เวลานัด"})
        self.assertIsInstance(time_w, TI1)

        num_w = factory1({"type": "number", "name": "ทุนทรัพย์"})
        self.assertIsInstance(num_w, NI1)

        sel_w = factory1({"type": "select", "name": "ผลการเจรจา", "options": ["ก", "ข"]})
        self.assertIsInstance(sel_w, SI1)

        # 4. Dialog modular import
        from ui.dialogs.variable_define_dialog import VariableDefineDialog
        from ui.dialogs import VariableDefineDialog as Dlg2
        self.assertIs(VariableDefineDialog, Dlg2)

    def test_number_comma_formatting(self):
        from services.template_variable_service import format_number_comma
        self.assertEqual(format_number_comma("1000"), "1,000")
        self.assertEqual(format_number_comma("50000"), "50,000")
        self.assertEqual(format_number_comma("1000000"), "1,000,000")
        self.assertEqual(format_number_comma("1234567.50"), "1,234,567.50")
        self.assertEqual(format_number_comma("50000 บาท"), "50,000 บาท")
        self.assertEqual(format_number_comma("1,000,000 บาท"), "1,000,000 บาท")
        self.assertEqual(format_number_comma("-50000"), "-50,000")

    def test_number_widget_auto_formatting(self):
        widget = NumberVariableInputWidget("50000")
        self.assertEqual(widget.get_value(), "50,000")
        widget.set_value("1000000")
        self.assertEqual(widget.get_value(), "1,000,000")
        widget._append_baht()
        self.assertEqual(widget.get_value(), "1,000,000 บาท")


if __name__ == '__main__':
    unittest.main()

