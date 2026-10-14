"""
Signatory Role Manager Dialog Component
Dialog to manage the quick-add role chips for court attendees (ผู้มาศาล).
Roles are stored in SQLite via storage_service and shown as one-tap chips
in the SignatoriesManagerWidget.
"""
from typing import Optional, List, Dict, Any
from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from services import storage_service
from services.icon_service import get_icon, get_app_logo_icon


class SignatoryRoleManagerDialog(QDialog):
    """Dialog to manage the quick-add role chips used by the attendee list."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("ระบบจัดการบทบาทผู้มาศาล (Quick Add) - CODS")
        self.setWindowIcon(get_app_logo_icon())
        self.resize(720, 560)
        self.selected_role_id: Optional[int] = None
        self.roles: List[Dict[str, Any]] = storage_service.load_preset_roles()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header
        top_bar = QHBoxLayout()
        v_head = QVBoxLayout()
        lbl_title = QLabel("บทบาทผู้มาศาล (ปุ่มเพิ่มด่วน)")
        lbl_title.setStyleSheet("font-size: 19px; font-weight: 700; color: #4c1d95;")
        lbl_sub = QLabel("บทบาทที่นี่จะแสดงเป็นปุ่มกดเพิ่มด้านบนส่วนรายชื่อผู้มาศาล กดเพิ่ม/แก้ไข/ลบได้ตามที่ใช้ประจำ")
        lbl_sub.setStyleSheet("font-size: 13px; color: #475569;")
        lbl_sub.setWordWrap(True)
        v_head.addWidget(lbl_title)
        v_head.addWidget(lbl_sub)
        top_bar.addLayout(v_head)
        top_bar.addStretch()

        self.btn_add_top = QPushButton("เพิ่มบทบาทใหม่")
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
            QPushButton:hover { background-color: #5b21b6; }
            QPushButton:pressed { background-color: #3b0764; }
            QPushButton:disabled { background-color: #94a3b8; color: #e2e8f0; }
        """)
        self.btn_add_top.clicked.connect(self.prepare_new_role)
        top_bar.addWidget(self.btn_add_top)

        layout.addLayout(top_bar)

        # Table of roles
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ลำดับ", "ชื่อบทบาท (ปุ่มเพิ่มด่วน)"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        layout.addWidget(self.table)

        # Edit form box
        form_frame = QFrame()
        form_frame.setObjectName("roleFormFrame")
        form_frame.setStyleSheet("""
            QFrame#roleFormFrame {
                background-color: #f8fafc;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
            }
        """)
        v_form_outer = QVBoxLayout(form_frame)
        v_form_outer.setContentsMargins(14, 12, 14, 12)
        v_form_outer.setSpacing(10)

        self.lbl_form_mode = QLabel("โหมด: เพิ่มบทบาทผู้มาศาลใหม่")
        self.lbl_form_mode.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #4c1d95;")
        v_form_outer.addWidget(self.lbl_form_mode)

        form_layout = QHBoxLayout()
        form_layout.setSpacing(12)
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("ชื่อบทบาท / ตำแหน่ง:"))
        self.edt_role = QLineEdit()
        self.edt_role.setPlaceholderText("เช่น ผู้รับมอบอำนาจโจทก์, ผู้อำนวยการสำนวน, แพทย์ผู้ตรวจ...")
        self.edt_role.returnPressed.connect(self.save_role)
        v1.addWidget(self.edt_role)
        form_layout.addLayout(v1)
        v_form_outer.addLayout(form_layout)

        layout.addWidget(form_frame)

        # Buttons bar
        btn_bar = QHBoxLayout()

        self.btn_new_bottom = QPushButton("เพิ่มบทบาทใหม่")
        self.btn_new_bottom.setObjectName("secondaryButton")
        self.btn_new_bottom.setIcon(get_icon("plus", color="#4c1d95", size=15))
        self.btn_new_bottom.clicked.connect(self.prepare_new_role)
        btn_bar.addWidget(self.btn_new_bottom)

        self.btn_move_up = QPushButton("เลื่อนขึ้น")
        self.btn_move_up.setObjectName("secondaryButton")
        self.btn_move_up.setIcon(get_icon("chevron-up", color="#4c1d95", size=15))
        self.btn_move_up.setToolTip("เลื่อนบทบาทที่เลือกขึ้นหนึ่งอันดับ")
        self.btn_move_up.clicked.connect(self.move_up)
        btn_bar.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("เลื่อนลง")
        self.btn_move_down.setObjectName("secondaryButton")
        self.btn_move_down.setIcon(get_icon("chevron-down", color="#4c1d95", size=15))
        self.btn_move_down.setToolTip("เลื่อนบทบาทที่เลือกลงหนึ่งอันดับ")
        self.btn_move_down.clicked.connect(self.move_down)
        btn_bar.addWidget(self.btn_move_down)

        self.btn_del = QPushButton("ลบบทบาทนี้")
        self.btn_del.setObjectName("secondaryButton")
        self.btn_del.setEnabled(False)
        self.btn_del.setIcon(get_icon("trash", color="#dc2626", size=15))
        self.btn_del.setStyleSheet("""
            QPushButton { color: #dc2626; border: 1.5px solid #fca5a5; }
            QPushButton:hover { background-color: #fee2e2; }
            QPushButton:disabled { color: #94a3b8; border-color: #e2e8f0; background-color: #f8fafc; }
        """)
        self.btn_del.clicked.connect(self.delete_role)
        btn_bar.addWidget(self.btn_del)

        self.btn_clear_all = QPushButton("ลบทั้งหมด")
        self.btn_clear_all.setObjectName("secondaryButton")
        self.btn_clear_all.setIcon(get_icon("trash", color="#b91c1c", size=15))
        self.btn_clear_all.setStyleSheet("""
            QPushButton { color: #b91c1c; border: 1.5px solid #fecaca; }
            QPushButton:hover { background-color: #fee2e2; border-color: #fca5a5; }
        """)
        self.btn_clear_all.clicked.connect(self.delete_all_roles)
        btn_bar.addWidget(self.btn_clear_all)

        btn_bar.addStretch()

        self.btn_save = QPushButton("บันทึกบทบาท")
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
            QPushButton:hover { background-color: #5b21b6; }
            QPushButton:pressed { background-color: #3b0764; }
            QPushButton:disabled { background-color: #94a3b8; color: #e2e8f0; }
        """)
        self.btn_save.clicked.connect(self.save_role)
        btn_bar.addWidget(self.btn_save)

        btn_close = QPushButton("ปิดหน้าต่าง")
        btn_close.setObjectName("secondaryButton")
        btn_close.clicked.connect(self.accept)
        btn_bar.addWidget(btn_close)

        layout.addLayout(btn_bar)

        self.refresh_table()

    # ------------------------------------------------------------------
    # Row selection & form state
    # ------------------------------------------------------------------
    def prepare_new_role(self):
        """Clear form and prepare for adding a new role chip."""
        self.selected_role_id = None
        self.table.blockSignals(True)
        self.table.clearSelection()
        self.table.blockSignals(False)
        self.edt_role.clear()
        self.edt_role.setFocus()
        self.lbl_form_mode.setText("โหมด: เพิ่มบทบาทผู้มาศาลใหม่ (พิมพ์ชื่อแล้วกดบันทึก)")
        self.btn_del.setEnabled(False)
        self._update_move_buttons()

    def on_row_selected(self):
        rows = self.table.selectionModel().selectedRows()
        if rows:
            r = rows[0].row()
            if 0 <= r < len(self.roles):
                role = self.roles[r]
                self.selected_role_id = role.get("id")
                self.edt_role.setText(role.get("role", ""))
                self.lbl_form_mode.setText(f"โหมด: แก้ไขบทบาท '{role.get('role', '')}'")
                self.btn_del.setEnabled(True)
        else:
            self.selected_role_id = None
            self.btn_del.setEnabled(False)
        self._update_move_buttons()

    def _update_move_buttons(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        has_sel = bool(rows) and self.selected_role_id is not None
        r = rows[0].row() if rows else -1
        self.btn_move_up.setEnabled(has_sel and r > 0)
        self.btn_move_down.setEnabled(has_sel and 0 <= r < len(self.roles) - 1)

    # ------------------------------------------------------------------
    # Table refresh
    # ------------------------------------------------------------------
    def refresh_table(self, select_id: Optional[int] = None):
        self.roles = storage_service.load_preset_roles()
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.roles))
        selected_row = -1
        for idx, role in enumerate(self.roles):
            item_order = QTableWidgetItem(str(idx + 1))
            item_order.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_role = QTableWidgetItem(role.get("role", ""))
            item_role.setData(Qt.ItemDataRole.UserRole, role.get("id"))
            self.table.setItem(idx, 0, item_order)
            self.table.setItem(idx, 1, item_role)
            if select_id is not None and role.get("id") == select_id:
                selected_row = idx

        self.table.blockSignals(False)
        self.btn_clear_all.setEnabled(len(self.roles) > 0)

        if selected_row >= 0:
            self.table.selectRow(selected_row)
        elif self.roles:
            self.table.selectRow(0)
        else:
            self.prepare_new_role()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def save_role(self):
        text = self.edt_role.text().strip()
        if not text:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาระบุชื่อบทบาทผู้มาก่อนบันทึก")
            self.edt_role.setFocus()
            return

        if self.selected_role_id is not None:
            storage_service.update_preset_role(self.selected_role_id, text)
            QMessageBox.information(self, "สำเร็จ", f"บันทึกบทบาท '{text}' เรียบร้อยแล้ว")
            self.refresh_table(select_id=self.selected_role_id)
        else:
            if storage_service.add_preset_role(text):
                QMessageBox.information(self, "สำเร็จ", f"เพิ่มบทบาท '{text}' เรียบร้อยแล้ว")
            else:
                QMessageBox.information(self, "แจ้งเตือน", f"บทบาท '{text}' มีอยู่ในรายการแล้ว")
            # Select the newly added role by name
            new_id = None
            for r in storage_service.load_preset_roles():
                if r.get("role") == text:
                    new_id = r.get("id")
            self.refresh_table(select_id=new_id)

    def delete_role(self):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(self, "แจ้งเตือน", "กรุณาเลือกบทบาทที่ต้องการลบจากตารางก่อน")
            return
        r = rows[0].row()
        if 0 <= r < len(self.roles):
            role = self.roles[r]
            role_id = role.get("id")
            name = role.get("role", "")
            reply = QMessageBox.question(
                self, "ยืนยันการลบ",
                f"คุณต้องการลบบทบาท '{name}' ออกจากรายการปุ่มเพิ่มด่วนใช่หรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                storage_service.delete_preset_role(role_id)
                self.refresh_table()

    def delete_all_roles(self):
        if not self.roles:
            QMessageBox.information(self, "แจ้งเตือน", "ไม่มีบทบาทผู้มาศาลในระบบ")
            return
        reply = QMessageBox.question(
            self, "ยืนยันการลบทั้งหมด",
            f"คุณต้องการลบบทบาทผู้มาศาลทั้งหมดจำนวน {len(self.roles)} รายการ ออกจากฐานข้อมูลจริงใช่หรือไม่?\n"
            "(คุณสามารถเพิ่มกลับใหม่ได้ภายหลัง แต่รายการดั้งเดิมจะหายไป)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            storage_service.clear_all_preset_roles()
            self.refresh_table()

    # ------------------------------------------------------------------
    # Reorder
    # ------------------------------------------------------------------
    def _swap_move(self, delta: int):
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        r = rows[0].row()
        target = r + delta
        if not (0 <= r < len(self.roles) and 0 <= target < len(self.roles)):
            return
        ids = [role.get("id") for role in self.roles]
        ids[r], ids[target] = ids[target], ids[r]
        storage_service.reorder_preset_roles(ids)
        self.refresh_table(select_id=self.roles[target].get("id"))

    def move_up(self):
        self._swap_move(-1)

    def move_down(self):
        self._swap_move(1)
