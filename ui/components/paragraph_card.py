"""
Paragraph Card Component
Card representing one discrete paragraph with text box,
Drag & Drop reordering, template insertion, and template saving.
"""
import re
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QEvent, QMimeData
from PySide6.QtGui import QDrag
from services.icon_service import get_icon, get_pixmap
from ui.dialogs.template_select_dialog import TemplateSelectDialog
from ui.components.draggable_list import DraggableListWidget


class ParagraphCard(QFrame):
    """
    Card representing one discrete paragraph with text box,
    Drag & Drop reordering, template insertion, and template saving.
    """
    move_up_requested = Signal(object)
    move_down_requested = Signal(object)
    delete_requested = Signal(object)
    reorder_requested = Signal(int, int)  # (source_1based_index, target_1based_index)
    text_changed = Signal()

    def __init__(self, index: int = 1, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("paragraphCard")
        self.setAcceptDrops(True)
        self.drag_start_pos = None
        self.init_ui(text)

    def init_ui(self, initial_text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)

        # Header Row
        header_bar = QHBoxLayout()
        header_bar.setSpacing(8)

        # Drag grip handle
        self.drag_grip = QFrame()
        self.drag_grip.setObjectName("dragGripHandle")
        self.drag_grip.setToolTip("คลิกค้างแล้วลากเพื่อสลับลำดับย่อหน้านี้ (Drag & Drop)")
        self.drag_grip.setCursor(Qt.CursorShape.OpenHandCursor)
        grip_l = QHBoxLayout(self.drag_grip)
        grip_l.setContentsMargins(6, 4, 8, 4)
        grip_l.setSpacing(6)
        lbl_grip_icon = QLabel()
        lbl_grip_icon.setPixmap(get_pixmap("grip-vertical", color="#64748b", size=16))
        lbl_grip_txt = QLabel("ลากสลับตำแหน่ง")
        lbl_grip_txt.setStyleSheet("color: #475569; font-weight: 500; font-size: 13px;")
        grip_l.addWidget(lbl_grip_icon)
        grip_l.addWidget(lbl_grip_txt)
        self.drag_grip.installEventFilter(self)
        header_bar.addWidget(self.drag_grip)

        self.lbl_badge = QLabel(f"ย่อหน้าที่ {self.index}")
        self.lbl_badge.setObjectName("paragraphBadge")
        self.lbl_badge.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #4c1d95; "
            "background-color: #ede9fe; padding: 4px 10px; border-radius: 4px;"
        )
        header_bar.addWidget(self.lbl_badge)

        header_bar.addStretch()

        btn_mini_style = """
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #ddd6fe;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f3ff;
                border-color: #c4b5fd;
                color: #3b0764;
            }
            QPushButton:pressed {
                background-color: #ede9fe;
            }
            QPushButton:disabled {
                color: #94a3b8;
                border-color: #e2e8f0;
                background-color: #f8fafc;
            }
        """

        self.btn_insert_tpl = QPushButton("แทรก Template")
        self.btn_insert_tpl.setObjectName("cardMiniButton")
        self.btn_insert_tpl.setStyleSheet(btn_mini_style)
        self.btn_insert_tpl.setIcon(get_icon("clipboard-list", color="#4c1d95", size=15))
        self.btn_insert_tpl.setToolTip("เลือกข้อความสำเร็จรูปจาก Template มาใส่ในย่อหน้านี้")
        self.btn_insert_tpl.clicked.connect(self.handle_insert_template)
        header_bar.addWidget(self.btn_insert_tpl)

        self.btn_save_tpl = QPushButton("บันทึกเป็น Template")
        self.btn_save_tpl.setObjectName("cardMiniButton")
        self.btn_save_tpl.setStyleSheet(btn_mini_style)
        self.btn_save_tpl.setIcon(get_icon("save", color="#4c1d95", size=15))
        self.btn_save_tpl.setToolTip("บันทึกข้อความในย่อหน้านี้เป็น Template ส่วนตัว")
        self.btn_save_tpl.clicked.connect(self.handle_save_template)
        header_bar.addWidget(self.btn_save_tpl)

        self.btn_up = QPushButton("เลื่อนขึ้น")
        self.btn_up.setObjectName("cardMiniButton")
        self.btn_up.setStyleSheet(btn_mini_style)
        self.btn_up.setIcon(get_icon("chevron-up", color="#4c1d95", size=15))
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self))
        header_bar.addWidget(self.btn_up)

        self.btn_down = QPushButton("เลื่อนลง")
        self.btn_down.setObjectName("cardMiniButton")
        self.btn_down.setStyleSheet(btn_mini_style)
        self.btn_down.setIcon(get_icon("chevron-down", color="#4c1d95", size=15))
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self))
        header_bar.addWidget(self.btn_down)

        self.btn_del = QPushButton("ลบ")
        self.btn_del.setObjectName("cardMiniButtonDanger")
        self.btn_del.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #dc2626;
                border: 1.5px solid #fca5a5;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                color: #991b1b;
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
        self.btn_del.setToolTip("ลบย่อหน้านี้")
        self.btn_del.clicked.connect(self.handle_delete)
        header_bar.addWidget(self.btn_del)

        layout.addLayout(header_bar)

        # Paragraph Text Editor
        self.txt_editor = QTextEdit()
        self.txt_editor.setPlaceholderText(f"ระบุข้อความกระบวนพิจารณาสำหรับย่อหน้าที่ {self.index}...")
        self.txt_editor.setMinimumHeight(130)
        self.txt_editor.setPlainText(initial_text)
        self.txt_editor.textChanged.connect(self._on_internal_text_changed)
        layout.addWidget(self.txt_editor)

        # Variables badge indicator below editor
        self.lbl_vars_badge = QLabel()
        self.lbl_vars_badge.setStyleSheet("font-size: 13px; color: #4c1d95; background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 6px; padding: 6px 12px; font-weight: 500;")
        self.lbl_vars_badge.setVisible(False)
        layout.addWidget(self.lbl_vars_badge)
        self._update_vars_badge()

    def _on_internal_text_changed(self):
        self._update_vars_badge()
        self.text_changed.emit()

    def _update_vars_badge(self):
        txt = self.get_text()
        matches = re.findall(r'\{\{\s*([^}]+?)\s*\}\}|\{([^{}]+?)\}', txt)
        vars_found = []
        for m1, m2 in matches:
            t = (m1 or m2).strip()
            if t and not t.startswith(('#', '/')):
                vars_found.append(t)
        if vars_found:
            self.lbl_vars_badge.setText(f"ตรวจพบตัวแปรในย่อหน้านี้: {', '.join(vars_found)} (ระบบสร้างช่องกรอกข้อมูลให้ด้านบน)")
            self.lbl_vars_badge.setVisible(True)
        else:
            self.lbl_vars_badge.setVisible(False)

    def eventFilter(self, source, event):
        if source == self.drag_grip:
            if event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self.drag_start_pos = event.pos()
                self.drag_grip.setCursor(Qt.CursorShape.ClosedHandCursor)
            elif event.type() == QEvent.Type.MouseMove and event.buttons() == Qt.MouseButton.LeftButton:
                if self.drag_start_pos and (event.pos() - self.drag_start_pos).manhattanLength() > 4:
                    drag = QDrag(self)
                    mime_data = QMimeData()
                    mime_data.setData("application/x-cods-paragraph", str(self.index).encode('utf-8'))
                    mime_data.setData("application/x-jads-paragraph", str(self.index).encode('utf-8'))
                    drag.setMimeData(mime_data)
                    drag.exec(Qt.DropAction.MoveAction)
                    self.drag_grip.setCursor(Qt.CursorShape.OpenHandCursor)
                    self.drag_start_pos = None
                    return True
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self.drag_grip.setCursor(Qt.CursorShape.OpenHandCursor)
                self.drag_start_pos = None
        return super().eventFilter(source, event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-cods-paragraph") or event.mimeData().hasFormat("application/x-jads-paragraph"):
            event.acceptProposedAction()
            self.setProperty("dropTarget", True)
            self.style().unpolish(self)
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("dropTarget", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.setProperty("dropTarget", False)
        self.style().unpolish(self)
        self.style().polish(self)
        mime = event.mimeData()
        if mime.hasFormat("application/x-cods-paragraph") or mime.hasFormat("application/x-jads-paragraph"):
            try:
                tag = "application/x-cods-paragraph" if mime.hasFormat("application/x-cods-paragraph") else "application/x-jads-paragraph"
                src_str = mime.data(tag).data().decode('utf-8')
                src_idx = int(src_str)
                target_idx = self.index
                if src_idx != target_idx:
                    self.reorder_requested.emit(src_idx, target_idx)
                event.acceptProposedAction()
            except Exception:
                pass

    def set_index(self, index: int, is_first: bool = False, is_last: bool = False):
        self.index = index
        self.lbl_badge.setText(f"ย่อหน้าที่ {self.index}")
        self.txt_editor.setPlaceholderText(f"ระบุข้อความกระบวนพิจารณาสำหรับย่อหน้าที่ {self.index}...")
        self.btn_up.setEnabled(not is_first)
        self.btn_down.setEnabled(not is_last)

    @property
    def txt_content(self):
        """Backward compatibility alias for txt_editor."""
        return self.txt_editor

    def get_text(self) -> str:
        return self.txt_editor.toPlainText().strip()

    def set_text(self, text: str):
        self.txt_editor.setPlainText(text)

    def handle_insert_template(self):
        dlg = TemplateSelectDialog(self)
        if dlg.exec() and dlg.selected_content:
            existing = self.get_text()
            if existing:
                reply = QMessageBox.question(
                    self, "ยืนยันการแทรก Template",
                    "ย่อหน้านี้มีข้อความอยู่แล้ว คุณต้องการแทนที่ข้อความเดิม (Yes) หรือต่อท้ายข้อความเดิม (No)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.set_text(dlg.selected_content)
                elif reply == QMessageBox.StandardButton.No:
                    self.set_text(existing + "\n" + dlg.selected_content)
            else:
                self.set_text(dlg.selected_content)

    def handle_save_template(self):
        text = self.get_text()
        if not text:
            QMessageBox.warning(self, "แจ้งเตือน", "กรุณาพิมพ์ข้อความในย่อหน้านี้ก่อนทำการบันทึกเป็น Template")
            return
        from ui.dialogs.save_template_modal import SaveTemplateModal
        dlg = SaveTemplateModal(text, self)
        dlg.exec()

    def handle_delete(self):
        text = self.get_text()
        if text:
            reply = QMessageBox.question(
                self, "ยืนยันการลบย่อหน้า",
                f"คุณต้องการลบย่อหน้าที่ {self.index} หรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self.delete_requested.emit(self)
