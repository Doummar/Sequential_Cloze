// Sequential Cloze Revealer - Reviewer Frontend Script (with .ctrl + .ibtn system)

// Toggle Image: Injects content into #extra-area (Sentence Builder system)
window.toggleCardImage = function(event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    const extraArea = document.getElementById("extra-area");
    const rawImage = document.getElementById("raw-image");
    const btn = document.getElementById("image-toggle-btn");
    if (!extraArea || !rawImage) return;

    const isCurrent = extraArea.getAttribute("data-mode") === "image";
    if (isCurrent) {
        extraArea.innerHTML = "";
        extraArea.removeAttribute("data-mode");
        if (btn) btn.classList.remove("active");
    } else {
        extraArea.innerHTML = rawImage.innerHTML;
        extraArea.setAttribute("data-mode", "image");
        if (btn) btn.classList.add("active");

        const infoBtn = document.getElementById("info-toggle-btn");
        if (infoBtn) infoBtn.classList.remove("active");
    }
};

// Toggle Info: Injects content into #extra-area (Sentence Builder system)
window.toggleInfo = function(event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    const extraArea = document.getElementById("extra-area");
    const rawInfo = document.getElementById("raw-info");
    const btn = document.getElementById("info-toggle-btn");
    if (!extraArea || !rawInfo) return;

    const isCurrent = extraArea.getAttribute("data-mode") === "info";
    if (isCurrent) {
        extraArea.innerHTML = "";
        extraArea.removeAttribute("data-mode");
        if (btn) btn.classList.remove("active");
    } else {
        extraArea.innerHTML = '<div class="info-content">' + rawInfo.innerHTML + '</div>';
        extraArea.setAttribute("data-mode", "info");
        if (btn) btn.classList.add("active");

        const imgBtn = document.getElementById("image-toggle-btn");
        if (imgBtn) imgBtn.classList.remove("active");
    }
};

// ---------------------------------------------------------------------------
// Generic input-binding system (runtime half)
// ---------------------------------------------------------------------------

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

function normalizeKeyString(s) {
    if (typeof s !== "string") return s;
    return typeof s.normalize === "function" ? s.normalize("NFC") : s;
}

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
    var normValue = type === "key" ? normalizeKeyString(value) : value;
    for (var i = 0; i < bindingList.length; i++) {
        var b = bindingList[i];
        if (!b || b.type !== type) continue;
        var bValue = type === "key" ? normalizeKeyString(b.value) : b.value;
        if (bValue === normValue) return true;
    }
    return false;
}

window.teardownClozeInteractions = function() {
    if (window._sqKeyHandler) {
        document.removeEventListener("keydown", window._sqKeyHandler, false);
        window._sqKeyHandler = null;
    }
    if (window._sqWheelHandler) {
        document.removeEventListener("wheel", window._sqWheelHandler, { passive: false });
        window._sqWheelHandler = null;
    }
    if (window._sqMouseHandler) {
        document.removeEventListener("mousedown", window._sqMouseHandler, false);
        window._sqMouseHandler = null;
    }
    if (window._ibKeyHandler) {
        document.removeEventListener("keydown", window._ibKeyHandler, true);
        document.removeEventListener("keydown", window._ibKeyHandler, false);
        window._ibKeyHandler = null;
    }
    if (window._ibWheelHandler) {
        document.removeEventListener("wheel", window._ibWheelHandler, { passive: false });
        document.removeEventListener("wheel", window._ibWheelHandler, false);
        window._ibWheelHandler = null;
    }
    if (window._ibMouseHandler) {
        document.removeEventListener("mousedown", window._ibMouseHandler, false);
        window._ibMouseHandler = null;
    }
    if (document.onkeydown && document.onkeydown._isSequentialCloze) {
        document.onkeydown = null;
    }
};

window.performAction = function(action) {
    if (action === "reveal") {
        var hiddenCloze = document.querySelector(".cloze.active[data-state='hidden']");
        if (hiddenCloze) {
            window.revealCloze(hiddenCloze);
        }
    }
};

