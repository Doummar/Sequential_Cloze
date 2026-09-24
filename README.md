# Sequential Cloze

A focused Anki add-on for reviewing cloze cards step by step.

Sequential Cloze provides two ways to work with cloze deletions:

- **Sequential Reveal** — reveal hidden cloze parts one by one.
- **Sequential Context** — review ordered cloze items while keeping nearby information visible as context.

The goal is simple: reduce visual clutter and let you focus on the information you are currently studying.

---

## Review Modes

### Sequential Reveal

Reveal hidden cloze segments progressively instead of showing everything at once.

For example:

```text
The capital of France is {{c1::Paris}}.
The capital of Germany is {{c2::Berlin}}.
The capital of Italy is {{c3::Rome}}.

Instead of revealing all answers together, Sequential Reveal lets you move through them one at a time.

Controls:

Space / Enter — reveal the next cloze
Click — reveal or hide an individual cloze
Shift + Space — reveal all clozes
Mouse wheel down — reveal the next cloze
When all clozes are revealed, continue normally and flip the card
Sequential Context

Sequential Context is designed for ordered information such as:

Lists
Sequences
Steps in a process
Numbered information
Ordered study material

It uses numbered clozes such as:

{{c1::First item}}
{{c2::Second item}}
{{c3::Third item}}
{{c4::Fourth item}}

You can review one item while keeping nearby items visible.

This provides context without revealing the entire sequence.

Context Options

Sequential Context lets you control how much surrounding information is shown.

Context Before — show previous items on the front
Context After — show following items on the front
Back Context Before / After — control context shown on the back
Mask Subsequent Items — hide future items outside the selected context window
Optional Card Content

Sequential Cloze also supports additional content that can be revealed when needed.

Field	Purpose
Visible Image	Image that is always visible
Image	Image that can be toggled during review
Info	Additional information that can be toggled
Front Audio	Audio control on the front
Back Audio	Audio control on the back
Explanation	Additional explanation shown on the back
Default Shortcuts
G — toggle Image
H — toggle Info

Shortcuts and mouse bindings can be changed in:

Settings → Reveal Controls

Features
Sequential cloze reveal
Sequential context review
One-by-one cloze learning
Progressive information reveal
Context before and after selected items
Adjustable context window
Optional masking of subsequent items
Click-to-reveal clozes
Keyboard shortcuts
Mouse wheel reveal
Reveal-all option
Configurable reveal speed
Custom reveal behaviour
Animation and transition controls
Custom highlighting and visibility options
Centered and focused layouts
Custom font family and font size
Optional bold cloze text
Light and Dark mode support
Optional images, information, audio, and explanations
Settings
General

Configure the general appearance of your cards.

Layout
Font family
Font size
Bold cloze text
Reveal Controls

Configure how Sequential Reveal behaves.

Reveal speed
Click-to-reveal
Keyboard shortcuts
Mouse bindings
Compatibility

Optional custom cloze color settings for compatibility with different card styles.

Sequential Context

Configure the context-based review mode.

Enable or disable Sequential Context
Context before
Context after
Back context before
Back context after
Mask subsequent items
Works Across Anki

The interactive card functionality is built with standard:

HTML
CSS
JavaScript

The Python add-on is used for setup and configuration, but it is not required to run the interactive card functionality during review.

Once the cards are configured, they can be reviewed on:

Anki Desktop
AnkiMobile
AnkiDroid
AnkiWeb

This makes it possible to configure your cards on desktop and continue studying on other devices.

Good For

Sequential Cloze can be useful for:

Large cloze cards
Information-heavy cards
Active recall
Step-by-step learning
Ordered lists and sequences
Language learning
Vocabulary
Grammar
History
Science
Medicine
Anatomy
Complex topics
Reducing visual distractions
Focused study sessions
Installation
From AnkiWeb

Install Sequential Cloze from AnkiWeb:

Sequential Cloze – AnkiWeb

From GitHub

Clone or download this repository and install the add-on in your Anki add-ons directory.

Restart Anki after installation if required.

How It Works

Sequential Cloze uses Anki card templates together with HTML, CSS, and JavaScript to provide the interactive review experience.

The desktop Python component handles configuration and setup.

The interactive review logic runs inside the card itself, which is why the configured cards can continue to work on supported Anki clients without the desktop Python add-on running during review.

Compatibility

Designed for Anki Desktop and card review across:

Windows
macOS
Linux
AnkiMobile
AnkiDroid
AnkiWeb

The interactive card functionality is based on standard web technologies rather than requiring Python during review.

Feedback and Issues

Found a bug, compatibility problem, or have an idea for improving Sequential Cloze?

Please open an issue:

GitHub Issues

When reporting a problem, please include:

Anki version
Operating system
Anki client/device
Steps to reproduce the problem
Relevant card/template information
Screenshots or recordings when useful
Related Add-ons
FocusFlow — study activity, focus, and progress tracking
Cloze Dropdown — interactive dropdown choices for cloze cards
Mouse Buttons as Review Shortcuts — use mouse buttons as Anki review shortcuts
License

MIT License

Copyright (c) 2026 Adel Aitah
