"""
CODS Tutorial Spotlight Overlay
Interactive spotlight tour and contextual onboarding widget for PySide6.
Darkens background, cuts out a focused viewport around the target widget,
and displays an informative popover card guiding the user through features.
"""

from typing import List, Optional, Callable, Union
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QPoint, QRect, QRectF, Signal, QEvent
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QFont

from services import storage_service, icon_service
from ui.components.judicial_card import JudicialAccentCard


@dataclass
class TutorialStep:
    """Defines a single step in a tutorial tour."""
    target: Union[QWidget, Callable[[], Optional[QWidget]]]
    title: str
    description: str
    preferred_position: str = "auto"  # "auto", "bottom", "top", "left", "right"


class TutorialOverlay(QWidget):
    """
    Full-window translucent overlay that creates a spotlight cutout around
    target widgets and displays guided step-by-step instructions.
    """
    tour_finished = Signal(bool)  # emits True if completed, False if skipped

    def __init__(self, parent: QWidget, tutorial_key: str, steps: List[TutorialStep]):
        super().__init__(parent)
        self.tutorial_key = tutorial_key
        self.steps = steps
        self.current_step_idx = 0

        # Full-window coverage
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        if parent:
            self.setGeometry(parent.rect())
            parent.installEventFilter(self)

        self._init_ui()
        self.show_step(0)

    def _init_ui(self):
        # We don't use a standard layout for the overlay itself,
        # the card is placed manually in response to target geometries.
        self.card = JudicialAccentCard(
            stripe_color="#9333ea",  # Purple accent
            border_color="#d8b4fe",
            bg_color="#ffffff",
            stripe_width=5,
            radius=12,
            parent=self
        )
        self.card.setFixedWidth(420)
        self.card.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 12px;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(22, 16, 20, 16)
        card_layout.setSpacing(10)

        # Header Row: Badge + Step counter + Close (X)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.step_badge = QLabel("แนะนำการใช้งาน 1/1", self.card)
        self.step_badge.setStyleSheet("""
            QLabel {
                background-color: #f3e8ff;
                color: #7e22ce;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 10px;
                border-radius: 10px;
            }
        """)
        header_layout.addWidget(self.step_badge)
        header_layout.addStretch()

        self.btn_close = QPushButton("", self.card)
        self.btn_close.setIcon(icon_service.get_icon("x", color="#64748b", size=14))
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.setToolTip("ปิดคำแนะนำ (Esc)")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #94a3b8;
                font-size: 14px;
                font-weight: bold;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                color: #475569;
            }
        """)
        self.btn_close.clicked.connect(self.skip_tour)
        header_layout.addWidget(self.btn_close)
        card_layout.addLayout(header_layout)

        # Title
        self.lbl_title = QLabel("หัวข้อแนะนำ", self.card)
        self.lbl_title.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-weight: bold;
                color: #1e1b4b;
            }
        """)
        self.lbl_title.setWordWrap(True)
        card_layout.addWidget(self.lbl_title)

        # Description
        self.lbl_desc = QLabel("คำอธิบายขั้นตอน...", self.card)
        self.lbl_desc.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #475569;
                line-height: 1.5;
            }
        """)
        self.lbl_desc.setWordWrap(True)
        card_layout.addWidget(self.lbl_desc)

        # Divider
        divider = QFrame(self.card)
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #f1f5f9; max-height: 1px;")
        card_layout.addWidget(divider)

        # Bottom Row: Checkbox + Nav buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 4, 0, 0)
        bottom_layout.setSpacing(10)

        self.chk_dont_show = QCheckBox("ไม่ต้องแสดงอีก", self.card)
        self.chk_dont_show.setChecked(True)
        self.chk_dont_show.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_dont_show.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                font-weight: 600;
                color: #4c1d95;
                background-color: #f5f3ff;
                border: 1px solid #ddd6fe;
                border-radius: 5px;
                padding: 4px 10px;
                spacing: 6px;
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
        bottom_layout.addWidget(self.chk_dont_show)
        bottom_layout.addStretch()

        self.btn_back = QPushButton("ย้อนกลับ", self.card)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setFixedHeight(30)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
                color: #475569;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f1f5f9;
                border-color: #94a3b8;
            }
            QPushButton:disabled {
                color: #cbd5e1;
                border-color: #f1f5f9;
                background-color: #f8fafc;
            }
        """)
        self.btn_back.clicked.connect(self.prev_step)
        bottom_layout.addWidget(self.btn_back)

        self.btn_next = QPushButton("ถัดไป", self.card)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setFixedHeight(30)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #7e22ce;
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 12px;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6b21a8;
            }
        """)
        self.btn_next.clicked.connect(self.next_step)
        bottom_layout.addWidget(self.btn_next)

        card_layout.addLayout(bottom_layout)

    def _get_target_widget(self, step: TutorialStep) -> Optional[QWidget]:
        """Resolve target widget from either a QWidget reference or a callable."""
        if callable(step.target):
            try:
                return step.target()
            except Exception:
                return None
        return step.target

    def show_step(self, idx: int):
        if not self.steps:
            self.skip_tour()
            return

        if idx < 0:
            idx = 0
        if idx >= len(self.steps):
            self.complete_tour()
            return

        self.current_step_idx = idx
        step = self.steps[idx]

        total = len(self.steps)
        self.step_badge.setText(f"คำแนะนำ {idx + 1}/{total}")
        self.lbl_title.setText(step.title)
        self.lbl_desc.setText(step.description)

        # Nav button states
        self.btn_back.setEnabled(idx > 0)
        if idx == total - 1:
            self.btn_next.setText("เข้าใจแล้ว")
            self.btn_next.setStyleSheet("""
                QPushButton {
                    background-color: #16a34a;
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                    font-size: 12px;
                    color: #ffffff;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #15803d;
                }
            """)
        else:
            self.btn_next.setText("ถัดไป →")
            self.btn_next.setStyleSheet("""
                QPushButton {
                    background-color: #7e22ce;
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                    font-size: 12px;
                    color: #ffffff;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #6b21a8;
                }
            """)

        self.update_card_position()
        self.update()

    def update_card_position(self):
        """Position the card smartly relative to the target spotlight cutout."""
        if not self.parent():
            return

        self.setGeometry(self.parent().rect())
        step = self.steps[self.current_step_idx]
        target = self._get_target_widget(step)

        overlay_w = self.width()
        overlay_h = self.height()
        card_w = self.card.width()
        card_h = self.card.sizeHint().height()
        self.card.resize(card_w, card_h)

        if not target or not target.isVisible():
            # Center card if no target or target hidden
            cx = max(20, (overlay_w - card_w) // 2)
            cy = max(20, (overlay_h - card_h) // 2)
            self.card.move(cx, cy)
            return

        # Map target rect to overlay coordinates
        target_tl = target.mapToGlobal(QPoint(0, 0))
        overlay_tl = self.mapFromGlobal(target_tl)
        target_rect = QRect(overlay_tl, target.size())

        margin = 16
        pos_pref = step.preferred_position

        # Available space around target
        space_below = overlay_h - target_rect.bottom()
        space_above = target_rect.top()
        space_right = overlay_w - target_rect.right()
        space_left = target_rect.left()

        # Decide placement
        if pos_pref == "bottom" or (pos_pref == "auto" and space_below >= card_h + margin):
            # Place below
            x = target_rect.center().x() - (card_w // 2)
            y = target_rect.bottom() + margin
        elif pos_pref == "top" or (pos_pref == "auto" and space_above >= card_h + margin):
            # Place above
            x = target_rect.center().x() - (card_w // 2)
            y = target_rect.top() - card_h - margin
        elif pos_pref == "right" or (pos_pref == "auto" and space_right >= card_w + margin):
            # Place right
            x = target_rect.right() + margin
            y = target_rect.center().y() - (card_h // 2)
        elif pos_pref == "left" or (pos_pref == "auto" and space_left >= card_w + margin):
            # Place left
            x = target_rect.left() - card_w - margin
            y = target_rect.center().y() - (card_h // 2)
        else:
            # Fallback to center of largest space
            if space_below >= space_above:
                x = target_rect.center().x() - (card_w // 2)
                y = target_rect.bottom() + margin
            else:
                x = target_rect.center().x() - (card_w // 2)
                y = target_rect.top() - card_h - margin

        # Clamp within overlay bounds
        x = max(20, min(x, overlay_w - card_w - 20))
        y = max(20, min(y, overlay_h - card_h - 20))
        self.card.move(x, y)

    def paintEvent(self, event):
        """Draw darkened backdrop with rounded rectangular cutout over target."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        full_path = QPainterPath()
        full_path.addRect(QRectF(self.rect()))

        target_rect: Optional[QRect] = None
        if self.steps and self.current_step_idx < len(self.steps):
            step = self.steps[self.current_step_idx]
            target = self._get_target_widget(step)
            if target and target.isVisible():
                target_tl = target.mapToGlobal(QPoint(0, 0))
                overlay_tl = self.mapFromGlobal(target_tl)
                target_rect = QRect(overlay_tl, target.size())

        if target_rect and target_rect.isValid():
            # Pad cutout by 6px
            pad = 6
            cutout_rect = target_rect.adjusted(-pad, -pad, pad, pad)
            cutout_path = QPainterPath()
            cutout_path.addRoundedRect(QRectF(cutout_rect), 8, 8)
            full_path = full_path.subtracted(cutout_path)

        # Draw dark backdrop (slate-950 with 72% opacity)
        painter.fillPath(full_path, QColor(15, 23, 42, 185))

        # Draw glowing highlight border around spotlight cutout
        if target_rect and target_rect.isValid():
            pad = 6
            cutout_rect = target_rect.adjusted(-pad, -pad, pad, pad)
            highlight_pen = QPen(QColor(192, 132, 252, 230), 2)
            highlight_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(cutout_rect), 8, 8)

        painter.end()

    def next_step(self):
        if self.current_step_idx < len(self.steps) - 1:
            self.show_step(self.current_step_idx + 1)
        else:
            self.complete_tour()

    def prev_step(self):
        if self.current_step_idx > 0:
            self.show_step(self.current_step_idx - 1)

    def skip_tour(self):
        if self.chk_dont_show.isChecked():
            storage_service.mark_tutorial_completed(self.tutorial_key, True)
        self.tour_finished.emit(False)
        self.close_and_cleanup()

    def complete_tour(self):
        if self.chk_dont_show.isChecked():
            storage_service.mark_tutorial_completed(self.tutorial_key, True)
        self.tour_finished.emit(True)
        self.close_and_cleanup()

    def close_and_cleanup(self):
        if self.parent():
            self.parent().removeEventFilter(self)
        self.hide()
        self.deleteLater()

    def eventFilter(self, watched, event):
        """Keep overlay sized to parent and update spotlight if parent resizes/moves."""
        if watched == self.parent():
            if event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
                self.setGeometry(self.parent().rect())
                self.update_card_position()
                self.update()
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event):
        """Support keyboard navigation inside tutorial."""
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.skip_tour()
            event.accept()
        elif key in (Qt.Key.Key_Right, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.next_step()
            event.accept()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Backspace):
            self.prev_step()
            event.accept()
        else:
            super().keyPressEvent(event)
