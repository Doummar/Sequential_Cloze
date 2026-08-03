# Handles Reviewer settings GUI dialogs and overrides

import os
from aqt import mw
from aqt.utils import showInfo, qconnect
from aqt.qt import *

from . import bindings


# ---------------------------------------------------------------------------
# Theme detection
# ---------------------------------------------------------------------------

def _is_night_mode() -> bool:
    """Return True when Anki is running in dark / night mode."""
    try:
        from aqt.theme import theme_manager
        return theme_manager.night_mode
    except Exception:
        pass
    try:
        return bool(mw.pm.night_mode())
    except Exception:
        return False


_LIGHT = {
    "dialog_bg":      "#f7f7f7",
    "help_bg":        "#ffffff",
    "title":          "#000000",
    "label":          "#111111",
    "label_sub":      "#666666",
    "label_muted":    "#777777",
    "bullet":         "#444444",
    "section":        "#111111",
    "input_bg":       "#ffffff",
    "input_border":   "#adadad",
    "input_focus":    "#0078d7",
    "input_text":     "#111111",
    "sep":            "#d1d5db",
    "thick_sep":      "#1c1c1c",
    "btn_bg":         "#ffffff",
    "btn_border":     "#adadad",
    "btn_text":       "#333333",
    "btn_hover_bg":   "#eaf2f8",
    "btn_hover_bdr":  "#0078d7",
    "btn_hover_txt":  "#000000",
    "btn_press_bg":   "#daebf4",
    "btn_press_bdr":  "#005499",
}

_DARK = {
    "dialog_bg":      "#1e1e1e",
    "help_bg":        "#1e1e1e",
    "title":          "#f0f0f0",
    "label":          "#e0e0e0",
    "label_sub":      "#aaaaaa",
    "label_muted":    "#888888",
    "bullet":         "#bbbbbb",
    "section":        "#e8e8e8",
    "input_bg":       "#2a2a2a",
    "input_border":   "#4a4a4a",
    "input_focus":    "#4fa3e0",
    "input_text":     "#e0e0e0",
    "sep":            "#3a3a3a",
    "thick_sep":      "#555555",
    "btn_bg":         "#2d2d2d",
    "btn_border":     "#555555",
    "btn_text":       "#dddddd",
    "btn_hover_bg":   "#3a3a3a",
    "btn_hover_bdr":  "#4fa3e0",
    "btn_hover_txt":  "#ffffff",
    "btn_press_bg":   "#242424",
    "btn_press_bdr":  "#1a6aa8",
}


def _theme() -> dict:
    return _DARK if _is_night_mode() else _LIGHT


def _dialog_qss(t: dict) -> str:
    return f"""
        QDialog {{
            background-color: {t['dialog_bg']};
        }}
        QLabel {{
            color: {t['label']};
            font-size: 11px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QCheckBox {{
            font-size: 11px;
            color: {t['label']};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QLineEdit, QSpinBox {{
            background-color: {t['input_bg']};
            border: 1px solid {t['input_border']};
            border-radius: 3px;
            padding: 2px 4px;
            color: {t['input_text']};
            font-size: 11px;
            min-height: 18px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QLineEdit:focus, QSpinBox:focus {{
            border: 1px solid {t['input_focus']};
        }}
        QGroupBox {{
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 11px;
            font-weight: bold;
            color: {t['section']};
            border: 1px solid {t['sep']};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
        }}
        QListWidget {{
            background-color: {t['input_bg']};
            border: 1px solid {t['input_border']};
            border-radius: 3px;
            color: {t['input_text']};
            font-size: 11px;
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QTabWidget::pane {{
            border: 1px solid {t['sep']};
            border-radius: 6px;
            padding: 12px;
            top: -1px;
        }}
        QTabBar {{
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        QTabBar::tab {{
            background: transparent;
            color: {t['label_muted']};
            font-size: 11px;
            font-weight: bold;
            padding: 6px 10px;
            margin: 2px 2px 6px 0px;
            border-radius: 5px;
        }}
        QTabBar::tab:selected {{
            background: #0078d7;
            color: #ffffff;
        }}
        QTabBar::tab:hover:!selected {{
            background: {t['btn_hover_bg']};
            color: {t['label']};
        }}
    """


