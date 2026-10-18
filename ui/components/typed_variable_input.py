"""
CODS Typed Variable Input Components (Facade)
Re-exports modular components from `ui.components.variable_inputs`
and `ui.dialogs.variable_define_dialog` for backward compatibility.
"""

from ui.components.variable_inputs import (
    ThaiDatePickerWidget,
    TimeVariableInputWidget,
    NumberVariableInputWidget,
    SelectVariableInputWidget,
    create_typed_variable_input,
)
from ui.dialogs.variable_define_dialog import VariableDefineDialog

__all__ = [
    "ThaiDatePickerWidget",
    "TimeVariableInputWidget",
    "NumberVariableInputWidget",
    "SelectVariableInputWidget",
    "create_typed_variable_input",
    "VariableDefineDialog",
]
