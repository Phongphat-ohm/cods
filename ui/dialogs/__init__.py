"""
Dialogs Package
Modular dialogs and modals for CODS.
"""
from ui.dialogs.template_select_dialog import TemplateSelectDialog
from ui.dialogs.template_manager_dialog import TemplateManagerDialog
from ui.dialogs.save_template_modal import SaveTemplateModal
from ui.dialogs.bench_manager_dialog import BenchManagerDialog
from ui.dialogs.signatory_role_manager_dialog import SignatoryRoleManagerDialog
from ui.dialogs.court_settings_dialog import CourtSettingsDialog
from ui.dialogs.shortcuts_guide_dialog import ShortcutsGuideDialog
from ui.dialogs.doc_type_select_dialog import DocTypeSelectDialog, SelectableDocTypeCard
from ui.dialogs.welcome_wizard_dialog import WelcomeWizardDialog
from ui.dialogs.variable_define_dialog import VariableDefineDialog
from ui.dialogs.about_dialog import AboutDialog
from ui.dialogs.template_recovery_dialog import TemplateRecoveryDialog

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
    "WelcomeWizardDialog",
    "VariableDefineDialog",
    "AboutDialog",
    "TemplateRecoveryDialog",
]
