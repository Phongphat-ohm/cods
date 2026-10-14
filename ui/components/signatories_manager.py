"""
Signatories Manager Widget Component
Manages court attendees and signatories with Drag & Drop reordering,
court tradition auto-sort, preset chips, and live preview.
"""
import re
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLayout, QLabel, QPushButton,
    QLineEdit, QListWidgetItem, QFrame, QMessageBox,
    QAbstractItemView, QInputDialog, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QPoint
from services.docx_service import format_attendees_summary
from services.icon_service import get_icon
from services import storage_service
from constants import ROLE_WEIGHTS
from ui.components.draggable_list import DraggableListWidget


class FlowLayout(QLayout):
    """Left-to-right layout that wraps widgets to the next row like CSS flex-wrap."""

    def __init__(self, parent=None, margin: int = 0, h_spacing: int = 6, v_spacing: int = 6):
        super().__init__(parent)
        self._items = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        m = self.contentsMargins()
        effective = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        x = effective.x()
        y = effective.y()
        line_height = 0
        for item in self._items:
            hint = item.sizeHint()
            nx = x + hint.width() + self._h_spacing
            if nx - self._h_spacing > effective.right() + 1 and line_height > 0:
                x = effective.x()
                y = y + line_height + self._v_spacing
                nx = x + hint.width() + self._h_spacing
                line_height = 0
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x = nx
            line_height = max(line_height, hint.height())
        return y + line_height - rect.y() + m.bottom()

# Sort keys by length descending to match longer titles (e.g. 'ทนายโจทก์', 'พยานโจทก์') before substrings ('โจทก์')
SORTED_ROLE_WEIGHT_KEYS = sorted(ROLE_WEIGHTS.keys(), key=len, reverse=True)


def get_court_tradition_weight(role_name: str) -> int:
    """Calculate sorting weight according to Thai Court tradition.
    Checks exact matches first, then checks longer keys first to prevent
    substring collisions (e.g. 'โจทก์' incorrectly matching 'ทนายโจทก์' or 'พยานโจทก์').
    """
    cleaned = role_name.strip()
    if cleaned in ROLE_WEIGHTS:
        return ROLE_WEIGHTS[cleaned]
    for key in SORTED_ROLE_WEIGHT_KEYS:
        if key in cleaned:
            return ROLE_WEIGHTS[key]
    return 99


