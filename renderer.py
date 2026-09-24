# Custom injection of scripts and behavior into reviewer cards

import os
import re
import json
try:
    from aqt import mw, gui_hooks
except ImportError:
    mw = None
    gui_hooks = None

from . import bindings
from .reviewer import get_addon_config, get_addon_pkg

def get_payload_and_resources(card=None, force_reload: bool = False):
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

    config = get_addon_config(force_reload=force_reload)
    controls_pos          = f'"{config.get("controls_position", "top-right")}"'
    card_vpos             = f'"{config.get("card_vertical_position", "top")}"'
    card_halign           = f'"{config.get("card_horizontal_align", "center")}"'
    font_family           = f'"{config.get("font_family", "System Default")}"'
    font_size             = str(config.get("font_size", 20))
    bold_cloze            = "true" if config.get("bold_cloze_text", False)          else "false"
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
    review_mode           = f'"{config.get("review_mode", "sequential_context")}"'
    context_before        = json.dumps(config.get("context_before", 1))
    context_after         = json.dumps(config.get("context_after", 0))
    context_mask          = "true" if config.get("context_mask_subsequent", True) else "false"
    back_context_before   = json.dumps(config.get("back_context_before", "all"))
    back_context_after    = json.dumps(config.get("back_context_after", "all"))
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
        boldClozeText: {bold_cloze},
        bold_cloze_text: {bold_cloze},
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
        reviewMode: {review_mode},
        review_mode: {review_mode},
        contextBefore: {context_before},
        context_before: {context_before},
        contextAfter: {context_after},
        context_after: {context_after},
        contextMaskSubsequent: {context_mask},
        context_mask_subsequent: {context_mask},
        backContextBefore: {back_context_before},
        back_context_before: {back_context_before},
        backContextAfter: {back_context_after},
        back_context_after: {back_context_after},
        shortcutRoll: {shortcut_roll},
        shortcutRevealAll: {shortcut_reveal_all},
        shortcutInfo: {shortcut_info},
        shortcutImage: {shortcut_image},
        actionBindings: {action_bindings_json}
    }};
    """
    return css_content, js_content, payload_config


def enrich_html_clozes(html, matches, active_ord, is_back=False):
    card_active_matches = [m for m in matches if m[0] == active_ord]
    counter = [0]

    def repl(match):
        idx = counter[0]
        counter[0] += 1
        tag_open = match.group(0)
        if is_back:
            # On back, every cloze answer is revealed
            tag_open = re.sub(r'\bclass\s*=\s*["\']([^"\']*)["\']', lambda m: f'class="{m.group(1)} revealed"' if 'revealed' not in m.group(1) else m.group(0), tag_open)
        if idx < len(card_active_matches):
            cl_num, answer, hint = card_active_matches[idx]
            safe_answer = answer.replace('"', '&quot;')
            safe_hint   = hint.replace('"', '&quot;')
            state_attr = ' data-state="revealed"' if is_back else ''
            return re.sub(r'(?i)<span',
                f'<span data-answer="{safe_answer}" data-hint="{safe_hint}" '
                f'data-cloze-idx="{cl_num}"{state_attr}',
                tag_open, count=1)
        else:
            state_attr = ' data-state="revealed"' if is_back else ''
            return re.sub(r'(?i)<span',
                f'<span data-cloze-idx="{active_ord}"{state_attr}',
                tag_open, count=1)

    return re.sub(
        r'(?i)<span\b[^>]*\bclass\s*=\s*["\']?[^"\'>]*\bcloze\b[^"\'>]*["\']?[^>]*>',
        repl, html)


def balance_html(html: str) -> str:
    void_tags = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    tag_regex = re.compile(r"<\s*(/)?\s*([a-zA-Z0-9]+)(?:\s+[^>]*)?>")
    stack = []
    for match in tag_regex.finditer(html):
        is_closing = bool(match.group(1))
        tag_name = match.group(2).lower()
        if tag_name in void_tags:
            continue
        if match.group(0).endswith("/>"):
            continue
        if not is_closing:
            stack.append(tag_name)
        else:
            for i in range(len(stack) - 1, -1, -1):
                if stack[i] == tag_name:
                    stack = stack[:i]
                    break
    closing_tags = "".join(f"</{t}>" for t in reversed(stack))
    return html + closing_tags


def render_context_clozes(raw_text: str, active_ord: int, config: dict, is_back: bool) -> str:
    cb_val = config.get("context_before", 1)
    ca_val = config.get("context_after", 0)
    mask_subsequent = config.get("context_mask_subsequent", True)

    bcb_val = config.get("back_context_before", "all")
    bca_val = config.get("back_context_after", "all")

    try:
        if str(cb_val).strip().lower() == "all":
            cb = "all"
        else:
            cb = int(cb_val)
    except Exception:
        cb = 1

    try:
        if str(ca_val).strip().lower() == "all":
            ca = "all"
        else:
            ca = int(ca_val)
    except Exception:
        ca = 0

    try:
        if str(bcb_val).strip().lower() == "all":
            bcb = "all"
        else:
            bcb = int(bcb_val)
    except Exception:
        bcb = "all"

    try:
        if str(bca_val).strip().lower() == "all":
            bca = "all"
        else:
            bca = int(bca_val)
    except Exception:
        bca = "all"

    pattern = re.compile(r'\{\{c(\d+)::(.*?)\}\}', flags=re.IGNORECASE | re.DOTALL)
    bold_cloze = bool(config.get("bold_cloze_text", False))

    # Collect ordered list of cloze indices appearing in text for sequence-aware positioning
    ordered_cloze_nums = []
    for m in pattern.finditer(raw_text):
        cnum = int(m.group(1))
        if cnum not in ordered_cloze_nums:
            ordered_cloze_nums.append(cnum)

    active_pos = ordered_cloze_nums.index(active_ord) if active_ord in ordered_cloze_nums else -1

    if not is_back:
        # FRONT SIDE
        trimmed_text = raw_text
        if mask_subsequent:
            if ca != "all":
                if active_pos != -1:
                    allowed_idx = min(active_pos + (ca if isinstance(ca, int) else 0), len(ordered_cloze_nums) - 1)
                    max_allowed_ord = ordered_cloze_nums[allowed_idx]
                else:
                    max_allowed_ord = active_ord + (ca if isinstance(ca, int) else 0)

                last_end = None
                for m in pattern.finditer(raw_text):
                    cl_num = int(m.group(1))
                    if cl_num <= max_allowed_ord:
                        last_end = m.end()
                if last_end is not None and last_end < len(raw_text):
                    trimmed_text = balance_html(raw_text[:last_end].rstrip())

        def repl_front(m):
            cl_num = int(m.group(1))
            content = m.group(2)
            parts = content.split("::")
            if len(parts) > 1:
                hint = parts[-1]
                answer = "::".join(parts[:-1])
            else:
                answer = content
                hint = ""

            safe_answer = answer.replace('"', '&quot;')
            safe_hint   = hint.replace('"', '&quot;')
            blank_text  = f"[{hint}]" if hint else "[...]"

            if cl_num == active_ord:
                return (
                    f'<span class="cloze active current-cloze" '
                    f'data-cloze-idx="{cl_num}" data-state="hidden" data-active-cloze="true" '
                    f'data-answer="{safe_answer}" data-hint="{safe_hint}" '
                    f'style="pointer-events: auto !important; cursor: pointer !important;">{blank_text}</span>'
                )

            pos = ordered_cloze_nums.index(cl_num) if cl_num in ordered_cloze_nums else -1
            has_pos = (pos != -1 and active_pos != -1)

            is_before = (pos < active_pos) if has_pos else (cl_num < active_ord)
            if is_before:
                prev_dist = (active_pos - pos) if has_pos else (active_ord - cl_num)
                in_context = (cb == "all") or (isinstance(cb, int) and cb >= 0 and prev_dist <= cb)
                if in_context:
                    return f'<span class="cloze-context cloze-context-prev" data-cloze-idx="{cl_num}">{answer}</span>'
                else:
                    return ""
            else:
                after_dist = (pos - active_pos) if has_pos else (cl_num - active_ord)
                in_context_after = (ca == "all") or (isinstance(ca, int) and ca >= 0 and after_dist <= ca)
                if in_context_after:
                    return f'<span class="cloze-context cloze-context-after" data-cloze-idx="{cl_num}">{answer}</span>'
                else:
                    return ""

        res = pattern.sub(repl_front, trimmed_text)
        res = re.sub(r'<li\b[^>]*>\s*(?:[•\-*]|\d+[\.\)])?\s*</li>', '', res, flags=re.IGNORECASE)
        res = re.sub(r'<(div|p)\b[^>]*>\s*(?:[•\-*]|\d+[\.\)])?\s*</\1>', '', res, flags=re.IGNORECASE)
        res = re.sub(r'(?:^|\n)\s*(?:[•\-*]|\d+[\.\)])?\s*<br\s*/?>', '', res, flags=re.IGNORECASE)
        res = re.sub(r'[ \t]{2,}', ' ', res)
        return res
    else:
        # BACK SIDE: show context around active cloze according to back_context_before & back_context_after
        trimmed_text = raw_text
        if bca != "all":
            if active_pos != -1:
                allowed_idx = min(active_pos + (bca if isinstance(bca, int) else 0), len(ordered_cloze_nums) - 1)
                max_allowed_ord = ordered_cloze_nums[allowed_idx]
            else:
                max_allowed_ord = active_ord + (bca if isinstance(bca, int) else 0)

            last_end = None
            for m in pattern.finditer(raw_text):
                cl_num = int(m.group(1))
                if cl_num <= max_allowed_ord:
                    last_end = m.end()
            if last_end is not None and last_end < len(raw_text):
                trimmed_text = balance_html(raw_text[:last_end].rstrip())

        def repl_back(m):
            cl_num = int(m.group(1))
            content = m.group(2)
            parts = content.split("::")
            if len(parts) > 1:
                hint = parts[-1]
                answer = "::".join(parts[:-1])
            else:
                answer = content
                hint = ""

            safe_answer = answer.replace('"', '&quot;')
            safe_hint   = hint.replace('"', '&quot;')

            if cl_num == active_ord:
                return (
                    f'<span class="cloze active current-cloze revealed" '
                    f'data-cloze-idx="{cl_num}" data-state="revealed" data-active-cloze="true" '
                    f'data-answer="{safe_answer}" data-hint="{safe_hint}" '
                    f'style="pointer-events: auto !important;">{answer}</span>'
                )

            pos = ordered_cloze_nums.index(cl_num) if cl_num in ordered_cloze_nums else -1
            has_pos = (pos != -1 and active_pos != -1)

            is_before = (pos < active_pos) if has_pos else (cl_num < active_ord)
            if is_before:
                prev_dist = (active_pos - pos) if has_pos else (active_ord - cl_num)
                in_context = (bcb == "all") or (isinstance(bcb, int) and bcb >= 0 and prev_dist <= bcb)
                if in_context:
                    return f'<span class="cloze-context cloze-context-prev" data-cloze-idx="{cl_num}">{answer}</span>'
                else:
                    return ""
            else:
                after_dist = (pos - active_pos) if has_pos else (cl_num - active_ord)
                in_context_after = (bca == "all") or (isinstance(bca, int) and bca >= 0 and after_dist <= bca)
                if in_context_after:
                    return f'<span class="cloze-context cloze-context-after" data-cloze-idx="{cl_num}">{answer}</span>'
                else:
                    return ""

        res = pattern.sub(repl_back, trimmed_text)
        res = re.sub(r'<li\b[^>]*>\s*(?:[•\-*]|\d+[\.\)])?\s*</li>', '', res, flags=re.IGNORECASE)
        res = re.sub(r'<(div|p)\b[^>]*>\s*(?:[•\-*]|\d+[\.\)])?\s*</\1>', '', res, flags=re.IGNORECASE)
        res = re.sub(r'(?:^|\n)\s*(?:[•\-*]|\d+[\.\)])?\s*<br\s*/?>', '', res, flags=re.IGNORECASE)
        res = re.sub(r'[ \t]{2,}', ' ', res)
        return res


def _replace_minimal_front(html: str, new_content: str) -> str:
    m = re.search(r'<div\b[^>]*\bclass\s*=\s*["\']?[^"\'>]*\bminimal-front\b[^"\'>]*["\']?[^>]*>', html, re.IGNORECASE)
    if not m:
        return html
    start_pos = m.start()
    content_start = m.end()

    tag_pattern = re.compile(r'<\s*(/)?\s*div\b[^>]*>', re.IGNORECASE)
    depth = 1
    div_end = None
    for tm in tag_pattern.finditer(html[content_start:]):
        is_closing = bool(tm.group(1))
        if is_closing:
            depth -= 1
            if depth == 0:
                div_end = content_start + tm.end()
                break
        else:
            depth += 1

    if div_end is not None:
        return html[:start_pos] + f'<div class="minimal-front" data-interactive-rendered="true">{new_content}</div>' + html[div_end:]

    return re.sub(
        r'(<div\b[^>]*\bclass\s*=\s*["\']?[^"\'>]*\bminimal-front\b[^"\'>]*["\']?[^>]*>)(.*?)(</div>)',
        lambda _: f'<div class="minimal-front" data-interactive-rendered="true">{new_content}</div>',
        html, count=1, flags=re.DOTALL | re.IGNORECASE
    )


def enrich_html_clozes_context(html: str, note, matches, active_ord: int, config: dict, is_back: bool) -> str:
    # Under NO circumstances wrap or modify cards that lack anki-card-container!
    if 'anki-card-container' not in (html or ''):
        return html

    raw_text = ""
    if note:
        if "Front" in note and re.search(r'\{\{c\d+::', note["Front"] or "", re.IGNORECASE):
            raw_text = note["Front"] or ""
        elif "Text" in note and re.search(r'\{\{c\d+::', note["Text"] or "", re.IGNORECASE):
            raw_text = note["Text"] or ""
        else:
            for k in note.keys():
                val = note[k] or ""
                if re.search(r'\{\{c\d+::', val, re.IGNORECASE):
                    raw_text = val
                    break

    if not raw_text:
        return enrich_html_clozes(html, matches, active_ord)

    rendered_field = render_context_clozes(raw_text, active_ord, config, is_back)

    html = re.sub(
        r'(<div\b[^>]*\bclass\s*=\s*["\']?[^"\'>]*\banki-card-container\b[^"\'>]*["\']?[^>]*>)',
        lambda m: m.group(0) if 'mode-context' in m.group(0) else m.group(0).replace('anki-card-container', 'anki-card-container mode-context'),
        html, count=1
    )
    if 'minimal-front' in html:
        html = _replace_minimal_front(html, rendered_field)
    else:
        html = enrich_html_clozes(html, matches, active_ord)

    return html


def _is_our_card(card) -> bool:
    if not card:
        return False
    try:
        note = card.note()
        if not note:
            return False
        model = note.model()
        if not model:
            return False
        model_name = (model.get('name') or "").strip()
        if "Sequential Cloze" in model_name:
            return True
        for tmpl in model.get('tmpls', []):
            qfmt = tmpl.get('qfmt', '') or ''
            afmt = tmpl.get('afmt', '') or ''
            if 'anki-card-container' in qfmt or 'anki-card-container' in afmt:
                return True
    except Exception:
        pass
    return False


def _uses_our_template(output, card=None) -> bool:
    if output:
        q = getattr(output, 'question_text', '') or ''
        a = getattr(output, 'answer_text', '') or ''
        if 'anki-card-container' in q or 'anki-card-container' in a:
            return True
    return _is_our_card(card)


def generate_injected_css_vars(config: dict) -> str:
    font_family_val = config.get("font_family", "System Default")
    font_families_map = {
        "System Default": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        "Arial": "Arial, Helvetica, sans-serif",
        "Georgia": "Georgia, Cambria, 'Times New Roman', Times, serif",
        "Times New Roman": "'Times New Roman', Times, Georgia, serif",
        "Courier New": "'Courier New', Courier, monospace",
        "Segoe UI": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "SF Pro": "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', sans-serif",
        "Comic Sans MS": "'Comic Sans MS', 'Comic Sans', cursive, sans-serif",
    }
    if font_family_val in font_families_map:
        font_family_css = font_families_map[font_family_val]
    elif font_family_val and font_family_val != "System Default":
        font_family_css = f'"{font_family_val}", sans-serif' if (' ' in font_family_val and '"' not in font_family_val) else font_family_val
    else:
        font_family_css = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

    font_size_val = config.get("font_size", 20)
    font_size_css = f"{font_size_val}px"
    reveal_speed_css = f"{config.get('reveal_speed', 120)}ms"

    rev_custom = config.get("cloze_revealed_custom", False)
    hid_custom = config.get("cloze_hidden_custom", False)
    bold_cloze = bool(config.get("bold_cloze_text", False))

    custom_vars = ""
    if bold_cloze:
        custom_color_rules = (
            ".anki-card-container.bold-cloze .cloze.revealed,\n"
            ".anki-card-container.bold-cloze .cloze[data-state=\"revealed\"] {\n"
            "  font-weight: 700 !important;\n"
            "}\n"
            ".anki-card-container .cloze:not(.revealed):not([data-state=\"revealed\"]),\n"
            ".anki-card-container.bold-cloze .cloze:not(.revealed):not([data-state=\"revealed\"]),\n"
            ".anki-card-container .cloze[data-state=\"hidden\"],\n"
            ".anki-card-container.bold-cloze .cloze[data-state=\"hidden\"],\n"
            ".anki-card-container .cloze.active[data-state=\"hidden\"],\n"
            ".anki-card-container.bold-cloze .cloze.active[data-state=\"hidden\"],\n"
            ".anki-card-container .cloze-context,\n"
            ".anki-card-container .cloze-context-prev,\n"
            ".anki-card-container .cloze-context-after,\n"
            ".anki-card-container.bold-cloze .cloze-context,\n"
            ".anki-card-container.bold-cloze .cloze-context-prev,\n"
            ".anki-card-container.bold-cloze .cloze-context-after {\n"
            "  font-weight: 400 !important;\n"
            "}\n"
        )
    else:
        custom_color_rules = (
            ".anki-card-container:not(.bold-cloze) .cloze,\n"
            ".anki-card-container:not(.bold-cloze) .cloze.revealed,\n"
            ".anki-card-container:not(.bold-cloze) .cloze[data-state=\"revealed\"],\n"
            ".anki-card-container .cloze-context,\n"
            ".anki-card-container .cloze-context-prev,\n"
            ".anki-card-container .cloze-context-after,\n"
            ".anki-card-container:not(.bold-cloze) .cloze-context,\n"
            ".anki-card-container:not(.bold-cloze) .cloze-context-prev,\n"
            ".anki-card-container:not(.bold-cloze) .cloze-context-after {\n"
            "  font-weight: 400 !important;\n"
            "}\n"
        )

    if rev_custom:
        rev_color = config.get("cloze_revealed_color", "#c00000")
        custom_vars += f"  --cloze-revealed-color: {rev_color};\n"
        custom_color_rules += (
            f".anki-card-container .cloze.active[data-state=\"revealed\"],\n"
            f".anki-card-container .cloze.revealed,\n"
            f".anki-card-container .cloze[data-state=\"revealed\"] {{\n"
            f"  color: {rev_color} !important;\n"
            f"}}\n"
        )

    if hid_custom:
        hid_color = config.get("cloze_hidden_color", "#0284c7")
        custom_vars += f"  --cloze-hidden-color: {hid_color};\n"
        custom_color_rules += (
            f".anki-card-container .cloze.active:not([data-state=\"revealed\"]),\n"
            f".anki-card-container .cloze.active[data-state=\"hidden\"],\n"
            f".anki-card-container .cloze.active.current-cloze:not([data-state=\"revealed\"]) {{\n"
            f"  color: {hid_color} !important;\n"
            f"}}\n"
        )

    return (
        f'<style id="sq-injected-vars">\n'
        f'.anki-card-container {{\n'
        f'  --card-font-family: {font_family_css};\n'
        f'  --card-font-size: {font_size_css};\n'
        f'  --reveal-speed: {reveal_speed_css};\n'
        f'{custom_vars}'
        f'  font-family: {font_family_css} !important;\n'
        f'  font-size: {font_size_css} !important;\n'
        f'}}\n'
        f'.anki-card-container .minimal-front,\n'
        f'.anki-card-container .minimal-back {{\n'
        f'  font-family: {font_family_css} !important;\n'
        f'  font-size: {font_size_css} !important;\n'
        f'}}\n'
        f'{custom_color_rules}'
        f'</style>\n'
    )


def apply_container_classes(html: str, config: dict, is_context_mode: bool) -> str:
    vpos = config.get("card_vertical_position", "top")
    halign = config.get("card_horizontal_align", "center")
    mode_cls = " mode-context" if is_context_mode else ""
    bold_cls = " bold-cloze" if config.get("bold_cloze_text", False) else ""
    target_classes = f"anki-card-container vpos-{vpos} halign-{halign}{mode_cls}{bold_cls}"

    def repl(m):
        tag = m.group(0)
        clean_tag = re.sub(r'\b(vpos-(?:top|center|bottom)|halign-(?:left|center|right)|mode-context|center-mode|left-mode|mitcent-mode|bold-cloze)\b', '', tag)
        clean_tag = re.sub(r'class\s*=\s*["\'][^"\']*anki-card-container[^"\']*["\']', f'class="{target_classes}"', clean_tag)
        if 'data-vpos' not in clean_tag:
            clean_tag = clean_tag.rstrip('>') + f' data-vpos="{vpos}" data-halign="{halign}">'
        else:
            clean_tag = re.sub(r'data-vpos\s*=\s*["\'][^"\']*["\']', f'data-vpos="{vpos}"', clean_tag)
            clean_tag = re.sub(r'data-halign\s*=\s*["\'][^"\']*["\']', f'data-halign="{halign}"', clean_tag)
        return clean_tag

    return re.sub(
        r'<div\b[^>]*\bclass\s*=\s*["\']?[^"\'>]*\banki-card-container\b[^"\'>]*["\']?[^>]*>',
        repl, html, count=1
    )


def on_card_will_render(output, card, kind) -> None:
    # STRICT NOTE TYPE / TEMPLATE SCOPE:
    # Must NEVER touch Basic, standard Cloze, or any other note types!
    if not _uses_our_template(output, card):
        return

    note = card.note() if card else None
    if not note:
        return

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

    if not matches:
        # No clozes found on card, don't intervene
        return

    css_content, js_content, payload_config = get_payload_and_resources(card, force_reload=True)
    active_ord = card.ord + 1
    config = get_addon_config(force_reload=True)
    review_mode = config.get("review_mode", "sequential_context")

    if review_mode == "sequential_context":
        enriched_q = enrich_html_clozes_context(output.question_text, note, matches, active_ord, config, is_back=False)
        enriched_a = enrich_html_clozes_context(output.answer_text,   note, matches, active_ord, config, is_back=True)
    else:
        enriched_q = enrich_html_clozes(output.question_text, matches, active_ord, is_back=False)
        enriched_a = enrich_html_clozes(output.answer_text,   matches, active_ord, is_back=True)
    
    injected_style = generate_injected_css_vars(config)
    is_ctx = (review_mode == "sequential_context")
    enriched_q = apply_container_classes(enriched_q, config, is_ctx)
    enriched_a = apply_container_classes(enriched_a, config, is_ctx)

    # Prepend config so window.MINIMAL_CLOZE_CONFIG is ready before any script runs.
    # Also append a trigger script so setupClozeInteractions immediately executes with latest settings.
    config_script = f"<script id=\"sq-desktop-config\">{payload_config}</script>"
    trigger_script = (
        "<script>"
        "if (document.querySelector('.anki-card-container')) { "
        "if (typeof window.applyClozeConfigLive === 'function') { window.applyClozeConfigLive(window.MINIMAL_CLOZE_CONFIG); } "
        "else if (typeof window.setupClozeInteractions === 'function') { window.setupClozeInteractions(); } "
        "}"
        "</script>"
    )

    if "setupClozeInteractions" in (output.question_text or '') or "setupClozeInteractions" in (output.answer_text or ''):
        # Template is self-contained: inject user configuration and execution trigger
        output.question_text = injected_style + config_script + enriched_q + trigger_script + injected_style
        output.answer_text   = injected_style + config_script + enriched_a + trigger_script + injected_style
    elif 'anki-card-container' in (output.question_text or '') or 'anki-card-container' in (output.answer_text or ''):
        # Legacy template fallback strictly when anki-card-container is present
        style_tag  = f"<style>{css_content}</style>"
        script_tag = f"<script>{payload_config}\n{js_content}\nif (document.querySelector('.anki-card-container') && typeof window.setupClozeInteractions === 'function') {{ window.setupClozeInteractions(); }}</script>"
        output.question_text = injected_style + enriched_q + style_tag + script_tag + injected_style
        output.answer_text   = injected_style + enriched_a + style_tag + script_tag + injected_style


def on_card_will_show(html: str, card, context: str) -> str:
    # STRICT NOTE TYPE / TEMPLATE SCOPE:
    if not _is_our_card(card) and 'anki-card-container' not in (html or ''):
        return html

    config = get_addon_config(force_reload=True)
    review_mode = config.get("review_mode", "sequential_context")

    # Strict rule: if review_mode is not sequential_context, do not touch html here at all
    if review_mode != "sequential_context":
        return html

    # If already rendered via on_card_will_render, do not duplicate
    if 'data-interactive-rendered="true"' in (html or ''):
        return html

    # If not containing our container, return untouched!
    if 'anki-card-container' not in (html or ''):
        return html

    note = card.note() if card else None
    if not note:
        return html

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

    if not matches:
        return html

    css_content, js_content, payload_config = get_payload_and_resources(card, force_reload=True)
    active_ord = card.ord + 1

    # Determine if we are rendering front or back
    is_back = bool(context and "answer" in str(context).lower()) or ('<hr id="answer-splitter">' in html) or ('<hr id="answer">' in html) or ('<hr id=answer>' in html)

    enriched = enrich_html_clozes_context(html, note, matches, active_ord, config, is_back=is_back)

    config_script = f'<script id="sq-desktop-config">{payload_config}</script>'
    trigger_script = (
        '<script>'
        'if (document.querySelector(\'.anki-card-container\')) { '
        'if (typeof window.applyClozeConfigLive === \'function\') { window.applyClozeConfigLive(window.MINIMAL_CLOZE_CONFIG); } '
        'else if (typeof window.setupClozeInteractions === \'function\') { window.setupClozeInteractions(); } '
        '}'
        '</script>'
    )

    if "setupClozeInteractions" in enriched:
        return config_script + enriched + trigger_script
    elif 'anki-card-container' in enriched:
        style_tag  = f'<style>{css_content}</style>'
        script_tag = f"<script>{payload_config}\n{js_content}\nif (document.querySelector('.anki-card-container') && typeof window.setupClozeInteractions === 'function') {{ window.setupClozeInteractions(); }}</script>"
        return enriched + style_tag + script_tag
    else:
        return html


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
        _, _, payload_config = get_payload_and_resources(mw.reviewer.card, force_reload=True)
        mw.reviewer.web.eval(
            f"{payload_config}\n"
            "if (typeof window.applyClozeConfigLive === 'function') { "
            "window.applyClozeConfigLive(window.MINIMAL_CLOZE_CONFIG); } "
            "else if (typeof window.setupClozeInteractions === 'function') "
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
        _, _, payload_config = get_payload_and_resources(mw.reviewer.card, force_reload=True)
        mw.reviewer.web.eval(
            f"{payload_config}\n"
            "if (typeof window.applyClozeConfigLive === 'function') { "
            "window.applyClozeConfigLive(window.MINIMAL_CLOZE_CONFIG); } "
            "else if (typeof window.setupClozeInteractions === 'function') "
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
    gui_hooks.card_will_show.append(on_card_will_show)
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
