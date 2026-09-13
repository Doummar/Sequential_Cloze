# Handles Reviewer settings GUI dialogs and overrides for Sequential Cloze Revealer
# Styled after native Anki dark/light preferences dialogs.

import os
import json
import webbrowser
try:
    from aqt import mw
    from aqt.utils import showInfo, qconnect
    from aqt.qt import *
except ImportError:
    mw = None

try:
    from PyQt6.QtGui import QFont, QColor
except ImportError:
    try:
        from PyQt5.QtGui import QFont, QColor
    except ImportError:
        pass

from . import bindings


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
    return """
        QDialog {
            font-size: 12px;
        }
        QGroupBox {
            margin-top: 12px;
            padding: 12px 10px 10px 10px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 4px;
        }
        QLabel {
            font-weight: normal;
        }
        QComboBox, QSpinBox, QLineEdit {
            min-height: 24px;
            padding: 2px 6px;
        }
        QPushButton {
            min-height: 24px;
            padding: 2px 14px;
        }
    """


def setup_reviewer() -> None:
    # Ensure config is initialized, safely merged with defaults on update/startup, and cached
    get_addon_config()


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


_CONFIG_CACHE = None


def get_default_config() -> dict:
    """Returns author default settings from config.json with a reliable fallback."""
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    cfg_path = os.path.join(addon_dir, "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return json.loads(json.dumps(data))
        except Exception:
            pass

    return {
        "controls_position": "top-right",
        "card_vertical_position": "center",
        "card_horizontal_align": "center",
        "font_family": "System Default",
        "font_size": 18,
        "center_mode": True,
        "mitcent_mode": True,
        "reveal_speed": 120,
        "enable_click_reveal": True,
        "show_info_by_default": False,
        "enable_dark_compatibility": True,
        "auto_reveal_back": True,
        "cloze_revealed_custom": False,
        "cloze_revealed_color": "#c00000",
        "cloze_hidden_custom": False,
        "cloze_hidden_color": "#0284c7",
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


def get_addon_config() -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    default_cfg = get_default_config()
    pkg = get_addon_pkg()

    user_cfg = None
    if mw and hasattr(mw, "addonManager") and mw.addonManager:
        candidates = [pkg, "sequential_cloze_revealer", __name__.split(".")[0]]
        for k in candidates:
            if not k:
                continue
            try:
                c = mw.addonManager.getConfig(k)
                if c and isinstance(c, dict):
                    user_cfg = c
                    break
            except Exception:
                pass

    if user_cfg is None:
        # First install scenario: use defaults
        merged_cfg, _ = merge_configs({}, default_cfg)
        bindings.migrate_legacy_config(merged_cfg)
        if mw and hasattr(mw, "addonManager") and mw.addonManager:
            try:
                mw.addonManager.writeConfig(pkg, merged_cfg)
            except Exception:
                pass
        _CONFIG_CACHE = merged_cfg
        return _CONFIG_CACHE

    # Update or existing install: preserve user config and merge defaults for missing keys only
    merged_cfg, was_modified = merge_configs(user_cfg, default_cfg)
    bindings.migrate_legacy_config(merged_cfg)

    # Save merged config back only when new keys were added during the update
    if was_modified and mw and hasattr(mw, "addonManager") and mw.addonManager:
        try:
            mw.addonManager.writeConfig(pkg, merged_cfg)
        except Exception:
            pass

    _CONFIG_CACHE = merged_cfg
    return _CONFIG_CACHE


def show_settings_dialog() -> None:
    if not mw:
        return

    pkg = get_addon_pkg()
    config = get_addon_config()
    bindings.migrate_legacy_config(config)

    is_night = _is_night_mode()

    dialog = QDialog(mw)
    dialog.setWindowTitle("Sequential Cloze — Preferences")
    dialog.setMinimumWidth(540)
    dialog.setStyleSheet(_get_dialog_qss(is_night))

    root_layout = QVBoxLayout(dialog)
    root_layout.setContentsMargins(18, 16, 18, 16)
    root_layout.setSpacing(12)

    # 2-Tab Structure: General | Reveal Controls
    tabs = QTabWidget()
    tabs.setUsesScrollButtons(False)
    try:
        if hasattr(tabs, "tabBar") and tabs.tabBar():
            tabs.tabBar().setFixedHeight(22)
    except Exception:
        pass

    align_left = getattr(getattr(Qt, "AlignmentFlag", Qt), "AlignLeft", getattr(Qt, "AlignLeft", None))
    align_vcenter = getattr(getattr(Qt, "AlignmentFlag", Qt), "AlignVCenter", getattr(Qt, "AlignVCenter", None))

    def create_tab_page() -> tuple:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(6, 10, 6, 6)
        page_layout.setSpacing(12)
        return page, page_layout

    # Helper for form layout with uniform, neatly aligned label and control columns
    def create_form_layout() -> QFormLayout:
        form = QFormLayout()
        if align_left is not None and align_vcenter is not None:
            try:
                form.setLabelAlignment(align_left | align_vcenter)
            except Exception:
                pass
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(8)
        form.setContentsMargins(12, 8, 12, 10)
        return form

    def add_form_row(form: QFormLayout, text: str, widget_or_layout, label_width: int = 175) -> QLabel:
        lbl = QLabel(text)
        lbl.setFixedWidth(label_width)
        if align_left is not None and align_vcenter is not None:
            try:
                lbl.setAlignment(align_left | align_vcenter)
            except Exception:
                pass
        form.addRow(lbl, widget_or_layout)
        return lbl

    # =========================================================================
    # TAB 1: GENERAL
    # =========================================================================
    general_page, general_layout = create_tab_page()

    # --- Group 1: Appearance & Positioning ---
    layout_group = QGroupBox("Appearance")
    gen_form1 = create_form_layout()

    # 1. Vertical Position
    vpos_cb = QComboBox()
    vpos_cb.setFixedHeight(26)
    vpos_cb.addItem("Center (Default)", "center")
    vpos_cb.addItem("Top", "top")
    vpos_cb.addItem("Bottom", "bottom")
    cur_vpos = config.get("card_vertical_position", "center")
    vpos_map = {"center": 0, "top": 1, "bottom": 2}
    vpos_cb.setCurrentIndex(vpos_map.get(cur_vpos, vpos_cb.findData(cur_vpos) if vpos_cb.findData(cur_vpos) != -1 else 0))
    add_form_row(gen_form1, "Vertical Position:", vpos_cb)

    # 2. Horizontal Alignment
    halign_cb = QComboBox()
    halign_cb.setFixedHeight(26)
    halign_cb.addItem("Center (Default)", "center")
    halign_cb.addItem("Left", "left")
    halign_cb.addItem("Right", "right")
    cur_halign = config.get("card_horizontal_align", "center")
    halign_map = {"center": 0, "left": 1, "right": 2}
    halign_cb.setCurrentIndex(halign_map.get(cur_halign, halign_cb.findData(cur_halign) if halign_cb.findData(cur_halign) != -1 else 0))
    add_form_row(gen_form1, "Horizontal Alignment:", halign_cb)

    # 3. Controls Position
    ctrl_pos_cb = QComboBox()
    ctrl_pos_cb.setFixedHeight(26)
    ctrl_pos_cb.addItem("Top Right (Default)", "top-right")
    ctrl_pos_cb.addItem("Top Left", "top-left")
    ctrl_pos_cb.addItem("Bottom Right", "bottom-right")
    ctrl_pos_cb.addItem("Bottom Left", "bottom-left")
    cur_ctrl = config.get("controls_position", "top-right")
    ctrl_map = {"top-right": 0, "top-left": 1, "bottom-right": 2, "bottom-left": 3}
    ctrl_pos_cb.setCurrentIndex(ctrl_map.get(cur_ctrl, ctrl_pos_cb.findData(cur_ctrl) if ctrl_pos_cb.findData(cur_ctrl) != -1 else 0))
    add_form_row(gen_form1, "Controls Position:", ctrl_pos_cb)

    layout_group.setLayout(gen_form1)
    general_layout.addWidget(layout_group)

    # --- Group 2: Typography ---
    typo_group = QGroupBox("Typography")
    gen_form2 = create_form_layout()

    # 4. Font family
    try:
        from aqt.qt import QFontComboBox, QFont
        font_cb = QFontComboBox()
        font_cb.setFixedHeight(26)
        if hasattr(QFontComboBox, "FontFilter") and hasattr(QFontComboBox.FontFilter, "AllFonts"):
            font_cb.setFontFilters(QFontComboBox.FontFilter.AllFonts)
        elif hasattr(QFontComboBox, "AllFonts"):
            font_cb.setFontFilters(QFontComboBox.AllFonts)
        cur_font = config.get("font_family", "System Default")
        if cur_font and cur_font != "System Default":
            font_cb.setCurrentFont(QFont(cur_font))
    except Exception:
        font_cb = QComboBox()
        font_cb.setFixedHeight(26)
        try:
            from aqt.qt import QFontDatabase
            if hasattr(QFontDatabase, "families"):
                families = sorted(QFontDatabase.families())
            else:
                db = QFontDatabase()
                families = sorted(db.families())
        except Exception:
            families = []
        if not families:
            families = [
                "System Default", "Arial", "Calibri", "Cambria", "Cascadia Code",
                "Comic Sans MS", "Consolas", "Courier New", "Georgia", "Segoe UI",
                "Times New Roman", "Trebuchet MS", "Verdana"
            ]
        for font_name in families:
            font_cb.addItem(font_name, font_name)
        cur_font = config.get("font_family", "System Default")
        idx_font = font_cb.findText(cur_font)
        if idx_font != -1:
            font_cb.setCurrentIndex(idx_font)
    add_form_row(gen_form2, "Font family:", font_cb)

    # 5. Font size (px)
    font_size_sb = QSpinBox()
    font_size_sb.setFixedHeight(26)
    font_size_sb.setRange(12, 32)
    font_size_sb.setValue(int(config.get("font_size", 18)))
    font_size_sb.setSuffix(" px")
    add_form_row(gen_form2, "Font size (px):", font_size_sb)

    typo_group.setLayout(gen_form2)
    general_layout.addWidget(typo_group)

    # --- Group 3: Review Behavior ---
    behavior_group = QGroupBox("Review Behavior")
    gen_form3 = create_form_layout()

    # 6. Show Info by Default
    show_info_cb = QComboBox()
    show_info_cb.setFixedHeight(26)
    show_info_cb.addItem("Disabled (Default)", False)
    show_info_cb.addItem("Enabled", True)
    cur_show_info = bool(config.get("show_info_by_default", False))
    show_info_cb.setCurrentIndex(1 if cur_show_info else 0)
    add_form_row(gen_form3, "Show Info by Default:", show_info_cb)

    # 7. Auto-reveal Back Card
    auto_reveal_cb = QComboBox()
    auto_reveal_cb.setFixedHeight(26)
    auto_reveal_cb.addItem("Enabled (Default)", True)
    auto_reveal_cb.addItem("Disabled", False)
    cur_auto_reveal = bool(config.get("auto_reveal_back", True))
    auto_reveal_cb.setCurrentIndex(0 if cur_auto_reveal else 1)
    add_form_row(gen_form3, "Auto-reveal Back Card:", auto_reveal_cb)

    behavior_group.setLayout(gen_form3)
    general_layout.addWidget(behavior_group)

    general_layout.addStretch()
    tabs.addTab(general_page, "General")

    # =========================================================================
    # TAB 2: REVEAL CONTROLS
    # =========================================================================
    reveal_page, reveal_layout = create_tab_page()

    # --- Group 1: Cloze Reveal Triggers ---
    trigger_group = QGroupBox("Cloze Reveal Triggers")
    rev_form1 = create_form_layout()

    # 1. Enable Click to Reveal
    click_reveal_cb = QCheckBox("Reveal cloze on click")
    click_reveal_cb.setFixedHeight(26)
    click_reveal_cb.setChecked(bool(config.get("enable_click_reveal", True)))
    add_form_row(rev_form1, "Enable Click to Reveal:", click_reveal_cb)

    # 2. Cloze Reveal Transition (ms)
    speed_sb = QSpinBox()
    speed_sb.setFixedHeight(26)
    speed_sb.setRange(0, 1000)
    speed_sb.setSingleStep(10)
    speed_sb.setSuffix(" ms")
    speed_sb.setValue(int(config.get("reveal_speed", 120)))
    add_form_row(rev_form1, "Reveal Transition Speed:", speed_sb)

    trigger_group.setLayout(rev_form1)
    reveal_layout.addWidget(trigger_group)

    # --- Group 2: Shortcuts ---
    shortcuts_group = QGroupBox("Shortcuts")
    rev_form2 = create_form_layout()

    # 3. Roll Shortcut Hotkey
    roll_input = QLineEdit()
    roll_input.setFixedHeight(26)
    roll_input.setText(str(config.get("shortcut_roll", "Space")))
    roll_input.setPlaceholderText("Space")
    add_form_row(rev_form2, "Roll Shortcut Hotkey:", roll_input)

    # 4. Reveal All Shortcut Hotkey
    reveal_all_input = QLineEdit()
    reveal_all_input.setFixedHeight(26)
    reveal_all_input.setText(str(config.get("shortcut_reveal_all", "Shift + Space")))
    reveal_all_input.setPlaceholderText("Shift + Space")
    add_form_row(rev_form2, "Reveal All Shortcut Hotkey:", reveal_all_input)

    # 5. Info Shortcut Hotkey
    info_input = QLineEdit()
    info_input.setFixedHeight(26)
    info_input.setText(str(config.get("shortcut_info", "H")))
    info_input.setPlaceholderText("H")
    add_form_row(rev_form2, "Info Shortcut Hotkey:", info_input)

    # 6. Image Shortcut Hotkey
    image_input = QLineEdit()
    image_input.setFixedHeight(26)
    image_input.setText(str(config.get("shortcut_image", "G")))
    image_input.setPlaceholderText("G")
    add_form_row(rev_form2, "Image Shortcut Hotkey:", image_input)

    shortcuts_group.setLayout(rev_form2)
    reveal_layout.addWidget(shortcuts_group)

    # Ensure controls expand nicely to match form columns
    expanding = getattr(getattr(QSizePolicy, "Policy", QSizePolicy), "Expanding", getattr(QSizePolicy, "Expanding", None))
    fixed = getattr(getattr(QSizePolicy, "Policy", QSizePolicy), "Fixed", getattr(QSizePolicy, "Fixed", None))
    if expanding is not None and fixed is not None:
        for w in (vpos_cb, halign_cb, ctrl_pos_cb, font_cb, font_size_sb, show_info_cb, auto_reveal_cb, speed_sb, roll_input, reveal_all_input, info_input, image_input):
            try:
                w.setSizePolicy(expanding, fixed)
            except Exception:
                pass

    # --- Group 3: Reveal Bindings (Mouse & Keys) ---
    wheel_group = QGroupBox("Reveal Bindings (Mouse & Keys)")
    wheel_layout = QVBoxLayout()
    wheel_layout.setContentsMargins(10, 10, 10, 10)
    wheel_layout.setSpacing(6)

    reveal_bindings = bindings.get_bindings(config, "reveal")
    binding_list_widget = bindings.BindingListWidget(reveal_bindings, parent=dialog, theme_qss=_get_dialog_qss(is_night))
    wheel_layout.addWidget(binding_list_widget)

    wheel_group.setLayout(wheel_layout)
    reveal_layout.addWidget(wheel_group)

    reveal_layout.addStretch()
    tabs.addTab(reveal_page, "Reveal Controls")

    # =========================================================================
    # TAB 3: COMPATIBILITY (Color Customization)
    # =========================================================================
    compat_page, compat_layout = create_tab_page()

    color_group = QGroupBox("Color Customization")
    compat_form = create_form_layout()

    # 1. Custom Cloze Word Color (Revealed)
    custom_revealed_cb = QCheckBox()
    custom_revealed_cb.setFixedHeight(26)
    custom_revealed_cb.setChecked(bool(config.get("cloze_revealed_custom", False)))
    add_form_row(compat_form, "Custom Cloze Word Color (Revealed):", custom_revealed_cb, label_width=245)

    # 2. Revealed Word Color (Hex)
    rev_color_layout = QHBoxLayout()
    rev_color_layout.setSpacing(6)
    revealed_color_input = QLineEdit()
    revealed_color_input.setFixedHeight(26)
    revealed_color_input.setText(str(config.get("cloze_revealed_color", "#c00000")))
    revealed_color_btn = QPushButton()
    revealed_color_btn.setFixedSize(26, 26)
    revealed_color_btn.setCursor(getattr(getattr(Qt, "CursorShape", Qt), "PointingHandCursor", getattr(Qt, "PointingHandCursor", None)))

    def update_rev_color_btn():
        c = revealed_color_input.text().strip() or "#c00000"
        revealed_color_btn.setStyleSheet(f"background-color: {c}; border: 1px solid #555; border-radius: 4px;")
    update_rev_color_btn()
    revealed_color_input.textChanged.connect(lambda: update_rev_color_btn())

    def pick_revealed_color():
        try:
            from aqt.qt import QColorDialog, QColor
            cur = QColor(revealed_color_input.text().strip())
            col = QColorDialog.getColor(cur, dialog, "Select Revealed Word Color")
            if col.isValid():
                revealed_color_input.setText(col.name())
                update_rev_color_btn()
        except Exception:
            pass
    revealed_color_btn.clicked.connect(pick_revealed_color)
    rev_color_layout.addWidget(revealed_color_input)
    rev_color_layout.addWidget(revealed_color_btn)
    add_form_row(compat_form, "Revealed Word Color (Hex):", rev_color_layout, label_width=245)

    # 3. Custom Cloze Bracket Color (Hidden)
    custom_hidden_cb = QCheckBox()
    custom_hidden_cb.setFixedHeight(26)
    custom_hidden_cb.setChecked(bool(config.get("cloze_hidden_custom", False)))
    add_form_row(compat_form, "Custom Cloze Bracket Color (Hidden):", custom_hidden_cb, label_width=245)

    # 4. Hidden Bracket Color (Hex)
    hid_color_layout = QHBoxLayout()
    hid_color_layout.setSpacing(6)
    hidden_color_input = QLineEdit()
    hidden_color_input.setFixedHeight(26)
    hidden_color_input.setText(str(config.get("cloze_hidden_color", "#0284c7")))
    hidden_color_btn = QPushButton()
    hidden_color_btn.setFixedSize(26, 26)
    hidden_color_btn.setCursor(getattr(getattr(Qt, "CursorShape", Qt), "PointingHandCursor", getattr(Qt, "PointingHandCursor", None)))

    def update_hid_color_btn():
        c = hidden_color_input.text().strip() or "#0284c7"
        hidden_color_btn.setStyleSheet(f"background-color: {c}; border: 1px solid #555; border-radius: 4px;")
    update_hid_color_btn()
    hidden_color_input.textChanged.connect(lambda: update_hid_color_btn())

    def pick_hidden_color():
        try:
            from aqt.qt import QColorDialog, QColor
            cur = QColor(hidden_color_input.text().strip())
            col = QColorDialog.getColor(cur, dialog, "Select Hidden Bracket Color")
            if col.isValid():
                hidden_color_input.setText(col.name())
                update_hid_color_btn()
        except Exception:
            pass
    hidden_color_btn.clicked.connect(pick_hidden_color)
    hid_color_layout.addWidget(hidden_color_input)
    hid_color_layout.addWidget(hidden_color_btn)
    add_form_row(compat_form, "Hidden Bracket Color (Hex):", hid_color_layout, label_width=245)

    color_group.setLayout(compat_form)
    compat_layout.addWidget(color_group)
    compat_layout.addStretch()
    tabs.addTab(compat_page, "Compatibility")

    root_layout.addWidget(tabs)

    # =========================================================================
    # BOTTOM ACTION BUTTONS:
    # Order: Restore Defaults (Left) | Save | Close | Help (Right)
    # Native Anki button size (24px height)
    # =========================================================================
    bottom_layout = QHBoxLayout()
    bottom_layout.setSpacing(8)
    bottom_layout.setContentsMargins(0, 8, 0, 0)

    reset_btn = QPushButton("Restore Defaults")
    reset_btn.setFixedHeight(24)

    def on_reset():
        vpos_cb.setCurrentIndex(vpos_cb.findData("center"))
        halign_cb.setCurrentIndex(halign_cb.findData("center"))
        ctrl_pos_cb.setCurrentIndex(ctrl_pos_cb.findData("top-right"))
        if hasattr(font_cb, "setCurrentFont"):
            try:
                from aqt.qt import QFont
                font_cb.setCurrentFont(QFont("Segoe UI" if os.name == "nt" else "Arial"))
            except Exception:
                pass
        else:
            font_cb.setCurrentIndex(0)
        font_size_sb.setValue(18)
        show_info_cb.setCurrentIndex(0)
        auto_reveal_cb.setCurrentIndex(0)

        click_reveal_cb.setChecked(True)
        speed_sb.setValue(120)
        roll_input.setText("Space")
        reveal_all_input.setText("Shift + Space")
        info_input.setText("H")
        image_input.setText("G")
        binding_list_widget.set_bindings(bindings.DEFAULT_BINDINGS.get("reveal", [{"type": "wheel", "value": "down"}]))

        custom_revealed_cb.setChecked(False)
        revealed_color_input.setText("#c00000")
        custom_hidden_cb.setChecked(False)
        hidden_color_input.setText("#0284c7")
        update_rev_color_btn()
        update_hid_color_btn()

    reset_btn.clicked.connect(on_reset)
    bottom_layout.addWidget(reset_btn)

    bottom_layout.addStretch()

    save_btn = QPushButton("Save")
    save_btn.setFixedHeight(24)
    save_btn.setObjectName("primary_save_btn")
    save_btn.setDefault(True)

    def on_save():
        v_idx = vpos_cb.currentIndex()
        v_data = vpos_cb.itemData(v_idx) or vpos_cb.currentData()
        v_pos = v_data if v_data in ("center", "top", "bottom") else (["center", "top", "bottom"][v_idx] if 0 <= v_idx < 3 else "center")

        h_idx = halign_cb.currentIndex()
        h_data = halign_cb.itemData(h_idx) or halign_cb.currentData()
        h_pos = h_data if h_data in ("center", "left", "right") else (["center", "left", "right"][h_idx] if 0 <= h_idx < 3 else "center")

        c_idx = ctrl_pos_cb.currentIndex()
        c_data = ctrl_pos_cb.itemData(c_idx) or ctrl_pos_cb.currentData()
        c_pos = c_data if c_data in ("top-right", "top-left", "bottom-right", "bottom-left") else (["top-right", "top-left", "bottom-right", "bottom-left"][c_idx] if 0 <= c_idx < 4 else "top-right")

        config["card_vertical_position"] = v_pos
        config["card_horizontal_align"] = h_pos
        config["controls_position"] = c_pos

        if hasattr(font_cb, "currentFont"):
            try:
                config["font_family"] = font_cb.currentFont().family()
            except Exception:
                config["font_family"] = font_cb.currentText() or "System Default"
        else:
            config["font_family"] = font_cb.currentText() or "System Default"
        config["font_size"] = int(font_size_sb.value())

        # Update legacy mode flags for full compatibility
        config["center_mode"] = (h_pos == "center")
        config["mitcent_mode"] = (v_pos == "center" and h_pos == "center")

        config["show_info_by_default"] = (show_info_cb.currentIndex() == 1)
        config["auto_reveal_back"] = (auto_reveal_cb.currentIndex() == 0)

        config["enable_click_reveal"] = bool(click_reveal_cb.isChecked())
        config["reveal_speed"] = int(speed_sb.value())
        config["shortcut_roll"] = roll_input.text().strip() or "Space"
        config["shortcut_reveal_all"] = reveal_all_input.text().strip() or "Shift + Space"
        config["shortcut_info"] = info_input.text().strip() or "H"
        config["shortcut_image"] = image_input.text().strip() or "G"

        bindings.set_bindings(config, "reveal", binding_list_widget.bindings())

        config["cloze_revealed_custom"] = bool(custom_revealed_cb.isChecked())
        config["cloze_revealed_color"] = revealed_color_input.text().strip() or "#c00000"
        config["cloze_hidden_custom"] = bool(custom_hidden_cb.isChecked())
        config["cloze_hidden_color"] = hidden_color_input.text().strip() or "#0284c7"

        # Update in-memory session cache immediately
        global _CONFIG_CACHE
        _CONFIG_CACHE = json.loads(json.dumps(config))

        addon_dir = os.path.dirname(os.path.abspath(__file__))

        # Write to Anki addonManager (which persists to meta.json preserving user settings across add-on updates)
        if mw and hasattr(mw, "addonManager") and mw.addonManager:
            keys_to_write = {pkg, os.path.basename(addon_dir), "sequential_cloze_revealer", __name__.split(".")[0]}
            for k in keys_to_write:
                if not k:
                    continue
                try:
                    mw.addonManager.writeConfig(k, config)
                except Exception:
                    pass
                try:
                    if hasattr(mw.addonManager, "_configs") and isinstance(mw.addonManager._configs, dict):
                        mw.addonManager._configs[k] = json.loads(json.dumps(config))
                except Exception:
                    pass
        else:
            # Standalone fallback when running outside of Anki
            try:
                cfg_path = os.path.join(addon_dir, "config.json")
                with open(cfg_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
            except Exception:
                pass

        # 3. Ensure collection note type templates and CSS are up to date
        try:
            from . import note_type
            note_type.setup_note_type()
        except Exception:
            pass

        # 4. Live-update the reviewer webview if user is currently reviewing
        try:
            if mw and hasattr(mw, "reviewer") and mw.reviewer:
                from . import renderer
                cur_card = getattr(mw.reviewer, "card", None)
                if cur_card:
                    _, _, payload_config = renderer.get_payload_and_resources(cur_card)
                    if hasattr(mw.reviewer, "web") and mw.reviewer.web:
                        mw.reviewer.web.eval(
                            f"{payload_config}\n"
                            "if (typeof window.setupClozeInteractions === 'function') { window.setupClozeInteractions(); }"
                        )
                    if hasattr(mw, "state") and mw.state == "review":
                        cur_card.load()
                        mw.reviewer.show()
        except Exception:
            pass

        dialog.accept()

    save_btn.clicked.connect(on_save)
    bottom_layout.addWidget(save_btn)

    close_btn = QPushButton("Close")
    close_btn.setFixedHeight(24)
    close_btn.clicked.connect(dialog.reject)
    bottom_layout.addWidget(close_btn)

    help_btn = QPushButton("Help")
    help_btn.setFixedHeight(24)
    help_btn.clicked.connect(lambda: show_help_dialog(dialog))
    bottom_layout.addWidget(help_btn)

    root_layout.addLayout(bottom_layout)
    dialog.setLayout(root_layout)
    if hasattr(dialog, "exec"):
        dialog.exec()
    else:
        dialog.exec_()


def show_help_dialog(parent=None) -> None:
    target_parent = parent or mw
    help_dlg = QDialog(target_parent)
    help_dlg.setWindowTitle("Sequential Cloze Revealer — Help & Guide (v1.0.1)")
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
            <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>How to review</p>
            <p style='margin: 0 0 3px 0;'>• Press <b>Space</b> or <b>Enter</b> to reveal the next cloze</p>
            <p style='margin: 0 0 3px 0;'>• Click a <b>[...]</b> to reveal only that word</p>
            <p style='margin: 0 0 3px 0;'>• Press <b>Shift + Space</b> to reveal all clozes at once</p>
            <p style='margin: 0 0 3px 0;'>• Mouse wheel down can also reveal the next cloze</p>
            <p style='margin: 0 0 14px 0;'>• When all clozes are revealed, press <b>Space</b> to flip the card</p>

            <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Shortcuts</p>
            <p style='margin: 0 0 3px 0;'>• <b>G</b> → toggle Image</p>
            <p style='margin: 0 0 3px 0;'>• <b>H</b> → toggle Info</p>
            <p style='margin: 0 0 14px 0;'>• You can also add or change shortcuts and mouse bindings in <b>Settings → Reveal Controls</b></p>

            <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Optional fields</p>
            <p style='margin: 0 0 3px 0;'>• <b>Visible Image</b> → always shown on the card</p>
            <p style='margin: 0 0 3px 0;'>• <b>Image</b> → hidden until you press G (or the Image button)</p>
            <p style='margin: 0 0 3px 0;'>• <b>Info</b> → hidden until you press H (or the Info button)</p>
            <p style='margin: 0 0 3px 0;'>• <b>Front Audio / Back Audio</b> → play buttons appear in the control bar</p>
            <p style='margin: 0 0 14px 0;'>• <b>Explanation</b> → shown on the back of the card</p>

            <p style='margin: 0 0 4px 0; font-size: 13px; font-weight: bold; color: {help_head_color};'>Settings</p>
            <p style='margin: 0 0 4px 0;'>• You can change layout, fonts, controls position, and reveal options in the Settings window</p>
        </div>
    """

    help_lbl = QLabel(help_content)
    help_lbl.setWordWrap(True)
    root_layout.addWidget(help_lbl)

    # Help Action Buttons: Report an Issue (left), v1.0.1 (center), and Close (right)
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(10)

    issue_btn = QPushButton("Report an Issue")
    issue_btn.setFixedHeight(24)
    issue_btn.clicked.connect(lambda: webbrowser.open("https://github.com/Doummar/Sequential_Cloze_Revealer/issues"))
    btn_layout.addWidget(issue_btn)

    btn_layout.addStretch()

    version_lbl = QLabel("v1.0.1")
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

    if hasattr(help_dlg, "exec"):
        help_dlg.exec()
    else:
        help_dlg.exec_()

