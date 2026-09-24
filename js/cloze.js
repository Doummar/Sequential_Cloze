// Sequential Cloze - Reviewer Frontend Script (with .ctrl + .ibtn system)

// Toggle Image: Injects content into #extra-area (Sentence Builder system)
window.toggleCardImage = function(event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    const container = document.querySelector(".anki-card-container");
    if (!container) return;
    const extraArea = container.querySelector("#extra-area");
    const rawImage = container.querySelector("#raw-image");
    const btn = container.querySelector("#image-toggle-btn");
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

        const infoBtn = container.querySelector("#info-toggle-btn");
        if (infoBtn) infoBtn.classList.remove("active");
    }
};

// Toggle Info: Injects content into #extra-area (Sentence Builder system)
window.toggleInfo = function(event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    const container = document.querySelector(".anki-card-container");
    if (!container) return;
    const extraArea = container.querySelector("#extra-area");
    const rawInfo = container.querySelector("#raw-info");
    const btn = container.querySelector("#info-toggle-btn");
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

        const imgBtn = container.querySelector("#image-toggle-btn");
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
    const container = document.querySelector(".anki-card-container");
    if (!container) return;
    if (action === "reveal") {
        var hiddenCloze = container.querySelector(".cloze.active[data-state='hidden']");
        if (hiddenCloze) {
            window.revealCloze(hiddenCloze);
        }
    } else if (action === "image") {
        window.toggleCardImage();
    } else if (action === "info") {
        window.toggleInfo();
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
        // STRICT SCOPING: Not a Sequential Cloze card - immediately exit
        return;
    }
    
    const config = window.MINIMAL_CLOZE_CONFIG || {
        reviewMode: "sequential_reveal",
        contextBefore: 1,
        contextAfter: 0,
        contextMaskSubsequent: true,
        backContextBefore: "all",
        backContextAfter: "all",
        cardVerticalPosition: "top",
        cardHorizontalAlign: "center",
        controlsPosition: "top-right",
        fontFamily: "System Default",
        fontSize: 20,
        boldClozeText: false,
        bold_cloze_text: false,
        showInfoByDefault: false,
        enableClickReveal: true,
        centerMode: true,
        mitcentMode: false,
        revealSpeed: 120,
        darkCompatibility: true,
        autoRevealBack: false,
        clozeRevealedCustom: false,
        clozeRevealedColor: "#c00000",
        clozeHiddenCustom: false,
        clozeHiddenColor: "#0284c7",
        activeClozeIdx: 1,
        shortcutRoll: "Space",
        shortcutRevealAll: "Shift + Space",
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
        container.style.removeProperty('--cloze-revealed-color');
    }
    
    if (config.clozeHiddenCustom && config.clozeHiddenColor) {
        container.style.setProperty('--cloze-hidden-color', config.clozeHiddenColor);
    } else {
        container.style.removeProperty('--cloze-hidden-color');
    }

    // Bold cloze text: Container-level class when enabled
    if (config.boldClozeText || config.bold_cloze_text) {
        container.classList.add("bold-cloze");
    } else {
        container.classList.remove("bold-cloze");
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

    var chosenFontSize = (config.fontSize ? config.fontSize : 20) + "px";
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
    
    const isBackCard = container.querySelector("#answer-splitter") !== null ||
                       container.querySelector(".minimal-back") !== null;

    // Apply layout and positioning modes strictly to .anki-card-container
    const applyCentering = function() {
        const cardContainer = container;
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
    const extraArea = container.querySelector("#extra-area");
    const infoBtn = container.querySelector("#info-toggle-btn");
    const imgBtn = container.querySelector("#image-toggle-btn");
    if (extraArea) {
        extraArea.innerHTML = "";
        extraArea.removeAttribute("data-mode");
        if (infoBtn) infoBtn.classList.remove("active");
        if (imgBtn) imgBtn.classList.remove("active");

        if (config.showInfoByDefault) {
            window.toggleInfo();
        }
    }

    const rawEl = container.querySelector("#raw-front");
    const frontContentEl = container.querySelector(".minimal-front");
    
    // Multi-platform enrichment: Parse raw Front if available (Sequential Reveal mode)
    if (config.reviewMode !== "sequential_context" && rawEl && frontContentEl) {
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
            activeIdx = parseInt(config.activeClozeIdx, 10);
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

        let cardMatches = rawClozes.filter(function(rc) { return rc.num === activeIdx; });
        if (cardMatches.length === 0) {
            cardMatches = rawClozes;
        }

        const clozeSpans = container.querySelectorAll(".cloze");
        clozeSpans.forEach(function(clozeSpan, idx) {
            const cardMatch = (clozeSpans.length === rawClozes.length && idx < rawClozes.length)
                ? rawClozes[idx]
                : ((idx < cardMatches.length) ? cardMatches[idx] : (idx < rawClozes.length ? rawClozes[idx] : null));

            if (cardMatch) {
                if (!clozeSpan.getAttribute("data-answer")) {
                    clozeSpan.setAttribute("data-answer", cardMatch.answer);
                }
                if (cardMatch.hint && !clozeSpan.getAttribute("data-hint")) {
                    clozeSpan.setAttribute("data-hint", cardMatch.hint);
                }
                if (!clozeSpan.getAttribute("data-cloze-idx")) {
                    clozeSpan.setAttribute("data-cloze-idx", String(cardMatch.num));
                }
            }
            const hint = clozeSpan.getAttribute("data-hint") || (cardMatch ? cardMatch.hint : "");
            const canonicalMarker = hint ? "[" + hint + "]" : "[...]";
            clozeSpan.setAttribute("data-original-text", canonicalMarker);

            if (isBackCard) {
                clozeSpan.setAttribute("data-state", "revealed");
                clozeSpan.classList.add("revealed");
            } else if (clozeSpan.getAttribute("data-state") !== "revealed") {
                clozeSpan.setAttribute("data-state", "hidden");
                clozeSpan.classList.add("active");
                clozeSpan.classList.remove("revealed");
                clozeSpan.innerHTML = canonicalMarker;
            }
        });
    }

    // Multi-platform enrichment: Parse raw Front if available (Strictly for Sequential Context mode)
    if (config.reviewMode === "sequential_context" && rawEl && frontContentEl && !frontContentEl.hasAttribute("data-interactive-rendered")) {
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

        const orderedClozeNums = [];
        for (let i = 0; i < rawClozes.length; i++) {
            if (orderedClozeNums.indexOf(rawClozes[i].num) === -1) {
                orderedClozeNums.push(rawClozes[i].num);
            }
        }
        const activePos = orderedClozeNums.indexOf(activeIdx);
        
        const isContextMode = (config.reviewMode === "sequential_context");
        if (isContextMode) {
            const cardContainer = document.querySelector(".anki-card-container");
            if (cardContainer) {
                cardContainer.classList.add("mode-context");
            }
        }

        function balanceHtmlTags(html) {
            const voidTags = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]);
            const tagRegex = /<\s*(\/)?\s*([a-zA-Z0-9]+)(?:\s+[^>]*)?>/g;
            const stack = [];
            let match;
            while ((match = tagRegex.exec(html)) !== null) {
                const isClosing = Boolean(match[1]);
                const tagName = match[2].toLowerCase();
                if (voidTags.has(tagName) || match[0].endsWith("/>")) continue;
                if (!isClosing) {
                    stack.push(tagName);
                } else {
                    const idx = stack.lastIndexOf(tagName);
                    if (idx !== -1) {
                        stack.splice(idx);
                    }
                }
            }
            let closing = "";
            for (let i = stack.length - 1; i >= 0; i--) {
                closing += "</" + stack[i] + ">";
            }
            return html + closing;
        }

        let processedRawText = rawText;
        if (isContextMode && !isBackCard && (config.contextMaskSubsequent !== false)) {
            const ca = (config.contextAfter !== undefined) ? config.contextAfter : 0;
            if (ca !== "all") {
                const caNum = (typeof ca === "number" ? ca : (parseInt(ca, 10) || 0));
                let maxAllowedOrd = activeIdx + caNum;
                if (activePos !== -1) {
                    const allowedIdx = Math.min(activePos + caNum, orderedClozeNums.length - 1);
                    maxAllowedOrd = orderedClozeNums[allowedIdx];
                }
                let lastEnd = null;
                const cutoffRegex = /\{\{c(\d+)::(.*?)\}\}/gi;
                let cm;
                while ((cm = cutoffRegex.exec(rawText)) !== null) {
                    const cNum = parseInt(cm[1], 10);
                    if (cNum <= maxAllowedOrd) {
                        lastEnd = cm.index + cm[0].length;
                    }
                }
                if (lastEnd !== null && lastEnd < rawText.length) {
                    processedRawText = balanceHtmlTags(rawText.slice(0, lastEnd).trimEnd());
                }
            }
        } else if (isContextMode && isBackCard) {
            const bca = (config.backContextAfter !== undefined) ? config.backContextAfter : ((config.back_context_after !== undefined) ? config.back_context_after : "all");
            if (bca !== "all") {
                const bcaNum = (typeof bca === "number" ? bca : (parseInt(bca, 10) || 0));
                let maxAllowedOrd = activeIdx + bcaNum;
                if (activePos !== -1) {
                    const allowedIdx = Math.min(activePos + bcaNum, orderedClozeNums.length - 1);
                    maxAllowedOrd = orderedClozeNums[allowedIdx];
                }
                let lastEnd = null;
                const cutoffRegex = /\{\{c(\d+)::(.*?)\}\}/gi;
                let cm;
                while ((cm = cutoffRegex.exec(rawText)) !== null) {
                    const cNum = parseInt(cm[1], 10);
                    if (cNum <= maxAllowedOrd) {
                        lastEnd = cm.index + cm[0].length;
                    }
                }
                if (lastEnd !== null && lastEnd < rawText.length) {
                    processedRawText = balanceHtmlTags(rawText.slice(0, lastEnd).trimEnd());
                }
            }
        }

        const enrichedHtml = processedRawText.replace(/\{\{c(\d+)::(.*?)\}\}/gi, function(match, clNumStr, content) {
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
            
            if (isContextMode) {
                if (isBackCard) {
                    if (isActive) {
                        return '<span class="cloze active current-cloze revealed" data-cloze-idx="' + clNum + '" data-answer="' + safeAnswer + '" data-hint="' + safeHint + '" data-state="revealed" style="pointer-events: auto !important;">' + answer + '</span>';
                    }
                    const bcbRaw = (config.backContextBefore !== undefined) ? config.backContextBefore : config.back_context_before;
                    const bcb = (bcbRaw === "all" || bcbRaw === undefined) ? (bcbRaw || "all") : (typeof bcbRaw === "number" ? bcbRaw : parseInt(bcbRaw, 10));
                    const bcaRaw = (config.backContextAfter !== undefined) ? config.backContextAfter : config.back_context_after;
                    const bca = (bcaRaw === "all" || bcaRaw === undefined) ? (bcaRaw || "all") : (typeof bcaRaw === "number" ? bcaRaw : parseInt(bcaRaw, 10));
                    
                    const pos = orderedClozeNums.indexOf(clNum);
                    const hasPositions = (pos !== -1 && activePos !== -1);
                    const isBefore = hasPositions ? (pos < activePos) : (clNum < activeIdx);
                    
                    if (isBefore) {
                        const prevDist = hasPositions ? (activePos - pos) : (activeIdx - clNum);
                        const inContext = (bcb === "all") || (typeof bcb === "number" && bcb >= 0 && prevDist <= bcb);
                        if (inContext) {
                            return '<span class="cloze-context cloze-context-prev" data-cloze-idx="' + clNum + '">' + answer + '</span>';
                        }
                        return "";
                    } else {
                        const afterDist = hasPositions ? (pos - activePos) : (clNum - activeIdx);
                        const inContextAfter = (bca === "all") || (typeof bca === "number" && bca >= 0 && afterDist <= bca);
                        if (inContextAfter) {
                            return '<span class="cloze-context cloze-context-after" data-cloze-idx="' + clNum + '">' + answer + '</span>';
                        }
                        return "";
                    }
                } else {
                    // Front side in Sequential Context
                    if (isActive) {
                        return '<span class="cloze active current-cloze" data-cloze-idx="' + clNum + '" data-answer="' + safeAnswer + '" data-hint="' + safeHint + '" data-state="hidden" data-original-text="' + originalText + '" style="pointer-events: auto !important; cursor: pointer !important;">' + originalText + '</span>';
                    }
                    const cbRaw = (config.contextBefore !== undefined) ? config.contextBefore : config.context_before;
                    const cb = (cbRaw === "all") ? "all" : (typeof cbRaw === "number" ? cbRaw : (parseInt(cbRaw, 10) || 1));
                    const caRaw = (config.contextAfter !== undefined) ? config.contextAfter : config.context_after;
                    const ca = (caRaw === "all") ? "all" : (typeof caRaw === "number" ? caRaw : (parseInt(caRaw, 10) || 0));

                    const pos = orderedClozeNums.indexOf(clNum);
                    const hasPositions = (pos !== -1 && activePos !== -1);
                    const isBefore = hasPositions ? (pos < activePos) : (clNum < activeIdx);

                    if (isBefore) {
                        const prevDist = hasPositions ? (activePos - pos) : (activeIdx - clNum);
                        const inContext = (cb === "all") || (typeof cb === "number" && cb >= 0 && prevDist <= cb);
                        if (inContext) {
                            return '<span class="cloze-context cloze-context-prev" data-cloze-idx="' + clNum + '">' + answer + '</span>';
                        }
                        return "";
                    } else {
                        const afterDist = hasPositions ? (pos - activePos) : (clNum - activeIdx);
                        const inContextAfter = (ca === "all") || (typeof ca === "number" && ca >= 0 && afterDist <= ca);
                        if (inContextAfter) {
                            return '<span class="cloze-context cloze-context-after" data-cloze-idx="' + clNum + '">' + answer + '</span>';
                        }
                        return "";
                    }
                }
            }
            return "";
        });
        
        let cleanedHtml = enrichedHtml.replace(/<li\b[^>]*>\s*(?:[•\-*]|\d+[\.\)])?\s*<\/li>/gi, "")
                                     .replace(/<(div|p)\b[^>]*>\s*(?:[•\-*]|\d+[\.\)])?\s*<\/\1>/gi, "")
                                     .replace(/(?:^|\n)\s*(?:[•\-*]|\d+[\.\)])?\s*<br\s*\/?>/gi, "")
                                     .replace(/[ \t]{2,}/g, " ");
        frontContentEl.innerHTML = cleanedHtml;

        if (isContextMode && !isBackCard) {
            const maskedNext = frontContentEl.querySelectorAll(".cloze-context-next-masked");
            maskedNext.forEach(function(el) {
                const li = el.closest("li");
                if (li) {
                    const clone = li.cloneNode(true);
                    const subMasks = clone.querySelectorAll(".cloze-context-next-masked");
                    subMasks.forEach(function(sm) { sm.remove(); });
                    if ((clone.textContent || "").trim() === "") {
                        li.style.display = "none";
                    }
                }
            });
        }
    }
    
    const cardContainer = container;
    if (cardContainer) {
        if (config.reviewMode === "sequential_context") {
            cardContainer.classList.add("mode-context");
        } else {
            cardContainer.classList.remove("mode-context");
        }
    }

    // Select all clozes strictly within this card container
    const clozes = container.querySelectorAll(".cloze");
    
    clozes.forEach(function(cloze) {
        const text = (cloze.innerText || cloze.textContent || "").trim();
        const isBlank = cloze.hasAttribute("data-answer") || text.includes("...") || text.includes("…") || (text.startsWith("[") && text.endsWith("]")) || cloze.classList.contains("cloze");
        
        let isActive = false;
        if (config.reviewMode === "sequential_context") {
            const clozeIdxAttr = cloze.getAttribute("data-cloze-idx");
            if (clozeIdxAttr && config.activeClozeIdx) {
                isActive = (parseInt(clozeIdxAttr, 10) === config.activeClozeIdx);
            } else {
                isActive = isBlank || cloze.classList.contains("active");
            }
        } else {
            // SEQUENTIAL REVEAL: All cloze blanks start as active and hidden as [...] on front side
            isActive = true;
        }
        
        const hint = cloze.getAttribute("data-hint") || "";
        const canonicalMarker = hint ? "[" + hint + "]" : "[...]";
        
        if (isActive) {
            cloze.classList.add("active");
            cloze.classList.remove("passive");
            
            if (isBackCard) {
                var currentTxt = (cloze.innerText || cloze.textContent || cloze.innerHTML || "").trim();
                var isExplicitlyHidden = (cloze.getAttribute("data-state") === "hidden") || currentTxt === "[...]" || currentTxt === "..." || currentTxt === canonicalMarker;
                var shouldBeRevealed = !isExplicitlyHidden || (config.autoRevealBack !== false);

                if (!cloze.getAttribute("data-original-text")) {
                    cloze.setAttribute("data-original-text", canonicalMarker);
                }

                if (shouldBeRevealed) {
                    cloze.setAttribute("data-state", "revealed");
                    cloze.classList.add("revealed");
                    if (!cloze.getAttribute("data-answer") && currentTxt !== "[...]" && currentTxt !== "...") {
                        cloze.setAttribute("data-answer", cloze.innerHTML);
                    }
                    if (config.clozeRevealedCustom && config.clozeRevealedColor) {
                        cloze.style.color = config.clozeRevealedColor;
                    } else {
                        cloze.style.color = "";
                        cloze.style.removeProperty("color");
                    }
                } else {
                    cloze.setAttribute("data-state", "hidden");
                    cloze.classList.remove("revealed");
                    cloze.innerHTML = canonicalMarker;
                    if (config.clozeHiddenCustom && config.clozeHiddenColor) {
                        cloze.style.color = config.clozeHiddenColor;
                    } else {
                        cloze.style.color = "";
                        cloze.style.removeProperty("color");
                    }
                }
            } else {
                var currentState = cloze.getAttribute("data-state");
                if (currentState === "revealed") {
                    cloze.classList.add("revealed");
                    if (config.clozeRevealedCustom && config.clozeRevealedColor) {
                        cloze.style.color = config.clozeRevealedColor;
                    } else {
                        cloze.style.color = "";
                        cloze.style.removeProperty("color");
                    }
                } else {
                    cloze.setAttribute("data-state", "hidden");
                    cloze.classList.remove("revealed");
                    cloze.setAttribute("data-original-text", canonicalMarker);
                    if (config.reviewMode !== "sequential_context") {
                        // Unconditionally canonical marker [...] on front side: NO "..." EVER
                        cloze.innerHTML = canonicalMarker;
                    }
                    if (config.clozeHiddenCustom && config.clozeHiddenColor) {
                        cloze.style.color = config.clozeHiddenColor;
                    } else {
                        cloze.style.color = "";
                        cloze.style.removeProperty("color");
                    }
                }
            }
            cloze.style.pointerEvents = "auto";
            cloze.style.touchAction = "manipulation";
            cloze.style.cursor = "pointer";
        } else {
            cloze.classList.add("passive");
            cloze.classList.remove("active");
            cloze.setAttribute("data-state", "revealed");
            cloze.style.color = "";
        }
        
        // Touch & Click Interactions:
        // Clicking/tapping [...] must reliably reveal the cloze on desktop and mobile!
        var isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (window.innerWidth <= 768) || /android|iphone|ipad|ipod|mobile/i.test(navigator.userAgent || "");
        var shouldAttachListener = true;

        if (shouldAttachListener) {
            if (!cloze.hasAttribute("data-has-listener")) {
                cloze.setAttribute("data-has-listener", "true");
                
                var lastTouchEndTime = 0;
                var touchStartX = 0;
                var touchStartY = 0;
                var touchDidMove = false;

                cloze.addEventListener("touchstart", function(e) {
                    if (e.touches && e.touches.length > 0) {
                        touchStartX = e.touches[0].clientX;
                        touchStartY = e.touches[0].clientY;
                        touchDidMove = false;
                    }
                }, { passive: true });

                cloze.addEventListener("touchmove", function(e) {
                    if (e.touches && e.touches.length > 0) {
                        var dx = Math.abs(e.touches[0].clientX - touchStartX);
                        var dy = Math.abs(e.touches[0].clientY - touchStartY);
                        if (dx > 24 || dy > 24) {
                            touchDidMove = true;
                        }
                    }
                }, { passive: true });

                cloze.addEventListener("touchcancel", function() {
                    touchDidMove = false;
                }, { passive: true });

                var handleInteract = function(e) {
                    if (e.type === "touchend") {
                        if (touchDidMove) {
                            return; // User was scrolling on mobile, do not reveal
                        }
                        lastTouchEndTime = Date.now();
                        window._lastTouchEndTime = lastTouchEndTime;
                    } else if (e.type === "click") {
                        if (Date.now() - lastTouchEndTime < 600) {
                            return; // Suppress simulated ghost click following touchend on mobile
                        }
                    }
                    if (e.stopPropagation) e.stopPropagation();
                    if (e.cancelable && e.preventDefault) e.preventDefault();
                    
                    var state = cloze.getAttribute("data-state");
                    var isRevealedState = (state === "revealed" || cloze.classList.contains("revealed"));
                    var currentText = (cloze.innerText || cloze.textContent || "").trim();
                    var origMarker = (cloze.getAttribute("data-original-text") || "[...]").trim();
                    
                    var isHidden = (state === "hidden") || (!isRevealedState) || (currentText === origMarker) || (currentText === "[...]") || (currentText === "...");

                    if (isHidden) {
                        window.revealCloze(cloze);
                    } else if (cloze.classList.contains("active")) {
                        window.hideCloze(cloze);
                    } else if (cloze.classList.contains("passive")) {
                        window.togglePassiveCloze(cloze);
                    }
                };
                
                cloze.addEventListener("touchend", handleInteract, { passive: false });
                cloze.addEventListener("click", handleInteract, false);
                
                cloze.addEventListener("dblclick", function(e) {
                    if (e.stopPropagation) e.stopPropagation();
                    if (e.cancelable && e.preventDefault) e.preventDefault();
                    if (cloze.classList.contains("active")) {
                        window.hideCloze(cloze);
                    }
                });
            }
        }
    });

    // Delegated container click fallback: guarantees clickability even if any node is refreshed
    if (!container.hasAttribute("data-has-delegated-cloze-click")) {
        container.setAttribute("data-has-delegated-cloze-click", "true");
        container.addEventListener("click", function(e) {
            var targetCloze = e.target && typeof e.target.closest === "function" ? e.target.closest(".cloze") : null;
            if (!targetCloze || !container.contains(targetCloze)) return;
            if (Date.now() - (window._lastTouchEndTime || 0) < 600) return;

            var state = targetCloze.getAttribute("data-state");
            var isRevealedState = (state === "revealed" || targetCloze.classList.contains("revealed"));
            var currentText = (targetCloze.innerText || targetCloze.textContent || "").trim();
            var origMarker = (targetCloze.getAttribute("data-original-text") || "[...]").trim();
            var isHidden = (state === "hidden") || (!isRevealedState) || (currentText === origMarker) || (currentText === "[...]") || (currentText === "...");

            if (isHidden) {
                window.revealCloze(targetCloze);
            } else if (targetCloze.classList.contains("active")) {
                window.hideCloze(targetCloze);
            } else if (targetCloze.classList.contains("passive")) {
                window.togglePassiveCloze(targetCloze);
            }
        }, false);
    }
    
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
            var rawInfo = currentContainer.querySelector("#raw-info");
            var infoBtn = currentContainer.querySelector("#info-toggle-btn");
            if (infoBtn || (rawInfo && rawInfo.innerHTML.trim())) {
                e.preventDefault();
                window.toggleInfo();
                return;
            }
            return;
        }

        // 6. Image toggle shortcut (Default: G)
        if (eventMatchesShortcut(parsedImage, e)) {
            var rawImg = currentContainer.querySelector("#raw-image");
            var imgBtn = currentContainer.querySelector("#image-toggle-btn");
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

            // Minimum delta threshold to suppress trackpad micro-movements and inertia drift
            var absDeltaY = Math.abs(e.deltaY);
            var minThreshold = e.deltaMode === 1 ? 1 : (e.deltaMode === 2 ? 1 : 20);
            if (absDeltaY < minThreshold) return;

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

    if (typeof window.updateClozeSequencing === "function") {
        window.updateClozeSequencing();
    }
};