function isEditingField(el) {
    if (!el) return false;
    var tag = (el.tagName || "").toUpperCase();
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
    if (el.isContentEditable || el.getAttribute("contenteditable") === "true" || el.getAttribute("contenteditable") === "") return true;
    if (typeof el.closest === "function") {
        if (el.closest("input, textarea, select, [contenteditable='true'], [contenteditable=''], .type-ans, #typeans, form")) {
            return true;
        }
    }
    return false;
}

function parseShortcut(str) {
    if (!str || typeof str !== "string") return null;
    var clean = str.toLowerCase().replace(/\s+/g, "");
    var parts = clean.split("+").filter(Boolean);
    if (parts.length === 0) return null;

    var wantsCtrl = false;
    var wantsAlt = false;
    var wantsShift = false;
    var wantsMeta = false;
    var keyPart = "";

    for (var i = 0; i < parts.length; i++) {
        var p = parts[i];
        if (p === "ctrl" || p === "control") wantsCtrl = true;
        else if (p === "alt") wantsAlt = true;
        else if (p === "shift") wantsShift = true;
        else if (p === "meta" || p === "cmd" || p === "command" || p === "win") wantsMeta = true;
        else keyPart = p;
    }
    return {
        wantsCtrl: wantsCtrl,
        wantsAlt: wantsAlt,
        wantsShift: wantsShift,
        wantsMeta: wantsMeta,
        keyPart: keyPart
    };
}

function eventMatchesShortcut(parsed, e) {
    if (!parsed || !parsed.keyPart) return false;

    if (!!e.ctrlKey !== parsed.wantsCtrl) return false;
    if (!!e.altKey !== parsed.wantsAlt) return false;
    if (!!e.shiftKey !== parsed.wantsShift) return false;
    if (!!e.metaKey !== parsed.wantsMeta) return false;

    var k = (e.key || "").toLowerCase();
    var c = (e.code || "").toLowerCase();
    var kp = parsed.keyPart;

    if (kp === "space") {
        return k === " " || k === "space" || c === "space";
    }
    return k === kp || c === ("key" + kp) || c === kp;
}

