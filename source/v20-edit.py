#!/usr/bin/env python3
"""v19 -> v20: the OneNote import points to the picture picker, which takes the "OneNote pictures" folder."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

rep('''        <div id="oneReview"></div>''', '''        <div id="oneReview"></div>
        <div class="stack" style="margin-top:8px;border-top:1px solid var(--line);padding-top:14px">
          <div class="section-label">Pictures from OneNote</div>
          <p class="muted">The pictures from your OneNote PDF come in through the same picker as Notion's. Choose the "OneNote pictures" folder there, and each picture goes on its day under Charts.</p>
          <div class="actions" style="justify-content:flex-start"><button type="button" data-open-import="notion" data-scroll-to="notionPics">Go to the picture import</button></div>
        </div>''')
rep('''if (b) { showTab("import"); setImportMode(b.dataset.openImport); } });''', '''if (b) { showTab("import"); setImportMode(b.dataset.openImport); if (b.dataset.scrollTo) $(b.dataset.scrollTo)?.closest(".stack")?.scrollIntoView({ behavior: "smooth", block: "center" }); } });''')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