window.updateClozeSequencing = function() {
    const container = document.querySelector(".anki-card-container");
    if (!container) return;
    const isBack = container.querySelector("#answer-splitter") !== null || container.querySelector(".minimal-back") !== null;
    const conf = window.MINIMAL_CLOZE_CONFIG || {};
    const isBold = !!(conf.boldClozeText || conf.bold_cloze_text);
    const activeIdx = conf.activeClozeIdx ? parseInt(conf.activeClozeIdx, 10) : 1;

    // Apply bold-cloze container class
    if (isBold) {
        container.classList.add("bold-cloze");
    } else {
        container.classList.remove("bold-cloze");
    }

    const allClozes = container.querySelectorAll(".cloze");
    allClozes.forEach(function(el) {
        el.classList.remove("current-cloze");
        el.removeAttribute("data-active-cloze");
    });

    // Apply font-weight and state strictly to cloze answers:
    // Only revealed cloze answers are bold (700) when isBold is true.
    // Context items (.cloze-context-prev, .cloze-context-after) and hidden markers stay 400.
    const allClozesList = container.querySelectorAll(".cloze");
    allClozesList.forEach(function(el) {
        const state = el.getAttribute("data-state");
        const currentText = (el.innerText || el.textContent || el.innerHTML || "").trim();
        const origMarker = (el.getAttribute("data-original-text") || "[...]").trim();
        const isRevealed = (state === "revealed" || el.classList.contains("revealed")) && (currentText !== origMarker && currentText !== "[...]" && currentText !== "...");

        if (isRevealed) {
            el.classList.add("revealed");
            el.setAttribute("data-state", "revealed");
            el.style.fontWeight = isBold ? "700" : "400";
        } else {
            el.classList.remove("revealed");
            el.setAttribute("data-state", "hidden");
            el.style.fontWeight = "400";
        }
        el.style.pointerEvents = "auto";
        el.style.cursor = "pointer";
    });

    const allContexts = container.querySelectorAll(".cloze-context, .cloze-context-prev, .cloze-context-after");
    allContexts.forEach(function(el) {
        el.style.fontWeight = "400";
    });

    let activeEl = null;

    if (!isBack) {
        // FRONT: The active cloze the user must guess
        const hiddenActive = container.querySelectorAll(".cloze.active[data-state='hidden']");
        if (hiddenActive.length > 0) {
            if (conf.reviewMode === "sequential_context") {
                for (let i = 0; i < hiddenActive.length; i++) {
                    const cidx = hiddenActive[i].getAttribute("data-cloze-idx");
                    if (cidx && parseInt(cidx, 10) === activeIdx) {
                        activeEl = hiddenActive[i];
                        break;
                    }
                }
                if (!activeEl) activeEl = hiddenActive[0];
            } else {
                // Sequential Reveal: The first unrevealed cloze is the one the user must guess
                activeEl = hiddenActive[0];
            }
        }
    } else {
        // BACK: Track active cloze matching activeIdx
        if (conf.reviewMode === "sequential_context") {
            const revealedClozes = container.querySelectorAll(".cloze.revealed, .cloze[data-state='revealed']");
            for (let i = 0; i < revealedClozes.length; i++) {
                const cidx = revealedClozes[i].getAttribute("data-cloze-idx");
                if (cidx && parseInt(cidx, 10) === activeIdx) {
                    activeEl = revealedClozes[i];
                    break;
                }
            }
            if (!activeEl && revealedClozes.length > 0) {
                activeEl = revealedClozes[0];
            }
        } else {
            // Sequential Reveal on Back: Find cloze matching activeIdx
            for (let i = 0; i < allClozes.length; i++) {
                const cidx = allClozes[i].getAttribute("data-cloze-idx");
                if (cidx && parseInt(cidx, 10) === activeIdx) {
                    activeEl = allClozes[i];
                    break;
                }
            }
            if (!activeEl && allClozes.length > 0) {
                activeEl = allClozes[0];
            }
        }
    }

    if (activeEl) {
        activeEl.classList.add("current-cloze");
        activeEl.setAttribute("data-active-cloze", "true");
    }
};

