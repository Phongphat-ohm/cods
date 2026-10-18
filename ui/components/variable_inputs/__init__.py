"""
Variable Inputs Package
Modular input widgets for template variables:
- ThaiDatePickerWidget
- TimeVariableInputWidget
- NumberVariableInputWidget
- SelectVariableInputWidget
- create_typed_variable_input
"""

from ui.components.variable_inputs.date_picker import ThaiDatePickerWidget
from ui.components.variable_inputs.time_input import TimeVariableInputWidget
from ui.components.variable_inputs.number_input import NumberVariableInputWidget
from ui.components.variable_inputs.select_input import SelectVariableInputWidget
from ui.components.variable_inputs.factory import create_typed_variable_input

__all__ = [
    "ThaiDatePickerWidget",
    "TimeVariableInputWidget",
    "NumberVariableInputWidget",
    "SelectVariableInputWidget",
    "create_typed_variable_input",
]
