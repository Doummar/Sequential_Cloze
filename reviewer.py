# Handles Reviewer settings GUI dialogs and overrides for Sequential Cloze Revealer
# Styled after native Anki dark/light preferences dialogs.

import os
import json
import copy
import webbrowser
try:
    import aqt
    from aqt import mw
    from aqt.utils import showInfo, askUser, qconnect
    from aqt.qt import *
except ImportError:
    aqt = None
    mw = None
    try:
        from PyQt6.QtWidgets import *
        from PyQt6.QtCore import *
    except ImportError:
        try:
            from PyQt5.QtWidgets import *
            from PyQt5.QtCore import *
        except ImportError:
            class _DummySignal:
                def connect(self, *a, **k): pass
                def emit(self, *a, **k): pass

            class _DummyWidget:
                def __init__(self, *args, **kwargs):
                    self.clicked = _DummySignal()
                    self.rejected = _DummySignal()
                    self.textChanged = _DummySignal()
                    self.currentIndexChanged = _DummySignal()
                    self.toggled = _DummySignal()
                    self.finished = _DummySignal()
                def currentIndex(self): return 0
                def currentText(self): return ""
                def currentData(self): return None
                def itemData(self, *a): return None
                def itemText(self, *a): return ""
                def count(self): return 0
                def value(self): return 20
                def text(self): return ""
                def isChecked(self): return False
                def findData(self, *a): return 0
                def findText(self, *a): return 0
                def addItem(self, *a, **k): pass
                def clear(self): pass
                def insertSeparator(self, *a): pass
                def setItemData(self, *a, **k): pass
                def setCurrentIndex(self, *a): pass
                def setCurrentText(self, *a): pass
                def setMaxVisibleItems(self, *a): pass
                def setView(self, *a): pass
                def view(self): return self
                def setFont(self, *a): pass
                def setVisible(self, *a): pass
                def setRowVisible(self, *a): pass
                def setChecked(self, *a): pass
                def setValue(self, *a): pass
                def setText(self, *a): pass
                def setRange(self, *a): pass
                def setSuffix(self, *a): pass
                def setEnabled(self, *a): pass
                def family(self): return "Arial"
                def bindings(self): return [{"type": "wheel", "value": "down"}]
                def exec(self): return 0
                def exec_(self): return 0
                def isVisible(self): return False
                def raise_(self): pass
                def activateWindow(self): pass
                def addRow(self, *a): pass
                def addTab(self, *a): pass
                def addWidget(self, *a): pass
                def addLayout(self, *a): pass
                def addStretch(self, *a): pass
                def setContentsMargins(self, *a): pass
                def setSpacing(self, *a): pass
                def setWindowTitle(self, *a): pass
                def resize(self, *a): pass
                def setMinimumSize(self, *a): pass
                def setMinimumWidth(self, *a): pass
                def setMinimumHeight(self, *a): pass
                def setSizePolicy(self, *a): pass
                def adjustSize(self, *a): pass
                def sizeHint(self): return type("SH", (), {"width": lambda s: 580, "height": lambda s: 680})()
                def width(self): return 580
                def height(self): return 680
                def showEvent(self, *a): pass
                def layout(self): return self
                def activate(self): pass
                def saveGeometry(self): return b""
                def restoreGeometry(self, *a): return False
                def accept(self): pass
                def reject(self): pass
                def closeEvent(self, *a): pass
                def setLayout(self, *a): pass
                def __getattr__(self, name): return lambda *a, **k: _DummyWidget()

            class _DummyButtonBox(_DummyWidget):
                StandardButton = type("SB", (), {"Close": 1})()
                Close = 1

            class _DummySettings:
                def __init__(self, *a, **k): pass
                def value(self, key, default=None): return default
                def setValue(self, key, val): pass

            QDialog = _DummyWidget
            QWidget = _DummyWidget
            QLayout = _DummyWidget
            QVBoxLayout = _DummyWidget
            QHBoxLayout = _DummyWidget
            QFormLayout = _DummyWidget
            QTabWidget = _DummyWidget
            QGroupBox = _DummyWidget
            QLabel = _DummyWidget
            QPushButton = _DummyWidget
            QComboBox = _DummyWidget
            QSpinBox = _DummyWidget
            QCheckBox = _DummyWidget
            QLineEdit = _DummyWidget
            QAction = _DummyWidget
            QDialogButtonBox = _DummyButtonBox
            QColorDialog = _DummyWidget
            QSizePolicy = _DummyWidget
            QProxyStyle = _DummyWidget
            QStyle = _DummyWidget
            QSettings = _DummySettings
            Qt = type("DummyQt", (), {"AlignmentFlag": type("AF", (), {"AlignLeft": 1, "AlignVCenter": 2})()})()

try:
    from PyQt6.QtGui import QFont, QColor
except ImportError:
    try:
        from PyQt5.QtGui import QFont, QColor
    except ImportError:
        class _DummyColor:
            def __init__(self, *a, **k): pass
            def isValid(self): return True
            def name(self): return "#c00000"
        QColor = _DummyColor

from . import bindings


def _qt_val(base_obj, *paths, default=None, **kwargs):
    """Safely retrieves Qt enum values across PyQt5 and PyQt6."""
    if "fallback" in kwargs:
        default = kwargs["fallback"]
    if base_obj is None:
        return default
    for path in paths:
        try:
            curr = base_obj
            for part in str(path).split('.'):
                curr = getattr(curr, part)
            if curr is not None:
                return curr
        except (AttributeError, TypeError):
            continue
    return default


def _is_night_mode() -> bool:
    if not mw:
        return False
    try:
        from aqt.theme import theme_manager
        return theme_manager.night_mode
    except Exception:
        pass
    try:
        return bool(mw.pm.night_mode())
    except Exception:
        return False


def _get_dialog_qss(is_night: bool) -> str:
    """Clean native Qt styles that blend seamlessly with Anki without artificial color overrides."""
    if is_night:
        return """
            QDialog {
                font-size: 12px;
            }
            QGroupBox {
                margin-top: 8px;
                padding: 10px 10px 8px 10px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                font-weight: normal;
            }
            QComboBox {
                combobox-popup: 0;
            }
            QComboBox QAbstractItemView {
                max-height: 320px;
            }
            QComboBox, QSpinBox, QLineEdit {
                min-height: 26px;
                max-height: 26px;
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 4px;
                padding: 2px 8px;
                background-color: rgba(255, 255, 255, 0.06);
                color: #e6e6e6;
                selection-background-color: #2b5b88;
            }
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
                border: 1px solid #4a9eff;
                background-color: rgba(255, 255, 255, 0.09);
            }
            QListWidget {
                border: 1px solid rgba(255, 255, 255, 0.20);
                border-radius: 4px;
                background-color: rgba(255, 255, 255, 0.05);
                color: #e6e6e6;
                padding: 3px;
                outline: none;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 3px;
                min-height: 22px;
            }
            QListWidget::item:selected {
                background-color: #2b5b88;
                color: #ffffff;
            }
            QListWidget::item:hover:!selected {
                background-color: rgba(255, 255, 255, 0.08);
            }
            QPushButton {
                min-height: 26px;
                max-height: 26px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 4px;
                padding: 2px 14px;
                background-color: rgba(255, 255, 255, 0.07);
                color: #e6e6e6;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.30);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.04);
            }
            QPushButton:default {
                background-color: #1a68b5;
                border: 1px solid #3388dc;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:default:hover {
                background-color: #2079d2;
                border: 1px solid #4da3f5;
            }
            QCheckBox {
                spacing: 8px;
            }
        """
    else:
        return """
            QDialog {
                font-size: 12px;
            }
            QGroupBox {
                margin-top: 8px;
                padding: 10px 10px 8px 10px;
                font-weight: bold;
                border: 1px solid #d4d4d8;
                border-radius: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                font-weight: normal;
            }
            QComboBox {
                combobox-popup: 0;
            }
            QComboBox QAbstractItemView {
                max-height: 320px;
            }
            QComboBox, QSpinBox, QLineEdit {
                min-height: 26px;
                max-height: 26px;
                border: 1px solid #c4c4c8;
                border-radius: 4px;
                padding: 2px 8px;
                background-color: #ffffff;
                color: #1f1f1f;
                selection-background-color: #1a73e8;
            }
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {
                border: 1px solid #1a73e8;
            }
            QListWidget {
                border: 1px solid #c4c4c8;
                border-radius: 4px;
                background-color: #ffffff;
                color: #1f1f1f;
                padding: 3px;
                outline: none;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 3px;
                min-height: 22px;
            }
            QListWidget::item:selected {
                background-color: #e8f0fe;
                color: #1a73e8;
            }
            QListWidget::item:hover:!selected {
                background-color: #f1f3f4;
            }
            QPushButton {
                min-height: 26px;
                max-height: 26px;
                border: 1px solid #c4c4c8;
                border-radius: 4px;
                padding: 2px 14px;
                background-color: #f8f9fa;
                color: #1f1f1f;
            }
            QPushButton:hover {
                background-color: #f1f3f4;
                border-color: #b0b0b4;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
            }
            QPushButton:default {
                background-color: #1a73e8;
                border: 1px solid #1558b0;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton:default:hover {
                background-color: #1765cc;
            }
            QCheckBox {
                spacing: 8px;
            }
        """


