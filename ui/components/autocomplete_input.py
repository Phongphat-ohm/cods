"""
Judicial Autocomplete Input Component
Custom standalone autocomplete input for Court of Justice workflows.
Displays filtered suggestions immediately on focus/click without requiring prior typing.
Supports Up/Down keyboard navigation, Enter/Tab commit, Esc dismiss, and real-time substring filtering.
100% Offline, Native PySide6 implementation. Zero emojis.
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QLineEdit, QListWidget, QListWidgetItem, QFrame,
    QVBoxLayout, QApplication
)
from PySide6.QtCore import Qt, Signal, QPoint, QEvent
from PySide6.QtGui import QKeyEvent, QFocusEvent


class AutocompletePopup(QFrame):
    """Frameless dropdown popup container holding the suggestions list."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("autocompletePopup")
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.list_widget = QListWidget(self)
        self.list_widget.setObjectName("autocompleteList")
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.list_widget)


class JudicialAutocompleteInput(QLineEdit):
    """
    Enhanced QLineEdit with instant popup suggestions on focus,
    keyboard navigation (Up/Down/Enter/Tab/Esc), and real-time substring matching.
    """

    item_selected = Signal(str)

    def __init__(self, items: Optional[List[str]] = None, placeholder: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("judicialAutocompleteInput")
        if placeholder:
            self.setPlaceholderText(placeholder)

        self._all_items: List[str] = list(items) if items else []
        self._filtered_items: List[str] = []
        self._show_on_focus: bool = True
        self._max_visible_items: int = 7

        # Setup popup
        self.popup = AutocompletePopup(None)
        self.popup.list_widget.itemClicked.connect(self._on_item_clicked)
        self.popup.list_widget.itemPressed.connect(self._on_item_clicked)

        # Install event filter on application to handle clicks outside the popup/input
        QApplication.instance().installEventFilter(self)

        # Wire text edits for live filtering
        self.textEdited.connect(self._on_text_edited)

    def set_items(self, items: List[str]):
        """Update the list of suggestion items."""
        self._all_items = [str(it).strip() for it in items if str(it).strip()]
        if self.popup.isVisible():
            self._filter_and_show(self.text())

    def get_items(self) -> List[str]:
        """Get the current suggestion items."""
        return list(self._all_items)

    def currentText(self) -> str:
        """Compatibility accessor returning current text."""
        return self.text()

    def setEditText(self, val: str):
        """Compatibility setter updating text."""
        self.setText(str(val))

    def add_item(self, item: str):
        """Add a single item if not already present."""
        clean = str(item).strip()
        if clean and clean not in self._all_items:
            self._all_items.append(clean)
            if self.popup.isVisible():
                self._filter_and_show(self.text())

    def set_show_on_focus(self, enabled: bool):
        """Enable or disable showing popup immediately upon receiving focus."""
        self._show_on_focus = enabled

    # -------------------------------------------------------------------------
    # Filtering & Popup Display
    # -------------------------------------------------------------------------
    def _filter_and_show(self, query: str = ""):
        if not self.isVisible():
            self.hide_popup()
            return

        q = query.strip().lower()
        if not q:
            self._filtered_items = list(self._all_items)
        else:
            self._filtered_items = [it for it in self._all_items if q in it.lower()]

        if not self._filtered_items:
            self.hide_popup()
            return

        self.popup.list_widget.clear()
        for it in self._filtered_items:
            item = QListWidgetItem(it)
            self.popup.list_widget.addItem(item)

        # Calculate height based on item count
        item_count = min(len(self._filtered_items), self._max_visible_items)
        item_height = 34
        popup_height = (item_count * item_height) + 6

        # Position popup directly beneath the QLineEdit or flip above if bottom overflows screen
        screen = self.screen() or QApplication.primaryScreen()
        avail_geo = screen.availableGeometry() if screen else None

        popup_width = max(self.width(), 220)
        global_pos = self.mapToGlobal(QPoint(0, self.height() + 2))

        if avail_geo and (global_pos.y() + popup_height > avail_geo.bottom() - 10):
            above_y = self.mapToGlobal(QPoint(0, -popup_height - 2)).y()
            if above_y >= avail_geo.top():
                global_pos.setY(above_y)

        self.popup.setGeometry(global_pos.x(), global_pos.y(), popup_width, popup_height)

        if not self.popup.isVisible():
            self.popup.show()

    def hide_popup(self):
        """Hide the suggestion popup if visible."""
        try:
            if hasattr(self, 'popup') and self.popup is not None and self.popup.isVisible():
                self.popup.hide()
        except (RuntimeError, AttributeError):
            pass

    def is_popup_visible(self) -> bool:
        """Check if suggestion popup is currently visible."""
        try:
            return hasattr(self, 'popup') and self.popup is not None and self.popup.isVisible()
        except (RuntimeError, AttributeError):
            return False

    # -------------------------------------------------------------------------
    # Selection Handlers
    # -------------------------------------------------------------------------
    def _commit_selection(self, index: int):
        if 0 <= index < len(self._filtered_items):
            chosen = self._filtered_items[index]
            self.setText(chosen)
            self.hide_popup()
            self.item_selected.emit(chosen)

    def _on_item_clicked(self, item: QListWidgetItem):
        if not item:
            return
        chosen = item.text()
        self.setText(chosen)
        self.hide_popup()
        self.item_selected.emit(chosen)

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------
    def _on_text_edited(self, text: str):
        if self.isVisible():
            self._filter_and_show(text)

    def focusInEvent(self, event: QFocusEvent):
        super().focusInEvent(event)
        if self._show_on_focus and self.isVisible():
            self._filter_and_show(self.text())

    def hideEvent(self, event):
        self.hide_popup()
        super().hideEvent(event)

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        # Note: Do not hide popup immediately here so mouse clicks on popup items work.
        # Clicking outside will be caught by eventFilter, and Tab/Enter are handled by keyPressEvent.

    def eventFilter(self, watched, event):
        if self.is_popup_visible():
            if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick):
                # Check if click is on input or popup
                pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
                input_rect = self.geometry()
                input_global = self.mapToGlobal(QPoint(0, 0))
                input_rect.moveTo(input_global)
                
                popup_rect = self.popup.geometry()
                if not input_rect.contains(pos) and not popup_rect.contains(pos):
                    self.hide_popup()
            elif event.type() == QEvent.Type.ApplicationDeactivate:
                self.hide_popup()
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if self._show_on_focus and not self.popup.isVisible():
            self._filter_and_show(self.text())

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()

        if self.popup.isVisible():
            if key == Qt.Key.Key_Down:
                current_row = self.popup.list_widget.currentRow()
                if current_row < self.popup.list_widget.count() - 1:
                    self.popup.list_widget.setCurrentRow(current_row + 1)
                else:
                    self.popup.list_widget.setCurrentRow(0)
                event.accept()
                return

            elif key == Qt.Key.Key_Up:
                current_row = self.popup.list_widget.currentRow()
                if current_row > 0:
                    self.popup.list_widget.setCurrentRow(current_row - 1)
                else:
                    self.popup.list_widget.setCurrentRow(self.popup.list_widget.count() - 1)
                event.accept()
                return

            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_row = self.popup.list_widget.currentRow()
                if current_row >= 0:
                    self._commit_selection(current_row)
                    event.accept()
                    return
                elif self._filtered_items:
                    # Select first match if none explicitly highlighted
                    self._commit_selection(0)
                    event.accept()
                    return

            elif key == Qt.Key.Key_Tab:
                current_row = self.popup.list_widget.currentRow()
                if current_row >= 0:
                    self._commit_selection(current_row)
                else:
                    self.hide_popup()
                # Pass Tab event to super so Qt moves focus to the next field smoothly
                super().keyPressEvent(event)
                return

            elif key == Qt.Key.Key_Escape:
                self.hide_popup()
                event.accept()
                return

        elif key == Qt.Key.Key_Down:
            # If popup is hidden, pressing down opens it
            self._filter_and_show(self.text())
            if self.popup.list_widget.count() > 0:
                self.popup.list_widget.setCurrentRow(0)
            event.accept()
            return

        super().keyPressEvent(event)

    def moveEvent(self, event):
        super().moveEvent(event)
        try:
            if hasattr(self, 'popup') and self.popup is not None and self.popup.isVisible():
                global_pos = self.mapToGlobal(QPoint(0, self.height() + 2))
                self.popup.move(global_pos)
        except (RuntimeError, AttributeError):
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            if hasattr(self, 'popup') and self.popup is not None and self.popup.isVisible():
                self.popup.setFixedWidth(max(self.width(), 220))
        except (RuntimeError, AttributeError):
            pass

    def hideEvent(self, event):
        self.hide_popup()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.hide_popup()
        app = QApplication.instance()
        if app:
            try:
                app.removeEventFilter(self)
            except Exception:
                pass
        super().closeEvent(event)
