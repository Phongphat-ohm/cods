"""
Backward-compatibility forwarder module for Dialogs.
All active dialog implementations are modularized under `ui.dialogs`.
"""
from ui.dialogs.template_select_dialog import TemplateSelectDialog
from ui.dialogs.template_manager_dialog import TemplateManagerDialog
from ui.dialogs.save_template_modal import SaveTemplateModal
from ui.dialogs.bench_manager_dialog import BenchManagerDialog
from ui.dialogs.signatory_role_manager_dialog import SignatoryRoleManagerDialog
from ui.dialogs.court_settings_dialog import CourtSettingsDialog
from ui.dialogs.shortcuts_guide_dialog import ShortcutsGuideDialog
from ui.dialogs.doc_type_select_dialog import DocTypeSelectDialog, SelectableDocTypeCard

__all__ = [
    "TemplateSelectDialog",
    "TemplateManagerDialog",
    "SaveTemplateModal",
    "BenchManagerDialog",
    "SignatoryRoleManagerDialog",
    "CourtSettingsDialog",
    "ShortcutsGuideDialog",
    "DocTypeSelectDialog",
    "SelectableDocTypeCard",
]
