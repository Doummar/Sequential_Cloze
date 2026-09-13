# Sequential Cloze Revealer
# Created by Adel Aitah
# GitHub: https://github.com/Doummar/Sequential_Cloze_Revealer
# Copyright (c) 2026 Adel Aitah — All rights reserved

"""
Sequential Cloze Revealer — Anki cloze-deletion addon
Minimalistic replacement for Enhanced Cloze that centres study content,
hides passive clozes, and provides sequential click / shortcut reveals
with unified .ctrl + .ibtn action bar matching Sentence Builder style.
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
ADDON_VERSION = "1.0.1"
ADDON_URL     = "https://github.com/Doummar/Sequential_Cloze_Revealer"

def init_addon() -> None:
    note_type.setup_note_type()
    reviewer.setup_reviewer()
    setup_menu()

def setup_menu() -> None:
    action = QAction("Sequential Cloze", mw)
    qconnect(action.triggered, reviewer.show_settings_dialog)
    mw.form.menuTools.addAction(action)

    if hasattr(mw.addonManager, "setConfigAction"):
        pkg = __name__.split(".")[0]
        mw.addonManager.setConfigAction(__name__, reviewer.show_settings_dialog)
        mw.addonManager.setConfigAction(pkg, reviewer.show_settings_dialog)
        mw.addonManager.setConfigAction("sequential_cloze_revealer", reviewer.show_settings_dialog)

gui_hooks.profile_did_open.append(init_addon)
