#!/usr/bin/env python3
"""v18 -> v19: the picture import also takes the "OneNote pictures" folder (pulled from the OneNote PDF, one .md page per day)."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

rep('Pictures from the Notion export</div>', 'Pictures from Notion or OneNote</div>')
rep('Choose the unzipped export folder, the one with the .md pages and the image files.', 'Choose the unzipped Notion export folder (the one with the .md pages and the image files), or the "OneNote pictures" folder.')
rep('<label for="notionPics">Choose the export folder</label>', '<label for="notionPics">Choose the pictures folder</label>')
rep('That folder has no Notion pages (.md files). Choose the unzipped export folder.', 'That folder has no pages (.md files). Choose the unzipped Notion export folder or the OneNote pictures folder.')
rep("Couldn't read that folder. Choose the unzipped Notion export folder.", "Couldn't read that folder. Choose the unzipped Notion export folder or the OneNote pictures folder.")

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