window.setupClozeInteractions = function() {
    window.teardownClozeInteractions();

    const container = document.querySelector(".anki-card-container");
    if (!container) {
        if (!window._setupClozeRetryCount) window._setupClozeRetryCount = 0;
        if (window._setupClozeRetryCount < 10) {
            window._setupClozeRetryCount++;
            setTimeout(window.setupClozeInteractions, 50);
        }
        return;
    }
    window._setupClozeRetryCount = 0;
    
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
        shortcutInfo: "H",
        shortcutImage: "G",
        actionBindings: { reveal: [{ type: "wheel", value: "down" }] }
    };

    config.activeClozeIdx = parseInt(config.activeClozeIdx || 0, 10);

    // Apply reveal transition speed strictly to card container
    container.style.setProperty('--reveal-speed', (config.revealSpeed || 120) + "ms");
    
    if (config.clozeRevealedCustom && config.clozeRevealedColor) {
        container.style.setProperty('--cloze-revealed-color', config.clozeRevealedColor);
    } else {
        container.style.setProperty('--cloze-revealed-color', 'inherit');
    }
    
    if (config.clozeHiddenCustom && config.clozeHiddenColor) {
        container.style.setProperty('--cloze-hidden-color', config.clozeHiddenColor);
    } else {
        container.style.setProperty('--cloze-hidden-color', 'inherit');
    }

    // Apply font family and font size strictly to card container
    var fontFamilies = {
        "System Default": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "Arial": "Arial, Helvetica, sans-serif",
        "Georgia": "Georgia, Cambria, 'Times New Roman', Times, serif",
        "Times New Roman": "'Times New Roman', Times, Georgia, serif",
        "Courier New": "'Courier New', Courier, monospace",
        "Segoe UI": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "SF Pro": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', sans-serif",
        "Comic Sans MS": "'Comic Sans MS', 'Comic Sans', cursive, sans-serif"
    };

    var chosenFont = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif";
    if (config.fontFamily && fontFamilies[config.fontFamily]) {
        chosenFont = fontFamilies[config.fontFamily];
    } else if (config.fontFamily && config.fontFamily !== "System Default") {
        chosenFont = (config.fontFamily.indexOf(' ') !== -1 && config.fontFamily.indexOf('"') === -1)
            ? '"' + config.fontFamily + '", sans-serif'
            : config.fontFamily;
    }
    container.style.setProperty('--card-font-family', chosenFont);
    container.style.fontFamily = chosenFont;

    var chosenFontSize = (config.fontSize ? config.fontSize : 18) + "px";
    container.style.setProperty('--card-font-size', chosenFontSize);
    container.style.fontSize = chosenFontSize;

    var frontEl = container.querySelector(".minimal-front");
    if (frontEl) {
        frontEl.style.fontFamily = chosenFont;
        frontEl.style.fontSize = chosenFontSize;
    }
    var backEl = container.querySelector(".minimal-back");
    if (backEl) {
        backEl.style.fontFamily = chosenFont;
        backEl.style.fontSize = chosenFontSize;
    }
    
    const isBackCard = document.getElementById("answer-splitter") !== null ||
                       document.querySelector(".minimal-back") !== null;

    // Apply layout and positioning modes strictly to .anki-card-container
    const applyCentering = function() {
        const cardContainer = document.querySelector(".anki-card-container");
        if (!cardContainer) return;

        // 1. Controls Position (.ctrl bar: Audio + Image + Info)
        const ctrlEl = cardContainer.querySelector(".ctrl");
        if (ctrlEl) {
            ctrlEl.classList.remove(
                "pos-top-right", "pos-top-left", "pos-bottom-right", "pos-bottom-left",
                "ctrl-top-right", "ctrl-top-left", "ctrl-bottom-right", "ctrl-bottom-left"
            );
            const cpos = config.controlsPosition || "top-right";
            ctrlEl.classList.add("pos-" + cpos);

            // Platform Detection: Desktop / AnkiMobile / AnkiDroid vs AnkiWeb
            const isAnkiWeb = (function() {
                try {
                    const host = (window.location && window.location.hostname) ? window.location.hostname.toLowerCase() : "";
                    const href = (window.location && window.location.href) ? window.location.href.toLowerCase() : "";
                    if (host.indexOf("ankiweb") !== -1 || host.indexOf("ankiuser") !== -1 || href.indexOf("ankiweb") !== -1 || href.indexOf("ankiuser") !== -1) {
                        return true;
                    }
                } catch (e) {}
                return false;
            })();

            if (isAnkiWeb) {
                cardContainer.classList.add("is-ankiweb");
            } else {
                cardContainer.classList.remove("is-ankiweb");
            }

            // Clear any manual inline styles so CSS classes have full control
            ctrlEl.style.position = "";
            ctrlEl.style.top = "";
            ctrlEl.style.right = "";
            ctrlEl.style.bottom = "";
            ctrlEl.style.left = "";
            ctrlEl.style.alignItems = "";
        }

        // 2. Card Position Settings (Vertical & Horizontal)
        const vpos = config.cardVerticalPosition || (config.mitcentMode ? "center" : (config.centerMode ? "center" : "top"));
        const halign = config.cardHorizontalAlign || (config.centerMode ? "center" : "left");

        cardContainer.classList.remove(
            "vpos-top", "vpos-center", "vpos-bottom",
            "halign-left", "halign-center", "halign-right",
            "center-mode", "mitcent-mode", "left-mode"
        );
        cardContainer.classList.add("vpos-" + vpos, "halign-" + halign);
        cardContainer.setAttribute("data-vpos", vpos);
        cardContainer.setAttribute("data-halign", halign);

        // Backwards-compatible support for legacy styles
        if (halign === "center" && vpos === "center") {
            cardContainer.classList.add("center-mode", "mitcent-mode");
        } else if (halign === "center") {
            cardContainer.classList.add("center-mode");
        } else if (halign === "left") {
            cardContainer.classList.add("left-mode");
        }

        // Clear inline styles so CSS classes handle sizing & alignment cleanly
        cardContainer.style.alignItems = "";
        cardContainer.style.textAlign = "";
        cardContainer.style.justifyContent = "";
        cardContainer.style.minHeight = "";
        cardContainer.style.marginTop = "";
        cardContainer.style.marginBottom = "";
        cardContainer.style.marginLeft = "";
        cardContainer.style.marginRight = "";
        cardContainer.style.maxWidth = "";
        cardContainer.style.width = "";
        cardContainer.style.paddingTop = "";
        cardContainer.style.paddingBottom = "";
        cardContainer.style.paddingLeft = "";
        cardContainer.style.paddingRight = "";
    };
    applyCentering();
    setTimeout(applyCentering, 0);
    setTimeout(applyCentering, 100);

    // Extra area initial state (Sentence Builder system)
    const extraArea = document.getElementById("extra-area");
    const infoBtn = document.getElementById("info-toggle-btn");
    const imgBtn = document.getElementById("image-toggle-btn");
    if (extraArea) {
        extraArea.innerHTML = "";
        extraArea.removeAttribute("data-mode");
        if (infoBtn) infoBtn.classList.remove("active");
        if (imgBtn) imgBtn.classList.remove("active");

        if (config.showInfoByDefault) {
            window.toggleInfo();
        }
    }

    const rawEl = document.getElementById("raw-front");
    const frontContentEl = document.querySelector(".minimal-front");
    
    // Multi-platform enrichment: Parse raw Front if available
    if (rawEl && frontContentEl && !frontContentEl.hasAttribute("data-interactive-rendered")) {
        frontContentEl.setAttribute("data-interactive-rendered", "true");
        let rawText = rawEl.innerHTML || rawEl.textContent || "";
        
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
        
        let activeIdx = 1;
        if (config.activeClozeIdx) {
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
    
    // Select all clozes
    const clozes = document.querySelectorAll(".cloze");
    
    clozes.forEach(function(cloze) {
        const text = (cloze.innerText || cloze.textContent || "").trim();
        const isBlank = cloze.hasAttribute("data-answer") || text.includes("...") || (text.startsWith("[") && text.endsWith("]"));
        
        const clozeIdxAttr = cloze.getAttribute("data-cloze-idx");
        let isActive = false;
        if (clozeIdxAttr && config.activeClozeIdx) {
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
                if (config.clozeRevealedCustom && config.clozeRevealedColor) {
                    cloze.style.color = config.clozeRevealedColor;
                }
            } else {
                cloze.setAttribute("data-state", "hidden");
                if (!cloze.getAttribute("data-original-text")) {
                    cloze.setAttribute("data-original-text", cloze.innerHTML);
                }
                if (config.clozeHiddenCustom && config.clozeHiddenColor) {
                    cloze.style.color = config.clozeHiddenColor;
                }
            }
        } else {
            cloze.classList.add("passive");
            cloze.classList.remove("active");
            cloze.setAttribute("data-state", "revealed");
            cloze.style.color = "";
        }
        
        if (config.enableClickReveal) {
            if (!cloze.hasAttribute("data-has-listener")) {
                cloze.setAttribute("data-has-listener", "true");
                
                var lastTouchTime = 0;
                const handleInteract = function(e) {
                    if (e.type === "touchend") {
                        lastTouchTime = Date.now();
                    } else if (e.type === "click") {
                        if (Date.now() - lastTouchTime < 450) {
                            return; // Suppress simulated ghost click following touchend on mobile
                        }
                    }
                    e.stopPropagation();
                    e.preventDefault();
                    
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
    
    // -----------------------------------------------------------------------
    // Production-Grade Keyboard & Input Handling
    // -----------------------------------------------------------------------
    window._sqKeyHandler = function(e) {
        // 1. Only handle keys during review of Sequential Cloze cards
        var currentContainer = document.querySelector(".anki-card-container");
        if (!currentContainer) {
            window.teardownClozeInteractions();
            return;
        }

        // 2. Never block typing in input, textarea, select, contenteditable, or form fields
        if (isEditingField(e.target) || isEditingField(document.activeElement)) {
            return;
        }

        var rollShortcut = config.shortcutRoll || "Space";
        var revealAllShortcut = config.shortcutRevealAll || "Shift + Space";
        var infoShortcut = config.shortcutInfo || "H";
        var imgShortcut = config.shortcutImage || "G";

        var parsedRevealAll = parseShortcut(revealAllShortcut);
        var parsedRoll = parseShortcut(rollShortcut);
        var parsedInfo = parseShortcut(infoShortcut);
        var parsedImage = parseShortcut(imgShortcut);

        // 3. Reveal All Clozes (Default: Shift + Space)
        if (eventMatchesShortcut(parsedRevealAll, e)) {
            var activeHiddenClozes = currentContainer.querySelectorAll(".cloze.active[data-state='hidden']");
            if (activeHiddenClozes && activeHiddenClozes.length > 0) {
                e.preventDefault();
                activeHiddenClozes.forEach(function(c) {
                    window.revealCloze(c);
                });
                return;
            }
            // No hidden clozes remain; allow natural event flow
            return;
        }

        // 4. Roll / Next Cloze (Default: Space)
        // Space / Enter special care:
        // Only use Space for "next cloze" while there are still hidden clozes.
        // When all clozes are revealed, allow normal Anki behavior (flip / answer) to work!
        if (eventMatchesShortcut(parsedRoll, e)) {
            var hiddenCloze = currentContainer.querySelector(".cloze.active[data-state='hidden']");
            if (hiddenCloze) {
                e.preventDefault();
                window.revealCloze(hiddenCloze);
                return;
            }
            // All clozes revealed or not on question: do NOT preventDefault or trigger pycmd!
            // Let Anki's native reviewer handle Space to flip or grade.
            return;
        }

        // 5. Info toggle shortcut (Default: H)
        if (eventMatchesShortcut(parsedInfo, e)) {
            var rawInfo = document.getElementById("raw-info");
            var infoBtn = document.getElementById("info-toggle-btn");
            if (infoBtn || (rawInfo && rawInfo.innerHTML.trim())) {
                e.preventDefault();
                window.toggleInfo();
                return;
            }
            return;
        }

        // 6. Image toggle shortcut (Default: G)
        if (eventMatchesShortcut(parsedImage, e)) {
            var rawImg = document.getElementById("raw-image");
            var imgBtn = document.getElementById("image-toggle-btn");
            if (imgBtn || (rawImg && rawImg.innerHTML.trim())) {
                e.preventDefault();
                window.toggleCardImage();
                return;
            }
            return;
        }

        // 7. Custom input bindings (if configured for keys)
        var actionBindings = config.actionBindings || {};
        for (var action in actionBindings) {
            var bList = actionBindings[action];
            if (!bList || !bList.length) continue;
            for (var bIdx = 0; bIdx < bList.length; bIdx++) {
                var b = bList[bIdx];
                if (b && b.type === "key" && b.value) {
                    var parsedBinding = parseShortcut(b.value);
                    if (eventMatchesShortcut(parsedBinding, e)) {
                        if (action === "reveal") {
                            var nextHidden = currentContainer.querySelector(".cloze.active[data-state='hidden']");
                            if (nextHidden) {
                                e.preventDefault();
                                window.revealCloze(nextHidden);
                                return;
                            }
                            return;
                        } else {
                            e.preventDefault();
                            window.performAction(action);
                            return;
                        }
                    }
                }
            }
        }

        // 8. If the key does not belong to this add-on, do nothing and let it propagate!
    };

    document.addEventListener("keydown", window._sqKeyHandler, false);

    // Optional mouse / wheel bindings (only attached if configured)
    var actionBindings = config.actionBindings || {};
    var hasWheelBinding = false;
    var hasMouseBinding = false;
    for (var act in actionBindings) {
        var bl = actionBindings[act];
        if (bl) {
            for (var bi = 0; bi < bl.length; bi++) {
                if (bl[bi].type === "wheel") hasWheelBinding = true;
                if (bl[bi].type === "mouse_button") hasMouseBinding = true;
            }
        }
    }

    if (hasWheelBinding) {
        var _ibWheelLocked = false;
        window._sqWheelHandler = function(e) {
            var cContainer = document.querySelector(".anki-card-container");
            if (!cContainer || _ibWheelLocked) return;
            var dir = e.deltaY > 0 ? "down" : (e.deltaY < 0 ? "up" : null);
            if (!dir) return;

            var matched = false;
            for (var a in actionBindings) {
                if (bindingListMatches(actionBindings[a], "wheel", dir)) {
                    matched = true;
                    break;
                }
            }
            if (!matched) return;

            var nextHidden = cContainer.querySelector(".cloze.active[data-state='hidden']");
            if (!nextHidden) return; // Allow normal scrolling if no hidden clozes remain

            e.preventDefault();
            _ibWheelLocked = true;
            setTimeout(function() { _ibWheelLocked = false; }, 400);
            window.revealCloze(nextHidden);
        };
        document.addEventListener("wheel", window._sqWheelHandler, { passive: false });
    }

    if (hasMouseBinding) {
        window._sqMouseHandler = function(e) {
            var cContainer = document.querySelector(".anki-card-container");
            if (!cContainer) return;
            var btn = mouseButtonName(e.button);
            if (!btn) return;
            if (e.target && typeof e.target.closest === "function" && (e.target.closest(".cloze") || e.target.closest(".ctrl"))) return;

            for (var a in actionBindings) {
                if (bindingListMatches(actionBindings[a], "mouse_button", btn)) {
                    if (a === "reveal") {
                        var nextHidden = cContainer.querySelector(".cloze.active[data-state='hidden']");
                        if (nextHidden) {
                            e.preventDefault();
                            window.revealCloze(nextHidden);
                            return;
                        }
                    } else {
                        e.preventDefault();
                        window.performAction(a);
                        return;
                    }
                }
            }
        };
        document.addEventListener("mousedown", window._sqMouseHandler, false);
    }
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
        const conf = window.MINIMAL_CLOZE_CONFIG || {};
        const animDelay = Math.max(20, Math.min(150, Math.round((conf.revealSpeed || 120) * 0.5)));
        setTimeout(function() {
            const actualAnswer = el.getAttribute("data-answer");
            if (actualAnswer) {
                el.innerHTML = actualAnswer;
            } else {
                el.innerHTML = el.innerHTML.replace(/\[|\]/g, '');
            }
            el.setAttribute("data-state", "revealed");
            if (conf.clozeRevealedCustom && conf.clozeRevealedColor) {
                el.style.color = conf.clozeRevealedColor;
            } else {
                el.style.color = "";
            }
            el.style.opacity = "1";
            window.updateClozeSequencing();
            
            const remainingHidden = document.querySelectorAll(".cloze.active[data-state='hidden']");
            const shouldAutoReveal = (conf.autoRevealBack !== undefined) ? conf.autoRevealBack : true;
            if (remainingHidden.length === 0 && shouldAutoReveal) {
                if (window.pycmd) {
                    window.pycmd("ans");
                } else if (typeof showAnswer === "function") {
                    showAnswer();
                }
            }
        }, animDelay);
    }
};

window.hideCloze = function(el) {
    if (el.getAttribute("data-state") === "revealed" && el.classList.contains("active")) {
        el.style.opacity = "0";
        const conf = window.MINIMAL_CLOZE_CONFIG || {};
        const animDelay = Math.max(20, Math.min(150, Math.round((conf.revealSpeed || 120) * 0.5)));
        setTimeout(function() {
            const originalText = el.getAttribute("data-original-text") || "[...]";
            el.innerHTML = originalText;
            el.setAttribute("data-state", "hidden");
            if (conf.clozeHiddenCustom && conf.clozeHiddenColor) {
                el.style.color = conf.clozeHiddenColor;
            } else {
                el.style.color = "";
            }
            el.style.opacity = "1";
            window.updateClozeSequencing();
        }, animDelay);
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

// Auto-execute initialization for mobile (AnkiMobile / AnkiDroid) and standalone contexts
if (typeof window.setupClozeInteractions === "function") {
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function() {
            window.setupClozeInteractions();
        });
    } else {
        window.setupClozeInteractions();
    }
    setTimeout(function() {
        if (typeof window.setupClozeInteractions === "function") {
            window.setupClozeInteractions();
        }
    }, 40);
    setTimeout(function() {
        if (typeof window.setupClozeInteractions === "function") {
            window.setupClozeInteractions();
        }
    }, 150);
}

