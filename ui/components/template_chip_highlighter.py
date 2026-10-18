"""
Template Chip Highlighter & Key Filter Component
Provides visual chip-style highlighting for template variables inside QTextEdit,
and intelligent keyboard navigation/editing so that:
- Pressing Backspace right after a chip enters inside to edit the variable name instead of breaking the chip.
- Deleting all content inside a variable removes the variable and its brackets completely.
- Pressing Delete right before a chip enters inside or cleanly removes empty chips.
"""

import re
from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QTextCursor, QKeyEvent
from PySide6.QtWidgets import QTextEdit, QApplication

TOKEN_PATTERN = re.compile(r'(\[[^\]\n]*\]|\{\{[^}\n]*\}\}|\{[^{}\n]*\})')


class TemplateChipKeyFilter(QObject):
    """
    Event filter for QTextEdit that manages seamless keyboard interaction with variable chips.
    - Pressing Backspace right after a closing bracket enters inside the variable for editing.
    - Pressing Backspace at the start of inner content moves cursor outside before the opening bracket.
    - Deleting all characters inside a variable removes the variable completely (including delimiters).
    - Backspacing or deleting inside an empty variable ([]) removes it completely.
    """

    def __init__(self, editor: QTextEdit):
        super().__init__(editor)
        self.editor = editor

    @classmethod
    def install(cls, editor: QTextEdit) -> "TemplateChipKeyFilter":
        """Convenience method to install this key filter onto a QTextEdit and its viewport."""
        filt = cls(editor)
        editor.installEventFilter(filt)
        if hasattr(editor, 'viewport') and editor.viewport():
            editor.viewport().installEventFilter(filt)
        return filt

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.KeyPress:
            if self._handle_key_press(event):
                return True
        elif event.type() in (QEvent.Type.MouseButtonRelease, QEvent.Type.MouseButtonPress):
            # If user clicked in the editor, ensure cursor doesn't land inside invisible hidden metadata
            self._snap_cursor_if_in_hidden_zone()
        return super().eventFilter(watched, event)

    def _snap_cursor_if_in_hidden_zone(self):
        """If cursor lands inside invisible metadata (:type:format), snap it immediately to visible name end."""
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            return
        pos = cursor.position()
        text = self.editor.toPlainText()
        for m in TOKEN_PATTERN.finditer(text):
            start, end = m.span(1)
            raw = m.group(1)
            open_len = 2 if raw.startswith('{{') else 1
            close_len = 2 if raw.endswith('}}') else 1
            inner_start = start + open_len
            inner_text = raw[open_len:len(raw)-close_len]
            colon_idx = inner_text.find(':')
            if colon_idx > 0:
                visible_name_end = inner_start + colon_idx
                if visible_name_end < pos < end:
                    cursor.setPosition(visible_name_end)
                    self.editor.setTextCursor(cursor)
                    return

    def _delete_range(self, start: int, end: int):
        cur = self.editor.textCursor()
        cur.beginEditBlock()
        cur.setPosition(start)
        cur.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cur.removeSelectedText()
        cur.endEditBlock()
        self.editor.setTextCursor(cur)

    def _handle_key_press(self, event: QKeyEvent) -> bool:
        key = event.key()
        modifiers = event.modifiers()
        is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        is_alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)

        if is_alt:
            return False

        # Handle Cut (Ctrl+X) with selection inside or covering a variable
        if is_ctrl and key == Qt.Key.Key_X:
            cursor = self.editor.textCursor()
            if cursor.hasSelection():
                sel_start = cursor.selectionStart()
                sel_end = cursor.selectionEnd()
                text = self.editor.toPlainText()
                for m in TOKEN_PATTERN.finditer(text):
                    start, end = m.span(1)
                    raw = m.group(1)
                    open_len = 2 if raw.startswith('{{') else 1
                    close_len = 2 if raw.endswith('}}') else 1
                    inner_start = start + open_len
                    inner_end = end - close_len
                    if sel_start <= inner_start and sel_end >= inner_end:
                        clip = QApplication.clipboard()
                        if clip:
                            clip.setText(cursor.selectedText())
                        self._delete_range(start, end)
                        return True
            return False

        if key not in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            return False

        cursor = self.editor.textCursor()
        pos = cursor.position()
        text = self.editor.toPlainText()

        # -------------------------------------------------------------
        # 1. Selection deletion handling (e.g. Ctrl+A -> Backspace, or mouse select)
        # -------------------------------------------------------------
        if cursor.hasSelection():
            sel_start = cursor.selectionStart()
            sel_end = cursor.selectionEnd()

            # Expand selection bounds so any variable whose visible content or boundaries
            # are included in the selection gets completely cleanly removed in a single keystroke
            expanded_start = sel_start
            expanded_end = sel_end
            for m in TOKEN_PATTERN.finditer(text):
                start, end = m.span(1)
                raw = m.group(1)
                open_len = 2 if raw.startswith('{{') else 1
                close_len = 2 if raw.endswith('}}') else 1
                inner_text = raw[open_len:len(raw)-close_len]
                colon_idx = inner_text.find(':')
                vis_len = colon_idx if colon_idx > 0 else len(inner_text)
                vis_start = start + open_len
                vis_end = vis_start + vis_len

                # Check if this token intersects with the selection
                if not (sel_end < start or sel_start > end):
                    # If selection covers the visible name or whole token, expand to delete the whole variable
                    if (sel_start <= vis_start and sel_end >= vis_end) or (sel_start <= start and sel_end >= end):
                        expanded_start = min(expanded_start, start)
                        expanded_end = max(expanded_end, end)

            self._delete_range(expanded_start, expanded_end)
            return True

        # -------------------------------------------------------------
        # 2. No selection: check position against variable tokens
        # -------------------------------------------------------------
        for m in TOKEN_PATTERN.finditer(text):
            start, end = m.span(1)
            raw = m.group(1)
            open_len = 2 if raw.startswith('{{') else 1
            close_len = 2 if raw.endswith('}}') else 1
            inner_start = start + open_len
            inner_end = end - close_len
            inner_text = raw[open_len:len(raw)-close_len]

            # Fast case: Empty or whitespace-only token (e.g. [], [ ])
            if len(inner_text.strip()) == 0:
                if key == Qt.Key.Key_Backspace and start < pos <= end:
                    self._delete_range(start, end)
                    return True
                elif key == Qt.Key.Key_Delete and start <= pos < end:
                    self._delete_range(start, end)
                    return True
                continue

            # Non-empty token:
            colon_idx = inner_text.find(':')
            visible_name_len = colon_idx if colon_idx > 0 else len(inner_text)
            visible_name_end = inner_start + visible_name_len

            if key == Qt.Key.Key_Backspace:
                # Ctrl+Backspace on or inside token: delete the entire variable
                if is_ctrl and (pos == end or (start < pos <= inner_end)):
                    self._delete_range(start, end)
                    return True

                # Cursor is right after closing delimiter (e.g. [วันนัด]| or [วันนัด:วันที่:เต็ม]|)
                # Enter inside before ':' to edit the visible variable name directly
                if pos == end:
                    cur = self.editor.textCursor()
                    cur.setPosition(visible_name_end)
                    self.editor.setTextCursor(cur)
                    return True

                # Cursor is right after opening delimiter (e.g. [|วันนัด])
                # Pressing Backspace here should delete the character BEFORE the variable (outside '[')
                if pos == inner_start:
                    if start > 0:
                        self._delete_range(start - 1, start)
                    return True

                # Cursor is inside the visible variable name
                if inner_start < pos <= visible_name_end:
                    # If only 1 character is left in visible name, deleting it removes the entire variable!
                    if visible_name_len <= 1:
                        self._delete_range(start, end)
                        return True
                    # Otherwise, normal Backspace edits the variable name
                    return False

                # If cursor is past visible name (inside hidden type part or right at closing delimiter)
                # pressing Backspace should directly delete the character at visible_name_end!
                if visible_name_end < pos < end:
                    if visible_name_len <= 1:
                        self._delete_range(start, end)
                        return True
                    else:
                        # Delete the last character of the visible name
                        self._delete_range(visible_name_end - 1, visible_name_end)
                        return True

            elif key == Qt.Key.Key_Delete:
                # Ctrl+Delete before or inside token: delete the entire variable
                if is_ctrl and (pos == start or (inner_start <= pos < end)):
                    self._delete_range(start, end)
                    return True

                # Cursor is right before opening delimiter (e.g. |[วันนัด])
                # Enter inside after opening delimiter
                if pos == start:
                    cur = self.editor.textCursor()
                    cur.setPosition(inner_start)
                    self.editor.setTextCursor(cur)
                    return True

                # Cursor is right before closing delimiter or hidden type end
                if pos == inner_end:
                    cur = self.editor.textCursor()
                    cur.setPosition(end)
                    self.editor.setTextCursor(cur)
                    return True

                # Cursor is inside the visible variable name
                if inner_start <= pos < visible_name_end:
                    # If only 1 character is left in visible name, deleting it removes the entire variable!
                    if visible_name_len <= 1:
                        self._delete_range(start, end)
                        return True
                    # Otherwise, normal Delete edits the variable name
                    return False

        return False


class TemplateChipHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter that formats variable tokens as clean chip components.
    The inner text receives a judicial lavender background and bold purple text,
    while enclosing delimiters ([ ], {{ }}, { }) and any type/format annotations
    are rendered transparent so the user sees ONLY the clean variable name in a pill chip.
    """

    def __init__(self, target):
        """
        Accepts either a QTextEdit or a QTextDocument.
        If a QTextEdit is passed, TemplateChipKeyFilter is automatically installed
        so that backspace navigates inside chips and empty variables are cleanly removed.
        """
        if isinstance(target, QTextEdit):
            super().__init__(target.document())
            self.editor = target
            self.key_filter = TemplateChipKeyFilter.install(target)
        else:
            super().__init__(target)
            self.editor = None
            self.key_filter = None
        
        # Chip Pill Format for the text
        self.chip_format = QTextCharFormat()
        self.chip_format.setBackground(QColor("#ede9fe"))  # Soft lavender chip background
        self.chip_format.setForeground(QColor("#4c1d95"))  # Official judicial deep purple
        self.chip_format.setFontWeight(QFont.Weight.Bold)

        self.hide_format = QTextCharFormat()
        self.hide_format.setForeground(QColor(0, 0, 0, 0))  # Fully transparent
        self.hide_format.setFontPointSize(1)  # Minimal valid size (> 0) to avoid taking visible space
        self.hide_format.setFontLetterSpacing(0.001)  # Minimal letter spacing to prevent ghost whitespace

        # Match [variable], {{variable}}, {variable}
        self.pattern = re.compile(r'(\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]\n]+)\]|\{\{\s*([^}\n]+)\}\}|\{([^{}\n]+)\})')

    def highlightBlock(self, text: str):
        for m in self.pattern.finditer(text):
            full_span = m.span(1)
            raw_full = m.group(1)
            
            start = full_span[0]
            end = full_span[1]

            if raw_full.startswith('{{') and raw_full.endswith('}}'):
                open_len = 2
                close_len = 2
            elif raw_full.startswith('[') and raw_full.endswith(']'):
                open_len = 1
                close_len = 1
                if '\U0001f3f7' in raw_full:
                    tag_pos = raw_full.find('\U0001f3f7')
                    open_len = tag_pos + len('\U0001f3f7\ufe0f') + (1 if raw_full[tag_pos + len('\U0001f3f7\ufe0f'):].startswith(' ') else 0)
            elif raw_full.startswith('{') and raw_full.endswith('}'):
                open_len = 1
                close_len = 1
            else:
                open_len = 0
                close_len = 0

            # 1. Hide opening delimiter
            if open_len > 0:
                self.setFormat(start, open_len, self.hide_format)

            # 2. Format variable name as clean Chip Component (hide any type and data annotations)
            inner_start = start + open_len
            inner_len = (end - close_len) - inner_start
            if inner_len > 0:
                inner_text = text[inner_start : end - close_len]
                if ':' in inner_text:
                    colon_pos = inner_text.find(':')
                    name_len = colon_pos
                    type_len = inner_len - name_len
                    # Format ONLY the variable name as clean Chip Component
                    if name_len > 0:
                        self.setFormat(inner_start, name_len, self.chip_format)
                    # Completely hide the type and options annotation (:type:format)
                    self.setFormat(inner_start + name_len, type_len, self.hide_format)
                else:
                    self.setFormat(inner_start, inner_len, self.chip_format)

            # 3. Hide closing delimiter
            if close_len > 0:
                self.setFormat(end - close_len, close_len, self.hide_format)


def attach_chip_editor(editor: QTextEdit) -> TemplateChipHighlighter:
    """Convenience helper to attach both highlighter and chip key filter to a QTextEdit."""
    return TemplateChipHighlighter(editor)


def format_text_as_chips_html(text: str) -> str:
    """
    Convert text with variables into safe HTML where variables are rendered as
    clean, symbol-free Chip Component pills (pure text without type badge).
    """
    if not text:
        return ""
    
    escaped = (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
    )
    
    from services.template_variable_service import parse_variable_tag

    def _chip_replacer(m):
        raw_tag = (m.group(1) or m.group(2) or "").strip()
        raw_tag = re.sub(r'^[\U0001f3f7\ufe0f\s]+', '', raw_tag).strip()
        meta = parse_variable_tag(raw_tag)
        base_name = meta['name'] or raw_tag

        return (
            f'<span style="background-color: #ede9fe; color: #4c1d95; '
            f'border: 1.5px solid #c4b5fd; border-radius: 12px; padding: 2px 10px; '
            f'font-weight: 600; font-size: 13px; margin: 0 3px; display: inline-block;">'
            f'{base_name}</span>'
        )

    html_with_chips = re.sub(r'\[\s*(?:\U0001f3f7\ufe0f)?\s*([^\]]+?)\s*\]|\{\{\s*([^}]+?)\s*\}\}', _chip_replacer, escaped)
    html_with_chips = re.sub(r'\{([^{}]+?)\}', _chip_replacer, html_with_chips)
    
    return f'<div style="font-family: Kanit, sans-serif; line-height: 1.8; color: #0f172a;">{html_with_chips}</div>'
