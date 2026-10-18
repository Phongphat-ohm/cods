"""
Form Sections Modular Components.
Reusable section components for case information, bench pairing, paragraph management,
compromise case details, and dynamic template variables.
"""

from ui.components.form_sections.case_info_section import (
    CaseInfoSectionWidget,
    COMMON_HEARING_PURPOSES,
    COMMON_COURTS
)
from ui.components.form_sections.bench_pairing_section import BenchPairingWidget
from ui.components.form_sections.compromise_details_section import (
    CompromiseDetailsWidget,
    COMMON_COMPROMISE_SUBJECTS
)
from ui.components.form_sections.paragraphs_section import ParagraphsSectionWidget
from ui.components.form_sections.dynamic_variables_panel import DynamicVariablesPanel

__all__ = [
    "CaseInfoSectionWidget",
    "BenchPairingWidget",
    "CompromiseDetailsWidget",
    "ParagraphsSectionWidget",
    "DynamicVariablesPanel",
    "COMMON_HEARING_PURPOSES",
    "COMMON_COURTS",
    "COMMON_COMPROMISE_SUBJECTS",
]
