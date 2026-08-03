# Generic input-binding system
#
# Provides a reusable framework for mapping keyboard keys and mouse input
# (buttons + wheel) onto abstract "actions". Bindings are stored in the
# add-on config as a plain list of {"type": ..., "value": ...} dicts per
# action, so the same system can serve today's "Reveal" action as well as
# future actions (Reveal Previous, Reveal All, Reset Reveal) without any
# changes to the storage format, capture dialog, or matching logic — new
# actions only need a new key in ACTIONS / DEFAULT_BINDINGS.

from aqt.qt import *

import unicodedata


# ---------------------------------------------------------------------------
# Action registry
# ---------------------------------------------------------------------------
# Every bindable action is declared here. The settings UI currently only
# exposes "reveal", but the other actions are already fully supported by
# the storage format and capture dialog below — wiring them up in the
# reviewer JS later is a matter of adding logic, not a new binding system.
ACTIONS = {
    "reveal":          "Reveal",
    "reveal_previous": "Reveal Previous",
    "reveal_all":      "Reveal All",
    "reset_reveal":    "Reset Reveal",
}

# Bindings shipped for a brand-new install and restored on "Reset to
# Default". Mouse Wheel Down is kept as the default trigger for "Reveal"
# for backwards compatibility with the old single-purpose "Mouse Scroll
# Reveal" checkbox it replaces.
DEFAULT_BINDINGS = {
    "reveal": [{"type": "wheel", "value": "down"}],
}


# ---------------------------------------------------------------------------
# Mouse buttons
# ---------------------------------------------------------------------------

MOUSE_BUTTON_NAMES = {
    Qt.MouseButton.LeftButton:    "left",
    Qt.MouseButton.RightButton:   "right",
    Qt.MouseButton.MiddleButton:  "middle",
    Qt.MouseButton.BackButton:    "back",
    Qt.MouseButton.ForwardButton: "forward",
}

MOUSE_BUTTON_LABELS = {
    "left":    "Left Click",
    "right":   "Right Click",
    "middle":  "Middle Click",
    "back":    "Mouse Back Button",
    "forward": "Mouse Forward Button",
}


# ---------------------------------------------------------------------------
# Keyboard keys
# ---------------------------------------------------------------------------
# Canonical key names. These are mirrored (by name, not by Qt value) in
# js/cloze.js's keyEventToBindingString(), so a binding captured here in
# the Qt settings dialog matches the string built from a browser
# KeyboardEvent inside the reviewer webview.

_QT_KEY_NAMES = {
    Qt.Key.Key_Space:     "Space",
    Qt.Key.Key_Return:    "Enter",
    Qt.Key.Key_Enter:     "Enter",
    Qt.Key.Key_Escape:    "Escape",
    Qt.Key.Key_Tab:       "Tab",
    Qt.Key.Key_Backspace: "Backspace",
    Qt.Key.Key_Delete:    "Delete",
    Qt.Key.Key_Up:        "Up",
    Qt.Key.Key_Down:      "Down",
    Qt.Key.Key_Left:      "Left",
    Qt.Key.Key_Right:     "Right",
    Qt.Key.Key_Home:      "Home",
    Qt.Key.Key_End:       "End",
    Qt.Key.Key_PageUp:    "PageUp",
    Qt.Key.Key_PageDown:  "PageDown",
}
for _i in range(1, 13):
    _QT_KEY_NAMES[getattr(Qt.Key, f"Key_F{_i}")] = f"F{_i}"

# Qt.Key values line up with ASCII for printable characters (letters,
# digits, punctuation), so anything not in the table above falls back to
# chr(key) rather than needing an exhaustive mapping.
_IGNORED_KEYS = {
    Qt.Key.Key_Control, Qt.Key.Key_Alt,
    Qt.Key.Key_Shift, Qt.Key.Key_Meta,
}


def qt_key_to_binding_name(key: int) -> str:
    """Convert a Qt.Key value into the canonical string used in bindings."""
    if key in _QT_KEY_NAMES:
        return _QT_KEY_NAMES[key]
    if 0x20 <= key <= 0x7e:
        return chr(key).upper()
    text = QKeySequence(key).toString()
    name = text if text else f"Key_{key}"
    # Qt can hand back accented/composed characters (e.g. "Å") in either
    # Unicode normalization form depending on platform and input method.
    # Normalize to NFC so it reliably matches the string the reviewer
    # webview's KeyboardEvent produces for the same key (see
    # js/cloze.js:normalizeKeyString).
    return unicodedata.normalize("NFC", name)


def format_key_binding(key_name: str, modifiers) -> str:
    """Build the final "Ctrl+Shift+K" style binding string."""
    parts = []
    if modifiers & Qt.KeyboardModifier.ControlModifier:
        parts.append("Ctrl")
    if modifiers & Qt.KeyboardModifier.AltModifier:
        parts.append("Alt")
    if modifiers & Qt.KeyboardModifier.ShiftModifier:
        parts.append("Shift")
    if modifiers & Qt.KeyboardModifier.MetaModifier:
        parts.append("Meta")
    parts.append(key_name)
    return "+".join(parts)


