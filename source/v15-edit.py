#!/usr/bin/env python3
"""v14 -> v15: import the old journal (OneNote notebook text, Notion CSV) from Trades > Import."""
import pathlib, sys

HERE = pathlib.Path(__file__).parent
SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

# ---- import view: three sources ----
rep('''      <div class="panel-head"><h2>Import trades</h2><button id="importClose">Back</button></div>
      <div class="stack">
        <p class="muted">Export your closed trades''', '''      <div class="panel-head"><h2>Import trades</h2><button id="importClose">Back</button></div>
      <div class="filters" style="margin-bottom:14px"><div class="seg" role="group" aria-label="What to import" id="impModes"><button type="button" data-imp-mode="platform" aria-pressed="true">Platform</button><button type="button" data-imp-mode="onenote" aria-pressed="false">OneNote</button><button type="button" data-imp-mode="notion" aria-pressed="false">Notion</button></div></div>
      <div class="stack" id="imp-platform">
        <p class="muted">Export your closed trades''')
rep('''        <div id="impPreview"></div>
      </div>
    </div>
  </section>''', '''        <div id="impPreview"></div>
      </div>
      <div class="stack" id="imp-onenote" hidden>
        <p class="muted">Brings in your OneNote trading journal. Each page becomes a day in the journal with its thoughts and its good and bad points, and each P/L becomes a trade. Nothing is saved until you check the list and click Bring in.</p>
        <ul class="muted" style="margin:0;padding-left:1.2em;font-size:.88rem">
          <li>In OneNote, print your trading journal section to PDF.</li>
          <li>Open the PDF in Chrome or Edge, press Ctrl+A and then Ctrl+C, and paste it below. If you have the notebook as a .txt file, choose that instead.</li>
        </ul>
        <div class="fields">
          <div class="field"><label for="oneFile">Choose a .txt file</label><input type="file" id="oneFile" accept=".txt,text/plain"></div>
          <div class="field wide"><label for="onePaste">Or paste the notebook's text</label><textarea id="onePaste" placeholder="Paste everything copied from the PDF"></textarea></div>
        </div>
        <div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="oneRead">Read my notebook</button></div>
        <div id="oneReview"></div>
      </div>
      <div class="stack" id="imp-notion" hidden>
        <p class="muted">Brings in a Notion trading journal. Each row with a P/L becomes a trade, and rows without one are saved as notes on their day.</p>
        <ul class="muted" style="margin:0;padding-left:1.2em;font-size:.88rem">
          <li>In Notion, open the journal database as a full page, click ••• at the top right, then Export. Pick Markdown &amp; CSV and export.</li>
          <li>Unzip the download and choose the .csv file inside. If there are two, choose the one ending in _all.</li>
        </ul>
        <div class="fields">
          <div class="field"><label for="notionFile">Choose the .csv file</label><input type="file" id="notionFile" accept=".csv,text/csv,.txt,.zip"></div>
          <div class="field"><label for="notionDateOrder">Date format</label><select id="notionDateOrder"><option value="auto">Detect automatically</option><option value="mdy">Month / day / year</option><option value="dmy">Day / month / year</option></select></div>
          <div class="field"><label for="notionInstr">Market when a row has none</label><select id="notionInstr"></select></div>
          <div class="field"><span class="flabel">Mock, backtest and BE rows</span><div class="chips"><label for="notionMock"><input type="checkbox" id="notionMock">Count them as trades</label></div></div>
        </div>
        <div id="notionMap" hidden>
          <div class="section-label">Match the columns</div>
          <div class="map-grid" id="notionMapGrid"></div>
        </div>
        <div id="notionPreview"></div>
      </div>
    </div>
  </section>''')
rep('#impPaste { field-sizing: fixed; }', '#impPaste, #onePaste { field-sizing: fixed; }\n#oneReview td { vertical-align: top; }\n#oneReview thead th { position: sticky; top: 0; background: var(--surface-solid); z-index: 1; }')

# ---- journal: a way in from Past entries ----
rep('''        <div class="panel-head"><h2>Past entries</h2></div>''', '''        <div class="panel-head"><h2>Past entries</h2><button type="button" class="btn-small" data-open-import="onenote">Bring in my old journal</button></div>''')

# ---- online storage: save many in one go (the desktop storage already has putMany) ----
rep('''    async saveSettings(s) { S.settings = s; lsSave(); render(); },
  };''', '''    async saveSettings(s) { S.settings = s; lsSave(); render(); },
    async putMany(coll, list) { list.forEach((o) => S[coll].set(o.id, o)); lsSave(); render(); },
  };''')
rep('''      put: (coll, obj) => refs[coll].doc(obj.id).set(strip(obj)),''', '''      put: (coll, obj) => refs[coll].doc(obj.id).set(strip(obj)),
      async putMany(coll, list) { for (let i = 0; i < list.length; i += 20) await Promise.all(list.slice(i, i + 20).map((o) => refs[coll].doc(o.id).set(strip(o)))); },''')

# ---- the importer itself ----
rep('''  // ---------- settings: accounts ----------''', (HERE / "oldjournal.js").read_text() + '''  // ---------- settings: accounts ----------''')

# ---- small fixes the import brings up: imported trades have no direction; Back returns where you came from ----
rep('<select id="tDir"><option>Long</option><option>Short</option></select>', '<select id="tDir"><option value="">Not set</option><option>Long</option><option>Short</option></select>')
rep('      if (x != null) bits.push(`captured', '      if (x != null && $("tDir").value) bits.push(`captured')
rep('prev.instrument === t.instrument && prev.dir !== t.dir', 'prev.instrument === t.instrument && prev.dir && t.dir && prev.dir !== t.dir')
rep('  $("importBtn").addEventListener("click", () => showTab("import"));\n  $("importClose").addEventListener("click", () => showTab("trades"));', '  $("importBtn").addEventListener("click", () => { showTab("import"); setImportMode("platform"); });\n  $("importClose").addEventListener("click", () => showTab(lastTab));')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
