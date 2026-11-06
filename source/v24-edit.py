#!/usr/bin/env python3
"""v23 -> v24 (PC): accessibility fixes from the design review. The folder gate keeps keyboard focus and hides
the app behind it, every select shows a focus ring when reached by Tab, and the session labels on the kill-zone
track are larger with stronger contrast."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

# Tab must stay inside the gate: make everything else inert while it is open, and focus its first button.
rep('''    const g = $("gate");
    g.hidden = !state;
    if (!state) return;''', '''    const g = $("gate");
    g.hidden = !state;
    for (const el of document.body.children) if (el !== g && el.tagName !== "SCRIPT") el.inert = !!state;
    if (!state) return;''')
rep('''    $("gateBody").innerHTML = body;
  }''', '''    $("gateBody").innerHTML = body;
    g.querySelector("button")?.focus();
  }''')

# Selects (and inputs) show a visible ring on keyboard focus.
rep('input:focus, select:focus, textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(110,168,255,0.18); }',
    'input:focus, select:focus, textarea:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(110,168,255,0.18); }\n'
    'input:focus-visible, select:focus-visible, textarea:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; box-shadow: 0 0 0 3px rgba(110,168,255,0.35); }')

# Kill-zone session labels: readable size and contrast.
rep('.kz-track i span { position: absolute; left: 4px; top: 4px; font-size: 0.62rem; color: var(--fg); white-space: nowrap; letter-spacing: 0.04em; }',
    '.kz-track i span { position: absolute; left: 4px; top: 3px; font-size: 0.72rem; font-weight: 600; color: #fff; white-space: nowrap; letter-spacing: 0.03em; padding: 0 4px; border-radius: 4px; background: rgba(5,9,20,0.75); }')

OUT.write_text(s)
