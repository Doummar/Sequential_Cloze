# Generic input-binding system

try:
    from aqt.qt import *
except ImportError:
    class _DummyKey:
        Key_Space = 0x20
        Key_Return = 0x01000004
        Key_Enter = 0x01000005
        Key_Escape = 0x01000000
        Key_Tab = 0x01000001
        Key_Backspace = 0x01000003
        Key_Delete = 0x01000007
        Key_Home = 0x01000010
        Key_End = 0x01000011
        Key_PageUp = 0x01000016
        Key_PageDown = 0x01000017
        Key_Up = 0x01000013
        Key_Down = 0x01000015
        Key_Left = 0x01000012
        Key_Right = 0x01000014
        Key_Control = 0x01000021
        Key_Alt = 0x01000023
        Key_Shift = 0x01000020
        Key_Meta = 0x01000022

    for _idx in range(1, 13):
        setattr(_DummyKey, f"Key_F{_idx}", 0x01000030 + _idx)

    class _DummyMouseButton:
        LeftButton = 1
        RightButton = 2
        MiddleButton = 4
        BackButton = 8
        ForwardButton = 16

    class _DummyKeyboardModifier:
        ControlModifier = 0x04000000
        AltModifier = 0x08000000
        ShiftModifier = 0x02000000
        MetaModifier = 0x10000000

    class _DummyQt:
        Key = _DummyKey
        MouseButton = _DummyMouseButton
        KeyboardModifier = _DummyKeyboardModifier

    Qt = _DummyQt

    class _DummySignal:
        def connect(self, *a, **k): pass
        def emit(self, *a, **k): pass

    class _DummyWidget:
        def __init__(self, *args, **kwargs):
            self.clicked = _DummySignal()
            self.textChanged = _DummySignal()
            self.currentIndexChanged = _DummySignal()
            self.finished = _DummySignal()
        def __getattr__(self, name): return lambda *a, **k: _DummyWidget()

    QDialog = _DummyWidget
    QWidget = _DummyWidget
    QVBoxLayout = _DummyWidget
    QHBoxLayout = _DummyWidget
    QLabel = _DummyWidget
    QPushButton = _DummyWidget
    QListWidget = _DummyWidget
    QListWidgetItem = _DummyWidget
try:
    from PyQt6.QtGui import QFont
except ImportError:
    try:
        from PyQt5.QtGui import QFont
    except ImportError:
        pass
import unicodedata

ACTIONS = {
    "reveal":          "Reveal",
    "reveal_previous": "Reveal Previous",
    "reveal_all":      "Reveal All",
    "reset_reveal":    "Reset Reveal",
}

DEFAULT_BINDINGS = {
    "reveal": [{"type": "wheel", "value": "down"}],
}

def _qt_val(scope: str, name: str, fallback=0):
    if hasattr(Qt, scope) and hasattr(getattr(Qt, scope), name):
        return getattr(getattr(Qt, scope), name)
    if hasattr(Qt, name):
        return getattr(Qt, name)
    return fallback

MOUSE_BUTTON_NAMES = {
    _qt_val("MouseButton", "LeftButton", 1):    "left",
    _qt_val("MouseButton", "RightButton", 2):   "right",
    _qt_val("MouseButton", "MiddleButton", 4):  "middle",
    _qt_val("MouseButton", "BackButton", 8):    "back",
    _qt_val("MouseButton", "ForwardButton", 16): "forward",
}

MOUSE_BUTTON_LABELS = {
    "left":    "Left Click",
    "right":   "Right Click",
    "middle":  "Middle Click",
    "back":    "Mouse Back Button",
    "forward": "Mouse Forward Button",
}

_QT_KEY_NAMES = {
    _qt_val("Key", "Key_Space", 0x20):           "Space",
    _qt_val("Key", "Key_Return", 0x01000004):    "Enter",
    _qt_val("Key", "Key_Enter", 0x01000005):     "Enter",
    _qt_val("Key", "Key_Escape", 0x01000000):    "Escape",
    _qt_val("Key", "Key_Tab", 0x01000001):       "Tab",
    _qt_val("Key", "Key_Backspace", 0x01000003): "Backspace",
    _qt_val("Key", "Key_Delete", 0x01000007):    "Delete",
    _qt_val("Key", "Key_Up", 0x01000013):        "Up",
    _qt_val("Key", "Key_Down", 0x01000015):      "Down",
    _qt_val("Key", "Key_Left", 0x01000012):      "Left",
    _qt_val("Key", "Key_Right", 0x01000014):     "Right",
    _qt_val("Key", "Key_Home", 0x01000010):      "Home",
    _qt_val("Key", "Key_End", 0x01000011):       "End",
    _qt_val("Key", "Key_PageUp", 0x01000016):    "PageUp",
    _qt_val("Key", "Key_PageDown", 0x01000017):  "PageDown",
    0x20:       "Space",
    0x01000004: "Enter",
    0x01000005: "Enter",
    0x01000000: "Escape",
    0x01000001: "Tab",
    0x01000003: "Backspace",
    0x01000007: "Delete",
    0x01000013: "Up",
    0x01000015: "Down",
    0x01000012: "Left",
    0x01000014: "Right",
    0x01000010: "Home",
    0x01000011: "End",
    0x01000016: "PageUp",
    0x01000017: "PageDown",
}
for _i in range(1, 13):
    _k = _qt_val("Key", f"Key_F{_i}", 0x01000030 + _i)
    if _k is not None:
        _QT_KEY_NAMES[_k] = f"F{_i}"
        _QT_KEY_NAMES[0x01000030 + _i] = f"F{_i}"

