// Sequential Cloze Revealer - Reviewer Frontend Script

// Explicitly bind functions to window/global scope for reliable access from python .eval()
window.toggleInfo = function(event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    const info = document.getElementById("info-content");
    if (info) {
        info.classList.toggle("hidden");
    }
};

// ---------------------------------------------------------------------------
// Generic input-binding system (runtime half)
//
// The Qt settings dialog (bindings.py) lets the user attach any mix of
// keyboard keys, mouse buttons, and mouse-wheel directions to an "action"
// name, stored in config.actionBindings as { actionName: [ {type, value} ] }.
// Everything below is action-agnostic: it just figures out which action(s)
// a given browser event maps to and calls window.performAction(name) — the
// same call regardless of whether a key, a click, or a wheel scroll
// triggered it. Adding a future action (Reveal Previous, Reveal All, Reset
// Reveal) only means adding a branch inside performAction().
// ---------------------------------------------------------------------------

// Mirrors bindings.py's qt_key_to_binding_name()/format_key_binding() so a
// binding captured in the Qt dialog matches what a KeyboardEvent produces.
//
// Note: for accented / non-ASCII keys (e.g. "Å" on a Nordic layout), Qt and
// Chromium can report the *same visible character* using different Unicode
// normalization forms (composed "NFC" vs decomposed "NFD" — a single "Å"
// code point vs "A" + a separate combining ring). They look identical but
// fail a strict "===" comparison, so both this function's output and the
// stored binding value are normalized to NFC before ever being compared
// (see bindingListMatches below).
function keyEventToBindingString(e) {
    var parts = [];
    if (e.ctrlKey) parts.push("Ctrl");
    if (e.altKey) parts.push("Alt");
    if (e.shiftKey) parts.push("Shift");
    if (e.metaKey) parts.push("Meta");

    var specialMap = {
        " ": "Space",
        "ArrowUp": "Up",
        "ArrowDown": "Down",
        "ArrowLeft": "Left",
        "ArrowRight": "Right"
    };

    var key = e.key;
    if (specialMap.hasOwnProperty(key)) {
        key = specialMap[key];
    } else if (key.length === 1) {
        key = key.toUpperCase();
    } else {
        key = key.charAt(0).toUpperCase() + key.slice(1);
    }
    parts.push(key);
    return normalizeKeyString(parts.join("+"));
}

// Best-effort Unicode normalization; String.prototype.normalize isn't
// available in every embedded engine, so degrade gracefully if missing.
function normalizeKeyString(s) {
    if (typeof s !== "string") return s;
    return typeof s.normalize === "function" ? s.normalize("NFC") : s;
}

// Mirrors bindings.py's MOUSE_BUTTON_NAMES.
function mouseButtonName(button) {
    switch (button) {
        case 0: return "left";
        case 1: return "middle";
        case 2: return "right";
        case 3: return "back";
        case 4: return "forward";
        default: return null;
    }
}

function bindingListMatches(bindingList, type, value) {
    if (!bindingList) return false;
    // Normalize the incoming key value once; stored binding values are
    // normalized per-entry below so this also self-heals bindings saved by
    // an older build before this normalization fix existed.
    var normValue = type === "key" ? normalizeKeyString(value) : value;
    for (var i = 0; i < bindingList.length; i++) {
        var b = bindingList[i];
        if (!b || b.type !== type) continue;
        var bValue = type === "key" ? normalizeKeyString(b.value) : b.value;
        if (bValue === normValue) return true;
    }
    return false;
}

// Single dispatch point for every bindable action. New actions plug in here.
window.performAction = function(action) {
    if (action === "reveal") {
        var hiddenCloze = document.querySelector(".cloze.active[data-state='hidden']");
        if (hiddenCloze) {
            window.revealCloze(hiddenCloze);
        }
    } else if (action === "reveal_previous") {
        // Reserved for a future update.
    } else if (action === "reveal_all") {
        // Reserved for a future update.
    } else if (action === "reset_reveal") {
        // Reserved for a future update.
    }
};

