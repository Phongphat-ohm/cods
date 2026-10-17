"""
Online Signatories Manager Widget Component
Specialized for electronic / online court proceedings (รายงานกระบวนพิจารณาออนไลน์).
Cloned 100% from standard SignatoriesManagerWidget with matching styles, UI structure,
preset chips, drag-and-drop, and enriched with online meeting platform & attendee online toggle.
"""
import re
from typing import List, Dict, Any, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidgetItem, QFrame, QMessageBox,
    QAbstractItemView, QInputDialog, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QSize
from services.docx_service import format_online_attendees_summary
from services.icon_service import get_icon
from services import storage_service
from constants import ROLE_WEIGHTS
from ui.components.draggable_list import DraggableListWidget
from ui.components.autocomplete_input import JudicialAutocompleteInput
from ui.components.signatories_manager import FlowLayout, get_court_tradition_weight


class OnlineAttendeeRowWidget(QWidget):
    """Row widget for each attendee in the online list with an inline 'ออนไลน์' checkbox."""
    online_toggled = Signal(int, bool)

    def __init__(self, index: int, position: str, is_online: bool, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.index = index
        self.position = position

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 3, 12, 3)
        layout.setSpacing(10)

        # Rank and position label matching standard signatories style
        self.lbl_text = QLabel(f"ลำดับที่ {index + 1}: {position}")
        self.lbl_text.setStyleSheet("font-size: 15px; color: #0f172a;")
        layout.addWidget(self.lbl_text, 1)

        # Online checkbox
        self.chk_online = QCheckBox("ออนไลน์")
        self.chk_online.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_online.setToolTip("ติ๊กเลือกหากบุคคลนี้ปรากฏตัวผ่านระบบการประชุมทางจอภาพ (หากไม่ติ๊กจะถือว่ามาศาล)")
        self.chk_online.setChecked(is_online)
        self.chk_online.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                font-weight: 600;
                color: #4c1d95;
                background-color: #f5f3ff;
                border: 1px solid #ddd6fe;
                border-radius: 5px;
                padding: 3px 8px;
            }
            QCheckBox:hover {
                background-color: #ede9fe;
                border-color: #c4b5fd;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)
        self.chk_online.toggled.connect(self._on_toggled)
        layout.addWidget(self.chk_online)

    def _on_toggled(self, checked: bool):
        self.online_toggled.emit(self.index, checked)


class OnlineSignatoriesManagerWidget(QFrame):
    """
    Dedicated manager component for online court hearings:
    - Identical structure, styling, and sizing to standard SignatoriesManagerWidget
    - Online Platform Autocomplete input with default setting for court
    - Attendee list with inline online checkbox per person
    - Real-time attendees_summary preview
    """
    changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("signatoriesBox")
        # Each item: {'position': str, 'is_online': bool}
        self.signatories: List[Dict[str, Any]] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title & Controls Bar (Identical to standard manager)
        top_row = QHBoxLayout()
        lbl_title = QLabel("2. รายชื่อผู้มาศาลและผู้ลงลายมือชื่อท้ายรายงาน (พิจารณาออนไลน์)")
        lbl_title.setObjectName("sectionHeaderTitle")
        top_row.addWidget(lbl_title)
        top_row.addStretch()

        btn_sort = QPushButton("เรียงตามธรรมเนียมศาล")
        btn_sort.setObjectName("secondaryButtonSmall")
        btn_sort.setIcon(get_icon("scale", color="#4c1d95", size=14))
        btn_sort.setToolTip("จัดลำดับ: โจทก์ -> ทนายโจทก์ -> จำเลย -> ทนายจำเลย")
        btn_sort.clicked.connect(self.sort_by_court_tradition)
        top_row.addWidget(btn_sort)

        btn_clear = QPushButton("ล้างทั้งหมด")
        btn_clear.setObjectName("secondaryButtonSmall")
        btn_clear.setIcon(get_icon("trash", color="#64748b", size=14))
        btn_clear.clicked.connect(self.clear_all)
        top_row.addWidget(btn_clear)

        layout.addLayout(top_row)

        # ---------------------------------------------------------------------
        # Online Platform Autocomplete Section (Harmonized with theme)
        # ---------------------------------------------------------------------
        platform_box = QFrame()
        platform_box.setStyleSheet("""
            QFrame {
                background-color: #faf5ff;
                border: 1px solid #ddd6fe;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        plat_lay = QHBoxLayout(platform_box)
        plat_lay.setContentsMargins(10, 6, 10, 6)
        plat_lay.setSpacing(10)

        lbl_plat = QLabel("ระบบการประชุมทางจอภาพ:")
        lbl_plat.setStyleSheet("font-size: 13.5px; font-weight: 600; color: #4c1d95;")
        plat_lay.addWidget(lbl_plat)

        platforms = storage_service.get_online_platforms()
        default_platform = storage_service.get_default_online_platform()

        self.txt_platform = JudicialAutocompleteInput(
            items=platforms,
            placeholder="เช่น Google Meet, Zoom, Cisco Webex, Microsoft Teams"
        )
        self.txt_platform.setText(default_platform)
        self.txt_platform.textChanged.connect(self._on_platform_changed)
        plat_lay.addWidget(self.txt_platform, 1)

        btn_set_default = QPushButton("ตั้งเป็นค่าเริ่มต้นของศาล")
        btn_set_default.setObjectName("secondaryButtonSmall")
        btn_set_default.setIcon(get_icon("check", color="#4c1d95", size=13))
        btn_set_default.setToolTip("บันทึกระบบที่กรอกนี้เป็นค่าเริ่มต้นประจำศาลในระบบ")
        btn_set_default.clicked.connect(self.save_current_platform_as_default)
        plat_lay.addWidget(btn_set_default)

        layout.addWidget(platform_box)

        # ---------------------------------------------------------------------
        # Preset Role Chips (Exact standard layout)
        # ---------------------------------------------------------------------
        v_chips = QVBoxLayout()
        v_chips.setSpacing(5)

        chips_head = QHBoxLayout()
        lbl_chips_title = QLabel("ปุ่มเพิ่มด่วน (บทบาทผู้มาศาลที่ใช้ประจำ)")
        lbl_chips_title.setObjectName("fieldLabel")
        chips_head.addWidget(lbl_chips_title)
        chips_head.addStretch()

        btn_manage_roles = QPushButton("จัดการบทบาท")
        btn_manage_roles.setObjectName("secondaryButtonSmall")
        btn_manage_roles.setIcon(get_icon("settings", color="#4c1d95", size=14))
        btn_manage_roles.setToolTip("เพิ่ม/แก้ไข/ลบ/จัดเรียงปุ่มบทบาทผู้มาศาล (จัดเก็บในฐานข้อมูล)")
        btn_manage_roles.clicked.connect(self.open_role_manager)
        chips_head.addWidget(btn_manage_roles)
        v_chips.addLayout(chips_head)

        self.chips_container = QWidget()
        sp = self.chips_container.sizePolicy()
        sp.setHeightForWidth(True)
        self.chips_container.setSizePolicy(sp)
        self.chips_layout = FlowLayout(self.chips_container, margin=0, h_spacing=6, v_spacing=6)
        v_chips.addWidget(self.chips_container)
        layout.addLayout(v_chips)

        # ---------------------------------------------------------------------
        # Custom Role Input Bar
        # ---------------------------------------------------------------------
        custom_bar = QHBoxLayout()
        custom_bar.setSpacing(8)

        self.txt_custom_role = QLineEdit()
        self.txt_custom_role.setPlaceholderText("พิมพ์ตำแหน่งหรือชื่อผู้มาศาลอื่นๆ เพิ่มเติม เช่น นายสมหวัง (พยานโจทก์)...")
        self.txt_custom_role.returnPressed.connect(self.add_custom_role)
        custom_bar.addWidget(self.txt_custom_role)

        self.chk_new_online = QCheckBox("ออนไลน์")
        self.chk_new_online.setChecked(True)
        self.chk_new_online.setToolTip("ติ๊กเลือกหากต้องการให้รายการใหม่ที่กำลังจะเพิ่มมีสถานะเป็น 'ออนไลน์' ทันที")
        self.chk_new_online.setStyleSheet("font-size: 13px; font-weight: 600; color: #4c1d95;")
        custom_bar.addWidget(self.chk_new_online)

        btn_add_custom = QPushButton("เพิ่มเข้าลำดับ")
        btn_add_custom.setObjectName("primaryButtonSmall")
        btn_add_custom.setIcon(get_icon("plus", color="#ffffff", size=14))
        btn_add_custom.clicked.connect(self.add_custom_role)
        custom_bar.addWidget(btn_add_custom)

        self.btn_update_custom = QPushButton("บันทึกที่แก้ไข")
        self.btn_update_custom.setObjectName("secondaryButtonSmall")
        self.btn_update_custom.setIcon(get_icon("check", color="#4c1d95", size=14))
        self.btn_update_custom.setToolTip("บันทึกข้อความที่พิมพ์ลงในรายการที่เลือกอยู่ในขณะนี้")
        self.btn_update_custom.setEnabled(False)
        self.btn_update_custom.clicked.connect(self.update_custom_role)
        custom_bar.addWidget(self.btn_update_custom)
        layout.addLayout(custom_bar)

        # ---------------------------------------------------------------------
        # List & Action Controls (Exact styling & signatoriesList objectName)
        # ---------------------------------------------------------------------
        list_container = QHBoxLayout()
        list_container.setSpacing(12)

        self.list_widget = DraggableListWidget()
        self.list_widget.setObjectName("signatoriesList")
        self.list_widget.setMinimumHeight(280)
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.currentRowChanged.connect(self.update_control_buttons)
        self.list_widget.itemDoubleClicked.connect(self.edit_selected)
        self.list_widget.order_changed.connect(self.sync_from_list)
        self.list_widget.edit_requested.connect(self.edit_selected)
        self.list_widget.delete_requested.connect(self.delete_selected)
        list_container.addWidget(self.list_widget, 1)

        # Action buttons beside list (Identical to standard manager)
        actions_vbox = QVBoxLayout()
        actions_vbox.setSpacing(8)
        actions_vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_edit = QPushButton("แก้ไขรายการ")
        self.btn_edit.setObjectName("secondaryButtonSmall")
        self.btn_edit.setIcon(get_icon("edit", color="#4c1d95", size=14))
        self.btn_edit.setToolTip("แก้ไขข้อความในรายการที่เลือก [Enter หรือ F2 หรือดับเบิลคลิก]")
        self.btn_edit.clicked.connect(self.edit_selected)
        actions_vbox.addWidget(self.btn_edit)

        self.btn_up = QPushButton("เลื่อนขึ้น")
        self.btn_up.setObjectName("secondaryButtonSmall")
        self.btn_up.setIcon(get_icon("chevron-up", color="#4c1d95", size=14))
        self.btn_up.setToolTip("เลื่อนลำดับขึ้น")
        self.btn_up.clicked.connect(self.move_up)
        actions_vbox.addWidget(self.btn_up)

        self.btn_down = QPushButton("เลื่อนลง")
        self.btn_down.setObjectName("secondaryButtonSmall")
        self.btn_down.setIcon(get_icon("chevron-down", color="#4c1d95", size=14))
        self.btn_down.setToolTip("เลื่อนลำดับลง")
        self.btn_down.clicked.connect(self.move_down)
        actions_vbox.addWidget(self.btn_down)

        self.btn_del = QPushButton("ลบรายการ")
        self.btn_del.setObjectName("secondaryButtonSmall")
        self.btn_del.setStyleSheet("color: #dc2626; border-color: #fca5a5;")
        self.btn_del.setIcon(get_icon("trash", color="#dc2626", size=14))
        self.btn_del.setToolTip("ลบรายการที่เลือก [Delete]")
        self.btn_del.clicked.connect(self.delete_selected)
        actions_vbox.addWidget(self.btn_del)

        list_container.addLayout(actions_vbox)
        layout.addLayout(list_container, 1)

        lbl_drag_tip = QLabel("คำแนะนำ: สามารถคลิกค้างแล้วลาก (Drag & Drop) รายชื่อเพื่อสลับลำดับได้โดยตรง หรือคลิกช่อง 'ออนไลน์' เพื่อสลับสถานะ")
        lbl_drag_tip.setObjectName("helperText")
        lbl_drag_tip.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(lbl_drag_tip)

        # ---------------------------------------------------------------------
        # Live Preview Callout (Identical to standard previewCalloutBox)
        # ---------------------------------------------------------------------
        preview_box = QFrame()
        preview_box.setObjectName("previewCalloutBox")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(12, 7, 12, 7)
        preview_layout.setSpacing(2)

        lbl_pv_title = QLabel("ตัวอย่างข้อความสรุปผู้มาศาล (จะปรากฏในรายงานกระบวนพิจารณาออนใลน์):")
        lbl_pv_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #4c1d95;")
        preview_layout.addWidget(lbl_pv_title)

        self.lbl_preview_sentence = QLabel("")
        self.lbl_preview_sentence.setStyleSheet("font-size: 14px; color: #0f172a; font-weight: 500; line-height: 1.3;")
        self.lbl_preview_sentence.setWordWrap(True)
        preview_layout.addWidget(self.lbl_preview_sentence)

        layout.addWidget(preview_box)

        self.refresh_chips()
        self.refresh_ui()

    def get_platform(self) -> str:
        """Return the current online meeting platform string."""
        plat = self.txt_platform.text().strip()
        return plat if plat else "Google Meet"

    def _on_platform_changed(self, text: str):
        self.update_preview()
        self.changed.emit()

    def save_current_platform_as_default(self):
        plat = self.get_platform()
        if storage_service.set_default_online_platform(plat):
            QMessageBox.information(
                self, "บันทึกสำเร็จ",
                f"บันทึก '{plat}' เป็นระบบการประชุมออนไลน์เริ่มต้นของศาลเรียบร้อยแล้ว"
            )

    def refresh_chips(self):
        """Rebuild quick-add role chips from SQLite."""
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        roles = [r.get("role", "") for r in storage_service.load_preset_roles() if r.get("role")]
        if not roles:
            lbl_empty = QLabel("ยังไม่มีปุ่มบทบาทด่วน กด 'จัดการบทบาท' เพื่อเพิ่ม")
            lbl_empty.setObjectName("helperText")
            lbl_empty.setStyleSheet("font-size: 12px; color: #94a3b8;")
            self.chips_layout.addWidget(lbl_empty)
            return

        for role in roles:
            btn_role = QPushButton(role)
            btn_role.setObjectName("tagButton")
            btn_role.setIcon(get_icon("plus", color="#4c1d95", size=12))
            btn_role.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn_role.clicked.connect(lambda _, r=role: self.add_signatory(r, is_online=self.chk_new_online.isChecked()))
            self.chips_layout.addWidget(btn_role)

    def open_role_manager(self):
        from ui.dialogs.signatory_role_manager_dialog import SignatoryRoleManagerDialog
        dlg = SignatoryRoleManagerDialog(self)
        dlg.exec()
        self.refresh_chips()

    def sync_from_list(self):
        """Re-sync the internal signatories list following a drag & drop."""
        new_items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(data, dict):
                new_items.append(data)
            elif isinstance(data, str):
                new_items.append({"position": data, "is_online": False})
        self.signatories = new_items
        self.refresh_ui()

    def refresh_ui(self):
        curr_row = self.list_widget.currentRow()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        item_h = self.list_widget.fontMetrics().height() + 30
        for idx, entry in enumerate(self.signatories):
            pos = entry.get("position", "")
            is_on = entry.get("is_online", False)

            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, {"position": pos, "is_online": is_on})
            item.setSizeHint(QSize(0, item_h))
            self.list_widget.addItem(item)

            row_widget = OnlineAttendeeRowWidget(idx, pos, is_on, self)
            row_widget.online_toggled.connect(self._on_row_online_toggled)
            self.list_widget.setItemWidget(item, row_widget)

        self.list_widget.blockSignals(False)

        if 0 <= curr_row < len(self.signatories):
            self.list_widget.setCurrentRow(curr_row)
        elif self.signatories:
            self.list_widget.setCurrentRow(0)

        self.update_preview()
        self.update_control_buttons()
        self.changed.emit()

    def _on_row_online_toggled(self, row_idx: int, is_online: bool):
        if 0 <= row_idx < len(self.signatories):
            self.signatories[row_idx]["is_online"] = is_online
            item = self.list_widget.item(row_idx)
            if item:
                item.setData(Qt.ItemDataRole.UserRole, self.signatories[row_idx])
            self.update_preview()
            self.changed.emit()

    def update_preview(self):
        plat = self.get_platform()
        summary = format_online_attendees_summary(self.signatories, plat)
        if summary:
            self.lbl_preview_sentence.setText(f"\"วันนี้ {summary}\"")
        else:
            self.lbl_preview_sentence.setText("(ยังไม่ได้ระบุรายชื่อผู้มาศาล - เลือกหรือพิมพ์เพิ่มได้ที่ปุ่มด้านบน)")

    def update_control_buttons(self):
        r = self.list_widget.currentRow()
        has_sel = 0 <= r < len(self.signatories)
        self.btn_up.setEnabled(has_sel and r > 0)
        self.btn_down.setEnabled(has_sel and r < len(self.signatories) - 1)
        self.btn_edit.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel)
        if has_sel:
            role = self.signatories[r].get("position", "")
            self.txt_custom_role.setText(role)
            self.chk_new_online.setChecked(self.signatories[r].get("is_online", False))
            self.btn_update_custom.setEnabled(True)
        else:
            self.btn_update_custom.setEnabled(False)

    def edit_selected(self):
        r = self.list_widget.currentRow()
        if 0 <= r < len(self.signatories):
            current_val = self.signatories[r].get("position", "")
            text, ok = QInputDialog.getText(
                self,
                "แก้ไขรายชื่อผู้มาศาล",
                f"แก้ไขรายชื่อ / ตำแหน่ง ลำดับที่ {r + 1}:",
                QLineEdit.EchoMode.Normal,
                current_val
            )
            if ok and text.strip():
                self.signatories[r]["position"] = text.strip()
                self.refresh_ui()
                self.list_widget.setCurrentRow(r)

    def update_custom_role(self):
        r = self.list_widget.currentRow()
        text = self.txt_custom_role.text().strip()
        if 0 <= r < len(self.signatories) and text:
            self.signatories[r]["position"] = text
            self.signatories[r]["is_online"] = self.chk_new_online.isChecked()
            self.refresh_ui()
            self.list_widget.setCurrentRow(r)

    def add_signatory(self, role: str, is_online: bool = True):
        role_clean = role.strip()
        if not role_clean:
            return
        self.signatories.append({"position": role_clean, "is_online": is_online})
        self.refresh_ui()
        self.list_widget.setCurrentRow(len(self.signatories) - 1)

    def add_custom_role(self):
        txt = self.txt_custom_role.text().strip()
        if not txt:
            return
        self.add_signatory(txt, is_online=self.chk_new_online.isChecked())
        self.txt_custom_role.clear()

    def move_up(self):
        r = self.list_widget.currentRow()
        if r > 0:
            self.signatories[r], self.signatories[r - 1] = self.signatories[r - 1], self.signatories[r]
            self.refresh_ui()
            self.list_widget.setCurrentRow(r - 1)

    def move_down(self):
        r = self.list_widget.currentRow()
        if 0 <= r < len(self.signatories) - 1:
            self.signatories[r], self.signatories[r + 1] = self.signatories[r + 1], self.signatories[r]
            self.refresh_ui()
            self.list_widget.setCurrentRow(r + 1)

    def delete_selected(self):
        r = self.list_widget.currentRow()
        if 0 <= r < len(self.signatories):
            self.signatories.pop(r)
            self.refresh_ui()

    def clear_all(self):
        if not self.signatories:
            return
        reply = QMessageBox.question(
            self, "ยืนยัน", "คุณต้องการล้างรายชื่อผู้มาศาลทั้งหมดหรือไม่?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.signatories = []
            self.refresh_ui()

    def sort_by_court_tradition(self):
        self.signatories.sort(key=lambda x: get_court_tradition_weight(x.get("position", "")))
        self.refresh_ui()

    def get_signatories(self) -> List[Dict[str, Any]]:
        """Return list of signatory objects with position and is_online status."""
        return list(self.signatories)

    def get_signatories_positions(self) -> List[str]:
        """Return pure list of position strings for compatibility."""
        return [s.get("position", "") for s in self.signatories if s.get("position")]

    def get_attendees_summary(self) -> str:
        """Return the pre-calculated attendees summary string."""
        return format_online_attendees_summary(self.signatories, self.get_platform())

    def set_signatories(self, items: List[Any]):
        res = []
        for x in items:
            if isinstance(x, dict):
                p = str(x.get("position", "")).strip()
                if p:
                    res.append({"position": p, "is_online": bool(x.get("is_online", False))})
            elif isinstance(x, str):
                p = x.strip()
                if p:
                    res.append({"position": p, "is_online": False})
        self.signatories = res
        self.refresh_ui()
