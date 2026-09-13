# Custom injection of scripts and behavior into reviewer cards

import os
import re
import json
from aqt import mw, gui_hooks

from . import bindings
from .reviewer import get_addon_config, get_addon_pkg

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

    config = get_addon_config()
    controls_pos          = f'"{config.get("controls_position", "top-right")}"'
    card_vpos             = f'"{config.get("card_vertical_position", "center")}"'
    card_halign           = f'"{config.get("card_horizontal_align", "center")}"'
    font_family           = f'"{config.get("font_family", "System Default")}"'
    font_size             = str(config.get("font_size", 18))
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
    shortcut_reveal_all   = f'"{config.get("shortcut_reveal_all", "Shift + Space")}"'
    shortcut_info         = f'"{config.get("shortcut_info", "H")}"'
    shortcut_image        = f'"{config.get("shortcut_image", "G")}"'

    input_bindings = config.get("input_bindings") or {}
    if not input_bindings:
        input_bindings = {
            action: [dict(b) for b in blist]
            for action, blist in bindings.DEFAULT_BINDINGS.items()
        }
    action_bindings_json = json.dumps(input_bindings)

    payload_config = f"""
    window.MINIMAL_CLOZE_CONFIG = {{
        controlsPosition: {controls_pos},
        cardVerticalPosition: {card_vpos},
        cardHorizontalAlign: {card_halign},
        fontFamily: {font_family},
        fontSize: {font_size},
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
        shortcutRevealAll: {shortcut_reveal_all},
        shortcutInfo: {shortcut_info},
        shortcutImage: {shortcut_image},
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


def _is_our_card(card) -> bool:
    if not card:
        return False
    try:
        model = card.note().model()
        if model.get('name') == "Sequential Cloze v1":
            return True
        for tmpl in model.get('tmpls', []):
            if 'anki-card-container' in tmpl.get('qfmt', '') or 'anki-card-container' in tmpl.get('afmt', ''):
                return True
    except Exception:
        pass
    return False


def _uses_our_template(output, card=None) -> bool:
    if 'anki-card-container' in output.question_text or 'anki-card-container' in output.answer_text:
        return True
    return _is_our_card(card)


def on_card_will_render(output, card, kind) -> None:
    if not _uses_our_template(output, card):
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
    
    # Prepend config so window.MINIMAL_CLOZE_CONFIG is ready before any script runs.
    # Also append a trigger script so setupClozeInteractions immediately executes with latest settings.
    config_script = f"<script id=\"sq-desktop-config\">{payload_config}</script>"
    trigger_script = (
        "<script>"
        "if (typeof window.setupClozeInteractions === 'function') { window.setupClozeInteractions(); }"
        "setTimeout(function() { if (typeof window.setupClozeInteractions === 'function') { window.setupClozeInteractions(); } }, 40);"
        "</script>"
    )

    if "setupClozeInteractions" in output.question_text or "setupClozeInteractions" in output.answer_text:
        # Template is self-contained: inject user configuration and execution trigger
        output.question_text = config_script + enriched_q + trigger_script
        output.answer_text   = config_script + enriched_a + trigger_script
    else:
        # Legacy template fallback without embedded scripts
        style_tag  = f"<style>{css_content}</style>"
        script_tag = f"<script>{payload_config}\n{js_content}\nif (typeof window.setupClozeInteractions === 'function') {{ window.setupClozeInteractions(); }}</script>"
        output.question_text = enriched_q + style_tag + script_tag
        output.answer_text   = enriched_a + style_tag + script_tag


def on_reviewer_did_show_question(*args, **kwargs) -> None:
    try:
        if not (mw.reviewer and mw.reviewer.web and mw.reviewer.card):
            return
        if not _is_our_card(mw.reviewer.card):
            mw.reviewer.web.eval(
                "if (typeof window.teardownClozeInteractions === 'function') { "
                "window.teardownClozeInteractions(); }"
            )
            return
        _, _, payload_config = get_payload_and_resources(mw.reviewer.card)
        mw.reviewer.web.eval(
            f"{payload_config}\n"
            "if (typeof window.setupClozeInteractions === 'function') "
            "{ window.setupClozeInteractions(); }"
        )
    except Exception:
        pass


def on_reviewer_did_show_answer(*args, **kwargs) -> None:
    try:
        if not (mw.reviewer and mw.reviewer.web and mw.reviewer.card):
            return
        if not _is_our_card(mw.reviewer.card):
            mw.reviewer.web.eval(
                "if (typeof window.teardownClozeInteractions === 'function') { "
                "window.teardownClozeInteractions(); }"
            )
            return
        _, _, payload_config = get_payload_and_resources(mw.reviewer.card)
        mw.reviewer.web.eval(
            f"{payload_config}\n"
            "if (typeof window.setupClozeInteractions === 'function') "
            "{ window.setupClozeInteractions(); }"
        )
    except Exception:
        pass


def on_reviewer_will_end() -> None:
    try:
        if mw.reviewer and mw.reviewer.web:
            mw.reviewer.web.eval(
                "if (typeof window.teardownClozeInteractions === 'function') { "
                "window.teardownClozeInteractions(); }"
            )
    except Exception:
        pass


try:
    gui_hooks.card_will_render.append(on_card_will_render)
except Exception:
    try:
        from anki.hooks import card_will_render
        card_will_render.append(on_card_will_render)
    except Exception:
        pass

try:
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
    gui_hooks.reviewer_did_show_answer.append(on_reviewer_did_show_answer)
    gui_hooks.reviewer_will_end.append(on_reviewer_will_end)
except Exception:
    pass