window.revealCloze = function(el) {
    const container = document.querySelector(".anki-card-container");
    if (!container || !el) return;

    var actualAnswer = el.getAttribute("data-answer");
    if (!actualAnswer) {
        // Multi-platform safety fallback: parse #raw-front if data-answer was missing on mobile
        const cardCont = el.closest(".anki-card-container") || container;
        const rawEl = cardCont ? cardCont.querySelector("#raw-front") : null;
        if (rawEl) {
            const rawText = rawEl.innerHTML || rawEl.textContent || "";
            const clozPattern = /\{\{c(\d+)::(.*?)\}\}/gi;
            const allAnswers = [];
            let m;
            while ((m = clozPattern.exec(rawText)) !== null) {
                const cParts = m[2].split("::");
                const ans = cParts.length > 1 ? cParts.slice(0, -1).join("::") : m[2];
                allAnswers.push(ans.trim());
            }
            const allClozes = Array.from(cardCont.querySelectorAll(".cloze"));
            const myIdx = allClozes.indexOf(el);
            if (myIdx !== -1 && myIdx < allAnswers.length) {
                actualAnswer = allAnswers[myIdx];
                el.setAttribute("data-answer", actualAnswer);
            }
        }
    }

    if (actualAnswer) {
        el.innerHTML = actualAnswer;
    } else {
        const orig = el.getAttribute("data-original-text") || "[...]";
        el.innerHTML = orig;
    }
    el.setAttribute("data-state", "revealed");
    el.classList.add("revealed");
    el.style.pointerEvents = "auto";
    el.style.cursor = "pointer";

    const conf = window.MINIMAL_CLOZE_CONFIG || {};
    if (conf.clozeRevealedCustom && conf.clozeRevealedColor) {
        el.style.color = conf.clozeRevealedColor;
    } else {
        el.style.color = "";
        el.style.removeProperty("color");
    }
    const isBold = Boolean(conf.boldClozeText || conf.bold_cloze_text || container.classList.contains("bold-cloze"));
    el.style.fontWeight = isBold ? "700" : "400";
    el.style.textDecoration = "";

    const revealSpeed = parseInt(conf.revealSpeed || (container.style.getPropertyValue('--reveal-speed') || "120"), 10);
    if (revealSpeed > 0) {
        el.style.opacity = "0.75";
        requestAnimationFrame(function() {
            el.style.opacity = "1";
        });
    } else {
        el.style.opacity = "1";
    }

    window.updateClozeSequencing();
    
    const isBack = container.querySelector("#answer-splitter") !== null || container.querySelector(".minimal-back") !== null;
    const remainingHidden = container.querySelectorAll(".cloze.active[data-state='hidden']");
    const shouldAutoReveal = (conf.autoRevealBack !== undefined) ? conf.autoRevealBack : true;
    if (!isBack && remainingHidden.length === 0 && shouldAutoReveal) {
        if (window.pycmd) {
            window.pycmd("ans");
        } else if (typeof showAnswer === "function") {
            showAnswer();
        }
    }
};