_IGNORED_KEYS = {
    _qt_val("Key", "Key_Control", 0x01000021),
    _qt_val("Key", "Key_Alt", 0x01000023),
    _qt_val("Key", "Key_Shift", 0x01000020),
    _qt_val("Key", "Key_Meta", 0x01000022),
    0x01000021,
    0x01000023,
    0x01000020,
    0x01000022,
}

def _mod_value(mods):
    try:
        return int(mods)
    except Exception:
        pass
    try:
        return int(mods.value)
    except Exception:
        return 0

def qt_key_to_binding_name(key) -> str:
    key_int = _mod_value(key)
    if key in _QT_KEY_NAMES:
        return _QT_KEY_NAMES[key]
    if key_int in _QT_KEY_NAMES:
        return _QT_KEY_NAMES[key_int]
    if 0x20 <= key_int <= 0x7e:
        return chr(key_int).upper()
    try:
        text = QKeySequence(key).toString()
        name = text if text else f"Key_{key_int}"
        return unicodedata.normalize("NFC", name)
    except Exception:
        return f"Key_{key_int}"

def format_key_binding(key_name: str, modifiers) -> str:
    parts = []
    try:
        ctrl = int(Qt.KeyboardModifier.ControlModifier)
        alt = int(Qt.KeyboardModifier.AltModifier)
        shift = int(Qt.KeyboardModifier.ShiftModifier)
        meta = int(Qt.KeyboardModifier.MetaModifier)
    except Exception:
        ctrl = _mod_value(_qt_val("KeyboardModifier", "ControlModifier", 0x04000000)) or 0x04000000
        alt = _mod_value(_qt_val("KeyboardModifier", "AltModifier", 0x08000000)) or 0x08000000
        shift = _mod_value(_qt_val("KeyboardModifier", "ShiftModifier", 0x02000000)) or 0x02000000
        meta = _mod_value(_qt_val("KeyboardModifier", "MetaModifier", 0x10000000)) or 0x10000000

    mod_val = _mod_value(modifiers)
    if mod_val & ctrl:
        parts.append("Ctrl")
    if mod_val & alt:
        parts.append("Alt")
    if mod_val & shift:
        parts.append("Shift")
    if mod_val & meta:
        parts.append("Meta")
    parts.append(key_name)
    return "+".join(parts)

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
    if "input_bindings" in config:
        return config
    if config.get("mouse_scroll_reveal", False):
        reveal_bindings = [dict(b) for b in DEFAULT_BINDINGS["reveal"]]
    else:
        reveal_bindings = []
    config["input_bindings"] = {"reveal": reveal_bindings}
    return config

class BindingCaptureDialog(QDialog):
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
        label.setAlignment(Qt.AlignmentFlag.AlignCenter if hasattr(Qt, 'AlignmentFlag') else Qt.AlignCenter)
        try:
            f = QFont()
            f.setPointSize(12)
            f.setBold(True)
            label.setFont(f)
        except Exception:
            pass
        label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(label)

        hint = QLabel(
            "Scroll the mouse wheel, click a mouse button,\n"
            "or press a keyboard key. Press Esc to cancel.")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter if hasattr(Qt, 'AlignmentFlag') else Qt.AlignCenter)
        layout.addWidget(hint)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(26)
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)
        focus_policy = _qt_val("FocusPolicy", "StrongFocus", getattr(Qt, "StrongFocus", None))
        if focus_policy is not None:
            try:
                self.setFocusPolicy(focus_policy)
            except Exception:
                pass

    def keyPressEvent(self, event) -> None:
        key = event.key()
        esc = _qt_val("Key", "Key_Escape", 0x01000000)
        esc_val = _mod_value(esc) or 0x01000000
        key_val = _mod_value(key)
        if key == esc or key_val == esc_val:
            self.reject()
            return
        if key in _IGNORED_KEYS or key_val in _IGNORED_KEYS:
            return
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
    dlg = BindingCaptureDialog(parent, theme_qss)
    accepted = getattr(getattr(QDialog, "DialogCode", QDialog), "Accepted", 1)
    res = dlg.exec() if hasattr(dlg, "exec") else dlg.exec_()
    if res == accepted:
        return dlg.result_binding
    return None

class BindingListWidget(QWidget):
    def __init__(self, binding_list: list, parent=None, theme_qss: str = ""):
        super().__init__(parent)
        self._bindings = [dict(b) for b in binding_list]
        self._theme_qss = theme_qss

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.list_widget = QListWidget()
        self.list_widget.setMinimumHeight(64)
        self.list_widget.setMaximumHeight(80)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.add_btn = QPushButton("+ Add Binding")
        self.add_btn.setFixedHeight(26)
        self.add_btn.clicked.connect(self._on_add)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.setFixedHeight(26)
        self.remove_btn.clicked.connect(self._on_remove)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.remove_btn)
        btn_row.addStretch()
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
            return
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

    def set_bindings(self, binding_list: list) -> None:
        self._bindings = [dict(b) for b in binding_list]
        self._refresh()
