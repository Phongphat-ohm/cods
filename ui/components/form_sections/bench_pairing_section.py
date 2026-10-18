"""
Bench Pairing Section Component.
Encapsulates judicial bench assignment (primary presiding judge and associate judge),
automatic pair discovery, pairing persistence, and bench management triggers.
"""

from typing import Tuple, Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from services import storage_service
from services.icon_service import get_icon
from ui.components.judicial_card import JudicialAccentCard
from ui.components.autocomplete_input import JudicialAutocompleteInput


class BenchPairingWidget(QWidget):
    """Component for judicial bench pairing and management."""

    bench_manager_requested = Signal()
    pairing_saved = Signal(str, str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        self.bench_frame = JudicialAccentCard(
            stripe_color="#4c1d95",
            border_color="#d8b4fe",
            bg_color="#faf5ff",
            stripe_width=5,
            radius=8
        )
        self.bench_frame.setObjectName("benchContainer")
        bench_layout = QVBoxLayout(self.bench_frame)
        bench_layout.setContentsMargins(18, 14, 16, 16)
        bench_layout.setSpacing(10)

        # Header Bar
        bench_header_bar = QHBoxLayout()
        lbl_bench_title = QLabel("องค์คณะผู้พิพากษา (เลือกผู้พิพากษาเจ้าของสำนวน แล้วองค์คณะจะแสดงอัตโนมัติตามที่จับคู่ไว้)")
        lbl_bench_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #4c1d95;")
        bench_header_bar.addWidget(lbl_bench_title)
        bench_header_bar.addStretch()

        self.btn_save_pairing = QPushButton("บันทึกการจับคู่นี้ (สำหรับครั้งต่อไป)")
        self.btn_save_pairing.setObjectName("secondaryButtonSmall")
        self.btn_save_pairing.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btn_save_pairing.setIcon(get_icon("link", color="#4c1d95", size=14))
        self.btn_save_pairing.setStyleSheet(
            "QPushButton { background-color: #f3e8ff; color: #4c1d95; border: 1px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #e9d5ff; border-color: #c084fc; }"
        )
        self.btn_save_pairing.setToolTip("บันทึกการจับคู่ระหว่างผู้พิพากษาเจ้าของสำนวนและองค์คณะไว้ในระบบ")
        self.btn_save_pairing.clicked.connect(self.handle_save_current_pairing)
        bench_header_bar.addWidget(self.btn_save_pairing)

        self.btn_bench_config = QPushButton("จัดการคู่องค์คณะ...")
        self.btn_bench_config.setObjectName("secondaryButtonSmall")
        self.btn_bench_config.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btn_bench_config.setIcon(get_icon("settings", color="#4c1d95", size=14))
        self.btn_bench_config.setStyleSheet(
            "QPushButton { background-color: #ffffff; color: #4c1d95; border: 1.5px solid #d8b4fe; border-radius: 5px; padding: 4px 10px; font-size: 13px; font-weight: 500; } "
            "QPushButton:hover { background-color: #f3e8ff; border-color: #c084fc; }"
        )
        self.btn_bench_config.setToolTip("จัดการคู่องค์คณะผู้พิพากษา [Ctrl+B]")
        self.btn_bench_config.clicked.connect(self.bench_manager_requested.emit)
        bench_header_bar.addWidget(self.btn_bench_config)

        bench_layout.addLayout(bench_header_bar)

        # Row: Judge 1 & Judge 2
        row_judges = QHBoxLayout()
        row_judges.setSpacing(14)

        # Judge 1
        v_j1 = QVBoxLayout()
        v_j1.setSpacing(5)
        lbl_j1 = QLabel("ผู้พิพากษาเจ้าของสำนวน")
        lbl_j1.setObjectName("fieldLabel")
        self.txt_judge1 = JudicialAutocompleteInput(items=[], placeholder="พิมพ์หรือเลือกชื่อผู้พิพากษาเจ้าของสำนวน...")
        self.txt_judge1.textChanged.connect(self.handle_judge1_changed)
        v_j1.addWidget(lbl_j1)
        v_j1.addWidget(self.txt_judge1)
        row_judges.addLayout(v_j1)

        # Judge 2
        v_j2 = QVBoxLayout()
        v_j2.setSpacing(5)
        lbl_j2 = QLabel("ผู้พิพากษาองค์คณะ")
        lbl_j2.setObjectName("fieldLabel")
        self.txt_judge2 = JudicialAutocompleteInput(items=[], placeholder="ชื่อผู้พิพากษาองค์คณะ (ขึ้นอัตโนมัติหรือเลือกได้)...")
        v_j2.addWidget(lbl_j2)
        v_j2.addWidget(self.txt_judge2)
        row_judges.addLayout(v_j2)

        bench_layout.addLayout(row_judges)

        # Bench Status Label
        self.lbl_bench_status = QLabel("")
        self.lbl_bench_status.setStyleSheet("font-size: 13px; color: #0284c7; font-weight: 500;")
        self.lbl_bench_status.setVisible(False)
        bench_layout.addWidget(self.lbl_bench_status)

        main_layout.addWidget(self.bench_frame)

    @property
    def cmb_judge1(self):
        """Compatibility adapter for code referencing cmb_judge1 as a QComboBox-like object."""
        return self.txt_judge1

    def refresh_completers(self):
        """Reload bench pairs from database/JSON and refresh autocomplete choices."""
        pairs = storage_service.load_bench_pairs()
        current_j1 = self.txt_judge1.text()
        current_j2 = self.txt_judge2.text()

        judge1_names: List[str] = []
        judge2_names: List[str] = []
        for p in pairs:
            j1 = p.get("judge1", "").strip()
            j2 = p.get("judge2", "").strip()
            if j1 and j1 not in judge1_names:
                judge1_names.append(j1)
            if j2 and j2 not in judge2_names:
                judge2_names.append(j2)

        self.txt_judge1.set_items(judge1_names)
        self.txt_judge2.set_items(judge2_names)

        if current_j1:
            self.txt_judge1.setText(current_j1)
        if current_j2:
            self.txt_judge2.setText(current_j2)

    def refresh_judge1_completer(self):
        """Alias for refresh_completers to maintain 100% backward compatibility."""
        self.refresh_completers()

    def handle_judge1_changed(self, text: str):
        j1_clean = text.strip()
        if not j1_clean:
            self.txt_judge2.clear()
            self.update_bench_status("")
            return

        paired_j2 = storage_service.find_paired_judge(j1_clean)
        if paired_j2:
            self.txt_judge2.setText(paired_j2)
            self.update_bench_status(f"ตรวจพบและเติมชื่อองค์คณะอัตโนมัติทันที: '{paired_j2}'", "font-size: 13px; color: #16a34a; font-weight: 600;")
        else:
            self.update_bench_status("ยังไม่มีการจับคู่สำหรับผู้พิพากษาท่านนี้ (พิมพ์ชื่อองค์คณะแล้วกดปุ่ม 'บันทึกการจับคู่นี้' ได้)", "font-size: 13px; color: #64748b;")

    def update_bench_status(self, text: str, style: str = ""):
        if not text:
            self.lbl_bench_status.setVisible(False)
            self.lbl_bench_status.setText("")
        else:
            self.lbl_bench_status.setVisible(True)
            self.lbl_bench_status.setText(text)
            if style:
                self.lbl_bench_status.setStyleSheet(style)

    def handle_save_current_pairing(self):
        j1 = self.txt_judge1.text().strip()
        j2 = self.txt_judge2.text().strip()
        if not j1:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อผู้พิพากษาเจ้าของสำนวน")
            self.txt_judge1.setFocus()
            return
        if not j2:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อผู้พิพากษาองค์คณะ")
            self.txt_judge2.setFocus()
            return

        storage_service.save_or_update_pair(j1, j2)
        self.refresh_completers()
        self.txt_judge1.setText(j1)
        self.update_bench_status(f"บันทึกการจับคู่ระหว่าง '{j1}' และ '{j2}' เรียบร้อยแล้ว", "font-size: 13px; color: #16a34a; font-weight: 600;")
        self.pairing_saved.emit(j1, j2)
        QMessageBox.information(
            self, "บันทึกสำเร็จ",
            f"บันทึกการจับคู่องค์คณะเรียบร้อยแล้ว:\n- ผู้พิพากษาเจ้าของสำนวน: {j1}\n- ผู้พิพากษาองค์คณะ: {j2}\n\nระบบจะจำค่านี้ไว้ทุกครั้งที่เปิดโปรแกรม"
        )

    def confirm_bench_pair_if_needed(self) -> bool:
        """
        Check bench pairing status:
        1. If judge2 is not filled but judge1 is present, check if paired judge exists and fill it.
        2. If both judge1 and judge2 are filled and pairing not yet saved, prompt to save for future.
        """
        j1 = self.txt_judge1.text().strip()
        j2 = self.txt_judge2.text().strip()

        if not j2 and j1:
            paired = storage_service.find_paired_judge(j1)
            if paired:
                self.txt_judge2.setText(paired)
                self.update_bench_status(f"เติมชื่อองค์คณะอัตโนมัติ: '{paired}'", "font-size: 13px; color: #16a34a; font-weight: 600;")
            return True

        if j1 and j2:
            paired = storage_service.find_paired_judge(j1)
            if not paired or paired != j2:
                reply = QMessageBox.question(
                    self,
                    "บันทึกการจับคู่องค์คณะ?",
                    f"พบว่ายังไม่มีการบันทึกการจับคู่ระหว่าง:\n"
                    f"- เจ้าของสำนวน: {j1}\n"
                    f"- องค์คณะ: {j2}\n\n"
                    f"ต้องการบันทึกการจับคู่นี้ไว้สำหรับคดีต่อๆ ไป หรือไม่?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    storage_service.save_or_update_pair(j1, j2)
                    self.refresh_completers()
                    self.update_bench_status(f"บันทึกการจับคู่ระหว่าง '{j1}' และ '{j2}' เรียบร้อยแล้ว", "font-size: 13px; color: #16a34a; font-weight: 600;")
        return True

    def get_judges(self) -> Tuple[str, str]:
        return self.txt_judge1.text().strip(), self.txt_judge2.text().strip()

    def set_judges(self, j1: str, j2: str):
        self.txt_judge1.setText(j1)
        self.txt_judge2.setText(j2)

    def load_bench_data(self, row: dict, mapping: dict):
        """Populate bench fields from Excel row mapping and discover paired associates immediately."""
        judge1_col = mapping.get('judge_1_name') or mapping.get('judge_name')
        judge2_col = mapping.get('judge_2_name')

        judge1_val = str(row.get(judge1_col, '')).strip() if (judge1_col and judge1_col in row and row[judge1_col] is not None) else ""
        judge2_val = str(row.get(judge2_col, '')).strip() if (judge2_col and judge2_col in row and row[judge2_col] is not None) else ""

        # Fallback search if column headers were not matched by mapping
        if not judge1_val:
            for k, v in row.items():
                if v and any(kw in str(k) for kw in ['เจ้าของสำนวน', 'ผู้พิพากษา 1', 'ผู้พิพากษาคนที่ 1', 'ผู้พิพากษา']):
                    judge1_val = str(v).strip()
                    break

        if not judge2_val:
            for k, v in row.items():
                if v and any(kw in str(k) for kw in ['องค์คณะ', 'ผู้พิพากษา 2', 'ผู้พิพากษาคนที่ 2']):
                    judge2_val = str(v).strip()
                    break

        self.txt_judge1.setText(judge1_val)

        if judge2_val:
            self.txt_judge2.setText(judge2_val)
            self.update_bench_status(f"ข้อมูลองค์คณะจากตาราง Excel: '{judge2_val}'", "font-size: 13px; color: #16a34a; font-weight: 600;")
        else:
            if judge1_val:
                paired = storage_service.find_paired_judge(judge1_val)
                if paired:
                    self.txt_judge2.setText(paired)
                    self.update_bench_status(f"ตรวจพบและเติมชื่อองค์คณะอัตโนมัติทันที: '{paired}'", "font-size: 13px; color: #16a34a; font-weight: 600;")
                else:
                    self.txt_judge2.clear()
                    self.update_bench_status("ยังไม่มีการจับคู่สำหรับผู้พิพากษาท่านนี้ (พิมพ์ชื่อองค์คณะแล้วกดปุ่ม 'บันทึกการจับคู่นี้' ได้)", "font-size: 13px; color: #64748b;")
            else:
                self.txt_judge2.clear()
                self.update_bench_status("")