window.hideCloze = function(el) {
    const container = document.querySelector(".anki-card-container");
    if (!container || !el) return;

    // Cache current answer in data-answer before replacing innerHTML
    const currentText = (el.innerText || el.textContent || "").trim();
    const origMarker = (el.getAttribute("data-original-text") || "[...]").trim();
    if (currentText !== origMarker && currentText !== "[...]" && currentText !== "...") {
        el.setAttribute("data-answer", el.innerHTML);
    }

    const originalText = el.getAttribute("data-original-text") || "[...]";
    el.innerHTML = originalText;
    el.setAttribute("data-state", "hidden");
    el.classList.remove("revealed");
    el.style.pointerEvents = "auto";
    el.style.cursor = "pointer";

    const conf = window.MINIMAL_CLOZE_CONFIG || {};
    if (conf.clozeHiddenCustom && conf.clozeHiddenColor) {
        el.style.color = conf.clozeHiddenColor;
    } else {
        el.style.color = "";
        el.style.removeProperty("color");
    }
    el.style.fontWeight = "400";
    el.style.textDecoration = "";

    const hideSpeed = parseInt(conf.revealSpeed || (container.style.getPropertyValue('--reveal-speed') || "120"), 10);
    if (hideSpeed > 0) {
        el.style.opacity = "0.75";
        requestAnimationFrame(function() {
            el.style.opacity = "1";
        });
    } else {
        el.style.opacity = "1";
    }

    window.updateClozeSequencing();
};

