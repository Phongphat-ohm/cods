"""
Judicial Accent Card Component
Dignified Court Card Frame with an antialiased vertical accent stripe on the left edge.
"""
from typing import Optional
from PySide6.QtWidgets import QWidget, QFrame
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QBrush


class JudicialAccentCard(QFrame):
    """
    Dignified Court Card Frame with an antialiased vertical accent stripe on the left edge.
    Eliminates Qt's asymmetric border-radius QSS rendering glitches by drawing via QPainter.
    """
    def __init__(
        self,
        stripe_color: str = "#4c1d95",
        border_color: str = "#ddd6fe",
        bg_color: str = "#f8fafc",
        stripe_width: int = 5,
        radius: int = 8,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.stripe_color = QColor(stripe_color)
        self.border_color = QColor(border_color)
        self.bg_color = QColor(bg_color)
        self.stripe_width = stripe_width
        self.radius = radius

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        rect = QRectF(1.0, 1.0, w - 2.0, h - 2.0)

        path = QPainterPath()
        path.addRoundedRect(rect, self.radius, self.radius)

        # 1. Fill card background
        painter.fillPath(path, QBrush(self.bg_color))

        # 2. Paint left accent stripe cleanly clipped within rounded card corners
        painter.save()
        painter.setClipPath(path)
        stripe_rect = QRectF(rect.x(), rect.y(), float(self.stripe_width), rect.height())
        painter.fillRect(stripe_rect, self.stripe_color)
        painter.restore()

        # 3. Draw outer rounded border
        pen = QPen(self.border_color, 1.5)
        painter.setPen(pen)
        painter.drawPath(path)
