"""
Paragraphs Management Section Component.
Encapsulates ordered judicial proceeding paragraph cards, placeholder display when empty,
card reordering, additions from templates, and synchronized variable extraction.
"""

from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal

from services.icon_service import get_icon, get_pixmap
from ui.components.paragraph_card import ParagraphCard


class ParagraphsSectionWidget(QWidget):
    """Component for managing list of ParagraphCard widgets and empty state."""

    template_select_requested = Signal()
    paragraphs_changed = Signal()
    chip_value_changed = Signal(str, str)  # var_name, new_val

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.paragraph_cards: List[ParagraphCard] = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)

        group_para = QFrame()
        group_para.setObjectName("innerGroupFrame")
        self.group_para_layout = QVBoxLayout(group_para)
        self.group_para_layout.setContentsMargins(20, 18, 20, 20)
        self.group_para_layout.setSpacing(14)

        # Header Toolbar
        para_top_bar = QHBoxLayout()
        v_para_title = QVBoxLayout()
        v_para_title.setSpacing(3)
        lbl_sec3 = QLabel("3. เนื้อหาข้อความกระบวนพิจารณาเพิ่มเติม (ไม่จำเป็นต้องมี)")
        lbl_sec3.setObjectName("sectionHeaderTitle")
        self.lbl_para_count = QLabel("(เริ่มต้นไม่มีกล่องข้อความ - กดปุ่มด้านขวาเพื่อเพิ่มหากต้องการ)")
        self.lbl_para_count.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 500;")
        v_para_title.addWidget(lbl_sec3)
        v_para_title.addWidget(self.lbl_para_count)
        para_top_bar.addLayout(v_para_title)
        para_top_bar.addStretch()

        self.btn_add_from_tpl = QPushButton("เพิ่มย่อหน้าจาก Template")
        self.btn_add_from_tpl.setObjectName("secondaryButtonSmall")
        self.btn_add_from_tpl.setStyleSheet("""
            QPushButton {
                background-color: #f3e8ff;
                color: #4c1d95;
                border: 1.5px solid #a855f7;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ede9fe;
                border-color: #7c3aed;
            }
        """)
        self.btn_add_from_tpl.setIcon(get_icon("clipboard-list", color="#4c1d95", size=15))
        self.btn_add_from_tpl.setToolTip("เลือกข้อความสำเร็จรูปจาก Template มาสร้างย่อหน้าใหม่ [Ctrl+T]")
        self.btn_add_from_tpl.clicked.connect(self.template_select_requested.emit)
        para_top_bar.addWidget(self.btn_add_from_tpl)

        self.btn_add_para = QPushButton("เพิ่มย่อหน้าเปล่า")
        self.btn_add_para.setObjectName("primaryButtonSmall")
        self.btn_add_para.setIcon(get_icon("plus", color="#ffffff", size=15))
        self.btn_add_para.setStyleSheet(
            "QPushButton { background-color: #4c1d95; color: #ffffff; border-radius: 5px; padding: 6px 14px; font-size: 13px; font-weight: 500; border: 1px solid #3b0764; } "
            "QPushButton:hover { background-color: #5b21b6; }"
        )
        self.btn_add_para.setToolTip("เพิ่มกล่องข้อความย่อหน้าเปล่าใหม่")
        self.btn_add_para.clicked.connect(lambda: self.add_paragraph_card())
        para_top_bar.addWidget(self.btn_add_para)

        self.group_para_layout.addLayout(para_top_bar)

        # Placeholder box when 0 paragraphs exist
        self.para_placeholder = QFrame()
        self.para_placeholder.setObjectName("paraPlaceholderBox")
        place_layout = QVBoxLayout(self.para_placeholder)
        place_layout.setContentsMargins(24, 28, 24, 28)
        place_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.setSpacing(12)

        place_icon = QLabel()
        place_icon.setPixmap(get_pixmap("file-text", color="#94a3b8", size=42))
        place_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.addWidget(place_icon)

        place_lbl_main = QLabel("ยังไม่มีข้อความกระบวนพิจารณาเพิ่มเติม")
        place_lbl_main.setStyleSheet("font-size: 16px; font-weight: 600; color: #334155;")
        place_lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.addWidget(place_lbl_main)

        place_lbl_sub = QLabel(
            "ย่อหน้าเพิ่มเติมเป็นตัวเลือกเสริม ท่านสามารถกดปุ่ม \"สร้างรายงานกระบวนพิจารณา (.docx)\" ได้ทันที\n"
            "หรือกดเลือกข้อความจาก Template หรือพิมพ์ย่อหน้าใหม่ได้ตามปุ่มด้านล่างนี้"
        )
        place_lbl_sub.setStyleSheet("font-size: 14px; color: #64748b; line-height: 1.5;")
        place_lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        place_layout.addWidget(place_lbl_sub)

        # Action Buttons in Central Placeholder Box
        place_btn_row = QHBoxLayout()
        place_btn_row.setSpacing(12)
        place_btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn_place_add_tpl = QPushButton("เพิ่มย่อหน้าจาก Template")
        btn_place_add_tpl.setObjectName("primaryButton")
        btn_place_add_tpl.setIcon(get_icon("clipboard-list", color="#ffffff", size=16))
        btn_place_add_tpl.setStyleSheet("""
            QPushButton {
                background-color: #4c1d95;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 22px;
                border-radius: 7px;
                border: 1px solid #3b0764;
            }
            QPushButton:hover {
                background-color: #5b21b6;
            }
        """)
        btn_place_add_tpl.setToolTip("เลือกข้อความสำเร็จรูปจาก Template มาเพิ่มเป็นย่อหน้าแรก [Ctrl+T]")
        btn_place_add_tpl.clicked.connect(self.template_select_requested.emit)
        place_btn_row.addWidget(btn_place_add_tpl)

        btn_place_add = QPushButton("เพิ่มย่อหน้าข้อความเปล่า")
        btn_place_add.setObjectName("secondaryButton")
        btn_place_add.setIcon(get_icon("plus", color="#4c1d95", size=15))
        btn_place_add.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                border-radius: 7px;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
                border-color: #c084fc;
            }
        """)
        btn_place_add.clicked.connect(lambda: self.add_paragraph_card())
        place_btn_row.addWidget(btn_place_add)

        place_layout.addLayout(place_btn_row)
        self.group_para_layout.addWidget(self.para_placeholder)

        # Container for paragraph cards
        self.para_cards_container = QVBoxLayout()
        self.para_cards_container.setSpacing(14)
        self.group_para_layout.addLayout(self.para_cards_container)

        # Bottom Add Paragraph Buttons (visible only when cards > 0)
        self.bottom_add_container = QHBoxLayout()
        self.bottom_add_container.setSpacing(10)

        self.btn_bottom_add_tpl = QPushButton("เพิ่มย่อหน้าจาก Template")
        self.btn_bottom_add_tpl.setObjectName("secondaryButton")
        self.btn_bottom_add_tpl.setIcon(get_icon("clipboard-list", color="#4c1d95", size=15))
        self.btn_bottom_add_tpl.setStyleSheet("""
            QPushButton {
                background-color: #f3e8ff;
                color: #4c1d95;
                border: 1.5px solid #a855f7;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #ede9fe;
            }
        """)
        self.btn_bottom_add_tpl.clicked.connect(self.template_select_requested.emit)
        self.btn_bottom_add_tpl.setVisible(False)
        self.bottom_add_container.addWidget(self.btn_bottom_add_tpl)

        self.btn_bottom_add_para = QPushButton("เพิ่มย่อหน้าเปล่าต่อท้าย")
        self.btn_bottom_add_para.setObjectName("secondaryButton")
        self.btn_bottom_add_para.setIcon(get_icon("plus", color="#4c1d95", size=15))
        self.btn_bottom_add_para.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #4c1d95;
                border: 1.5px solid #d8b4fe;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f3e8ff;
            }
        """)
        self.btn_bottom_add_para.clicked.connect(lambda: self.add_paragraph_card())
        self.btn_bottom_add_para.setVisible(False)
        self.bottom_add_container.addWidget(self.btn_bottom_add_para)
        self.bottom_add_container.addStretch()

        self.group_para_layout.addLayout(self.bottom_add_container)
        main_layout.addWidget(group_para)

    def add_paragraph_card(self, initial_text: str = "") -> ParagraphCard:
        idx = len(self.paragraph_cards) + 1
        card = ParagraphCard(index=idx, text=initial_text, parent=self)
        card.move_up_requested.connect(self.move_paragraph_up)
        card.move_down_requested.connect(self.move_paragraph_down)
        card.delete_requested.connect(self.delete_paragraph_card)
        card.reorder_requested.connect(self.reorder_paragraph_cards)
        card.text_changed.connect(self.paragraphs_changed.emit)
        card.chip_value_changed.connect(self.chip_value_changed.emit)

        # Pre-fill matching variable chips if already typed in another card
        if hasattr(card, 'chip_components'):
            for existing_card in self.paragraph_cards:
                if existing_card is not card and hasattr(existing_card, 'chip_components'):
                    for v_name, comp in existing_card.chip_components.items():
                        val = comp.get_value()
                        if val and v_name in card.chip_components and not card.chip_components[v_name].get_value():
                            card.chip_components[v_name].set_value(val)

        self.paragraph_cards.append(card)
        self.para_cards_container.addWidget(card)
        self.para_placeholder.setVisible(False)
        self.btn_bottom_add_para.setVisible(True)
        self.btn_bottom_add_tpl.setVisible(True)

        self.refresh_paragraph_indices()
        self.paragraphs_changed.emit()
        return card

    def reorder_paragraph_cards(self, src_idx: int, target_idx: int):
        s = src_idx - 1
        t = target_idx - 1
        if 0 <= s < len(self.paragraph_cards) and 0 <= t < len(self.paragraph_cards):
            card = self.paragraph_cards.pop(s)
            self.paragraph_cards.insert(t, card)
            self.rebuild_paragraph_layout()
            self.paragraphs_changed.emit()

    def move_paragraph_up(self, card: ParagraphCard):
        try:
            idx = self.paragraph_cards.index(card)
            if idx > 0:
                self.paragraph_cards[idx], self.paragraph_cards[idx - 1] = self.paragraph_cards[idx - 1], self.paragraph_cards[idx]
                self.rebuild_paragraph_layout()
                self.paragraphs_changed.emit()
        except ValueError:
            pass

    def move_paragraph_down(self, card: ParagraphCard):
        try:
            idx = self.paragraph_cards.index(card)
            if idx < len(self.paragraph_cards) - 1:
                self.paragraph_cards[idx], self.paragraph_cards[idx + 1] = self.paragraph_cards[idx + 1], self.paragraph_cards[idx]
                self.rebuild_paragraph_layout()
                self.paragraphs_changed.emit()
        except ValueError:
            pass

    def delete_paragraph_card(self, card: ParagraphCard):
        try:
            self.paragraph_cards.remove(card)
            self.para_cards_container.removeWidget(card)
            card.deleteLater()

            if not self.paragraph_cards:
                self.para_placeholder.setVisible(True)
                self.btn_bottom_add_para.setVisible(False)
                self.btn_bottom_add_tpl.setVisible(False)
                self.lbl_para_count.setText("(ไม่มีการระบุย่อหน้าเพิ่มเติม)")
            else:
                self.refresh_paragraph_indices()
            self.paragraphs_changed.emit()
        except ValueError:
            pass

    def rebuild_paragraph_layout(self):
        for card in self.paragraph_cards:
            self.para_cards_container.removeWidget(card)
        for card in self.paragraph_cards:
            self.para_cards_container.addWidget(card)
        self.refresh_paragraph_indices()

    def refresh_paragraph_indices(self):
        total = len(self.paragraph_cards)
        if total == 0:
            self.lbl_para_count.setText("(ไม่มีการระบุย่อหน้าเพิ่มเติม)")
        else:
            self.lbl_para_count.setText(f"(ทั้งหมด {total} ย่อหน้า)")
        for i, card in enumerate(self.paragraph_cards, start=1):
            card.set_index(i, is_first=(i == 1), is_last=(i == total))

    def get_paragraph_texts(self) -> List[str]:
        texts: List[str] = []
        for card in self.paragraph_cards:
            txt = card.get_text().strip() if hasattr(card, 'get_text') else ""
            if txt:
                texts.append(txt)
        return texts

    def clear_paragraphs(self):
        for card in list(self.paragraph_cards):
            self.para_cards_container.removeWidget(card)
            card.deleteLater()
        self.paragraph_cards.clear()
        self.para_placeholder.setVisible(True)
        self.btn_bottom_add_para.setVisible(False)
        self.btn_bottom_add_tpl.setVisible(False)
        self.refresh_paragraph_indices()
        self.paragraphs_changed.emit()
