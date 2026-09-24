# Sequential Cloze
# Created by Adel Aitah
# GitHub: https://github.com/Doummar/Sequential_Cloze_Revealer
# Copyright (c) 2026 Adel Aitah — All rights reserved

"""
Sequential Cloze — Anki cloze-deletion addon
Minimalistic replacement for Enhanced Cloze that centres study content,
hides passive clozes, and provides sequential click / shortcut reveals
with unified .ctrl + .ibtn action bar matching Sentence Builder style.
"""

try:
    from aqt import mw, gui_hooks
    from aqt.qt import *
    from aqt.utils import showInfo, qconnect
except ImportError:
    mw = None
    gui_hooks = None

import os

from . import note_type
from . import reviewer
from . import renderer

ADDON_NAME    = "Sequential Cloze"
ADDON_AUTHOR  = "Adel Aitah"
ADDON_VERSION = "1.0.4"
ADDON_URL     = "https://github.com/Doummar/Sequential_Cloze_Revealer"

def init_addon() -> None:
    note_type.setup_note_type()
    reviewer.setup_reviewer()
    setup_menu()

def setup_menu() -> None:
    if not mw:
        return

    # Ensure single menu action instance even if profiles are switched
    if not getattr(mw, "_seq_cloze_action_created", False):
        mw._seq_cloze_action_created = True
        action = QAction("Sequential Cloze", mw)
        qconnect(action.triggered, reviewer.open_settings)
        mw.form.menuTools.addAction(action)

    if hasattr(mw.addonManager, "setConfigAction"):
        pkg = __name__.split(".")[0]
        mw.addonManager.setConfigAction(__name__, reviewer.open_settings)
        if pkg != __name__:
            mw.addonManager.setConfigAction(pkg, reviewer.open_settings)
        mw.addonManager.setConfigAction("sequential_cloze_revealer", reviewer.open_settings)
        try:
            mod_pkg = mw.addonManager.addonFromModule(__name__)
            if mod_pkg:
                mw.addonManager.setConfigAction(mod_pkg, reviewer.open_settings)
        except Exception:
            pass
        try:
            addon_dir = os.path.dirname(os.path.abspath(__file__))
            if hasattr(mw.addonManager, "allAddons"):
                for a in mw.addonManager.allAddons():
                    try:
                        if os.path.abspath(mw.addonManager.addonFolder(a)) == addon_dir:
                            mw.addonManager.setConfigAction(a, reviewer.open_settings)
                    except Exception:
                        pass
        except Exception:
            pass

if mw:
    setup_menu()

if gui_hooks:
    gui_hooks.profile_did_open.append(init_addon)
