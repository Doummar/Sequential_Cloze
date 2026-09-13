# Create and registers the "Sequential Cloze v1" Note Type with unified .ctrl + .ibtn layout

import os
try:
    from aqt import mw
except ImportError:
    mw = None

NOTE_TYPE_NAME = "Sequential Cloze v1"

FIELDS = [
    "Front",
    "Back",
    "Explanation",
    "Front Audio",
    "Back Audio",
    "Visible Image",
    "Image",
    "Info"
]

FRONT_HTML = """<div class="anki-card-container">
  <div class="ctrl">
    {{#Front Audio}}
    {{Front Audio}}
    {{/Front Audio}}
    {{^Front Audio}}
      {{#Front Sound}}
      {{Front Sound}}
      {{/Front Sound}}
    {{/Front Audio}}

    {{#Image}}
    <button type="button" class="ibtn" id="image-toggle-btn" onclick="toggleCardImage(event)" aria-label="Toggle Image" title="Toggle Image (G)">image</button>
    {{/Image}}

    {{#Info}}
    <button type="button" class="ibtn" id="info-toggle-btn" onclick="toggleInfo(event)" aria-label="Toggle Info" title="Toggle Info (I)">info</button>
    {{/Info}}
  </div>

  <div class="minimal-front">
    {{cloze:Front}}
  </div>

  {{#Visible Image}}
  <div class="img-area">
    {{Visible Image}}
  </div>
  {{/Visible Image}}

  <div id="extra-area"></div>

  {{#Image}}
  <div id="raw-image" class="ms" style="display:none !important;">{{Image}}</div>
  {{/Image}}

  {{#Info}}
  <div id="raw-info" class="ms" style="display:none !important;">{{Info}}</div>
  {{/Info}}

  <div id="raw-front" class="ms" style="display:none !important;">{{Front}}</div>
</div>"""

BACK_HTML = """<div class="anki-card-container">
  <div class="ctrl">
    {{#Back Audio}}
    {{Back Audio}}
    {{/Back Audio}}
    {{^Back Audio}}
      {{#Back Sound}}
      {{Back Sound}}
      {{/Back Sound}}
    {{/Back Audio}}

    {{#Image}}
    <button type="button" class="ibtn" id="image-toggle-btn" onclick="toggleCardImage(event)" aria-label="Toggle Image" title="Toggle Image (G)">image</button>
    {{/Image}}

    {{#Info}}
    <button type="button" class="ibtn" id="info-toggle-btn" onclick="toggleInfo(event)" aria-label="Toggle Info" title="Toggle Info (I)">info</button>
    {{/Info}}
  </div>

  <div class="minimal-front">
    {{cloze:Front}}
  </div>

  {{#Visible Image}}
  <div class="img-area">
    {{Visible Image}}
  </div>
  {{/Visible Image}}

  <hr id="answer-splitter">

  {{#Back}}
  <div class="minimal-back">
    {{Back}}
  </div>
  {{/Back}}

  {{#Explanation}}
  <div class="minimal-explanation">
    {{Explanation}}
  </div>
  {{/Explanation}}

  <div id="extra-area"></div>

  {{#Image}}
  <div id="raw-image" class="ms" style="display:none !important;">{{Image}}</div>
  {{/Image}}

  {{#Info}}
  <div id="raw-info" class="ms" style="display:none !important;">{{Info}}</div>
  {{/Info}}

  <div id="raw-front" class="ms" style="display:none !important;">{{Front}}</div>
</div>"""

def _read_css() -> str:
    addon_dir = os.path.dirname(__file__)
    css_path = os.path.join(addon_dir, "styles", "sequential.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    return "/* Sequential Cloze CSS */"

def _read_js() -> str:
    addon_dir = os.path.dirname(__file__)
    js_path = os.path.join(addon_dir, "js", "cloze.js")
    if os.path.exists(js_path):
        with open(js_path, "r", encoding="utf-8") as f:
            return f.read()
    return "// Sequential Cloze JS"

def get_front_template() -> str:
    css = _read_css()
    js = _read_js()
    return f"{FRONT_HTML}\n\n<style id=\"sq-cloze-css\">\n{css}\n</style>\n\n<script id=\"sq-cloze-js\">\n{js}\n</script>"

def get_back_template() -> str:
    css = _read_css()
    js = _read_js()
    return f"{BACK_HTML}\n\n<style id=\"sq-cloze-css\">\n{css}\n</style>\n\n<script id=\"sq-cloze-js\">\n{js}\n</script>"

FRONT_TEMPLATE = get_front_template()
BACK_TEMPLATE = get_back_template()

def setup_note_type() -> None:
    models = mw.col.models
    existing = models.by_name(NOTE_TYPE_NAME)
    css = _read_css()
    fresh_front = get_front_template()
    fresh_back = get_back_template()

    if existing:
        existing_field_names = set(models.field_names(existing))
        modified = False

        for f_name in FIELDS:
            if f_name not in existing_field_names:
                fld = models.new_field(f_name)
                models.add_field(existing, fld)
                modified = True

        # Keep templates and CSS aligned with Sentence Builder system
        if existing.get('tmpls'):
            for tmpl in existing['tmpls']:
                if tmpl.get('qfmt') != fresh_front or tmpl.get('afmt') != fresh_back:
                    tmpl['qfmt'] = fresh_front
                    tmpl['afmt'] = fresh_back
                    modified = True

        if existing.get('css') != css:
            existing['css'] = css
            modified = True

        if modified:
            models.save(existing)
        return existing

    # Create new Cloze Note Type if not present
    m = models.new(NOTE_TYPE_NAME)
    m['type'] = 1  # Cloze note type in Anki

    for f_name in FIELDS:
        fld = models.new_field(f_name)
        models.add_field(m, fld)

    t = models.new_template("Card 1")
    t['qfmt'] = fresh_front
    t['afmt'] = fresh_back
    models.add_template(m, t)

    m['css'] = css
    models.add(m)
    models.save(m)
    return m