# ---------------------------------------------------------------------------
# Binding <-> human-readable label
# ---------------------------------------------------------------------------

def describe_binding(binding: dict) -> str:
    b_type = binding.get("type")
    value = binding.get("value", "")
    if b_type == "key":
        return f"Key: {value}"
    if b_type == "mouse_button":
        return MOUSE_BUTTON_LABELS.get(value, f"Mouse {value.title()}")
    if b_type == "wheel":
        return "Mouse Wheel Up" if value == "up" else "Mouse Wheel Down"
    return "Unknown binding"


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def get_bindings(config: dict, action: str) -> list:
    bindings_cfg = config.get("input_bindings") or {}
    stored = bindings_cfg.get(action)
    if stored is None:
        stored = DEFAULT_BINDINGS.get(action, [])
    return [dict(b) for b in stored]


def set_bindings(config: dict, action: str, binding_list: list) -> None:
    bindings_cfg = config.setdefault("input_bindings", {})
    bindings_cfg[action] = [dict(b) for b in binding_list]


def migrate_legacy_config(config: dict) -> dict:
    """One-time migration from the old single-purpose "Mouse Scroll Reveal"
    checkbox onto the generic input-binding system. Idempotent — a no-op
    once "input_bindings" already exists in the config.
    """
    if "input_bindings" in config:
        return config
    if config.get("mouse_scroll_reveal", False):
        reveal_bindings = [dict(b) for b in DEFAULT_BINDINGS["reveal"]]
    else:
        # User had explicitly turned the old checkbox off — respect that
        # choice rather than silently re-enabling wheel-down for them.
        reveal_bindings = []
    config["input_bindings"] = {"reveal": reveal_bindings}
    return config


# ---------------------------------------------------------------------------
# "Press any key or mouse button" capture dialog
# ---------------------------------------------------------------------------

class BindingCaptureDialog(QDialog):
    """Modal dialog that captures the next key press, mouse button click,
    or wheel scroll and exposes it as a binding dict via .result_binding.
    """

    def __init__(self, parent=None, theme_qss: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Set Binding")
        self.setModal(True)
        self.setMinimumSize(360, 150)
        self.result_binding = None
        if theme_qss:
            self.setStyleSheet(theme_qss)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        label = QLabel("Press any key or mouse button…")
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        f = QFont()
        f.setPointSize(12)
        f.setBold(True)
        label.setFont(f)
        layout.addWidget(label)

        hint = QLabel(
            "Scroll the mouse wheel, click a mouse button,\n"
            "or press a keyboard key. Press Esc to cancel.")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        if key in _IGNORED_KEYS:
            return  # wait for a real, non-modifier key
        name = qt_key_to_binding_name(key)
        value = format_key_binding(name, event.modifiers())
        self.result_binding = {"type": "key", "value": value}
        self.accept()

    def mousePressEvent(self, event) -> None:
        btn = MOUSE_BUTTON_NAMES.get(event.button())
        if btn:
            self.result_binding = {"type": "mouse_button", "value": btn}
            self.accept()

    def wheelEvent(self, event) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            return
        value = "up" if delta > 0 else "down"
        self.result_binding = {"type": "wheel", "value": value}
        self.accept()


def capture_binding(parent=None, theme_qss: str = ""):
    """Show the capture dialog; return a binding dict, or None if cancelled."""
    dlg = BindingCaptureDialog(parent, theme_qss)
    if dlg.exec() == QDialog.DialogCode.Accepted:
        return dlg.result_binding
    return None


# ---------------------------------------------------------------------------
# Reusable "bindings for one action" list widget
# ---------------------------------------------------------------------------

class BindingListWidget(QWidget):
    """Shows the current bindings for a single action as a list, with
    controls to add a new one (via the capture dialog) or remove the
    selected one. Any action name from ACTIONS can be managed this way.
    """

    def __init__(self, binding_list: list, parent=None, theme_qss: str = ""):
        super().__init__(parent)
        self._bindings = [dict(b) for b in binding_list]
        self._theme_qss = theme_qss

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(88)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("+ Add Binding")
        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.remove_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self._refresh()

    def _refresh(self) -> None:
        self.list_widget.clear()
        for b in self._bindings:
            self.list_widget.addItem(describe_binding(b))

    def _on_add(self) -> None:
        binding = capture_binding(self, self._theme_qss)
        if binding is None:
            return
        if binding in self._bindings:
            return  # already bound to this action, avoid exact duplicates
        self._bindings.append(binding)
        self._refresh()

    def _on_remove(self) -> None:
        row = self.list_widget.currentRow()
        if row < 0:
            return
        del self._bindings[row]
        self._refresh()

    def bindings(self) -> list:
        return [dict(b) for b in self._bindings]