window.setupClozeInteractions = function() {
    // Only apply interaction logic if the custom .anki-card-container is present
    const container = document.querySelector(".anki-card-container");
    if (!container) {
        if (!window._setupClozeRetryCount) window._setupClozeRetryCount = 0;
        if (window._setupClozeRetryCount < 10) {
            window._setupClozeRetryCount++;
            setTimeout(window.setupClozeInteractions, 50);
        }
        return;
    }
    window._setupClozeRetryCount = 0; // reset
    
    const config = window.MINIMAL_CLOZE_CONFIG || {
        showInfoByDefault: false,
        enableClickReveal: true,
        centerMode: true,
        mitcentMode: true,
        revealSpeed: 120,
        darkCompatibility: true,
        autoRevealBack: true,
        clozeRevealedCustom: false,
        clozeRevealedColor: "#c00000",
        clozeHiddenCustom: false,
        clozeHiddenColor: "#0284c7",
        activeClozeIdx: 1,
        shortcutRoll: "Space",
        shortcutInfo: "I",
        actionBindings: { reveal: [{ type: "wheel", value: "down" }] }
    };

    // Normalise activeClozeIdx to a plain integer.
    // Python injects it as a number literal (e.g. activeClozeIdx: 1) but the
    // JS default above used a string, so parseInt() handles both forms safely.
    config.activeClozeIdx = parseInt(config.activeClozeIdx || 0, 10);

    // Apply default styles or timing from configuration
    document.documentElement.style.setProperty('--reveal-speed', config.revealSpeed + "ms");
    
    if (config.clozeRevealedCustom && config.clozeRevealedColor) {
        document.documentElement.style.setProperty('--cloze-revealed-color', config.clozeRevealedColor);
    } else {
        document.documentElement.style.setProperty('--cloze-revealed-color', 'inherit');
    }
    
    if (config.clozeHiddenCustom && config.clozeHiddenColor) {
        document.documentElement.style.setProperty('--cloze-hidden-color', config.clozeHiddenColor);
    } else {
        document.documentElement.style.setProperty('--cloze-hidden-color', 'inherit');
    }
    
    // Detect back card early — used by both applyCentering and cloze setup below
    const isBackCard = document.getElementById("answer-splitter") !== null ||
                       document.querySelector(".minimal-back") !== null;

    // Dynamically apply Center / Left layout
    const applyCentering = function() {
        // Neutralise Anki's own body-level flex centering so it doesn't
        // compound with our container centering and cause a position shift.
        if (document.body) {
            document.body.style.justifyContent = "flex-start";
            document.body.style.alignItems    = "stretch";
        }
        const containers = [
            document.body,
            document.querySelector(".card"),
            document.querySelector(".anki-card-container")
        ];
        containers.forEach(function(el) {
            if (el) {
                if (config.mitcentMode) {
                    el.classList.add("center-mode", "mitcent-mode");
                    el.classList.remove("left-mode");
                } else if (config.centerMode) {
                    el.classList.add("center-mode");
                    el.classList.remove("left-mode", "mitcent-mode");
                } else {
                    el.classList.add("left-mode");
                    el.classList.remove("center-mode", "mitcent-mode");
                }
            }
        });
    };
    applyCentering();
    setTimeout(applyCentering, 0);
    setTimeout(applyCentering, 100);

    // Initial info field visibility state
    const infoContent = document.getElementById("info-content");
    if (infoContent) {
        if (config.showInfoByDefault) {
            infoContent.classList.remove("hidden");
        } else {
            infoContent.classList.add("hidden");
        }
    }
    
    const rawEl = document.getElementById("raw-front");
    const frontContentEl = document.querySelector(".minimal-front");
    
    // Multi-platform enrichment: Parse raw Front if available and not yet marked
    if (rawEl && frontContentEl && !frontContentEl.hasAttribute("data-interactive-rendered")) {
        frontContentEl.setAttribute("data-interactive-rendered", "true");
        let rawText = rawEl.innerHTML || rawEl.textContent || "";
        
        // Find raw clozes to determine active index
        const clozPattern = /\{\{c(\d+)::(.*?)\}\}/gi;
        const rawClozes = [];
        let match;
        while ((match = clozPattern.exec(rawText)) !== null) {
            const clNum = parseInt(match[1], 10);
            const content = match[2];
            const parts = content.split("::");
            let hint = "";
            let answer = content;
            if (parts.length > 1) {
                hint = parts[parts.length - 1];
                answer = parts.slice(0, -1).join("::");
            }
            rawClozes.push({ num: clNum, answer: answer.trim(), hint: hint.trim() });
        }
        
        // Detect active cloze index
        let activeIdx = 1;
        if (config.activeClozeIdx) {
            // Already normalised to a number by the parseInt() call above
            activeIdx = config.activeClozeIdx;
        } else {
            const nativeClozeSpan = frontContentEl.querySelector(".cloze");
            if (nativeClozeSpan) {
                const natText = (nativeClozeSpan.textContent || nativeClozeSpan.innerText || "").trim();
                const plainNativeText = frontContentEl.innerText || frontContentEl.textContent || "";
                for (let i = 0; i < rawClozes.length; i++) {
                    const rc = rawClozes[i];
                    if (rc.hint && natText.includes(rc.hint)) {
                        activeIdx = rc.num;
                        break;
                    }
                }
                if (activeIdx === 1) {
                    for (let i = 0; i < rawClozes.length; i++) {
                        const rc = rawClozes[i];
                        if (!plainNativeText.includes(rc.answer)) {
                            activeIdx = rc.num;
                            break;
                        }
                    }
                }
            }
        }
        
        // Rebuild HTML with interactive span elements
        const enrichedHtml = rawText.replace(/\{\{c(\d+)::(.*?)\}\}/gi, function(match, clNumStr, content) {
            const clNum = parseInt(clNumStr, 10);
            const parts = content.split("::");
            let hint = "";
            let answer = content;
            if (parts.length > 1) {
                hint = parts[parts.length - 1];
                answer = parts.slice(0, -1).join("::");
            }
            const isActive = (clNum === activeIdx);
            
            const safeAnswer = answer.replace(/"/g, "&quot;");
            const safeHint = hint.replace(/"/g, "&quot;");
            const originalText = hint ? "[" + hint + "]" : "[...]";
            
            if (isActive) {
                if (isBackCard) {
                    return '<span class="cloze active" data-cloze-idx="' + clNum + '" data-answer="' + safeAnswer + '" data-hint="' + safeHint + '" data-state="revealed" data-original-text="' + originalText + '" style="pointer-events: auto !important; cursor: pointer !important;">' + answer + '</span>';
                } else {
                    return '<span class="cloze active" data-cloze-idx="' + clNum + '" data-answer="' + safeAnswer + '" data-hint="' + safeHint + '" data-state="hidden" data-original-text="' + originalText + '" style="pointer-events: auto !important; cursor: pointer !important;">' + originalText + '</span>';
                }
            } else {
                return '<span class="cloze passive" data-cloze-idx="' + clNum + '" data-answer="' + safeAnswer + '" data-hint="' + safeHint + '" data-state="revealed" data-original-text="' + originalText + '" style="pointer-events: auto !important; cursor: pointer !important;">' + answer + '</span>';
            }
        });
        
        frontContentEl.innerHTML = enrichedHtml;
    }
    
    // Select all clozes (native or reconstructed)
    const clozes = document.querySelectorAll(".cloze");
    
    clozes.forEach(function(cloze) {
        const text = (cloze.innerText || cloze.textContent || "").trim();
        const isBlank = cloze.hasAttribute("data-answer") || text.includes("...") || (text.startsWith("[") && text.endsWith("]"));
        
        const clozeIdxAttr = cloze.getAttribute("data-cloze-idx");
        let isActive = false;
        if (clozeIdxAttr && config.activeClozeIdx) {
            // clozeIdxAttr is always a string from getAttribute(); config value
            // is a number — parse the attribute so === strict equality works.
            isActive = (parseInt(clozeIdxAttr, 10) === config.activeClozeIdx);
        } else {
            isActive = isBlank || cloze.classList.contains("active");
        }
        
        const hint = cloze.getAttribute("data-hint") || "";
        
        if (isActive) {
            cloze.classList.add("active");
            cloze.classList.remove("passive");
            
            if (isBackCard) {
                cloze.setAttribute("data-state", "revealed");
                if (!cloze.getAttribute("data-answer")) {
                    cloze.setAttribute("data-answer", cloze.innerHTML);
                }
                if (!cloze.getAttribute("data-original-text")) {
                    cloze.setAttribute("data-original-text", hint ? "[" + hint + "]" : "[...]");
                }
            } else {
                cloze.setAttribute("data-state", "hidden");
                if (!cloze.getAttribute("data-original-text")) {
                    cloze.setAttribute("data-original-text", cloze.innerHTML);
                }
            }
        } else {
            cloze.classList.add("passive");
            cloze.classList.remove("active");
            cloze.setAttribute("data-state", "revealed");
        }
        
        // Setup click/touchend handlers
        if (config.enableClickReveal) {
            if (!cloze.hasAttribute("data-has-listener")) {
                cloze.setAttribute("data-has-listener", "true");
                
                const handleInteract = function(e) {
                    e.stopPropagation();
                    e.preventDefault(); // Critically prevent card flipping on click
                    
                    if (cloze.classList.contains("active")) {
                        if (cloze.getAttribute("data-state") === "hidden") {
                            window.revealCloze(cloze);
                        } else {
                            window.hideCloze(cloze);
                        }
                    } else if (cloze.classList.contains("passive")) {
                        window.togglePassiveCloze(cloze);
                    }
                };
                
                cloze.addEventListener("click", handleInteract);
                cloze.addEventListener("touchend", handleInteract, { passive: false });
                
                cloze.addEventListener("dblclick", function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                    if (cloze.classList.contains("active")) {
                        window.hideCloze(cloze);
                    }
                });
            }
        }
    });
    
    window.updateClozeSequencing();
    
    // Set up Keyboard Shortcuts
    document.onkeydown = function(e) {
        // Isolation guard: this handler persists in the webview across card
        // changes. Do nothing when our card type is no longer in the DOM.
        if (!document.querySelector(".anki-card-container")) return;

        const rollKey = (config.shortcutRoll || "Space").toLowerCase();
        const infoKey = (config.shortcutInfo || "I").toLowerCase();

        // Helper: does this event match a configured key string?
        const keyMatchesRoll = rollKey === "space"
            ? (e.code === "Space" || e.key === " ")
            : e.key.toLowerCase() === rollKey;

        // Shift+Roll: reveal ALL hidden active clozes at once.
        // MUST be checked before plain Roll so Shift+Space is not swallowed first.
        if (keyMatchesRoll && e.shiftKey) {
            e.preventDefault();
            const activeClozes = document.querySelectorAll(".cloze.active[data-state='hidden']");
            activeClozes.forEach(function(c) { window.revealCloze(c); });
            return;
        }

        // Roll: reveal next hidden cloze, or flip card when none remain
        if (keyMatchesRoll) {
            const hiddenCloze = document.querySelector(".cloze.active[data-state='hidden']");
            if (hiddenCloze) {
                e.preventDefault();
                window.revealCloze(hiddenCloze);
                return;
            }
            if (window.pycmd) {
                window.pycmd("ans");
            }
        }

        if (e.key.toLowerCase() === "a") {
            e.preventDefault();
            if (window.pycmd) {
                window.pycmd("ans");
            }
        }

        // Info toggle shortcut
        if (e.key.toLowerCase() === infoKey) {
            e.preventDefault();
            window.toggleInfo();
        }
    };

    // Generic input bindings (keyboard / mouse button / mouse wheel), wired
    // up to whatever actions are configured in config.actionBindings.
    // Always remove any previous listeners first — they're attached to
    // `document`, which persists across card navigations in Anki's webview,
    // so without explicit cleanup they'd accumulate and fire on every card
    // type after the user has seen at least one Sequential card.
    if (window._ibKeyHandler) {
        document.removeEventListener("keydown", window._ibKeyHandler, true);
        window._ibKeyHandler = null;
    }
    if (window._ibMouseHandler) {
        document.removeEventListener("mousedown", window._ibMouseHandler);
        window._ibMouseHandler = null;
    }
    if (window._ibWheelHandler) {
        document.removeEventListener("wheel", window._ibWheelHandler);
        window._ibWheelHandler = null;
    }

    var actionBindings = config.actionBindings || {};

    // Isolation guard: if the user has navigated to a different card type,
    // our container is gone — detach every listener and bail.
    var _ibAlive = function() {
        if (document.querySelector(".anki-card-container")) return true;
        if (window._ibKeyHandler) document.removeEventListener("keydown", window._ibKeyHandler, true);
        if (window._ibMouseHandler) document.removeEventListener("mousedown", window._ibMouseHandler);
        if (window._ibWheelHandler) document.removeEventListener("wheel", window._ibWheelHandler);
        window._ibKeyHandler = window._ibMouseHandler = window._ibWheelHandler = null;
        return false;
    };

    // Fires performAction() for every action bound to this (type, value)
    // input — the same reveal logic runs whether a key, a click, or a wheel
    // scroll triggered it.
    var _ibDispatch = function(type, value) {
        for (var action in actionBindings) {
            if (bindingListMatches(actionBindings[action], type, value)) {
                window.performAction(action);
            }
        }
    };

    window._ibKeyHandler = function(e) {
        if (!_ibAlive()) return;
        _ibDispatch("key", keyEventToBindingString(e));
    };
    document.addEventListener("keydown", window._ibKeyHandler, true);

    window._ibMouseHandler = function(e) {
        if (!_ibAlive()) return;
        var btn = mouseButtonName(e.button);
        if (!btn) return;
        // Clicks landing directly on a cloze are already handled by the
        // click-to-reveal listener set up above; don't double-fire.
        if (e.target && e.target.closest && e.target.closest(".cloze")) return;
        _ibDispatch("mouse_button", btn);
    };
    document.addEventListener("mousedown", window._ibMouseHandler);

    // 400 ms cooldown prevents the 3-10 rapid wheel events a single scroll
    // gesture fires from triggering an action multiple times per gesture.
    var _ibWheelLocked = false;
    window._ibWheelHandler = function(e) {
        if (!_ibAlive() || _ibWheelLocked) return;
        var dir = e.deltaY > 0 ? "down" : (e.deltaY < 0 ? "up" : null);
        if (!dir) return;

        var matched = false;
        for (var action in actionBindings) {
            if (bindingListMatches(actionBindings[action], "wheel", dir)) matched = true;
        }
        if (!matched) return;

        // Only swallow the native scroll when a binding actually matched, so
        // normal page scrolling still works when the wheel isn't bound.
        e.preventDefault();
        _ibWheelLocked = true;
        setTimeout(function() { _ibWheelLocked = false; }, 400);
        _ibDispatch("wheel", dir);
    };
    document.addEventListener("wheel", window._ibWheelHandler, { passive: false });
};

window.updateClozeSequencing = function() {
    const hiddenActive = document.querySelectorAll(".cloze.active[data-state='hidden']");
    document.querySelectorAll(".cloze").forEach(function(el) {
        el.classList.remove("current-cloze");
    });
    if (hiddenActive.length > 0) {
        hiddenActive[0].classList.add("current-cloze");
    }
};

window.revealCloze = function(el) {
    if (el.getAttribute("data-state") === "hidden") {
        el.style.opacity = "0";
        setTimeout(function() {
            const actualAnswer = el.getAttribute("data-answer");
            if (actualAnswer) {
                el.innerHTML = actualAnswer;
            } else {
                el.innerHTML = el.innerHTML.replace(/\[|\]/g, '');
            }
            el.setAttribute("data-state", "revealed");
            el.style.opacity = "1";
            window.updateClozeSequencing();
            
            // Auto open the back card if this was the last hidden active cloze
            const remainingHidden = document.querySelectorAll(".cloze.active[data-state='hidden']");
            const conf = window.MINIMAL_CLOZE_CONFIG || { autoRevealBack: true };
            if (remainingHidden.length === 0 && window.pycmd && conf.autoRevealBack) {
                window.pycmd("ans");
            }
        }, 65);
    }
};

window.hideCloze = function(el) {
    if (el.getAttribute("data-state") === "revealed" && el.classList.contains("active")) {
        el.style.opacity = "0";
        setTimeout(function() {
            const originalText = el.getAttribute("data-original-text") || "[...]";
            el.innerHTML = originalText;
            el.setAttribute("data-state", "hidden");
            el.style.opacity = "1";
            window.updateClozeSequencing();
        }, 65);
    }
};

window.togglePassiveCloze = function(el) {
    if (el.style.opacity === "0.3" || el.classList.contains("hidden-passive")) {
        el.classList.remove("hidden-passive");
        el.style.opacity = "1";
    } else {
        el.classList.add("hidden-passive");
        el.style.opacity = "0.3";
    }
};
