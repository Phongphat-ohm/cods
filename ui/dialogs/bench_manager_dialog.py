"""
Bench Manager Dialog Component
Dialog to manage judge pairings (องค์คณะผู้พิพากษา).
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from services import storage_service
from services.icon_service import get_icon, get_app_logo_icon


class BenchManagerDialog(QDialog):
    """Dialog to manage judge pairings (องค์คณะผู้พิพากษา)."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("ระบบจัดการองค์คณะผู้พิพากษา (Bench Pairing) - JADS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(840, 580)
        self.selected_pair_id = None
        self.pairs = storage_service.load_bench_pairs()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header
        top_bar = QHBoxLayout()
        v_head = QVBoxLayout()
        lbl_title = QLabel("คู่องค์คณะผู้พิพากษา")
        lbl_title.setStyleSheet("font-size: 19px; font-weight: 700; color: #4c1d95;")
        lbl_sub = QLabel("เมื่อเลือกหรือกรอกผู้พิพากษาคนที่ 1 ระบบจะเติมคนที่ 2 ให้อัตโนมัติตามที่จับคู่ไว้")
        lbl_sub.setStyleSheet("font-size: 13px; color: #475569;")
        v_head.addWidget(lbl_title)
        v_head.addWidget(lbl_sub)
        top_bar.addLayout(v_head)
        top_bar.addStretch()

        self.btn_add_top = QPushButton("เพิ่มคู่องค์คณะใหม่")
        self.btn_add_top.setObjectName("primaryButton")
        self.btn_add_top.setIcon(get_icon("plus", color="#ffffff", size=15))
        self.btn_add_top.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 600;
                padding: 8px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                color: #e2e8f0;
            }
        """)
        self.btn_add_top.clicked.connect(self.prepare_new_pair)
        top_bar.addWidget(self.btn_add_top)

        layout.addLayout(top_bar)

        # Table of pairs
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            "ผู้พิพากษาคนที่ 1 (เจ้าของสำนวน)",
            "ผู้พิพากษาคนที่ 2 (องค์คณะ)",
            "หมายเหตุ / บัลลังก์"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout.addWidget(self.table)

        # Edit Form box (Properly scoped with ID)
        form_frame = QFrame()
        form_frame.setObjectName("benchFormFrame")
        form_frame.setStyleSheet("""
            QFrame#benchFormFrame {
                background-color: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        v_form_outer = QVBoxLayout(form_frame)
        v_form_outer.setContentsMargins(14, 12, 14, 12)
        v_form_outer.setSpacing(10)

        self.lbl_form_mode = QLabel("โหมด: รายละเอียดคู่องค์คณะ")
        self.lbl_form_mode.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #4c1d95;")
        v_form_outer.addWidget(self.lbl_form_mode)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(12)

        v1 = QVBoxLayout()
        v1.addWidget(QLabel("คนที่ 1 (เจ้าของสำนวน):"))
        self.edt_j1 = QLineEdit()
        self.edt_j1.setPlaceholderText("ชื่อ-สกุล ผู้พิพากษาคนที่ 1")
        v1.addWidget(self.edt_j1)
        form_layout.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("คนที่ 2 (องค์คณะ):"))
        self.edt_j2 = QLineEdit()
        self.edt_j2.setPlaceholderText("ชื่อ-สกุล ผู้พิพากษาคนที่ 2")
        v2.addWidget(self.edt_j2)
        form_layout.addLayout(v2)

        v3 = QVBoxLayout()
        v3.addWidget(QLabel("ห้องพิจารณาคดี / หมายเหตุ:"))
        self.edt_note = QLineEdit()
        self.edt_note.setPlaceholderText("เช่น ห้องพิจารณาคดี 5")
        v3.addWidget(self.edt_note)
        form_layout.addLayout(v3)

        v_form_outer.addLayout(form_layout)
        layout.addWidget(form_frame)

        # Buttons bar
        btn_bar = QHBoxLayout()

        self.btn_new_bottom = QPushButton("เพิ่มคู่องค์คณะใหม่")
        self.btn_new_bottom.setObjectName("secondaryButton")
        self.btn_new_bottom.setIcon(get_icon("plus", color="#4c1d95", size=15))
        self.btn_new_bottom.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #ddd6fe;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f3ff;
                border-color: #c4b5fd;
            }
            QPushButton:pressed {
                background-color: #ede9fe;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        self.btn_new_bottom.clicked.connect(self.prepare_new_pair)
        btn_bar.addWidget(self.btn_new_bottom)

        self.btn_del = QPushButton("ลบคู่นี้")
        self.btn_del.setObjectName("secondaryButton")
        self.btn_del.setEnabled(False)
        self.btn_del.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #dc2626;
                border: 1.5px solid #fca5a5;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #fee2e2;
            }
            QPushButton:pressed {
                background-color: #fecaca;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        self.btn_del.setIcon(get_icon("trash", color="#dc2626", size=15))
        self.btn_del.clicked.connect(self.delete_pair)
        btn_bar.addWidget(self.btn_del)

        self.btn_clear_all = QPushButton("ลบทั้งหมด")
        self.btn_clear_all.setObjectName("secondaryButton")
        self.btn_clear_all.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #b91c1c;
                border: 1.5px solid #fecaca;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-color: #fca5a5;
            }
            QPushButton:pressed {
                background-color: #fecaca;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        self.btn_clear_all.setIcon(get_icon("trash", color="#b91c1c", size=15))
        self.btn_clear_all.clicked.connect(self.delete_all_pairs)
        btn_bar.addWidget(self.btn_clear_all)

        btn_bar.addStretch()

        self.btn_save = QPushButton("บันทึกคู่องค์คณะ")
        self.btn_save.setObjectName("primaryButton")
        self.btn_save.setIcon(get_icon("save", color="#ffffff", size=15))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 600;
                padding: 8px 18px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
            QPushButton:pressed {
                background-color: #3b0764;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
                color: #e2e8f0;
            }
        """)
        self.btn_save.clicked.connect(self.save_pair)
        btn_bar.addWidget(self.btn_save)

        btn_close = QPushButton("ปิดหน้าต่าง")
        btn_close.setObjectName("secondaryButton")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #1e293b;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 13.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #0f172a;
            }
            QPushButton:pressed {
                background-color: #e2e8f0;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """)
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)

        layout.addLayout(btn_bar)

        self.refresh_table()

    def prepare_new_pair(self):
        """Clear form and prepare for entering a new bench pairing."""
        self.selected_pair_id = None
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.blockSignals(False)
        self.edt_j1.clear()
        self.edt_j2.clear()
        self.edt_note.clear()
        self.edt_j1.setFocus()
        self.lbl_form_mode.setText("โหมด: เพิ่มคู่องค์คณะผู้พิพากษาใหม่ (กรอกชื่อเจ้าของสำนวนและองค์คณะแล้วกดบันทึก)")
        self.lbl_form_mode.setStyleSheet("font-size: 13px; color: #4c1d95; font-weight: 600;")
        self.btn_del.setEnabled(False)

    def refresh_table(self, select_j1: str = ""):
        self.pairs = storage_service.load_bench_pairs()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.pairs))
        selected_row = -1
        for r_idx, pair in enumerate(self.pairs):
            j1 = pair.get("judge1", "")
            item1 = QTableWidgetItem(j1)
            item2 = QTableWidgetItem(pair.get("judge2", ""))
            item3 = QTableWidgetItem(pair.get("note", ""))
            self.table.setItem(r_idx, 0, item1)
            self.table.setItem(r_idx, 1, item2)
            self.table.setItem(r_idx, 2, item3)
            if select_j1 and storage_service.is_name_match(j1, select_j1):
                selected_row = r_idx

        self.table.blockSignals(False)
        self.btn_clear_all.setEnabled(len(self.pairs) > 0)

        if selected_row >= 0:
            self.table.selectRow(selected_row)
        elif self.pairs:
            self.table.selectRow(0)
        else:
            self.prepare_new_pair()

    def on_row_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            r = rows[0].row()
            if 0 <= r < len(self.pairs):
                p = self.pairs[r]
                self.selected_pair_id = p.get("id")
                j1 = p.get("judge1", "")
                j2 = p.get("judge2", "")
                note = p.get("note", "")
                self.edt_j1.setText(j1)
                self.edt_j2.setText(j2)
                self.edt_note.setText(note)
                self.lbl_form_mode.setText(f"โหมด: ข้อมูลคู่องค์คณะของ '{j1}' (องค์คณะ: '{j2}')")
                self.lbl_form_mode.setStyleSheet("font-size: 13px; color: #4c1d95; font-weight: 600;")
                self.btn_del.setEnabled(True)
        else:
            self.selected_pair_id = None
            self.btn_del.setEnabled(False)

    def save_pair(self):
        j1 = self.edt_j1.text().strip()
        j2 = self.edt_j2.text().strip()
        note = self.edt_note.text().strip()

        if not j1:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อผู้พิพากษาเจ้าของสำนวน")
            self.edt_j1.setFocus()
            return
        if not j2:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อผู้พิพากษาองค์คณะ")
            self.edt_j2.setFocus()
            return

        storage_service.save_or_update_pair(j1, j2, note, pair_id=getattr(self, "selected_pair_id", None))
        QMessageBox.information(self, "สำเร็จ", f"บันทึกคู่องค์คณะผู้พิพากษาเรียบร้อยแล้ว:\n- เจ้าของสำนวน: {j1}\n- องค์คณะ: {j2}" + (f"\n- ห้องพิจารณา/หมายเหตุ: {note}" if note else ""))
        self.refresh_table(select_j1=j1)

    def delete_pair(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกคู่ที่ต้องการลบจากตารางก่อน")
            return

        if len(rows) == 1:
            r = rows[0].row()
            if 0 <= r < len(self.pairs):
                p = self.pairs[r]
                j1 = p.get("judge1", "")
                j2 = p.get("judge2", "")
                pair_id = p.get("id")
                reply = QMessageBox.question(
                    self, "ยืนยันการลบ",
                    f"คุณต้องการลบคู่ระหว่าง '{j1}' กับ '{j2}' ใช่หรือไม่?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    storage_service.delete_bench_pair(judge1=j1, pair_id=pair_id)
                    self.refresh_table()
        else:
            reply = QMessageBox.question(
                self, "ยืนยันการลบ",
                f"คุณต้องการลบคู่ที่เลือกทั้งหมดจำนวน {len(rows)} รายการ ใช่หรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                for row_item in rows:
                    r = row_item.row()
                    if 0 <= r < len(self.pairs):
                        p = self.pairs[r]
                        storage_service.delete_bench_pair(judge1=p.get("judge1", ""), pair_id=p.get("id"))
                self.refresh_table()

    def delete_all_pairs(self):
        if not self.pairs:
            QMessageBox.information(self, "แจ้งเตือน", "ไม่มีข้อมูลคู่องค์คณะในระบบ")
            return
        reply = QMessageBox.question(
            self, "ยืนยันการลบทั้งหมด",
            f"คุณต้องการลบคู่องค์คณะผู้พิพากษาทั้งหมดจำนวน {len(self.pairs)} รายการ ออกจากฐานข้อมูลจริงใช่หรือไม่?\n(ข้อมูลจะถูกลบออกจากฐานข้อมูลอย่างถาวร)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            storage_service.clear_all_bench_pairs()
            self.refresh_table()
            QMessageBox.information(self, "สำเร็จ", "ลบข้อมูลคู่องค์คณะทั้งหมดออกจากฐานข้อมูลเรียบร้อยแล้ว")
