"""
Typed Variable Input Widget Factory
Instantiates the appropriate specialized variable widget according to type and options.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QLineEdit
from ui.components.variable_inputs.date_picker import ThaiDatePickerWidget
from ui.components.variable_inputs.time_input import TimeVariableInputWidget
from ui.components.variable_inputs.number_input import NumberVariableInputWidget
from ui.components.variable_inputs.select_input import SelectVariableInputWidget


def create_typed_variable_input(var_def: Any, initial_value: str = "", parent=None) -> QWidget:
    """
    Factory function to create the appropriate specialized input widget
    matching the variable's type and format specifications.
    Accepts either parsed variable dict or raw variable tag string.
    """
    if isinstance(var_def, str):
        from services.template_variable_service import parse_variable_tag
        var_def = parse_variable_tag(var_def)

    v_type = var_def.get('type', 'text')
    v_format = var_def.get('format_style', 'full')
    options = var_def.get('options', [])

    if v_type == 'date':
        return ThaiDatePickerWidget(initial_value=initial_value, default_format=v_format, parent=parent)
    elif v_type == 'time':
        return TimeVariableInputWidget(initial_value=initial_value, parent=parent)
    elif v_type == 'number':
        return NumberVariableInputWidget(initial_value=initial_value, parent=parent)
    elif v_type == 'select':
        return SelectVariableInputWidget(options=options, initial_value=initial_value, parent=parent)
    else:
        # Standard Text input
        txt = QLineEdit(parent)
        txt.setObjectName("formInput")
        txt.setPlaceholderText(f"กรอกข้อมูลสำหรับ \"{var_def.get('name', '')}\"...")
        txt.setText(initial_value)
        txt.setStyleSheet("""
            QLineEdit {
                font-size: 13.5px;
                padding: 7px 10px;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                color: #0f172a;
            }
            QLineEdit:focus {
                border: 1.5px solid #7c3aed;
                background: #faf5ff;
            }
        """)
        return txt