_CONFIG_CACHE = None


def invalidate_config_cache() -> None:
    """Clears the in-memory config cache so any updates take effect immediately in the reviewer."""
    global _CONFIG_CACHE
    _CONFIG_CACHE = None


def apply_config_to_reviewer(card=None) -> None:
    """
    Applies current configuration directly to the active Anki reviewer webview live without restart.
    Updates CSS variables, card alignment/position classes, control positions, font styles, colors,
    and binding definitions.
    """
    try:
        if not (mw and hasattr(mw, "reviewer") and mw.reviewer and hasattr(mw.reviewer, "web") and mw.reviewer.web):
            return
        cur_card = card or getattr(mw.reviewer, "card", None)
        if not cur_card:
            return
        from . import renderer
        if not renderer._is_our_card(cur_card):
            return

        _, _, payload_config = renderer.get_payload_and_resources(cur_card, force_reload=True)
        config = get_addon_config(force_reload=True)
        injected_style_raw = renderer.generate_injected_css_vars(config)
        injected_style_escaped = injected_style_raw.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
        is_bold_str = "true" if config.get("bold_cloze_text", False) else "false"
        script = (
            f"{payload_config}\n"
            "var existingVars = document.getElementById('sq-injected-vars');\n"
            f"if (existingVars) {{ existingVars.outerHTML = \"{injected_style_escaped}\"; }}\n"
            f"else if (document.head) {{ document.head.insertAdjacentHTML('beforeend', \"{injected_style_escaped}\"); }}\n"
            "var cont = document.querySelector('.anki-card-container');\n"
            "if (cont) {\n"
            f"    if ({is_bold_str}) {{ cont.classList.add('bold-cloze'); }}\n"
            "    else { cont.classList.remove('bold-cloze'); }\n"
            "    if (typeof window.applyClozeConfigLive === 'function') {\n"
            "        window.applyClozeConfigLive(window.MINIMAL_CLOZE_CONFIG);\n"
            "    } else if (typeof window.setupClozeInteractions === 'function') {\n"
            "        window.setupClozeInteractions();\n"
            "    }\n"
            "}"
        )
        mw.reviewer.web.eval(script)
    except Exception:
        pass


def on_config_updated(new_conf=None) -> None:
    """Invoked when Anki or user modifies config externally."""
    invalidate_config_cache()
    get_addon_config(force_reload=True)
    apply_config_to_reviewer()


def setup_reviewer() -> None:
    # Ensure config is initialized, safely merged with defaults on update/startup, and cached
    invalidate_config_cache()
    get_addon_config(force_reload=True)
    pkg = get_addon_pkg()
    if mw and hasattr(mw, "addonManager") and mw.addonManager:
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        keys = {pkg, os.path.basename(addon_dir), "sequential_cloze_revealer", __name__.split(".")[0]}
        for k in keys:
            if not k:
                continue
            try:
                if hasattr(mw.addonManager, "setConfigUpdatedAction"):
                    mw.addonManager.setConfigUpdatedAction(k, lambda _c: on_config_updated(_c))
            except Exception:
                pass


def get_addon_pkg() -> str:
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    dir_name = os.path.basename(addon_dir)
    if mw and hasattr(mw, "addonManager") and mw.addonManager:
        try:
            pkg = mw.addonManager.addonFromModule(__name__)
            if pkg:
                return pkg
        except Exception:
            pass
        try:
            if hasattr(mw.addonManager, "allAddons"):
                for a in mw.addonManager.allAddons():
                    try:
                        if os.path.abspath(mw.addonManager.addonFolder(a)) == addon_dir:
                            return a
                    except Exception:
                        pass
        except Exception:
            pass
    top_pkg = __name__.split(".")[0]
    return top_pkg or dir_name or "sequential_cloze_revealer"