window.revealAllClozes = function() {
    var container = document.querySelector(".anki-card-container");
    if (!container) return;
    var activeHiddenClozes = container.querySelectorAll(".cloze.active[data-state='hidden']");
    if (activeHiddenClozes && activeHiddenClozes.length > 0) {
        activeHiddenClozes.forEach(function(c) {
            window.revealCloze(c);
        });
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

window.applyClozeConfigLive = function(newConfig) {
    if (!newConfig) return;
    window.MINIMAL_CLOZE_CONFIG = Object.assign({}, window.MINIMAL_CLOZE_CONFIG || {}, newConfig);
    const config = window.MINIMAL_CLOZE_CONFIG;
    const container = document.querySelector(".anki-card-container");
    if (!container) return;

    // 1. Reveal speed CSS property
    container.style.setProperty('--reveal-speed', (config.revealSpeed || 120) + "ms");

    // 2. Cloze custom colors
    if (config.clozeRevealedCustom && config.clozeRevealedColor) {
        container.style.setProperty('--cloze-revealed-color', config.clozeRevealedColor);
    } else {
        container.style.removeProperty('--cloze-revealed-color');
    }
    if (config.clozeHiddenCustom && config.clozeHiddenColor) {
        container.style.setProperty('--cloze-hidden-color', config.clozeHiddenColor);
    } else {
        container.style.removeProperty('--cloze-hidden-color');
    }

    var liveClozes = container.querySelectorAll(".cloze.active");
    liveClozes.forEach(function(c) {
        var state = c.getAttribute("data-state");
        if (state === "revealed") {
            if (config.clozeRevealedCustom && config.clozeRevealedColor) {
                c.style.color = config.clozeRevealedColor;
            } else {
                c.style.color = "";
                c.style.removeProperty("color");
            }
        } else {
            if (config.clozeHiddenCustom && config.clozeHiddenColor) {
                c.style.color = config.clozeHiddenColor;
            } else {
                c.style.color = "";
                c.style.removeProperty("color");
            }
        }
    });

    // 3. Font family & font size
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

    var chosenFontSize = (config.fontSize ? config.fontSize : 20) + "px";
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

    // Bold cloze text: Container-level class when enabled
    if (config.boldClozeText || config.bold_cloze_text) {
        container.classList.add("bold-cloze");
    } else {
        container.classList.remove("bold-cloze");
    }

    // 4. Controls position (.ctrl)
    const ctrlEl = container.querySelector(".ctrl");
    if (ctrlEl) {
        ctrlEl.classList.remove(
            "pos-top-right", "pos-top-left", "pos-bottom-right", "pos-bottom-left",
            "ctrl-top-right", "ctrl-top-left", "ctrl-bottom-right", "ctrl-bottom-left"
        );
        const cpos = config.controlsPosition || "top-right";
        ctrlEl.classList.add("pos-" + cpos);
    }

    // 5. Card Vertical Position & Horizontal Alignment
    const vpos = config.cardVerticalPosition || (config.mitcentMode ? "center" : (config.centerMode ? "center" : "top"));
    const halign = config.cardHorizontalAlign || (config.centerMode ? "center" : "left");
    container.classList.remove(
        "vpos-top", "vpos-center", "vpos-bottom",
        "halign-left", "halign-center", "halign-right",
        "center-mode", "mitcent-mode", "left-mode"
    );
    container.classList.add("vpos-" + vpos, "halign-" + halign);
    container.setAttribute("data-vpos", vpos);
    container.setAttribute("data-halign", halign);
    if (halign === "center" && vpos === "center") {
        container.classList.add("center-mode", "mitcent-mode");
    } else if (halign === "center") {
        container.classList.add("center-mode");
    } else if (halign === "left") {
        container.classList.add("left-mode");
    }

    // 6. Cloze element colors updated live; font weight strictly handled on active cloze only
    const allClozes = container.querySelectorAll(".cloze");
    allClozes.forEach(function(cloze) {
        const state = cloze.getAttribute("data-state");
        if (state === "revealed") {
            if (config.clozeRevealedCustom && config.clozeRevealedColor) {
                cloze.style.color = config.clozeRevealedColor;
            } else {
                cloze.style.color = "";
                cloze.style.removeProperty("color");
            }
        } else if (state === "hidden") {
            if (config.clozeHiddenCustom && config.clozeHiddenColor) {
                cloze.style.color = config.clozeHiddenColor;
            } else {
                cloze.style.color = "";
                cloze.style.removeProperty("color");
            }
        }
    });

    if (typeof window.updateClozeSequencing === "function") {
        window.updateClozeSequencing();
    }

    // 7. Auto-reveal on back card
    const isBack = container.querySelector("#answer-splitter") !== null || container.querySelector(".minimal-back") !== null;
    if (isBack && config.autoRevealBack && typeof window.revealAllClozes === "function") {
        window.revealAllClozes();
    }

    // 8. Info by default
    const extraArea = container.querySelector("#extra-area");
    if (extraArea && config.showInfoByDefault && extraArea.getAttribute("data-mode") !== "info" && typeof window.toggleInfo === "function") {
        window.toggleInfo();
    }

    // 9. Review mode container class & live context re-render
    if (config.reviewMode === "sequential_context") {
        container.classList.add("mode-context");
    } else {
        container.classList.remove("mode-context");
    }
    if (newConfig.reviewMode !== undefined || newConfig.contextBefore !== undefined || newConfig.contextAfter !== undefined || newConfig.contextMaskSubsequent !== undefined || newConfig.backContextBefore !== undefined || newConfig.backContextAfter !== undefined || newConfig.back_context_before !== undefined || newConfig.back_context_after !== undefined) {
        if (frontEl) {
            frontEl.removeAttribute("data-interactive-rendered");
        }
    }

    // 10. Teardown and re-setup listeners so new bindings take effect immediately
    if (typeof window.teardownClozeInteractions === "function") {
        window.teardownClozeInteractions();
    }
    if (typeof window.setupClozeInteractions === "function") {
        window.setupClozeInteractions();
    }
};

// Auto-execute initialization strictly when .anki-card-container is present
(function() {
    if (!document.querySelector(".anki-card-container")) {
        if (typeof window.teardownClozeInteractions === "function") {
            window.teardownClozeInteractions();
        }
        return;
    }
    if (typeof window.setupClozeInteractions === "function") {
        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", function() {
                if (document.querySelector(".anki-card-container")) {
                    window.setupClozeInteractions();
                }
            });
        } else {
            window.setupClozeInteractions();
        }
    }
})();

