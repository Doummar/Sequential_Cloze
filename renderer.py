# Custom injection of scripts and behavior into reviewer cards

import os
import re
import json
from aqt import mw, gui_hooks

from . import bindings

def get_payload_and_resources(card=None):
    addon_dir = os.path.dirname(__file__)

    js_path = os.path.join(addon_dir, "js", "cloze.js")
    js_content = ""
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

    css_path = os.path.join(addon_dir, "styles", "sequential.css")
    css_content = ""
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

    config = mw.addonManager.getConfig(__name__) or {}
    show_info             = "true" if config.get("show_info_by_default", False)     else "false"
    click_rev             = "true" if config.get("enable_click_reveal", True)       else "false"
    center_mode           = "true" if config.get("center_mode", True)               else "false"
    mitcent_mode          = "true" if config.get("mitcent_mode", True)              else "false"
    reveal_speed          = str(config.get("reveal_speed", 120))
    dark_compat           = "true" if config.get("enable_dark_compatibility", True) else "false"
    auto_reveal           = "true" if config.get("auto_reveal_back", True)          else "false"
    cloze_revealed_custom = "true" if config.get("cloze_revealed_custom", False)    else "false"
    cloze_revealed_color  = f'"{config.get("cloze_revealed_color", "#c00000")}"'
    cloze_hidden_custom   = "true" if config.get("cloze_hidden_custom", False)      else "false"
    cloze_hidden_color    = f'"{config.get("cloze_hidden_color", "#0284c7")}"'
    active_cloze_idx      = str(card.ord + 1) if card is not None else "0"
    shortcut_roll         = f'"{config.get("shortcut_roll", "Space")}"'
    shortcut_info         = f'"{config.get("shortcut_info", "I")}"'

    # Generic input bindings, per action (e.g. "reveal" -> list of key /
    # mouse_button / wheel bindings). Falls back to the shipped defaults
    # (Mouse Wheel Down for "reveal") when nothing has been configured yet.
    input_bindings = config.get("input_bindings") or {}
    if not input_bindings:
        input_bindings = {
            action: [dict(b) for b in blist]
            for action, blist in bindings.DEFAULT_BINDINGS.items()
        }
    action_bindings_json = json.dumps(input_bindings)

    payload_config = f"""
    window.MINIMAL_CLOZE_CONFIG = {{
        showInfoByDefault: {show_info},
        enableClickReveal: {click_rev},
        centerMode: {center_mode},
        mitcentMode: {mitcent_mode},
        revealSpeed: {reveal_speed},
        darkCompatibility: {dark_compat},
        autoRevealBack: {auto_reveal},
        clozeRevealedCustom: {cloze_revealed_custom},
        clozeRevealedColor: {cloze_revealed_color},
        clozeHiddenCustom: {cloze_hidden_custom},
        clozeHiddenColor: {cloze_hidden_color},
        activeClozeIdx: {active_cloze_idx},
        shortcutRoll: {shortcut_roll},
        shortcutInfo: {shortcut_info},
        actionBindings: {action_bindings_json}
    }};
    """
    return css_content, js_content, payload_config


def enrich_html_clozes(html, matches, active_ord):
    card_active_matches = [m for m in matches if m[0] == active_ord]
    counter = [0]

    def repl(match):
        idx = counter[0]
        counter[0] += 1
        tag_open = match.group(0)
        if idx < len(card_active_matches):
            cl_num, answer, hint = card_active_matches[idx]
            safe_answer = answer.replace('"', '&quot;')
            safe_hint   = hint.replace('"', '&quot;')
            return re.sub(r'(?i)<span',
                f'<span data-answer="{safe_answer}" data-hint="{safe_hint}" '
                f'data-cloze-idx="{cl_num}"',
                tag_open, count=1)
        else:
            return re.sub(r'(?i)<span',
                f'<span data-cloze-idx="{active_ord}"',
                tag_open, count=1)

    return re.sub(
        r'(?i)<span\b[^>]*\bclass\s*=\s*["\']?[^"\'>]*\bcloze\b[^"\'>]*["\']?[^>]*>',
        repl, html)


