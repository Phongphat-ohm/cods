"""
UI Components Package
Modular collection of specialized widgets and cards for CODS.
"""
from ui.components.sidebar import SidebarWidget
from ui.components.autocomplete_input import JudicialAutocompleteInput
from ui.components.shortcut_bar import ShortcutTipBar
from ui.components.judicial_card import JudicialAccentCard
from ui.components.draggable_list import DraggableListWidget
from ui.components.paragraph_card import ParagraphCard
from ui.components.signatories_manager import SignatoriesManagerWidget
from ui.components.tutorial_overlay import TutorialOverlay, TutorialStep

__all__ = [
    "SidebarWidget",
    "JudicialAutocompleteInput",
    "ShortcutTipBar",
    "JudicialAccentCard",
    "DraggableListWidget",
    "ParagraphCard",
    "SignatoriesManagerWidget",
    "TutorialOverlay",
    "TutorialStep",
]
