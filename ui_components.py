"""
Backward-compatibility forwarder module for UI Components.
All active component implementations are modularized under `ui.components`.
"""
from ui.components.judicial_card import JudicialAccentCard
from ui.components.draggable_list import DraggableListWidget
from ui.components.paragraph_card import ParagraphCard
from ui.components.signatories_manager import SignatoriesManagerWidget
from ui.components.autocomplete_input import JudicialAutocompleteInput
from ui.components.sidebar import SidebarWidget
from ui.components.shortcut_bar import ShortcutTipBar

__all__ = [
    "JudicialAccentCard",
    "DraggableListWidget",
    "ParagraphCard",
    "SignatoriesManagerWidget",
    "JudicialAutocompleteInput",
    "SidebarWidget",
    "ShortcutTipBar",
]
