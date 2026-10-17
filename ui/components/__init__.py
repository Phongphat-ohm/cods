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
]