class SignatoriesManagerWidget(QFrame):
    """
    Component for managing court attendees and signatories:
    - Drag & Drop reordering support
    - Rank badges (#1, #2, ...)
    - Move Up / Down
    - Delete individual items
    - Preset chips for quick add
    - Custom role input
    - Court tradition auto-sort
    - Live attendees summary preview
    """
    changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("signatoriesBox")
        self.signatories: List[str] = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title & Controls
        top_row = QHBoxLayout()
        lbl_title = QLabel("2. รายชื่อผู้มาศาลและผู้ลงลายมือชื่อท้ายรายงาน")
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

        # Preset Role Chips (dynamic, DB-backed via storage_service.preset_roles)
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
        # Enable heightForWidth so the parent layout reserves enough vertical
        # space for wrapped chip rows instead of clipping them.
        sp = self.chips_container.sizePolicy()
        sp.setHeightForWidth(True)
        self.chips_container.setSizePolicy(sp)
        self.chips_layout = FlowLayout(self.chips_container, margin=0, h_spacing=6, v_spacing=6)
        v_chips.addWidget(self.chips_container)

        layout.addLayout(v_chips)

        # Custom Role Input Bar
        custom_bar = QHBoxLayout()
        custom_bar.setSpacing(8)
        self.txt_custom_role = QLineEdit()
        self.txt_custom_role.setPlaceholderText("พิมพ์ตำแหน่งหรือชื่อผู้มาศาลอื่นๆ เพิ่มเติม เช่น นายสมหวัง (พยานโจทก์)...")
        self.txt_custom_role.returnPressed.connect(self.add_custom_role)
        custom_bar.addWidget(self.txt_custom_role)

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

        # List & Action Controls Container
        list_container = QHBoxLayout()
        list_container.setSpacing(12)

        # Draggable List Widget
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

        # Action buttons beside list
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

        lbl_drag_tip = QLabel("คำแนะนำ: สามารถคลิกค้างแล้วลาก (Drag & Drop) รายชื่อเพื่อสลับลำดับได้โดยตรง หรือใช้ปุ่ม เลื่อนขึ้น / เลื่อนลง")
        lbl_drag_tip.setObjectName("helperText")
        lbl_drag_tip.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(lbl_drag_tip)

        # Real-time preview of attendees sentence
        preview_box = QFrame()
        preview_box.setObjectName("previewCalloutBox")
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(12, 7, 12, 7)
        preview_layout.setSpacing(2)

        lbl_pv_title = QLabel("ตัวอย่างข้อความสรุปผู้มาศาล (จะปรากฏในรายงานกระบวนพิจารณา):")
        lbl_pv_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #4c1d95;")
        preview_layout.addWidget(lbl_pv_title)

        self.lbl_preview_sentence = QLabel("")
        self.lbl_preview_sentence.setStyleSheet("font-size: 14px; color: #0f172a; font-weight: 500; line-height: 1.3;")
        self.lbl_preview_sentence.setWordWrap(True)
        preview_layout.addWidget(self.lbl_preview_sentence)

        layout.addWidget(preview_box)

        self.refresh_chips()
        self.refresh_ui()

    def refresh_chips(self):
        """Rebuild the quick-add role chips from the database (flex-wrap)."""
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        roles = [r.get("role", "") for r in storage_service.load_preset_roles() if r.get("role")]
        if not roles:
            lbl_empty = QLabel("ยังไม่มีปุ่มบทบาทด่วน กด 'จัดการบทบาท' เพื่อเพิ่มบทบาทที่คุณใช้ประจำ")
            lbl_empty.setObjectName("helperText")
            lbl_empty.setStyleSheet("font-size: 12px; color: #94a3b8;")
            self.chips_layout.addWidget(lbl_empty)
            return

        for role in roles:
            btn_role = QPushButton(role)
            btn_role.setObjectName("tagButton")
            btn_role.setIcon(get_icon("plus", color="#4c1d95", size=12))
            btn_role.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            btn_role.clicked.connect(lambda _, r=role: self.add_signatory(r))
            self.chips_layout.addWidget(btn_role)

    def open_role_manager(self):
        """Open the quick-add role manager dialog, then refresh chips on close."""
        from ui.dialogs.signatory_role_manager_dialog import SignatoryRoleManagerDialog
        dlg = SignatoryRoleManagerDialog(self)
        dlg.exec()
        self.refresh_chips()

    def sync_from_list(self):
        new_roles = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            role = item.data(Qt.ItemDataRole.UserRole)
            if not role:
                role = re.sub(r'^ลำดับที่\s*\d+:\s*', '', item.text()).strip()
            new_roles.append(role)
        self.signatories = new_roles
        self.refresh_ui()

    def refresh_ui(self):
        curr_row = self.list_widget.currentRow()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        # Height must fit QSS chrome (item margin 3*2 + border 1*2 + padding 10*2)
        # plus the text line, otherwise the item border overlaps the text.
        item_h = self.list_widget.fontMetrics().height() + 30
        for idx, role in enumerate(self.signatories, start=1):
            item = QListWidgetItem(f"ลำดับที่ {idx}: {role}")
            item.setData(Qt.ItemDataRole.UserRole, role)
            item.setSizeHint(QSize(0, item_h))
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)

        if 0 <= curr_row < len(self.signatories):
            self.list_widget.setCurrentRow(curr_row)
        elif self.signatories:
            self.list_widget.setCurrentRow(0)

        summary = format_attendees_summary(self.signatories)
        if summary:
            self.lbl_preview_sentence.setText(f"\"วันนี้ {summary} มาศาล\"")
        else:
            self.lbl_preview_sentence.setText("(ยังไม่ได้ระบุรายชื่อผู้มาศาล - เลือกหรือพิมพ์เพิ่มได้ที่ปุ่มด้านบน)")

        self.update_control_buttons()
        self.changed.emit()

    def update_control_buttons(self):
        r = self.list_widget.currentRow()
        has_sel = 0 <= r < len(self.signatories)
        self.btn_up.setEnabled(has_sel and r > 0)
        self.btn_down.setEnabled(has_sel and r < len(self.signatories) - 1)
        self.btn_edit.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel)
        if has_sel:
            role = self.signatories[r]
            self.txt_custom_role.setText(role)
            self.btn_update_custom.setEnabled(True)
        else:
            self.btn_update_custom.setEnabled(False)

    def edit_selected(self):
        r = self.list_widget.currentRow()
        if 0 <= r < len(self.signatories):
            current_val = self.signatories[r]
            text, ok = QInputDialog.getText(
                self,
                "แก้ไขรายชื่อผู้มาศาล",
                f"แก้ไขรายชื่อ / ตำแหน่ง ลำดับที่ {r + 1}:",
                QLineEdit.EchoMode.Normal,
                current_val
            )
            if ok and text.strip():
                self.signatories[r] = text.strip()
                self.refresh_ui()
                self.list_widget.setCurrentRow(r)

    def update_custom_role(self):
        r = self.list_widget.currentRow()
        text = self.txt_custom_role.text().strip()
        if 0 <= r < len(self.signatories) and text:
            self.signatories[r] = text
            self.refresh_ui()
            self.list_widget.setCurrentRow(r)

    def add_signatory(self, role: str):
        role_clean = role.strip()
        if not role_clean:
            return
        self.signatories.append(role_clean)
        self.refresh_ui()
        self.list_widget.setCurrentRow(len(self.signatories) - 1)

    def add_custom_role(self):
        txt = self.txt_custom_role.text().strip()
        if not txt:
            return
        self.add_signatory(txt)
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
        self.signatories.sort(key=get_court_tradition_weight)
        self.refresh_ui()

    def get_signatories(self) -> List[str]:
        return list(self.signatories)

    def set_signatories(self, roles: List[str]):
        self.signatories = [r.strip() for r in roles if r and r.strip()]
        self.refresh_ui()
