"""
UI Components Package
Modular collection of specialized widgets and cards for CODS.
Uses PEP 562 lazy module loading for instantaneous startup performance.
"""

def __getattr__(name: str):
    if name == "CODSSplashScreen":
        from ui.components.splash_screen import CODSSplashScreen
        return CODSSplashScreen
    elif name == "SidebarWidget":
        from ui.components.sidebar import SidebarWidget
        return SidebarWidget
    elif name == "JudicialAutocompleteInput":
        from ui.components.autocomplete_input import JudicialAutocompleteInput
        return JudicialAutocompleteInput
    elif name == "ShortcutTipBar":
        from ui.components.shortcut_bar import ShortcutTipBar
        return ShortcutTipBar
    elif name == "JudicialAccentCard":
        from ui.components.judicial_card import JudicialAccentCard
        return JudicialAccentCard
    elif name == "DraggableListWidget":
        from ui.components.draggable_list import DraggableListWidget
        return DraggableListWidget
    elif name == "ParagraphCard":
        from ui.components.paragraph_card import ParagraphCard
        return ParagraphCard
    elif name == "SignatoriesManagerWidget":
        from ui.components.signatories_manager import SignatoriesManagerWidget
        return SignatoriesManagerWidget
    elif name == "OnlineSignatoriesManagerWidget":
        from ui.components.online_signatories_manager import OnlineSignatoriesManagerWidget
        return OnlineSignatoriesManagerWidget
    elif name in ("TutorialOverlay", "TutorialStep"):
        from ui.components.tutorial_overlay import TutorialOverlay, TutorialStep
        return TutorialOverlay if name == "TutorialOverlay" else TutorialStep
    elif name in ("TemplateChipHighlighter", "TemplateChipKeyFilter"):
        from ui.components.template_chip_highlighter import TemplateChipHighlighter, TemplateChipKeyFilter
        return TemplateChipHighlighter if name == "TemplateChipHighlighter" else TemplateChipKeyFilter
    elif name == "VariableChipComponent":
        from ui.components.variable_chip_widget import VariableChipComponent
        return VariableChipComponent
    elif name in ("ThaiDatePickerWidget", "TimeVariableInputWidget", "NumberVariableInputWidget", "SelectVariableInputWidget", "create_typed_variable_input"):
        import ui.components.variable_inputs as vi
        return getattr(vi, name)
    elif name in ("show_date_chip_menu", "show_time_chip_menu", "show_money_chip_menu", "show_select_chip_menu", "show_text_chip_menu", "show_combined_chip_menu", "prompt_custom_variable_define"):
        import ui.components.template_chip_menu as tcm
        return getattr(tcm, name)
    elif name in ("CaseInfoSectionWidget", "BenchPairingWidget", "CompromiseDetailsWidget", "ParagraphsSectionWidget", "DynamicVariablesPanel"):
        import ui.components.form_sections as fs
        return getattr(fs, name)
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "SidebarWidget",
    "JudicialAutocompleteInput",
    "ShortcutTipBar",
    "JudicialAccentCard",
    "DraggableListWidget",
    "ParagraphCard",
    "SignatoriesManagerWidget",
    "OnlineSignatoriesManagerWidget",
    "TutorialOverlay",
    "TutorialStep",
    "CODSSplashScreen",
    "TemplateChipHighlighter",
    "TemplateChipKeyFilter",
    "VariableChipComponent",
    "ThaiDatePickerWidget",
    "TimeVariableInputWidget",
    "NumberVariableInputWidget",
    "SelectVariableInputWidget",
    "create_typed_variable_input",
    "show_date_chip_menu",
    "show_time_chip_menu",
    "show_money_chip_menu",
    "show_select_chip_menu",
    "show_text_chip_menu",
    "show_combined_chip_menu",
    "prompt_custom_variable_define",
    "CaseInfoSectionWidget",
    "BenchPairingWidget",
    "CompromiseDetailsWidget",
    "ParagraphsSectionWidget",
    "DynamicVariablesPanel",
]
