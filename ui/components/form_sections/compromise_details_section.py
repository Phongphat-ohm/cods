"""
Compromise Agreement Details Section Component.
Encapsulates compromise case subjects, settlement agreement dates, court fee refunds,
Thai currency formatting, and real-time case settlement summary generation.
"""

import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from services.excel_service import to_full_buddhist_year, THAI_MONTHS
from services.icon_service import get_icon
from services import storage_service
from ui.components.autocomplete_input import JudicialAutocompleteInput

COMMON_COMPROMISE_SUBJECTS = [
    "กู้ยืม", "ผิดสัญญา", "ละเมิด", "บัตรเครดิต", "สินเชื่อบุคคล",
    "ซื้อขาย", "จ้างทำของ", "เช่าซื้อ", "ค้ำประกัน", "จำนอง", "มรดก"
]


class CompromiseDetailsWidget(QWidget):
    """Component for Compromise Settlement details & Court Fee Refund calculations."""

    summary_updated = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

        group_comp = QFrame()
        group_comp.setObjectName("innerGroupFrame")
        group_comp_lay = QVBoxLayout(group_comp)
        group_comp_lay.setContentsMargins(20, 18, 20, 20)
        group_comp_lay.setSpacing(14)

        # Title bar
        h_comp_title = QHBoxLayout()
        lbl_comp_title = QLabel("รายละเอียดสัญญาประนีประนอมยอมความและคำพิพากษาตามยอม")
        lbl_comp_title.setObjectName("sectionHeaderTitle")
        h_comp_title.addWidget(lbl_comp_title)
        h_comp_title.addStretch()

        badge_req = QLabel("* จำเป็นต้องกรอกทุกช่อง")
        badge_req.setStyleSheet("font-size: 13px; font-weight: 600; color: #dc2626; background: #fee2e2; border-radius: 6px; padding: 4px 10px;")
        h_comp_title.addWidget(badge_req)
        group_comp_lay.addLayout(h_comp_title)

        # Field 1: Subject (case_subject)
        v_subj = QVBoxLayout()
        v_subj.setSpacing(5)
        h_subj_lbl = QHBoxLayout()
        lbl_subj = QLabel("เรื่อง (ข้อหา / ข้อพิพาทแห่งคดี)")
        lbl_subj.setObjectName("fieldLabel")
        lbl_req1 = QLabel("* (จำเป็นต้องกรอก)")
        lbl_req1.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 600;")
        h_subj_lbl.addWidget(lbl_subj)
        h_subj_lbl.addWidget(lbl_req1)
        h_subj_lbl.addStretch()
        v_subj.addLayout(h_subj_lbl)

        self.txt_compromise_subject = JudicialAutocompleteInput(
            items=COMMON_COMPROMISE_SUBJECTS,
            placeholder="พิมพ์หรือเลือกข้อหาแห่งคดี เช่น กู้ยืม, บัตรเครดิต, ซื้อขาย, เช่าซื้อ..."
        )
        v_subj.addWidget(self.txt_compromise_subject)
        group_comp_lay.addLayout(v_subj)

        # Field 2: Compromise Agreement Date
        v_date = QVBoxLayout()
        v_date.setSpacing(5)
        h_date_lbl = QHBoxLayout()
        lbl_c_date = QLabel("สัญญาประนีประนอมยอมความ ฉบับลงวันที่")
        lbl_c_date.setObjectName("fieldLabel")
        lbl_req2 = QLabel("* (จำเป็นต้องกรอก)")
        lbl_req2.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 600;")
        h_date_lbl.addWidget(lbl_c_date)
        h_date_lbl.addWidget(lbl_req2)
        h_date_lbl.addStretch()

        self.btn_fill_excel_date = QPushButton("ใช้วันนัดจากข้อมูลคดี")
        self.btn_fill_excel_date.setObjectName("secondaryButtonSmall")
        self.btn_fill_excel_date.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btn_fill_excel_date.setIcon(get_icon("calendar", color="#4c1d95", size=13))
        self.btn_fill_excel_date.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; }"
        )
        h_date_lbl.addWidget(self.btn_fill_excel_date)

        self.btn_fill_today_date = QPushButton("ใช้วันนี้")
        self.btn_fill_today_date.setObjectName("secondaryButtonSmall")
        self.btn_fill_today_date.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btn_fill_today_date.setIcon(get_icon("clock", color="#4c1d95", size=13))
        self.btn_fill_today_date.setStyleSheet(
            "QPushButton { background-color: #f8fafc; color: #334155; border: 1px solid #cbd5e1; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f1f5f9; }"
        )
        self.btn_fill_today_date.clicked.connect(self.fill_compromise_date_today)
        h_date_lbl.addWidget(self.btn_fill_today_date)
        v_date.addLayout(h_date_lbl)

        self.txt_compromise_date = QLineEdit()
        self.txt_compromise_date.setPlaceholderText("ตัวอย่าง: 18 ตุลาคม 2569 หรือ 18 ต.ค. 69")
        v_date.addWidget(self.txt_compromise_date)
        group_comp_lay.addLayout(v_date)

        # Field 3: Court Fee Refund (refund_total)
        v_refund = QVBoxLayout()
        v_refund.setSpacing(5)
        h_refund_lbl = QHBoxLayout()
        lbl_refund = QLabel("คืนค่าขึ้นศาลเป็นกรณีพิเศษ (บาท)")
        lbl_refund.setObjectName("fieldLabel")
        lbl_req3 = QLabel("* (จำเป็นต้องกรอก)")
        lbl_req3.setStyleSheet("color: #dc2626; font-size: 12px; font-weight: 600;")
        h_refund_lbl.addWidget(lbl_refund)
        h_refund_lbl.addWidget(lbl_req3)
        h_refund_lbl.addStretch()

        self.btn_convert_thai_num = QPushButton("แปลงเป็นเลขไทย / อารบิก")
        self.btn_convert_thai_num.setObjectName("secondaryButtonSmall")
        self.btn_convert_thai_num.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btn_convert_thai_num.setIcon(get_icon("hash", color="#4c1d95", size=13))
        self.btn_convert_thai_num.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; }"
        )
        self.btn_convert_thai_num.clicked.connect(self.convert_refund_to_thai_digits)
        h_refund_lbl.addWidget(self.btn_convert_thai_num)
        v_refund.addLayout(h_refund_lbl)

        self.txt_refund_total = QLineEdit()
        self.txt_refund_total.setPlaceholderText("ระบุจำนวนเงินที่สั่งคืน เช่น 2,500 หรือ ๒,๕๐๐ (ระบบใส่ลูกน้ำให้อัตโนมัติ)")
        self.txt_refund_total.textEdited.connect(self.handle_refund_total_edited)
        v_refund.addWidget(self.txt_refund_total)
        group_comp_lay.addLayout(v_refund)

        main_layout.addWidget(group_comp)

        # Summary Frame (created here, but placed in Section 3 summary page)
        self.summary_card = QFrame()
        self.summary_card.setObjectName("innerGroupFrame")
        self.summary_card.setStyleSheet("background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px;")
        sum_layout = QVBoxLayout(self.summary_card)
        sum_layout.setContentsMargins(16, 14, 16, 14)
        sum_layout.setSpacing(8)

        lbl_sum_head = QLabel("สรุปข้อมูลสัญญาประนีประนอมยอมความและคำพิพากษาตามยอม:")
        lbl_sum_head.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")
        sum_layout.addWidget(lbl_sum_head)

        self.lbl_comp_summary_text = QLabel()
        self.lbl_comp_summary_text.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_comp_summary_text.setStyleSheet("font-size: 13.5px; color: #334155; line-height: 1.6;")
        self.lbl_comp_summary_text.setWordWrap(True)
        sum_layout.addWidget(self.lbl_comp_summary_text)

    def connect_case_date_button(self, callback):
        self.btn_fill_excel_date.clicked.connect(callback)

    def fill_compromise_date_from_values(self, d: str, m: str, y: str):
        if not (d or m or y):
            QMessageBox.information(self, "แจ้งเตือน", "ไม่พบข้อมูลวันที่ในฟอร์ม กรุณาระบุในแท็บ 'ข้อมูลคดี & องค์คณะ'")
            return
        full_y = to_full_buddhist_year(y) if y else ""
        parts = [p for p in [d, m, full_y] if p]
        self.txt_compromise_date.setText(" ".join(parts))

    def fill_compromise_date_today(self):
        now = datetime.now()
        d_val = str(now.day)
        m_val = THAI_MONTHS[now.month - 1] if 1 <= now.month <= 12 else ""
        y_val = str(now.year + 543)
        parts = [p for p in [d_val, m_val, y_val] if p]
        self.txt_compromise_date.setText(" ".join(parts))

    @staticmethod
    def format_thai_currency(text: str) -> str:
        """Format number string with Thai comma thousands separators, supporting both Arabic and Thai numerals."""
        if not text:
            return ""
        has_dot = '.' in text
        parts = text.split('.', 1)
        int_part = parts[0]
        dec_part = parts[1] if has_dot else ""

        clean_int = re.sub(r'[^0-9\u0e50-\u0e59]', '', int_part)
        if not clean_int:
            if has_dot:
                clean_dec = re.sub(r'[^0-9\u0e50-\u0e59]', '', dec_part)[:2]
                return f".{clean_dec}"
            return ""

        reversed_digits = clean_int[::-1]
        chunks = [reversed_digits[i:i+3] for i in range(0, len(reversed_digits), 3)]
        formatted_int = ','.join(chunks)[::-1]

        if has_dot:
            clean_dec = re.sub(r'[^0-9\u0e50-\u0e59]', '', dec_part)[:2]
            return f"{formatted_int}.{clean_dec}"
        return formatted_int

    def handle_refund_total_edited(self, raw_text: str):
        """Auto-formats currency with commas as the user types, preserving cursor position."""
        cursor_pos = self.txt_refund_total.cursorPosition()
        chars_before = raw_text[:cursor_pos]
        significant_before = len(re.findall(r'[0-9\u0e50-\u0e59.]', chars_before))

        formatted = self.format_thai_currency(raw_text)
        if formatted != raw_text:
            self.txt_refund_total.blockSignals(True)
            self.txt_refund_total.setText(formatted)
            self.txt_refund_total.blockSignals(False)

            if significant_before == 0:
                new_cursor = 0
            else:
                count = 0
                new_cursor = len(formatted)
                for idx, ch in enumerate(formatted):
                    if ch in '0123456789๐๑๒๓๔๕๖๗๘๙.':
                        count += 1
                    if count == significant_before:
                        new_cursor = idx + 1
                        break
            self.txt_refund_total.setCursorPosition(new_cursor)

    def convert_refund_to_thai_digits(self):
        val = self.txt_refund_total.text().strip()
        if not val:
            return
        arabic_to_thai = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
        thai_to_arabic = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")

        has_arabic = any(c in "0123456789" for c in val)
        if has_arabic:
            new_val = val.translate(arabic_to_thai)
        else:
            new_val = val.translate(thai_to_arabic)

        formatted = self.format_thai_currency(new_val)
        self.txt_refund_total.setText(formatted)

    def update_summary(self, case_data: Dict[str, str], j1: str, j2: str):
        default_court = storage_service.get_default_court_name()
        court = case_data.get("court_name", "") or default_court or "-"
        court_display = court if (court.startswith("ศาล") or court == "-") else f"ศาล{court}"

        black = case_data.get("case_black_no", "") or "-"
        red = case_data.get("case_red_no", "") or "-"
        d = case_data.get("day", "") or "-"
        m = case_data.get("month", "") or "-"
        y = case_data.get("year", "") or "-"
        c_type = case_data.get("case_type", "") or "-"
        plaintiff = case_data.get("plaintiff_name", "") or "-"
        defendant = case_data.get("defendant_name", "") or "-"

        subj = self.txt_compromise_subject.text().strip() or "(ยังไม่ระบุ)"
        c_date = self.txt_compromise_date.text().strip() or "(ยังไม่ระบุ)"
        refund = self.txt_refund_total.text().strip() or "(ยังไม่ระบุ)"
        j1_display = j1 or "-"
        j2_display = j2 or "(ไม่มีองค์คณะคนที่ ๒)"

        summary_html = f"""
        <b>ข้อมูลคดี:</b> คดีหมายเลขดำที่ <b>{black}</b> &nbsp;|&nbsp; คดีหมายเลขแดงที่ <b>{red}</b><br/>
        <b>ศาล:</b> {court_display} &nbsp;|&nbsp; <b>ความ:</b> {c_type}<br/>
        <b>วันที่ในเอกสาร:</b> วันที่ {d} เดือน {m} พุทธศักราช {y}<br/>
        <b>คู่ความ:</b> โจทก์: <b>{plaintiff}</b> &nbsp;|&nbsp; จำเลย: <b>{defendant}</b><br/>
        <b>เรื่อง (ข้อหาแห่งคดี):</b> <span style='color: #1e3a8a; font-weight: bold;'>{subj}</span><br/>
        <b>สัญญาประนีประนอมยอมความ:</b> ฉบับลงวันที่ <b>{c_date}</b><br/>
        <b>คืนค่าขึ้นศาลเป็นกรณีพิเศษ:</b> <span style='color: #16a34a; font-weight: bold;'>{refund} บาท</span><br/>
        <b>องค์คณะผู้พิพากษา:</b> เจ้าของสำนวน: {j1_display} &nbsp;|&nbsp; องค์คณะ: {j2_display}
        """
        self.lbl_comp_summary_text.setText(summary_html)
        self.summary_updated.emit()

    def get_compromise_data(self) -> Dict[str, str]:
        return {
            "case_subject": self.txt_compromise_subject.text().strip(),
            "compromise_date": self.txt_compromise_date.text().strip(),
            "refund_total": self.txt_refund_total.text().strip()
        }

    def load_compromise_data(self, row: dict, mapping: dict, d: str = "", m: str = "", y: str = ""):
        """Populate compromise subject and auto-suggest date from case information."""
        # Auto-suggest formatted compromise date if empty (e.g. 17 กันยายน 2569)
        if not self.txt_compromise_date.text().strip():
            if d and m and y:
                full_y = to_full_buddhist_year(y) if y else ""
                parts = [p for p in [d, m, full_y] if p]
                self.txt_compromise_date.setText(" ".join(parts))

        # Check if row has subject/matter column
        subj_col = mapping.get('case_subject') or mapping.get('เรื่อง')
        if not subj_col:
            for c in row.keys():
                if 'เรื่อง' in c or 'ข้อหา' in c:
                    subj_col = c
                    break
        if subj_col:
            v_subj = str(row.get(subj_col, '')).strip() if row.get(subj_col) is not None else ""
            if v_subj:
                self.txt_compromise_subject.setText(v_subj)
