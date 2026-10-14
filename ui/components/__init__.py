"""
UI Components Package
Modular collection of specialized widgets and cards for JADS.
"""
from ui.components.sidebar import SidebarWidget
from ui.components.autocomplete_input import JudicialAutocompleteInput
from ui.components.shortcut_bar import ShortcutTipBar
from ui.components.judicial_card import JudicialAccentCard
from ui.components.draggable_list import DraggableListWidget
from ui.components.paragraph_card import ParagraphCard
from ui.components.signatories_manager import SignatoriesManagerWidget

__all__ = [
    "SidebarWidget",
    "JudicialAutocompleteInput",
    "ShortcutTipBar",
    "JudicialAccentCard",
    "DraggableListWidget",
    "ParagraphCard",
    "SignatoriesManagerWidget",
]
