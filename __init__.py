# Sequential Cloze Revealer
# Created by Adel Aitah
# GitHub: https://github.com/Doummar/Sequential_Cloze_Revealer
# Copyright (c) 2026 Adel Aitah — All rights reserved
"""
Sequential Cloze Revealer — Anki cloze-deletion addon
Minimalistic replacement for Enhanced Cloze that centres study content,
hides passive clozes, and provides sequential click / shortcut reveals
with configurable colours, layout modes, and dark-mode compatibility.
"""

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo, qconnect
import os

from . import note_type
from . import reviewer
from . import renderer

ADDON_NAME    = "Sequential Cloze Revealer"
ADDON_AUTHOR  = "Adel Aitah"
ADDON_VERSION = "1.0.0"
ADDON_URL     = "https://github.com/Doummar/Sequential_Cloze_Revealer"

def init_addon() -> None:
    # Set up and register our custom note type
    note_type.setup_note_type()
    # Initialize the reviewer enhancements
    reviewer.setup_reviewer()
    # Setup configuration menus
    setup_menu()

def setup_menu() -> None:
    action_settings = QAction("Sequential Revealer", mw)
    qconnect(action_settings.triggered, reviewer.show_settings_dialog)
    mw.form.menuTools.addAction(action_settings)

# Register addon when the profile is opened
gui_hooks.profile_did_open.append(init_addon)