def get_default_config() -> dict:
    """Returns author default settings with config.json merged over standard defaults."""
    base_defaults = {
        "controls_position": "top-right",
        "card_vertical_position": "top",
        "card_horizontal_align": "center",
        "font_family": "System Default",
        "font_size": 20,
        "bold_cloze_text": False,
        "center_mode": True,
        "mitcent_mode": False,
        "reveal_speed": 120,
        "enable_click_reveal": True,
        "show_info_by_default": False,
        "enable_dark_compatibility": True,
        "auto_reveal_back": False,
        "cloze_revealed_custom": False,
        "cloze_revealed_color": "#c00000",
        "cloze_hidden_custom": False,
        "cloze_hidden_color": "#0284c7",
        "review_mode": "sequential_reveal",
        "context_before": 1,
        "context_after": 0,
        "context_mask_subsequent": True,
        "back_context_before": "all",
        "back_context_after": "all",
        "shortcut_roll": "Space",
        "shortcut_reveal_all": "Shift + Space",
        "shortcut_info": "H",
        "shortcut_image": "G",
        "auto_theme_mode": True,
        "input_bindings": {
            "reveal": [
                {"type": "wheel", "value": "down"}
            ]
        }
    }
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(addon_dir, "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    base_defaults.update(data)
        except Exception:
            pass
    return json.loads(json.dumps(base_defaults))


def merge_configs(user_cfg: dict, default_cfg: dict) -> tuple:
    """
    Safely merges user configuration with defaults:
    - Never overwrites existing user settings.
    - If user config has a key -> keep the user's value.
    - If user config is missing a key -> supply the default value.
    - Preserves unknown / legacy user keys.
    Returns (merged_dict, was_modified).
    """
    if not user_cfg or not isinstance(user_cfg, dict):
        return json.loads(json.dumps(default_cfg)), True

    merged = json.loads(json.dumps(user_cfg))
    was_modified = False

    for key, default_val in default_cfg.items():
        if key not in merged:
            merged[key] = json.loads(json.dumps(default_val))
            was_modified = True
        elif isinstance(default_val, dict) and isinstance(merged[key], dict):
            for subkey, subval in default_val.items():
                if subkey not in merged[key]:
                    merged[key][subkey] = json.loads(json.dumps(subval))
                    was_modified = True

    return merged, was_modified


def get_addon_config(force_reload: bool = False) -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None and not force_reload:
        return json.loads(json.dumps(_CONFIG_CACHE))

    default_cfg = get_default_config()
    pkg = get_addon_pkg()
    addon_dir = os.path.dirname(os.path.abspath(__file__))

    user_cfg = None
    if mw and hasattr(mw, "addonManager") and mw.addonManager:
        candidates = [pkg, os.path.basename(addon_dir), "sequential_cloze_revealer", __name__.split(".")[0]]
        for k in candidates:
            if not k:
                continue
            try:
                c = mw.addonManager.getConfig(k)
                if c and isinstance(c, dict) and len(c) > 0:
                    user_cfg = c
                    break
            except Exception:
                pass

    # Fallback to meta.json in add-on folder
    if user_cfg is None:
        try:
            meta_path = os.path.join(addon_dir, "meta.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                if isinstance(meta_data, dict) and "config" in meta_data and isinstance(meta_data["config"], dict):
                    user_cfg = meta_data["config"]
        except Exception:
            pass

    # Fallback to config.json in add-on folder
    if user_cfg is None:
        try:
            cfg_path = os.path.join(addon_dir, "config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    user_cfg = data
        except Exception:
            pass

    if user_cfg is None:
        user_cfg = {}

    merged_cfg, was_modified = merge_configs(user_cfg, default_cfg)
    bindings.migrate_legacy_config(merged_cfg)

    # Save merged config back only when new keys were added during the update
    if was_modified and mw and hasattr(mw, "addonManager") and mw.addonManager:
        try:
            mw.addonManager.writeConfig(pkg, merged_cfg)
        except Exception:
            pass

    _CONFIG_CACHE = json.loads(json.dumps(merged_cfg))
    return json.loads(json.dumps(_CONFIG_CACHE))


def save_addon_config(new_config: dict) -> bool:
    """
    Completely and persistently saves the add-on configuration:
    1. Updates the in-memory cache _CONFIG_CACHE immediately.
    2. Writes to Anki's AddonManager (writeConfig) using all potential package identifiers.
    3. Updates Anki's in-memory mw.addonManager._configs cache if present.
    4. Writes directly to config.json in the add-on directory as a permanent fallback.
    5. Updates meta.json in the add-on directory if it exists.
    6. Applies changes live to the active reviewer webview without requiring Anki restart.
    """
    global _CONFIG_CACHE
    current = get_addon_config()
    merged = {**current, **new_config}
    cloned = json.loads(json.dumps(merged))
    _CONFIG_CACHE = cloned

    addon_dir = os.path.dirname(os.path.abspath(__file__))
    pkg = get_addon_pkg()

    # 1. Write to Anki addonManager
    if mw and hasattr(mw, "addonManager") and mw.addonManager:
        keys_to_write = {pkg, os.path.basename(addon_dir), "sequential_cloze_revealer", __name__.split(".")[0]}
        for k in keys_to_write:
            if not k:
                continue
            try:
                mw.addonManager.writeConfig(k, cloned)
            except Exception:
                pass
            try:
                if hasattr(mw.addonManager, "_configs") and isinstance(mw.addonManager._configs, dict):
                    mw.addonManager._configs[k] = json.loads(json.dumps(cloned))
            except Exception:
                pass

    # 2. Always persist directly to config.json in addon_dir
    try:
        cfg_path = os.path.join(addon_dir, "config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cloned, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

    # 3. If meta.json exists, keep its "config" key in sync
    try:
        meta_path = os.path.join(addon_dir, "meta.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)
            if isinstance(meta_data, dict):
                meta_data["config"] = json.loads(json.dumps(cloned))
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

    # 4. Apply changes live to reviewer webview immediately
    apply_config_to_reviewer()
    return True


_settings_dialog = None
_help_dialog_instance = None


def _set_combo_data(combo, val):
    if not combo or val is None:
        return
    count = getattr(combo, "count", lambda: 0)()
    for i in range(count):
        d = getattr(combo, "itemData", lambda idx: None)(i)
        if d == val or str(d).lower() == str(val).lower():
            combo.setCurrentIndex(i)
            return
        t = getattr(combo, "itemText", lambda idx: "")(i)
        if str(t).lower() == str(val).lower():
            combo.setCurrentIndex(i)
            return


def _pick_color_for_edit(edit_widget, parent_widget):
    try:
        from aqt.qt import QColorDialog
    except Exception:
        try:
            from PyQt6.QtWidgets import QColorDialog
        except Exception:
            try:
                from PyQt5.QtWidgets import QColorDialog
            except Exception:
                QColorDialog = None
    if not QColorDialog:
        return
    cur_text = edit_widget.text().strip()
    try:
        init_col = QColor(cur_text)
    except Exception:
        init_col = QColor("#c00000")
    col = QColorDialog.getColor(init_col, parent_widget, "Choose Cloze Color")
    if col and getattr(col, "isValid", lambda: True)():
        edit_widget.setText(getattr(col, "name", lambda: cur_text)())


class SettingsDialog(QDialog):
    DEFAULT_WIDTH = 580
    DEFAULT_HEIGHT = 680

    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("Sequential Cloze — Preferences")

        # Force taller default size and comfortable minimum size
        self.setMinimumSize(520, 560)
        self.resize(SettingsDialog.DEFAULT_WIDTH, SettingsDialog.DEFAULT_HEIGHT)

        is_night = _is_night_mode()
        self.setStyleSheet(_get_dialog_qss(is_night))

        # 1. Single root layout on self only
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # 2. QTabWidget built on self with expanding stretch factor
        self.tabs = QTabWidget(self)
        root_layout.addWidget(self.tabs, 1)

        # 3. Load active config
        self.config = get_addon_config(force_reload=True)

        # =============================================================
        # TAB 1: General
        # =============================================================
        tab_general = QWidget(self.tabs)
        layout_general = QVBoxLayout(tab_general)
        layout_general.setContentsMargins(10, 10, 10, 10)
        layout_general.setSpacing(8)

        # 1A. Card Layout & Alignment
        grp_layout = QGroupBox("Card Layout & Alignment", tab_general)
        form_layout = QFormLayout(grp_layout)
        form_layout.setContentsMargins(10, 8, 10, 8)
        form_layout.setVerticalSpacing(6)

        self.controls_pos_combo = QComboBox(grp_layout)
        self.controls_pos_combo.addItem("Top Right", "top-right")
        self.controls_pos_combo.addItem("Top Left", "top-left")
        self.controls_pos_combo.addItem("Bottom Right", "bottom-right")
        self.controls_pos_combo.addItem("Bottom Left", "bottom-left")
        form_layout.addRow("Controls Position:", self.controls_pos_combo)

        self.card_vert_combo = QComboBox(grp_layout)
        self.card_vert_combo.addItem("Top", "top")
        self.card_vert_combo.addItem("Center", "center")
        self.card_vert_combo.addItem("Bottom", "bottom")
        form_layout.addRow("Card Vertical Position:", self.card_vert_combo)

        self.card_horiz_combo = QComboBox(grp_layout)
        self.card_horiz_combo.addItem("Center", "center")
        self.card_horiz_combo.addItem("Left", "left")
        self.card_horiz_combo.addItem("Right", "right")
        form_layout.addRow("Card Horizontal Align:", self.card_horiz_combo)

        layout_general.addWidget(grp_layout)

        # 1B. Typography
        grp_typo = QGroupBox("Typography", tab_general)
        form_typo = QFormLayout(grp_typo)
        form_typo.setContentsMargins(10, 8, 10, 8)
        form_typo.setVerticalSpacing(6)

        self.font_family_combo = QComboBox(grp_typo)

        # Enforce compact dropdown popup (14 visible items, ~320px, scrollable, no empty space)
        try:
            from aqt.qt import QProxyStyle, QStyle
            class _CompactComboProxyStyle(QProxyStyle):
                def styleHint(self, hint, option=None, widget=None, returnData=None):
                    # SH_ComboBox_Popup = 0 forces standard dropdown list instead of full-screen menu
                    try:
                        name = getattr(hint, "name", "")
                        if name == "SH_ComboBox_Popup" or "SH_ComboBox_Popup" in str(hint):
                            return 0
                        sh_hint = getattr(getattr(QStyle, "StyleHint", QStyle), "SH_ComboBox_Popup", None)
                        if sh_hint is None:
                            sh_hint = getattr(QStyle, "SH_ComboBox_Popup", None)
                        if sh_hint is not None and (hint == sh_hint or int(hint) == int(sh_hint)):
                            return 0
                        if int(hint) == 25:
                            return 0
                    except Exception:
                        pass
                    try:
                        return super().styleHint(hint, option, widget, returnData)
                    except Exception:
                        try:
                            return super().styleHint(hint)
                        except Exception:
                            return 0

            cur_style = self.font_family_combo.style()
            if cur_style is not None:
                self._font_combo_style = _CompactComboProxyStyle(cur_style)
                self.font_family_combo.setStyle(self._font_combo_style)
        except Exception:
            pass

        # Disable Qt menu-style popup in stylesheet to prevent screen-spanning container
        try:
            self.font_family_combo.setStyleSheet(
                "QComboBox { combobox-popup: 0; } QComboBox QAbstractItemView { max-height: 320px; }"
            )
        except Exception:
            pass

        if hasattr(self.font_family_combo, "setMaxVisibleItems"):
            self.font_family_combo.setMaxVisibleItems(14)

        try:
            view = self.font_family_combo.view()
            if view:
                if hasattr(view, "setUniformItemSizes"):
                    view.setUniformItemSizes(True)
                if hasattr(view, "setVerticalScrollBarPolicy"):
                    from aqt.qt import Qt
                    sb = getattr(getattr(Qt, "ScrollBarPolicy", Qt), "ScrollBarAsNeeded", None)
                    if sb is None:
                        sb = getattr(Qt, "ScrollBarAsNeeded", 0)
                    view.setVerticalScrollBarPolicy(sb)
                if hasattr(view, "setMaximumHeight"):
                    view.setMaximumHeight(320)
        except Exception:
            pass

        # Clamp popup container height to ~320px when shown, eliminating any empty white panels
        try:
            orig_show_popup = self.font_family_combo.showPopup
            def _clamped_show_popup():
                try:
                    orig_show_popup()
                    v = self.font_family_combo.view()
                    if v:
                        if hasattr(v, "setMaximumHeight"):
                            v.setMaximumHeight(320)
                        p = v.parentWidget()
                        if p and hasattr(p, "setMaximumHeight"):
                            p.setMaximumHeight(320)
                except Exception:
                    try:
                        orig_show_popup()
                    except Exception:
                        pass
            self.font_family_combo.showPopup = _clamped_show_popup
        except Exception:
            pass

        self._populate_font_families()
        # Aliases for compatibility
        self.font_family_combo.text = lambda: self.font_family_combo.currentText()
        self.font_family_combo.setText = lambda t: self._set_font_family_text(t)
        self.font_family_edit = self.font_family_combo
        form_typo.addRow("Font Family:", self.font_family_combo)

        # Small preview label under the dropdown using the selected font
        self.font_preview_lbl = QLabel("Aa Bb Cc 123", grp_typo)
        self.font_preview_lbl.setStyleSheet("padding: 2px 6px; border: 1px solid rgba(128, 128, 128, 0.25); border-radius: 4px;")
        form_typo.addRow("Preview:", self.font_preview_lbl)

        if hasattr(self.font_family_combo, "currentIndexChanged"):
            self.font_family_combo.currentIndexChanged.connect(self._update_font_preview)

        self.font_size_sb = QSpinBox(grp_typo)
        self.font_size_sb.setRange(10, 72)
        self.font_size_sb.setSuffix(" px")
        form_typo.addRow("Base Font Size:", self.font_size_sb)

        self.bold_cloze_text_cb = QCheckBox("Bold cloze text", grp_typo)
        form_typo.addRow(self.bold_cloze_text_cb)

        layout_general.addWidget(grp_typo)

        # 1C. Centering Options
        grp_centering = QGroupBox("Centering Options", tab_general)
        vbox_centering = QVBoxLayout(grp_centering)
        vbox_centering.setContentsMargins(10, 8, 10, 8)
        vbox_centering.setSpacing(6)

        self.center_mode_cb = QCheckBox("Center Cloze Text (Center Mode)", grp_centering)
        vbox_centering.addWidget(self.center_mode_cb)

        self.mitcent_mode_cb = QCheckBox("Compact Centered (Minimal Center)", grp_centering)
        vbox_centering.addWidget(self.mitcent_mode_cb)

        layout_general.addWidget(grp_centering)
        layout_general.addStretch(1)

        self.tabs.addTab(tab_general, "General")

        # =============================================================
        # TAB 2: Reveal Controls
        # =============================================================
        tab_reveal = QWidget(self.tabs)
        layout_reveal = QVBoxLayout(tab_reveal)
        layout_reveal.setContentsMargins(10, 10, 10, 10)
        layout_reveal.setSpacing(8)

        # 2A. Reveal Behavior
        grp_reveal = QGroupBox("Reveal Behavior", tab_reveal)
        vbox_reveal = QVBoxLayout(grp_reveal)
        vbox_reveal.setContentsMargins(10, 10, 10, 8)
        vbox_reveal.setSpacing(6)

        speed_row = QHBoxLayout()
        speed_row.setSpacing(10)
        speed_lbl = QLabel("Reveal Speed (Transition):", grp_reveal)
        self.reveal_speed_sb = QSpinBox(grp_reveal)
        self.reveal_speed_sb.setRange(0, 250)
        self.reveal_speed_sb.setSingleStep(5)
        self.reveal_speed_sb.setSuffix(" ms")
        self.reveal_speed_sb.setFixedWidth(100)
        self.reveal_speed_sb.setFixedHeight(26)
        speed_row.addWidget(speed_lbl)
        speed_row.addWidget(self.reveal_speed_sb)
        speed_row.addStretch(1)
        vbox_reveal.addLayout(speed_row)

        self.enable_click_reveal_cb = QCheckBox("Click [...] to reveal individual cloze", grp_reveal)
        vbox_reveal.addWidget(self.enable_click_reveal_cb)

        self.show_info_cb = QCheckBox("Show Info field by default on question", grp_reveal)
        vbox_reveal.addWidget(self.show_info_cb)

        self.auto_reveal_back_cb = QCheckBox("Auto-reveal all clozes when card flips to back", grp_reveal)
        vbox_reveal.addWidget(self.auto_reveal_back_cb)

        layout_reveal.addWidget(grp_reveal)

        # 2B. Shortcuts
        grp_shortcuts = QGroupBox("Keyboard Shortcuts", tab_reveal)
        form_shortcuts = QFormLayout(grp_shortcuts)
        form_shortcuts.setContentsMargins(10, 10, 10, 8)
        form_shortcuts.setVerticalSpacing(6)
        form_shortcuts.setHorizontalSpacing(16)

        self.shortcut_roll_edit = QLineEdit(grp_shortcuts)
        self.shortcut_roll_edit.setFixedHeight(26)
        self.shortcut_roll_edit.setFixedWidth(180)
        form_shortcuts.addRow("Reveal Next Cloze:", self.shortcut_roll_edit)

        self.shortcut_reveal_all_edit = QLineEdit(grp_shortcuts)
        self.shortcut_reveal_all_edit.setFixedHeight(26)
        self.shortcut_reveal_all_edit.setFixedWidth(180)
        form_shortcuts.addRow("Reveal All Clozes:", self.shortcut_reveal_all_edit)

        self.shortcut_info_edit = QLineEdit(grp_shortcuts)
        self.shortcut_info_edit.setFixedHeight(26)
        self.shortcut_info_edit.setFixedWidth(180)
        form_shortcuts.addRow("Toggle Info:", self.shortcut_info_edit)

        self.shortcut_image_edit = QLineEdit(grp_shortcuts)
        self.shortcut_image_edit.setFixedHeight(26)
        self.shortcut_image_edit.setFixedWidth(180)
        form_shortcuts.addRow("Toggle Image:", self.shortcut_image_edit)

        layout_reveal.addWidget(grp_shortcuts)

        # 2C. Mouse Wheel Bindings
        grp_bindings = QGroupBox("Mouse Wheel Bindings", tab_reveal)
        vbox_bindings = QVBoxLayout(grp_bindings)
        vbox_bindings.setContentsMargins(10, 10, 10, 8)
        vbox_bindings.setSpacing(6)

        initial_bindings = self.config.get("input_bindings", {}).get("reveal", [{"type": "wheel", "value": "down"}])
        self.binding_widget = bindings.BindingListWidget(initial_bindings, parent=grp_bindings, theme_qss=_get_dialog_qss(is_night))
        vbox_bindings.addWidget(self.binding_widget)

        layout_reveal.addWidget(grp_bindings)
        layout_reveal.addStretch(1)

        self.tabs.addTab(tab_reveal, "Reveal Controls")

        # =============================================================
        # TAB 3: Compatibility
        # =============================================================
        tab_compat = QWidget(self.tabs)
        layout_compat = QVBoxLayout(tab_compat)
        layout_compat.setContentsMargins(10, 10, 10, 10)
        layout_compat.setSpacing(8)

        # 3A. Theme & Dark Mode
        grp_theme = QGroupBox("Theme & Dark Mode", tab_compat)
        vbox_theme = QVBoxLayout(grp_theme)
        vbox_theme.setContentsMargins(10, 8, 10, 8)
        vbox_theme.setSpacing(6)

        self.auto_theme_cb = QCheckBox("Auto-detect Anki Theme (Night / Light Mode)", grp_theme)
        vbox_theme.addWidget(self.auto_theme_cb)

        self.enable_dark_cb = QCheckBox("Enable Dark Mode Compatibility Overrides", grp_theme)
        vbox_theme.addWidget(self.enable_dark_cb)

        layout_compat.addWidget(grp_theme)

        # 3B. Custom Cloze Colors
        grp_colors = QGroupBox("Custom Cloze Colors", tab_compat)
        form_colors = QFormLayout(grp_colors)
        form_colors.setContentsMargins(10, 8, 10, 8)
        form_colors.setVerticalSpacing(6)

        # Revealed Color
        self.cloze_revealed_custom_cb = QCheckBox("Use custom revealed cloze color", grp_colors)
        form_colors.addRow(self.cloze_revealed_custom_cb)

        row_revealed = QHBoxLayout()
        self.cloze_revealed_color_edit = QLineEdit(grp_colors)
        self.cloze_revealed_pick_btn = QPushButton("Pick Color", grp_colors)
        self.cloze_revealed_pick_btn.clicked.connect(lambda: _pick_color_for_edit(self.cloze_revealed_color_edit, self))
        row_revealed.addWidget(self.cloze_revealed_color_edit)
        row_revealed.addWidget(self.cloze_revealed_pick_btn)
        form_colors.addRow("Revealed Color:", row_revealed)

        # Hidden Color
        self.cloze_hidden_custom_cb = QCheckBox("Use custom hidden cloze [...] color", grp_colors)
        form_colors.addRow(self.cloze_hidden_custom_cb)

        row_hidden = QHBoxLayout()
        self.cloze_hidden_color_edit = QLineEdit(grp_colors)
        self.cloze_hidden_pick_btn = QPushButton("Pick Color", grp_colors)
        self.cloze_hidden_pick_btn.clicked.connect(lambda: _pick_color_for_edit(self.cloze_hidden_color_edit, self))
        row_hidden.addWidget(self.cloze_hidden_color_edit)
        row_hidden.addWidget(self.cloze_hidden_pick_btn)
        form_colors.addRow("Hidden Color:", row_hidden)

        layout_compat.addWidget(grp_colors)
        layout_compat.addStretch(1)

        self.tabs.addTab(tab_compat, "Compatibility")

        # =============================================================
        # TAB 4: Sequential Context
        # Rule 7:
        # - no Sequential Reveal item in mode control
        # - use Enable Sequential Context on/off (or equivalent)
        # - show context options only when enabled
        # =============================================================
        tab_context = QWidget(self.tabs)
        layout_context = QVBoxLayout(tab_context)
        layout_context.setContentsMargins(10, 10, 10, 10)
        layout_context.setSpacing(8)

        self.enable_seq_context_cb = QCheckBox("Enable Sequential Context", tab_context)
        self.enable_seq_context_cb.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout_context.addWidget(self.enable_seq_context_cb)

        context_desc = QLabel(
            "Review ordered items with surrounding context using {{c1::}}, {{c2::}}, {{c3::}}... "
            "Past context is visible to orient you while future clozes stay concealed until their turn.",
            tab_context
        )
        context_desc.setWordWrap(True)
        layout_context.addWidget(context_desc)

        self.context_group = QGroupBox("Sequential Context Settings", tab_context)
        form_ctx = QFormLayout(self.context_group)
        form_ctx.setContentsMargins(10, 8, 10, 8)
        form_ctx.setVerticalSpacing(6)

        self.context_before_sb = QSpinBox(self.context_group)
        self.context_before_sb.setRange(0, 20)
        self.context_before_sb.setSuffix(" items")
        form_ctx.addRow("Context Before (Previous items):", self.context_before_sb)

        self.context_after_sb = QSpinBox(self.context_group)
        self.context_after_sb.setRange(0, 20)
        self.context_after_sb.setSuffix(" items")
        form_ctx.addRow("Context After (Subsequent items):", self.context_after_sb)

        self.context_mask_subsequent_cb = QCheckBox("Mask subsequent clozes beyond context window", self.context_group)
        form_ctx.addRow(self.context_mask_subsequent_cb)

        self.back_context_before_combo = QComboBox(self.context_group)
        self.back_context_before_combo.addItem("Show All", "all")
        self.back_context_before_combo.addItem("0 items (None)", 0)
        self.back_context_before_combo.addItem("1 item", 1)
        self.back_context_before_combo.addItem("2 items", 2)
        self.back_context_before_combo.addItem("3 items", 3)
        self.back_context_before_combo.addItem("4 items", 4)
        self.back_context_before_combo.addItem("5 items", 5)
        form_ctx.addRow("Back Context Before:", self.back_context_before_combo)

        self.back_context_after_combo = QComboBox(self.context_group)
        self.back_context_after_combo.addItem("Show All", "all")
        self.back_context_after_combo.addItem("0 items (None)", 0)
        self.back_context_after_combo.addItem("1 item", 1)
        self.back_context_after_combo.addItem("2 items", 2)
        self.back_context_after_combo.addItem("3 items", 3)
        self.back_context_after_combo.addItem("4 items", 4)
        self.back_context_after_combo.addItem("5 items", 5)
        form_ctx.addRow("Back Context After:", self.back_context_after_combo)

        layout_context.addWidget(self.context_group)
        layout_context.addStretch(1)

        # Show context options only when Enable Sequential Context is ON
        self.enable_seq_context_cb.toggled.connect(self.context_group.setVisible)

        self.tabs.addTab(tab_context, "Sequential Context")

        # =============================================================
        # BOTTOM BUTTONS
        # Required:
        # - Restore Defaults
        # - Save
        # - Close
        # - Restore Templates
        # - Help
        # =============================================================
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_defaults = QPushButton("Restore Defaults", self)
        self.btn_defaults.setFixedHeight(26)
        self.btn_defaults.clicked.connect(self.on_restore_defaults)
        btn_layout.addWidget(self.btn_defaults)

        self.btn_templates = QPushButton("Restore Templates", self)
        self.btn_templates.setFixedHeight(26)
        self.btn_templates.clicked.connect(self.on_restore_templates)
        btn_layout.addWidget(self.btn_templates)

        self.btn_help = QPushButton("Help", self)
        self.btn_help.setFixedHeight(26)
        self.btn_help.clicked.connect(lambda: show_help_dialog(self))
        btn_layout.addWidget(self.btn_help)

        btn_layout.addStretch(1)

        self.btn_save = QPushButton("Save", self)
        self.btn_save.setFixedHeight(26)
        self.btn_save.setDefault(True)
        self.btn_save.setStyleSheet("font-weight: bold;")
        self.btn_save.clicked.connect(self.on_save)
        btn_layout.addWidget(self.btn_save)

        self.btn_close = QPushButton("Close", self)
        self.btn_close.setFixedHeight(26)
        self.btn_close.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_close)

        root_layout.addLayout(btn_layout)

        # Populate controls from self.config
        self.populate_form(self.config)

        # Clear legacy small geometry keys once so they never keep compressing the dialog
        try:
            qs = QSettings("Anki", "SequentialClozeRevealer")
            qs.remove("settings_dialog_geometry")
        except Exception:
            pass

        # Only restore saved geometry if it exists and has a comfortable height >= 640
        restored = False
        try:
            qs = QSettings("Anki", "SequentialClozeRevealer")
            geom = qs.value("settings_dialog_geometry_v2")
            if geom:
                if self.restoreGeometry(geom):
                    if self.width() >= 520 and self.height() >= 640:
                        restored = True
                    else:
                        try:
                            qs.remove("settings_dialog_geometry_v2")
                        except Exception:
                            pass
                        restored = False
        except Exception:
            restored = False

        # On first open or if no valid comfortable saved geometry, force taller size
        if not restored:
            self.resize(580, 680)

    def sizeHint(self):
        try:
            from aqt.qt import QSize
            return QSize(580, 680)
        except Exception:
            try:
                from PyQt6.QtCore import QSize
                return QSize(580, 680)
            except Exception:
                try:
                    from PyQt5.QtCore import QSize
                    return QSize(580, 680)
                except Exception:
                    pass
        return super().sizeHint()

    def showEvent(self, event) -> None:
        try:
            super().showEvent(event)
        except Exception:
            pass
        if self.height() < 640:
            self.resize(max(self.width(), 580), 680)

    def _save_dialog_geometry(self) -> None:
        try:
            # Only persist geometry if it meets the comfortable size threshold
            if self.width() >= 520 and self.height() >= 640:
                qs = QSettings("Anki", "SequentialClozeRevealer")
                geom = self.saveGeometry()
                if geom is not None:
                    qs.setValue("settings_dialog_geometry_v2", geom)
        except Exception:
            pass

    def closeEvent(self, event) -> None:
        self._save_dialog_geometry()
        try:
            super().closeEvent(event)
        except Exception:
            pass

    def reject(self) -> None:
        self._save_dialog_geometry()
        try:
            super().reject()
        except Exception:
            pass

    def accept(self) -> None:
        self._save_dialog_geometry()
        try:
            super().accept()
        except Exception:
            pass

    def _populate_font_families(self) -> None:
        self.font_family_combo.clear()

        # 1. Query full system fonts available on the computer using QFontDatabase.families()
        families = []
        try:
            from aqt.qt import QFontDatabase
            ws_any = None
            if hasattr(QFontDatabase, "WritingSystem"):
                ws_any = getattr(QFontDatabase.WritingSystem, "Any", None)
            if ws_any is None:
                ws_any = getattr(QFontDatabase, "Any", None)

            # Query static QFontDatabase.families()
            if hasattr(QFontDatabase, "families"):
                try:
                    if ws_any is not None:
                        families.extend(QFontDatabase.families(ws_any))
                except Exception:
                    pass
                try:
                    families.extend(QFontDatabase.families())
                except Exception:
                    pass

            # Query instance QFontDatabase().families()
            try:
                db = QFontDatabase()
                if ws_any is not None:
                    families.extend(db.families(ws_any))
                families.extend(db.families())
            except Exception:
                pass

            # Iterate all writing systems to guarantee non-Latin and special fonts are included
            ws_cls = getattr(QFontDatabase, "WritingSystem", None)
            if ws_cls is not None:
                for k in dir(ws_cls):
                    if not k.startswith("_"):
                        try:
                            val = getattr(ws_cls, k)
                            if hasattr(QFontDatabase, "families"):
                                families.extend(QFontDatabase.families(val))
                            else:
                                families.extend(db.families(val))
                        except Exception:
                            pass
        except Exception:
            pass

        # 2. OS-level system font fallback / supplement
        try:
            import platform
            system_name = platform.system()
            if system_name == "Windows":
                try:
                    import winreg
                    for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                        try:
                            with winreg.OpenKey(root, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts") as key:
                                i = 0
                                while True:
                                    try:
                                        val_name, _, _ = winreg.EnumValue(key, i)
                                        i += 1
                                        c_name = val_name.split(" (")[0].strip()
                                        if c_name:
                                            families.append(c_name)
                                    except OSError:
                                        break
                        except Exception:
                            pass
                except Exception:
                    pass
            elif system_name == "Darwin":
                try:
                    import glob, os
                    for pattern in ["/System/Library/Fonts/*", "/Library/Fonts/*", os.path.expanduser("~/Library/Fonts/*")]:
                        for fpath in glob.glob(pattern):
                            base = os.path.splitext(os.path.basename(fpath))[0].strip()
                            if base:
                                families.append(base)
                except Exception:
                    pass
            else:
                try:
                    import subprocess
                    out = subprocess.check_output(["fc-list", ":", "family"], text=True, timeout=1)
                    for line in out.splitlines():
                        for part in line.split(","):
                            p_clean = part.strip()
                            if p_clean:
                                families.append(p_clean)
                except Exception:
                    pass
        except Exception:
            pass

        # 3. Comprehensive standard fallback if environment blocked queries
        if not families:
            families = [
                "Arial", "Calibri", "Cambria", "Cascadia Code", "Cascadia Mono",
                "Comic Sans MS", "Consolas", "Courier New", "Georgia", "Helvetica",
                "Segoe UI", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana",
                "Agency FB", "Aldhabi", "Algerian", "Andalus", "Bodoni MT", "Book Antiqua",
                "Bookman Old Style", "Bookshelf Symbol 7", "Bradley Hand ITC", "Britannic Bold",
                "Broadway", "Brush Script MT", "Century Gothic", "Garamond", "Impact", "Rockwell"
            ]

        # 4. Clean, normalize, and sort unique font family names
        seen = set()
        cleaned_families = []
        for f in families:
            name = str(f).strip()
            # Strip @ prefix (vertical text orientation variants)
            if name.startswith("@"):
                name = name[1:].strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                cleaned_families.append(name)
        cleaned_families.sort(key=lambda s: s.lower())

        # 5. Helper to create visual TrueType "TT" icon beside each font name
        def _get_font_item_icon():
            try:
                from aqt.qt import QPixmap, QPainter, QColor, QFont, QIcon, Qt
                pm = QPixmap(16, 16)
                pm.fill(QColor(0, 0, 0, 0))
                p = QPainter(pm)
                antialiasing = getattr(getattr(QPainter, "RenderHint", QPainter), "Antialiasing", None)
                if antialiasing is None:
                    antialiasing = getattr(QPainter, "Antialiasing", 1)
                p.setRenderHint(antialiasing)
                p.setPen(QColor(220, 38, 38))  # Red #dc2626 TrueType symbol
                f = QFont("Arial", 8)
                f.setBold(True)
                p.setFont(f)
                align_flag = getattr(getattr(Qt, "AlignmentFlag", Qt), "AlignCenter", None)
                if align_flag is None:
                    align_flag = getattr(Qt, "AlignCenter", 0x0084)
                p.drawText(pm.rect(), int(align_flag), "TT")
                p.end()
                return QIcon(pm)
            except Exception:
                return None

        icon = _get_font_item_icon()

        # Top option: "System Default"
        if icon:
            self.font_family_combo.addItem(icon, "System Default", "System Default")
        else:
            self.font_family_combo.addItem("System Default", "System Default")

        # Common fonts at the top:
        # Arial, Calibri, Georgia, Segoe UI, Times New Roman, Verdana
        common_fonts = ["Arial", "Calibri", "Georgia", "Segoe UI", "Times New Roman", "Verdana"]
        for cf in common_fonts:
            if icon:
                self.font_family_combo.addItem(icon, cf, cf)
            else:
                self.font_family_combo.addItem(cf, cf)

        # Visual separator between common fonts and full system list
        try:
            self.font_family_combo.insertSeparator(self.font_family_combo.count())
        except Exception:
            pass

        # Full system list (A-Z)
        try:
            from aqt.qt import QFont, Qt
            font_role = getattr(getattr(Qt, "ItemDataRole", Qt), "FontRole", None)
            if font_role is None:
                font_role = getattr(Qt, "FontRole", 6)
        except Exception:
            font_role = None

        for font_name in cleaned_families:
            if font_name not in common_fonts and font_name.lower() != "system default":
                if icon:
                    self.font_family_combo.addItem(icon, font_name, font_name)
                else:
                    self.font_family_combo.addItem(font_name, font_name)

                # Set item font for previewing typeface while keeping symbol font names readable
                if font_role is not None:
                    try:
                        lower_name = font_name.lower()
                        is_symbol = any(sym in lower_name for sym in ["wingding", "webding", "symbol", "marlett", "holomdl2", "segoe mdl2", "icons", "extra", "assets"])
                        if not is_symbol:
                            f = QFont(font_name)
                            f.setPointSize(10)
                            self.font_family_combo.setItemData(self.font_family_combo.count() - 1, f, font_role)
                    except Exception:
                        pass

    def _update_font_preview(self) -> None:
        if not hasattr(self, "font_preview_lbl") or not hasattr(self, "font_family_combo"):
            return
        font_name = self.font_family_combo.currentText().strip()
        if not font_name or font_name == "System Default":
            try:
                from aqt.qt import QFont
                self.font_preview_lbl.setFont(QFont())
            except Exception:
                pass
            self.font_preview_lbl.setText("Aa Bb Cc 123")
        else:
            try:
                from aqt.qt import QFont
                font = QFont(font_name)
                font.setPointSize(13)
                self.font_preview_lbl.setFont(font)
            except Exception:
                pass
            self.font_preview_lbl.setText("Aa Bb Cc 123")

    def _set_font_family_text(self, text: str) -> None:
        target = str(text or "").strip()
        if not target:
            target = "System Default"
        idx = self.font_family_combo.findText(target)
        if idx != -1:
            self.font_family_combo.setCurrentIndex(idx)
        else:
            if target.lower() != "system default":
                icon = None
                try:
                    icon = _get_font_item_icon()
                except Exception:
                    pass
                if icon:
                    self.font_family_combo.addItem(icon, target, target)
                else:
                    self.font_family_combo.addItem(target, target)
                self.font_family_combo.setCurrentIndex(self.font_family_combo.count() - 1)
            else:
                idx_def = self.font_family_combo.findText("System Default")
                if idx_def != -1:
                    self.font_family_combo.setCurrentIndex(idx_def)
                else:
                    idx_arial = self.font_family_combo.findText("Arial")
                    if idx_arial != -1:
                        self.font_family_combo.setCurrentIndex(idx_arial)
                    elif self.font_family_combo.count() > 0:
                        self.font_family_combo.setCurrentIndex(0)
        self._update_font_preview()

    def populate_form(self, cfg: dict) -> None:
        # Tab 1: General
        _set_combo_data(self.controls_pos_combo, cfg.get("controls_position", "top-right"))
        _set_combo_data(self.card_vert_combo, cfg.get("card_vertical_position", "top"))
        _set_combo_data(self.card_horiz_combo, cfg.get("card_horizontal_align", "center"))
        cur_font = str(cfg.get("font_family", "System Default")).strip()
        self._set_font_family_text(cur_font)
        self.font_size_sb.setValue(int(cfg.get("font_size", 20)))
        self.bold_cloze_text_cb.setChecked(bool(cfg.get("bold_cloze_text", False)))
        self.center_mode_cb.setChecked(bool(cfg.get("center_mode", True)))
        self.mitcent_mode_cb.setChecked(bool(cfg.get("mitcent_mode", False)))

        # Tab 2: Reveal Controls
        self.reveal_speed_sb.setValue(int(cfg.get("reveal_speed", 20)))
        self.enable_click_reveal_cb.setChecked(bool(cfg.get("enable_click_reveal", False)))
        self.show_info_cb.setChecked(bool(cfg.get("show_info_by_default", False)))
        self.auto_reveal_back_cb.setChecked(bool(cfg.get("auto_reveal_back", True)))
        self.shortcut_roll_edit.setText(str(cfg.get("shortcut_roll", "Space")))
        self.shortcut_reveal_all_edit.setText(str(cfg.get("shortcut_reveal_all", "Shift + Space")))
        self.shortcut_info_edit.setText(str(cfg.get("shortcut_info", "H")))
        self.shortcut_image_edit.setText(str(cfg.get("shortcut_image", "G")))
        if hasattr(self, "binding_widget") and hasattr(self.binding_widget, "set_bindings"):
            self.binding_widget.set_bindings(cfg.get("input_bindings", {}).get("reveal", [{"type": "wheel", "value": "down"}]))

        # Tab 3: Compatibility
        self.auto_theme_cb.setChecked(bool(cfg.get("auto_theme_mode", True)))
        self.enable_dark_cb.setChecked(bool(cfg.get("enable_dark_compatibility", True)))
        self.cloze_revealed_custom_cb.setChecked(bool(cfg.get("cloze_revealed_custom", False)))
        self.cloze_revealed_color_edit.setText(str(cfg.get("cloze_revealed_color", "#c00000")))
        self.cloze_hidden_custom_cb.setChecked(bool(cfg.get("cloze_hidden_custom", False)))
        self.cloze_hidden_color_edit.setText(str(cfg.get("cloze_hidden_color", "#0284c7")))

        # Tab 4: Sequential Context
        is_context = (cfg.get("review_mode") == "sequential_context")
        self.enable_seq_context_cb.setChecked(is_context)
        self.context_group.setVisible(is_context)
        self.context_before_sb.setValue(int(cfg.get("context_before", 1)))
        self.context_after_sb.setValue(int(cfg.get("context_after", 0)))
        self.context_mask_subsequent_cb.setChecked(bool(cfg.get("context_mask_subsequent", True)))
        _set_combo_data(self.back_context_before_combo, cfg.get("back_context_before", "all"))
        _set_combo_data(self.back_context_after_combo, cfg.get("back_context_after", "all"))

    def collect_config(self) -> dict:
        cfg = copy.deepcopy(self.config)
        # Tab 1: General
        cd = self.controls_pos_combo.currentData()
        cfg["controls_position"] = cd if cd is not None else (self.controls_pos_combo.currentText() or "top-right")
        vd = self.card_vert_combo.currentData()
        cfg["card_vertical_position"] = vd if vd is not None else (self.card_vert_combo.currentText() or "top")
        hd = self.card_horiz_combo.currentData()
        cfg["card_horizontal_align"] = hd if hd is not None else (self.card_horiz_combo.currentText() or "center")
        cfg["font_family"] = self.font_family_combo.currentText().strip() or "System Default"
        cfg["font_size"] = int(self.font_size_sb.value())
        cfg["bold_cloze_text"] = bool(self.bold_cloze_text_cb.isChecked())
        cfg["center_mode"] = bool(self.center_mode_cb.isChecked())
        cfg["mitcent_mode"] = bool(self.mitcent_mode_cb.isChecked())

        # Tab 2: Reveal Controls
        cfg["reveal_speed"] = int(self.reveal_speed_sb.value())
        cfg["enable_click_reveal"] = bool(self.enable_click_reveal_cb.isChecked())
        cfg["show_info_by_default"] = bool(self.show_info_cb.isChecked())
        cfg["auto_reveal_back"] = bool(self.auto_reveal_back_cb.isChecked())
        cfg["shortcut_roll"] = self.shortcut_roll_edit.text().strip() or "Space"
        cfg["shortcut_reveal_all"] = self.shortcut_reveal_all_edit.text().strip() or "Shift + Space"
        cfg["shortcut_info"] = self.shortcut_info_edit.text().strip() or "H"
        cfg["shortcut_image"] = self.shortcut_image_edit.text().strip() or "G"
        if hasattr(self, "binding_widget") and hasattr(self.binding_widget, "bindings"):
            cfg["input_bindings"] = {"reveal": self.binding_widget.bindings()}

        # Tab 3: Compatibility
        cfg["auto_theme_mode"] = bool(self.auto_theme_cb.isChecked())
        cfg["enable_dark_compatibility"] = bool(self.enable_dark_cb.isChecked())
        cfg["cloze_revealed_custom"] = bool(self.cloze_revealed_custom_cb.isChecked())
        cfg["cloze_revealed_color"] = self.cloze_revealed_color_edit.text().strip() or "#c00000"
        cfg["cloze_hidden_custom"] = bool(self.cloze_hidden_custom_cb.isChecked())
        cfg["cloze_hidden_color"] = self.cloze_hidden_color_edit.text().strip() or "#0284c7"

        # Tab 4: Sequential Context
        if self.enable_seq_context_cb.isChecked():
            cfg["review_mode"] = "sequential_context"
        else:
            cfg["review_mode"] = "sequential_reveal"

        cfg["context_before"] = int(self.context_before_sb.value())
        cfg["context_after"] = int(self.context_after_sb.value())
        cfg["context_mask_subsequent"] = bool(self.context_mask_subsequent_cb.isChecked())

        bb = self.back_context_before_combo.currentData()
        cfg["back_context_before"] = bb if bb is not None else self.back_context_before_combo.currentText()
        ba = self.back_context_after_combo.currentData()
        cfg["back_context_after"] = ba if ba is not None else self.back_context_after_combo.currentText()

        return cfg

    def on_restore_defaults(self) -> None:
        try:
            defaults = get_default_config()
            self.populate_form(defaults)
            if aqt and hasattr(aqt, "utils") and hasattr(aqt.utils, "tooltip"):
                aqt.utils.tooltip("Restored defaults. Click Save to apply.", parent=self)
            elif showInfo:
                showInfo("Restored defaults in dialog. Click Save to apply.", parent=self)
        except Exception:
            pass

    def on_restore_templates(self) -> None:
        try:
            from . import note_type
            note_type.setup_note_type(force_update_templates=True)
            if aqt and hasattr(aqt, "utils") and hasattr(aqt.utils, "showInfo"):
                aqt.utils.showInfo("Card templates for 'Sequential Cloze v1' have been restored to defaults.", parent=self)
            elif showInfo:
                showInfo("Card templates for 'Sequential Cloze v1' have been restored to defaults.", parent=self)
        except Exception as err:
            if aqt and hasattr(aqt, "utils") and hasattr(aqt.utils, "showInfo"):
                aqt.utils.showInfo(f"Error restoring templates: {err}", parent=self)

    def on_save(self) -> None:
        try:
            new_cfg = self.collect_config()
            save_addon_config(new_cfg)
            try:
                from . import note_type
                note_type.setup_note_type(force_update_templates=False)
            except Exception:
                pass
            apply_config_to_reviewer()
            self.accept()
        except Exception as err:
            import traceback
            traceback.print_exc()
            if aqt and hasattr(aqt, "utils") and hasattr(aqt.utils, "showInfo"):
                aqt.utils.showInfo(f"Error saving preferences: {err}", parent=self)


def open_settings(*args, **kwargs):
    global _settings_dialog
    if _settings_dialog is not None and _settings_dialog.isVisible():
        _settings_dialog.raise_()
        _settings_dialog.activateWindow()
        return
    _settings_dialog = SettingsDialog(mw)
    if hasattr(_settings_dialog, "exec"):
        _settings_dialog.exec()
    else:
        _settings_dialog.exec_()
    _settings_dialog = None


def show_settings_dialog(*args, **kwargs) -> None:
    open_settings(*args, **kwargs)


def show_help_dialog(parent=None) -> None:
    global _help_dialog_instance
    target_parent = parent or mw

    if _help_dialog_instance is not None:
        try:
            if _help_dialog_instance.isVisible():
                _help_dialog_instance.raise_()
                _help_dialog_instance.activateWindow()
                return
        except Exception:
            _help_dialog_instance = None

    try:
        help_dlg = QDialog(target_parent)
        _help_dialog_instance = help_dlg
        help_dlg.setWindowTitle("Sequential Cloze — Help & Guide")
        help_dlg.setMinimumWidth(480)

        is_night = _is_night_mode()
        help_dlg.setStyleSheet(_get_dialog_qss(is_night))

        root_layout = QVBoxLayout(help_dlg)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(16)

        help_head_color = "#f1f5f9" if is_night else "#0f172a"
        help_body_color = "#cbd5e1" if is_night else "#334155"

        help_content = f"""
            <div style='font-size: 12px; line-height: 1.6; color: {help_body_color};'>
                <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Review Modes</p>
                <p style='margin: 0 0 3px 0;'>• <b>Sequential Reveal:</b> Reveal hidden parts one by one on the same card.</p>
                <p style='margin: 0 0 14px 0;'>• <b>Sequential Context:</b> Review ordered items with nearby context using {{{{c1::}}}}, {{{{c2::}}}}, {{{{c3::}}}}...</p>

                <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>How to review</p>
                <p style='margin: 0 0 3px 0;'>• Press <b>Space</b> or <b>Enter</b> to reveal the next cloze</p>
                <p style='margin: 0 0 3px 0;'>• Click <b>[...]</b> to reveal or hide that cloze</p>
                <p style='margin: 0 0 3px 0;'>• Press <b>Shift + Space</b> to reveal all clozes at once</p>
                <p style='margin: 0 0 3px 0;'>• Mouse wheel down can also reveal the next cloze</p>
                <p style='margin: 0 0 14px 0;'>• When all clozes are revealed, press <b>Space</b> to flip the card</p>

                <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Sequential Context options</p>
                <p style='margin: 0 0 3px 0;'>• <b>Context Before:</b> previous items shown on the front</p>
                <p style='margin: 0 0 3px 0;'>• <b>Context After:</b> next items shown on the front</p>
                <p style='margin: 0 0 3px 0;'>• <b>Back Context Before / After:</b> how much context to show on the back</p>
                <p style='margin: 0 0 14px 0;'>• <b>Mask Subsequent Items:</b> hide future items outside the context window</p>

                <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Shortcuts</p>
                <p style='margin: 0 0 3px 0;'>• <b>G</b> → toggle Image</p>
                <p style='margin: 0 0 3px 0;'>• <b>H</b> → toggle Info</p>
                <p style='margin: 0 0 14px 0;'>• You can change shortcuts and mouse bindings in <b>Settings → Reveal Controls</b></p>

                <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Optional fields</p>
                <p style='margin: 0 0 3px 0;'>• <b>Visible Image</b> → always shown on the card</p>
                <p style='margin: 0 0 3px 0;'>• <b>Image</b> → hidden until you press G (or the Image button)</p>
                <p style='margin: 0 0 3px 0;'>• <b>Info</b> → hidden until you press H (or the Info button)</p>
                <p style='margin: 0 0 3px 0;'>• <b>Front Audio / Back Audio</b> → play buttons in the control bar</p>
                <p style='margin: 0 0 14px 0;'>• <b>Explanation</b> → shown on the back of the card</p>

                <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Settings</p>
                <p style='margin: 0 0 3px 0;'>• <b>General:</b> layout, font family, font size, bold cloze text</p>
                <p style='margin: 0 0 3px 0;'>• <b>Reveal Controls:</b> reveal speed, click-to-reveal, shortcuts</p>
                <p style='margin: 0 0 3px 0;'>• <b>Compatibility:</b> optional custom cloze colors</p>
                <p style='margin: 0 0 4px 0;'>• <b>Sequential Context:</b> enable mode and context options</p>
            </div>
        """

        help_lbl = QLabel(help_content)
        help_lbl.setWordWrap(True)
        root_layout.addWidget(help_lbl)

        # Help Action Buttons: Report an Issue (left), v1.0.4 (center), and Close (right)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        issue_btn = QPushButton("Report an Issue")
        issue_btn.setFixedHeight(24)
        issue_btn.clicked.connect(lambda: webbrowser.open("https://github.com/Doummar/Sequential_Cloze_Revealer/issues"))
        btn_layout.addWidget(issue_btn)

        btn_layout.addStretch()

        version_lbl = QLabel("v1.0.4")
        version_lbl.setStyleSheet(f"color: {'#8b919e' if is_night else '#6b7280'}; font-size: 12px;")
        btn_layout.addWidget(version_lbl)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(24)
        close_btn.setObjectName("primary_save_btn")
        close_btn.clicked.connect(help_dlg.accept)
        btn_layout.addWidget(close_btn)

        root_layout.addLayout(btn_layout)
        help_dlg.setLayout(root_layout)

        def on_help_finished(*_):
            global _help_dialog_instance
            _help_dialog_instance = None

        try:
            help_dlg.finished.connect(on_help_finished)
        except Exception:
            pass

        if hasattr(help_dlg, "exec"):
            help_dlg.exec()
        else:
            help_dlg.exec_()
    except Exception as err:
        import traceback
        traceback.print_exc()
    finally:
        _help_dialog_instance = None