def _uses_our_template(output) -> bool:
    """Return True when the rendered card HTML contains our container element.

    Checking the rendered output (rather than the note-type name) means the
    addon works regardless of what the user names their note type, and
    correctly skips every built-in Anki template that does not include
    .anki-card-container.
    """
    return ('anki-card-container' in output.question_text or
            'anki-card-container' in output.answer_text)


def _template_uses_our_container(card) -> bool:
    """Return True when the card's question template source contains our container.

    Used by the show-question / show-answer hooks where we only have the card
    object, not the rendered output.
    """
    try:
        tmpl = card.note().model()['tmpls'][card.ord]
        return 'anki-card-container' in tmpl.get('qfmt', '')
    except Exception:
        return False


def on_card_will_render(output, card, kind) -> None:
    # Skip any card whose template does not use our .anki-card-container layout.
    # Replaces the old note-type-name check — works with any note type whose
    # template includes our HTML structure, and is immune to renames.
    if not _uses_our_template(output):
        return

    note    = card.note()
    pattern = re.compile(r'{{c(\d+)::(.*?)}}', re.IGNORECASE | re.DOTALL)
    matches = []
    for key in note.keys():
        val = note[key] or ""
        for cl_num_str, content in pattern.findall(val):
            cl_num = int(cl_num_str)
            parts  = content.split("::")
            if len(parts) > 1:
                hint   = parts[-1]
                answer = "::".join(parts[:-1])
            else:
                answer = content
                hint   = ""
            matches.append((cl_num, answer, hint))

    css_content, js_content, payload_config = get_payload_and_resources(card)
    active_ord = card.ord + 1
    enriched_q = enrich_html_clozes(output.question_text, matches, active_ord)
    enriched_a = enrich_html_clozes(output.answer_text,   matches, active_ord)
    style_tag  = f"<style>{css_content}</style>"
    script_tag = f"<script>{payload_config}\n{js_content}</script>"
    output.question_text = enriched_q + style_tag + script_tag
    output.answer_text   = enriched_a + style_tag + script_tag


def on_webview_will_set_content(web_content, context) -> None:
    """Pre-define all JS functions in the reviewer / previewer webview head.

    The card's own <script> tag (injected by on_card_will_render) also defines
    these functions, but it executes asynchronously after the card HTML is
    injected into the webview.  Without this head injection there is a race
    condition: on_reviewer_did_show_question fires its web.eval() call before
    the card scripts have had a chance to run, the typeof check returns false,
    and setupClozeInteractions() is never called — causing centering and scroll
    reveal to silently fail on every card.

    Scoped to reviewer and previewer only; browser / editor are excluded to
    prevent CSS bleeding into those panes.
    """
    class_name = context.__class__.__name__.lower()
    if "reviewer" not in class_name and "previewer" not in class_name:
        return
    css_content, js_content, payload_config = get_payload_and_resources()
    web_content.head += f"<style>{css_content}</style>"
    web_content.head += f"<script>{payload_config}\n{js_content}</script>"


def on_reviewer_did_show_question(*args, **kwargs) -> None:
    try:
        if not (mw.reviewer and mw.reviewer.web and mw.reviewer.card):
            return
        # Only call setup for cards that actually use our template, to avoid
        # the 10 × 50 ms retry overhead on every non-Sequential card.
        if not _template_uses_our_container(mw.reviewer.card):
            return
        mw.reviewer.web.eval(
            "if (typeof window.setupClozeInteractions === 'function') "
            "{ window.setupClozeInteractions(); }"
        )
    except Exception:
        pass


def on_reviewer_did_show_answer(*args, **kwargs) -> None:
    try:
        if not (mw.reviewer and mw.reviewer.web and mw.reviewer.card):
            return
        if not _template_uses_our_container(mw.reviewer.card):
            return
        mw.reviewer.web.eval(
            "if (typeof window.setupClozeInteractions === 'function') "
            "{ window.setupClozeInteractions(); }"
        )
    except Exception:
        pass


# ── Hook registration ──────────────────────────────────────────────────────────

try:
    gui_hooks.card_will_render.append(on_card_will_render)
except Exception:
    try:
        from anki.hooks import card_will_render
        card_will_render.append(on_card_will_render)
    except Exception:
        pass

try:
    # webview_will_set_content pre-defines the JS in the reviewer head so it is
    # guaranteed to be available when the show-question hook calls web.eval().
    gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
    gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_answer)
except Exception:
    pass