def _button_qss(t: dict) -> str:
    return f"""
    QPushButton {{
        background-color: {t['btn_bg']};
        border: 1px solid {t['btn_border']};
        border-radius: 4px;
        padding: 5px 12px;
        color: {t['btn_text']};
        font-family: 'Segoe UI', Arial;
        font-size: 11px;
    }}
    QPushButton:hover {{
        background-color: {t['btn_hover_bg']};
        border-color: {t['btn_hover_bdr']};
        color: {t['btn_hover_txt']};
    }}
    QPushButton:pressed {{
        background-color: {t['btn_press_bg']};
        border-color: {t['btn_press_bdr']};
    }}
    """


_PRIMARY_QSS = """
    QPushButton {
        background-color: #0078d7;
        border: 1px solid #005499;
        border-radius: 4px;
        padding: 5px 18px;
        color: #ffffff;
        font-family: 'Segoe UI', Arial;
        font-size: 11px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #1883db;
        border-color: #0078d7;
        color: #ffffff;
    }
    QPushButton:pressed {
        background-color: #004d8c;
        border-color: #003a6c;
        color: #ffffff;
    }
"""


# ---------------------------------------------------------------------------

def setup_reviewer() -> None:
    pass


def show_settings_dialog() -> None:
    config = mw.addonManager.getConfig(__name__) or {}
    bindings.migrate_legacy_config(config)
    t = _theme()
    button_qss     = _button_qss(t)
    primary_button_qss = _PRIMARY_QSS

    dialog = QDialog(mw)
    dialog.setWindowTitle("Sequential Cloze Revealer Settings")
    dialog.setMinimumWidth(460)
    dialog.setStyleSheet(_dialog_qss(t))

    layout = QVBoxLayout()
    layout.setContentsMargins(20, 15, 20, 15)
    layout.setSpacing(10)

    # ---- Header ----
    title_layout = QHBoxLayout()
    title_layout.setSpacing(6)

    title_text = QLabel("Sequential Cloze Revealer")
    title_font = QFont()
    title_font.setPointSize(12)
    title_font.setBold(True)
    title_text.setFont(title_font)
    title_text.setStyleSheet(f"color: {t['title']}; font-weight: bold; font-family: 'Segoe UI';")
    title_layout.addWidget(title_text)
    title_layout.addStretch()
    layout.addLayout(title_layout)

    # ---- Helper: build a tab page wrapping a QFormLayout ----
    def make_group(title: str) -> tuple:
        page = QWidget()
        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(4, 8, 4, 4)
        box_form = QFormLayout()
        box_form.setSpacing(6)
        page_layout.addLayout(box_form)
        page_layout.addStretch()
        page.setLayout(page_layout)
        tabs.addTab(page, title)
        return page, box_form

    tabs = QTabWidget()
    tabs.setUsesScrollButtons(False)
    tabs.tabBar().setExpanding(True)

    # ================= General =================
    general_box, general_form = make_group("General")

    center_mode_cb = QCheckBox()
    center_mode_cb.setChecked(config.get("center_mode", True))
    general_form.addRow("Enable Centered Mode:", center_mode_cb)

    mitcent_mode_cb = QCheckBox()
    mitcent_mode_cb.setChecked(config.get("mitcent_mode", True))
    general_form.addRow("Enable Mitcent Mode:", mitcent_mode_cb)

    show_info_cb = QCheckBox()
    show_info_cb.setChecked(config.get("show_info_by_default", False))
    general_form.addRow("Show Info by Default:", show_info_cb)

    auto_reveal_back_cb = QCheckBox()
    auto_reveal_back_cb.setChecked(config.get("auto_reveal_back", True))
    general_form.addRow("Auto-reveal Back Card:", auto_reveal_back_cb)

    # ================= Reveal Controls =================
    reveal_box, reveal_form = make_group("Reveal Controls")

    click_reveal_cb = QCheckBox()
    click_reveal_cb.setChecked(config.get("enable_click_reveal", True))
    reveal_form.addRow("Enable Click to Reveal:", click_reveal_cb)

    reveal_speed_sb = QSpinBox()
    reveal_speed_sb.setRange(0, 1000)
    reveal_speed_sb.setSingleStep(10)
    reveal_speed_sb.setSuffix(" ms")
    reveal_speed_sb.setValue(config.get("reveal_speed", 120))
    reveal_form.addRow("Cloze Reveal Transition:", reveal_speed_sb)

    shortcut_roll_le = QLineEdit()
    shortcut_roll_le.setText(config.get("shortcut_roll", "Space"))
    reveal_form.addRow("Roll Shortcut Hotkey:", shortcut_roll_le)

    shortcut_info_le = QLineEdit()
    shortcut_info_le.setText(config.get("shortcut_info", "I"))
    reveal_form.addRow("Info Shortcut Hotkey:", shortcut_info_le)

    # Generic input-binding list for the "Reveal" action — supports any mix
    # of keyboard keys, mouse buttons, and mouse-wheel directions, and
    # triggers the exact same reveal logic no matter which one fired it.
    reveal_bindings_widget = bindings.BindingListWidget(
        bindings.get_bindings(config, "reveal"), parent=dialog,
        theme_qss=_dialog_qss(t) + button_qss)
    reveal_bindings_widget.add_btn.setStyleSheet(button_qss)
    reveal_bindings_widget.remove_btn.setStyleSheet(button_qss)
    reveal_form.addRow("Reveal Bindings:", reveal_bindings_widget)

    # ================= Compatibility =================
    compat_box, compat_form = make_group("Compatibility")

    cl_rev_custom_cb = QCheckBox()
    cl_rev_custom_cb.setChecked(config.get("cloze_revealed_custom", False))
    compat_form.addRow("Custom Cloze Word Color (Revealed):", cl_rev_custom_cb)

    cl_rev_layout = QHBoxLayout()
    cl_rev_color_le = QLineEdit()
    cl_rev_color_le.setText(config.get("cloze_revealed_color", "#c00000"))
    cl_rev_color_le.setPlaceholderText("#c00000")
    cl_rev_btn = QPushButton()
    cl_rev_btn.setFixedSize(20, 20)
    cl_rev_btn.setToolTip("Pick a color")
    cl_rev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    cl_rev_btn.setStyleSheet(
        f"background-color: {config.get('cloze_revealed_color', '#c00000')};"
        " border: 1px solid #7a7a7a; border-radius: 3px;")

    def on_choose_rev_color():
        cur = QColor(cl_rev_color_le.text() or "#c00000")
        color = QColorDialog.getColor(cur, dialog, "Pick Ink Color")
        if color.isValid():
            cl_rev_color_le.setText(color.name())
            cl_rev_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #7a7a7a; border-radius: 3px;")

    cl_rev_btn.clicked.connect(on_choose_rev_color)
    cl_rev_color_le.textChanged.connect(lambda text: cl_rev_btn.setStyleSheet(
        f"background-color: {text or '#c00000'}; border: 1px solid #7a7a7a; border-radius: 3px;"))
    cl_rev_layout.addWidget(cl_rev_color_le)
    cl_rev_layout.addWidget(cl_rev_btn)
    compat_form.addRow("Revealed Word Color (Hex):", cl_rev_layout)

    cl_hid_custom_cb = QCheckBox()
    cl_hid_custom_cb.setChecked(config.get("cloze_hidden_custom", False))
    compat_form.addRow("Custom Cloze Bracket Color (Hidden):", cl_hid_custom_cb)

    cl_hid_layout = QHBoxLayout()
    cl_hid_color_le = QLineEdit()
    cl_hid_color_le.setText(config.get("cloze_hidden_color", "#0284c7"))
    cl_hid_color_le.setPlaceholderText("#0284c7")
    cl_hid_btn = QPushButton()
    cl_hid_btn.setFixedSize(20, 20)
    cl_hid_btn.setToolTip("Pick a color")
    cl_hid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    cl_hid_btn.setStyleSheet(
        f"background-color: {config.get('cloze_hidden_color', '#0284c7')};"
        " border: 1px solid #7a7a7a; border-radius: 3px;")

    def on_choose_hid_color():
        cur = QColor(cl_hid_color_le.text() or "#0284c7")
        color = QColorDialog.getColor(cur, dialog, "Pick Ink Color")
        if color.isValid():
            cl_hid_color_le.setText(color.name())
            cl_hid_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #7a7a7a; border-radius: 3px;")

    cl_hid_btn.clicked.connect(on_choose_hid_color)
    cl_hid_color_le.textChanged.connect(lambda text: cl_hid_btn.setStyleSheet(
        f"background-color: {text or '#0284c7'}; border: 1px solid #7a7a7a; border-radius: 3px;"))
    cl_hid_layout.addWidget(cl_hid_color_le)
    cl_hid_layout.addWidget(cl_hid_btn)
    compat_form.addRow("Hidden Bracket Color (Hex):", cl_hid_layout)

    # ---- Helper: separator line ----
    def make_sep(color: str, height: int = 1) -> QFrame:
        sep = QFrame()
        sep.setStyleSheet(
            f"background-color: {color}; border: none; margin-top: 4px; margin-bottom: 2px;")
        sep.setMinimumHeight(height)
        sep.setMaximumHeight(height)
        return sep

    # ================= Help =================
    help_page = QWidget()
    help_page_layout = QVBoxLayout()
    help_page_layout.setContentsMargins(4, 8, 4, 4)
    help_page_layout.setSpacing(8)
    help_page.setLayout(help_page_layout)
    tabs.addTab(help_page, "Help")

    # ---- Help guide dialog ----
    def on_help_guide():
        dialog.reject()
        help_dialog = QDialog(mw)
        help_dialog.setWindowTitle("Sequential Cloze Revealer — Guide")
        help_dialog.setMinimumWidth(440)
        help_dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {t['help_bg']};
            }}
            QLabel {{
                color: {t['label']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        h_layout = QVBoxLayout()
        h_layout.setContentsMargins(24, 20, 24, 20)
        h_layout.setSpacing(10)

        header_lbl = QLabel("Sequential Cloze Revealer")
        h_font = QFont()
        h_font.setPointSize(14)
        h_font.setBold(True)
        header_lbl.setFont(h_font)
        header_lbl.setStyleSheet(f"color: {t['title']}; font-weight: bold;")
        h_layout.addWidget(header_lbl)

        sub_lbl = QLabel(
            "Focus directly on your cards with clean, center-mode layout and custom clozes.")
        sub_lbl.setStyleSheet(f"color: {t['label_sub']}; font-size: 11px;")
        h_layout.addWidget(sub_lbl)

        h_layout.addWidget(make_sep(t['thick_sep'], 2))

        def section(text):
            lbl = QLabel(f"<b>{text}</b>")
            lbl.setStyleSheet(f"font-size: 12px; color: {t['section']}; margin-top: 8px;")
            return lbl

        def bullet(text):
            lbl = QLabel(text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(f"color: {t['bullet']}; font-size: 11px; margin-left: 5px;")
            return lbl

        h_layout.addWidget(section("What it does"))
        for text in [
            "• Keeps card review focal points physically centered both vertically & horizontally.",
            "• Reduces mental fatigue by automatically filtering and hiding passive segments.",
            "• Click to Reveal opens isolated cloze items individually during key steps.",
            "• Configurable transition delays for eye-friendly, comfortable visual fades.",
            "• Support for both native Light / Dark styles based on client skin parameters.",
        ]:
            h_layout.addWidget(bullet(text))

        h_layout.addWidget(section("How to use"))
        for text in [
            "• Click on any hidden segment [...] or Hint text to unveil its content.",
            "• Double tap or press keyboard Space or Enter to roll the folder sequence.",
            "• Press keyboard shortcut I to instantly slide supplementary mnemonic Info open.",
            "• Choose rating scores using number hotkeys: Again (1), Hard (2), Good (3), Easy (4).",
        ]:
            h_layout.addWidget(bullet(text))

        settings_section = QLabel(
            "<b>Settings (Tools \u2192 Sequential Cloze Revealer Settings)</b>")
        settings_section.setStyleSheet(
            f"font-size: 11.5px; color: {t['section']}; margin-top: 8px;")
        h_layout.addWidget(settings_section)
        for text in [
            "• Toggle Centered Modes to lock reviews at fixed spatial coordinates.",
            "• Customize revealed text highlighting vs hidden brackets separately.",
            "• Fine tune the milliseconds reveal transition slider for comfortable response times.",
        ]:
            h_layout.addWidget(bullet(text))

        h_layout.addWidget(make_sep(t['thick_sep'], 2))

        btn_layout = QHBoxLayout()
        open_settings_btn = QPushButton("Open Settings")
        open_settings_btn.setStyleSheet(button_qss)

        def open_settings_and_close_help():
            help_dialog.accept()
            show_settings_dialog()

        open_settings_btn.clicked.connect(open_settings_and_close_help)

        got_it_btn = QPushButton("Got it \u2713")
        got_it_btn.setStyleSheet(primary_button_qss)
        got_it_btn.clicked.connect(help_dialog.accept)

        btn_layout.addWidget(open_settings_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(got_it_btn)
        h_layout.addLayout(btn_layout)

        h_layout.addWidget(make_sep(t['thick_sep'], 2))

        footnote_lbl = QLabel("v1.0.0")
        footnote_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footnote_lbl.setStyleSheet(
            f"color: {t['label_muted']}; font-size: 10px; margin-top: 2px;")
        h_layout.addWidget(footnote_lbl)

        help_dialog.setLayout(h_layout)
        help_dialog.exec()

    guide_btn = QPushButton("Open Help Guide")
    guide_btn.setStyleSheet(button_qss)
    guide_btn.clicked.connect(on_help_guide)
    help_page_layout.addWidget(guide_btn)

    report_btn = QPushButton("\u2691 Report an Issue")
    report_btn.setStyleSheet(button_qss)

    def on_report():
        import webbrowser
        webbrowser.open("https://github.com/Doummar/Sequential_Cloze_Revealer/issues")

    report_btn.clicked.connect(on_report)
    help_page_layout.addWidget(report_btn)

    reset_btn = QPushButton("\u21ba Reset to Default")
    reset_btn.setStyleSheet(button_qss)

    def on_reset():
        config.clear()
        config.update({
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
            "welcome_shown": True,
            "shortcut_roll": "Space",
            "shortcut_info": "I",
            "auto_theme_mode": True,
            "input_bindings": {
                action: [dict(b) for b in blist]
                for action, blist in bindings.DEFAULT_BINDINGS.items()
            },
        })
        mw.addonManager.writeConfig(__name__, config)
        dialog.reject()
        showInfo("Settings reset successfully.", parent=mw)
        show_settings_dialog()

    reset_btn.clicked.connect(on_reset)
    help_page_layout.addWidget(reset_btn)
    help_page_layout.addStretch()

    layout.addWidget(tabs)

    # ---- Save / Cancel ----
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )

    def save() -> None:
        config["center_mode"]               = center_mode_cb.isChecked()
        config["mitcent_mode"]              = mitcent_mode_cb.isChecked()
        config["reveal_speed"]              = reveal_speed_sb.value()
        config["enable_click_reveal"]       = click_reveal_cb.isChecked()
        config["show_info_by_default"]      = show_info_cb.isChecked()
        config["auto_reveal_back"]          = auto_reveal_back_cb.isChecked()
        config["cloze_revealed_custom"]     = cl_rev_custom_cb.isChecked()
        config["cloze_revealed_color"]      = cl_rev_color_le.text()
        config["cloze_hidden_custom"]       = cl_hid_custom_cb.isChecked()
        config["cloze_hidden_color"]        = cl_hid_color_le.text()
        config["shortcut_roll"]             = shortcut_roll_le.text()
        config["shortcut_info"]             = shortcut_info_le.text()
        bindings.set_bindings(config, "reveal", reveal_bindings_widget.bindings())
        mw.addonManager.writeConfig(__name__, config)
        dialog.accept()
        showInfo(
            "Settings saved successfully. Please reload/restart Anki to apply.",
            parent=mw)

    buttons.accepted.connect(save)
    buttons.rejected.connect(dialog.reject)

    ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
    if ok_btn:
        ok_btn.setStyleSheet(primary_button_qss)
        ok_btn.setText("Save")
    cancel_btn = buttons.button(QDialogButtonBox.StandardButton.Cancel)
    if cancel_btn:
        cancel_btn.setStyleSheet(button_qss)
        cancel_btn.setText("Cancel")

    layout.addWidget(buttons)
    dialog.setLayout(layout)
    dialog.exec()
