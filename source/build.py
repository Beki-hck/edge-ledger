#!/usr/bin/env python3
"""Builds the desktop Edge Ledger (one HTML file that saves to a local folder) from the online artifact source."""
import pathlib, re, sys

HERE = pathlib.Path(__file__).parent
SRC = HERE.parent / "trading-journal.html"
OUT = HERE / "Edge Ledger.html"
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

def cut(start, end, new, keep_end=True):
    """Replace from `start` up to (not including, unless keep_end False) `end`."""
    global s
    i = s.index(start); j = s.index(end, i)
    if not keep_end:
        j += len(end)
    s = s[:i] + new + s[j:]

part = lambda n: (HERE / n).read_text()

# ---- document shell ----
rep('<title>Edge Ledger</title>', '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Edge Ledger</title>')
rep('</style>\n\n<header class="top">', '''
/* Folder gate: shown until the journal folder is open */
.gate { position: fixed; inset: 0; z-index: 40; display: grid; place-items: center; padding: 16px; background: var(--bg);
  background-image: radial-gradient(900px 500px at 85% -10%, rgba(167, 139, 250, 0.16), transparent 60%), radial-gradient(800px 500px at -10% 10%, rgba(110, 168, 255, 0.14), transparent 60%); }
.gate .panel { max-width: 560px; width: 100%; display: grid; gap: 14px; }
.gate .brandline { display: flex; align-items: center; gap: 10px; font-family: var(--font-display); font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; font-size: 0.95rem; }
.gate p { line-height: 1.6; }
.shot .shot-missing { position: absolute; inset: 0; display: grid; place-items: center; text-align: center; padding: 8px; }
.shot .shot-missing[hidden] { display: none; }
.keyrow { display: flex; gap: 8px; flex-wrap: wrap; }
.keyrow input { flex: 1 1 220px; width: auto; }
.switch { display: flex; gap: 10px; align-items: flex-start; font-size: 0.9rem; cursor: pointer; }
.switch input { margin-top: 4px; }
</style>
</head>
<body>

<div class="gate" id="gate" role="dialog" aria-modal="true" aria-label="Open your journal folder">
  <div class="panel">
    <div class="brandline"><span class="logo"><svg viewBox="0 0 24 24" fill="none" stroke="#061024" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l5-6 4 3 6-8"/><path d="M15 6h3v3"/></svg></span>Edge Ledger</div>
    <div class="stack" id="gateBody"><p class="muted">Opening your journal…</p></div>
  </div>
</div>

<header class="top">''')
rep('</script>\n', '</script>\n</body>\n</html>\n')
rep('<div class="notice" id="storageNotice">Connecting to your saved journal…</div>', '<div class="notice" id="storageNotice" hidden></div>')

# ---- state ----
rep('const S = { market: new Map(),', 'const S = { ff: new Map(), ffStatus: "", market: new Map(),')
rep('  let backend = null, assets = null, sampleFn = null;', '  let backend = null;')

# ---- storage: folder instead of claude.ai ----
cut('  // ---------- storage ----------', '\n  // ---------- accounts ----------', part('storage.js') + part('claude.js') + part('zip.js'))

# ---- screenshots ----
cut('  // screenshots: trades keep theirs', '  // ---------- playbooks ----------', part('shots.js') + '\n')
rep('<p class="calc field wide" id="shotOff" hidden>Screenshots need the journal opened from claude.ai while signed in.</p>\n', '')
rep('\n          <p class="calc" id="jShotOff" hidden>Screenshots need the journal opened from claude.ai while signed in.</p>', '')
rep('''    formShots = [...(t?.screenshots || [])]; renderShots();''', '''    discardShots(); formShots = [...(t?.screenshots || [])]; shotsOriginal = [...formShots]; renderShots();''')
rep('''    persist(() => backend.put("trades", t), sd && t.date < sd''', '''    const removedShots = [...shotsOriginal, ...shotsAdded].filter((n) => !t.screenshots.includes(n)); shotsAdded = new Set(); shotsOriginal = [];
    persist(() => backend.put("trades", t), sd && t.date < sd''')
rep('''it stays hidden. Change the start date in Settings to see it.` : reviewMode ? "Reviewed" : "Trade saved");''', '''it stays hidden. Change the start date in Settings to see it.` : reviewMode ? "Reviewed" : "Trade saved").then((ok) => { if (ok) commitShots(removedShots); else pendingDrops.push(...removedShots); });''')
rep('''    t.screenshots = formShots;''', '''    t.screenshots = [...formShots];''')
rep('''    const id = editingId; persist(() => backend.del("trades", id), "Trade deleted"); showTab(lastTab);''',
    '''    const id = editingId, files = [...(S.trades.get(id)?.screenshots || []), ...shotsAdded]; shotsAdded = new Set();
    persist(() => backend.del("trades", id), "Trade deleted").then((ok) => { if (ok) dropShots(files); else pendingDrops.push(...files); });
    showTab(lastTab);''')
rep('''  function showTab(tab) {
''', '''  function showTab(tab) {
    if (tab !== "editor") discardShots();
''')

# ---- greeting name ----
rep('  let viewerName = "";\n', '')
rep('${esc(viewerName || "trader")}', '${esc(String(S.settings.name || "").split(" ")[0] || "trader")}')

# ---- market news: ForexFactory scheduled events + Claude log ----
rep('''  const autoNews = (date) => ((S.market.get(date) || {}).events || []).filter((e) => e.impact === "high" && e.tag).map((e) => e.tag);''',
    '''  const autoNews = (date) => [...((S.market.get(date) || {}).events || []), ...(S.ff.get(date) || [])].filter((e) => e.impact === "high" && e.tag).map((e) => e.tag);''')
rep('''  function autoMarketHtml(date) {
    const m = S.market.get(date);
    if (!m) return "";''', '''  const evLine = (e) => `<div><span class="when">${esc(e.time || "")}</span><span>${e.impact === "high" ? "<strong>" : ""}${esc(e.name)}${e.impact === "high" ? "</strong>" : ""}${e.actual != null && e.actual !== "" ? ` · actual <span class="num">${esc(e.actual)}</span>` : ""}${e.forecast ? ` ${e.actual ? "vs" : "· forecast"} <span class="num">${esc(e.forecast)}</span>${e.actual ? " exp." : ""}` : ""}${e.previous ? ` <span class="muted">(prev ${esc(e.previous)})</span>` : ""}${e.note ? ` <span class="muted">${esc(e.note)}</span>` : ""}</span></div>`;
  function autoMarketHtml(date) {
    const m = S.market.get(date);
    if (!m) {
      const ff = S.ff.get(date) || [];
      return ff.length ? `<div class="stack" style="gap:8px;width:100%;margin-top:4px"><div class="events" style="margin-top:0">${ff.map(evLine).join("")}</div><span class="calc">Red-folder USD events from the ForexFactory calendar.</span></div>` : "";
    }''')
rep('''    const evs = (m.events || []).map((e) => `<div><span class="when">${esc(e.time || "")}</span><span>${e.impact === "high" ? "<strong>" : ""}${esc(e.name)}${e.impact === "high" ? "</strong>" : ""}${e.actual != null && e.actual !== "" ? ` · actual <span class="num">${esc(e.actual)}</span>` : ""}${e.forecast ? ` vs <span class="num">${esc(e.forecast)}</span> exp.` : ""}${e.previous ? ` <span class="muted">(prev ${esc(e.previous)})</span>` : ""}${e.note ? ` <span class="muted">${esc(e.note)}</span>` : ""}</span></div>`).join("");''',
    '''    const evs = (m.events || []).map(evLine).join("");''')
rep('''<span class="calc">Logged automatically${m.sources?.length''', '''<span class="calc">${m.by === "claude" ? "Logged by Claude" : "Logged automatically"}${m.sources?.length''')
rep('''(auto || (date < today() && S.mode === "cloud" ? `<span class="calc" style="width:100%">No automatic news log for this day.</span>` : ""));''',
    '''(auto || "") + newsButton(date);''')
s = s.replace('''  function marketHtml(date) {''', '''  function newsButton(date) {
    if (date > today() || !S.mode || S.mode !== "folder") return "";
    if (newsBusy === date) return `<span class="calc" style="width:100%">Claude is looking up the news for this day…</span>`;
    const has = S.market.has(date);
    return `<span style="width:100%;display:flex;gap:8px;flex-wrap:wrap;align-items:center">${has ? "" : `<span class="calc">No news log for this day yet.</span>`}<button type="button" class="btn-small" data-fetch-news="${esc(date)}">${has ? "Refresh news with Claude" : "Log this day's news with Claude"}</button></span>`;
  }
  document.addEventListener("click", async (e) => {
    const b = e.target.closest("[data-fetch-news]"); if (!b) return;
    if (!apiKey()) { toast("Add your Claude API key in Settings to log news."); return; }
    const d = b.dataset.fetchNews;
    if (await fetchNewsDay(d)) { if (!$("view-editor").hidden) updateMarket(); if (loadedDay === d) $("jMarket").innerHTML = marketHtml(d); }
  });
  function marketHtml(date) {''', 1)

# today console: today's red-folder releases with their times
rep('''      ...events.map((e) => `<span class="pill warn">⚑ ${esc(e)}</span>`),''',
    '''      ...(S.ff.get(day) || []).map((e) => `<span class="pill bad">⚑ ${esc(e.time ? e.time.replace(" ET", "") + " " : "")}${esc(e.name)}</span>`),
      ...events.filter((e) => !(S.ff.get(day) || []).some((f) => f.tag === e)).map((e) => `<span class="pill warn">⚑ ${esc(e)}</span>`),''')

# ---- coach: Claude API with the trader's key ----
rep('<p class="muted">Claude reads your trades, playbooks, journal entries and the account rules, then tells you what it sees. Each question uses your own Claude usage.</p>',
    '<p class="muted">Claude reads your trades, playbooks, journal entries and the account rules, then tells you what it sees. It uses your Claude API key, and each answer costs a few cents.</p>')
rep('<div id="coachOff" class="notice" hidden>The coach needs the journal opened from claude.ai while signed in, with Claude allowed for this page.</div>',
    '<div id="coachOff" class="notice" hidden>The coach needs your Claude API key. Add it in Settings under Claude.</div>')
rep('''    if (!sampleFn) { $("coachOff").hidden = false; return; }''', '''    if (!apiKey()) { $("coachOff").hidden = false; return; }
    $("coachOff").hidden = true;''')
rep('''      const res = await sampleFn(prompt, { signal: ctl.signal, cache: false, onText: ({ text }) => { if (coachCtl === ctl) $("coachOut").innerHTML = mdLite(text); } });
      if (coachCtl !== ctl) return;
      $("coachOut").innerHTML = mdLite(res.text) + (res.truncated ? `<p class="calc">The answer was cut short.</p>` : "");''',
    '''      const res = await callClaude({ max_tokens: 16000, output_config: { effort: "medium" }, messages: [{ role: "user", content: prompt }] }, { signal: ctl.signal, onText: (text) => { if (coachCtl === ctl) $("coachOut").innerHTML = mdLite(text); } });
      if (coachCtl !== ctl) return;
      $("coachOut").innerHTML = res.stop === "refusal" && !res.text ? `<p class="loss">Claude declined to answer that one. Try asking it differently.</p>` : mdLite(res.text) + (res.stop === "max_tokens" ? `<p class="calc">The answer was cut short.</p>` : "");''')
rep('''      else if (["not_granted", "sampling_disabled", "not_declared", "capability_disabled", "capability_removed"].includes(c)) { $("coachOut").innerHTML = ""; $("coachOff").hidden = false; }
      else if (c === "rate_limited") $("coachOut").innerHTML = `<p class="loss">You've hit your usage limit for now. Try again later.</p>`;
      else if (c === "prompt_too_large") $("coachOut").innerHTML = `<p class="loss">Too much journal data for one question. Try "Review this week".</p>`;
      else $("coachOut").innerHTML = (e?.text ? mdLite(e.text) : "") + `<p class="loss">The coach couldn't finish. Try again.</p>`;''',
    '''      else $("coachOut").innerHTML = (e?.text ? mdLite(e.text) : "") + `<p class="loss">${esc(claudeErrorText(c))}</p>`;''')

# ---- settings: folder, name, Claude key, news, backup ----
rep('''    <div class="panel">
      <div class="panel-head"><h2>Backup</h2></div>
      <p class="muted" style="margin-bottom:12px">Download everything as a JSON file, or restore from one. Screenshots stay in the journal and aren't included in the file. Moving to the desktop version? <strong>Export for desktop</strong> saves one .zip with everything, screenshots and news log included.</p>
      <div class="actions" style="justify-content:flex-start">
        <button class="btn-primary" id="exportDesktop">Export for desktop</button>
        <button id="exportBtn">Download backup</button>
        <label class="btn" for="importFile">Restore from file</label>
        <input type="file" id="importFile" accept="application/json,.json" hidden>
      </div>
    </div>''', '''    <div class="grid2">
      <div class="panel">
        <div class="panel-head"><h2>You and your folder</h2></div>
        <div class="stack">
          <div class="field"><label for="sName">Your name</label><div class="keyrow"><input id="sName" placeholder="Shown in the greeting"><button id="sNameSave">Save</button></div></div>
          <p class="calc" id="folderInfo"></p>
          <div class="actions" style="justify-content:flex-start"><button id="folderChange">Use a different folder</button></div>
          <p class="calc">Your folder keeps journal.json, a screenshots folder, a news folder, and a backups folder with one copy of your journal per day for the last 30 days. To back up everything, copy the whole folder, or keep it inside Google Drive or OneDrive on your computer.</p>
        </div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>Claude</h2><span class="label">Coach and news log</span></div>
        <div class="stack">
          <p class="muted" style="font-size:.9rem">The coach and the automatic news log use your own Claude API key. Create one at console.anthropic.com under API keys, add a little credit, and paste it here. A coach answer costs a few cents, and a day's news log costs roughly 10 to 30 cents.</p>
          <div class="field"><label for="sKey">Claude API key</label><div class="keyrow"><input id="sKey" type="password" autocomplete="off" spellcheck="false" placeholder="sk-ant-…"><button id="sKeySave">Save key</button><button id="sKeyRemove" class="btn-danger">Remove</button></div></div>
          <p class="calc" id="sKeyInfo"></p>
          <label class="switch" for="sAutoNews"><input type="checkbox" id="sAutoNews"><span>Log each weekday's market news automatically after 4:30 pm New York time, while Edge Ledger is open</span></label>
          <label class="switch" for="sFF"><input type="checkbox" id="sFF"><span>Show red-folder USD events from the free ForexFactory calendar (no key needed)</span></label>
          <p class="calc" id="sFFInfo"></p>
        </div>
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>Backup and moving in</h2></div>
      <p class="muted" style="margin-bottom:12px">Download everything except screenshots as one file, or bring in a backup. To move from Edge Ledger online, open it on claude.ai, go to Settings and click <strong>Export for desktop</strong>, then pick that .zip file here. Your trades, journal, playbooks, accounts, news log and screenshots all come across.</p>
      <div class="actions" style="justify-content:flex-start">
        <button id="exportBtn">Download backup</button>
        <label class="btn" for="importFile">Restore or move in from a file</label>
        <input type="file" id="importFile" accept="application/json,.json,application/zip,.zip" hidden>
      </div>
    </div>''')
rep('''    renderListEditor("listNews", "news", "News types", "Add a news type");
  }''', '''    renderListEditor("listNews", "news", "News types", "Add a news type");
    renderDesktopSettings();
  }
  function renderDesktopSettings() {
    if (document.activeElement !== $("sName")) $("sName").value = S.settings.name || "";
    $("folderInfo").innerHTML = dir ? `Saving to the folder <strong>${esc(dir.name)}</strong>.` : "No folder open.";
    const k = apiKey();
    if (document.activeElement !== $("sKey")) $("sKey").value = "";
    $("sKey").placeholder = k ? `Saved: ${k.slice(0, 10)}…${k.slice(-4)}` : "sk-ant-…";
    $("sKeyRemove").hidden = !k;
    $("sKeyInfo").textContent = k ? "Your key is saved in this browser on this computer only. It isn't written to your journal folder or backups." : "No key saved. The coach and news log are off.";
    $("sAutoNews").checked = !!S.settings.autoNews; $("sAutoNews").disabled = !k;
    $("sFF").checked = !S.settings.ffOff;
    $("sFFInfo").textContent = S.settings.ffOff ? "" : S.ffStatus === "failed" ? "The ForexFactory calendar couldn't be reached just now. Edge Ledger tries again later." : S.ff.size ? `Calendar loaded: ${[...S.ff.values()].reduce((a, v) => a + v.length, 0)} red-folder events.` : "";
  }
  $("sNameSave").addEventListener("click", () => saveSettings({ name: $("sName").value.trim() }).then((ok) => ok && toast("Name saved")));
  $("sName").addEventListener("keydown", (e) => { if (e.key === "Enter") $("sNameSave").click(); });
  $("folderChange").addEventListener("click", () => switchFolder());
  $("sKeySave").addEventListener("click", () => {
    const v = $("sKey").value.trim();
    if (!/^sk-ant-[A-Za-z0-9_\\-]{20,}$/.test(v)) { toast("That doesn't look like a Claude API key. It starts with sk-ant-."); return; }
    try { localStorage.setItem(KEY_LS, v); toast("Key saved"); } catch { toast("Couldn't save the key in this browser."); }
    renderDesktopSettings();
  });
  $("sKeyRemove").addEventListener("click", () => { try { localStorage.removeItem(KEY_LS); } catch {} saveSettings({ autoNews: false }); renderDesktopSettings(); toast("Key removed"); });
  $("sAutoNews").addEventListener("change", () => saveSettings({ autoNews: $("sAutoNews").checked }).then(() => { renderDesktopSettings(); autoLogNews(); }));
  $("sFF").addEventListener("change", () => saveSettings({ ffOff: !$("sFF").checked }).then(() => { if (!S.settings.ffOff) loadFF(); else { S.ff = new Map(); render(); } renderDesktopSettings(); }));''')

# ---- backup: plain download, restore handles .zip ----
cut("  // Export for the desktop app:", '  $("importFile").addEventListener', "")
rep('''    let dl = null; try { dl = await window.claude?.use?.("downloads"); } catch {}
    const filename = `trading-journal-${today()}.json`, data = JSON.stringify(o, null, 2);
    if (!dl) {
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([data], { type: "application/json" })); a.download = filename;
      document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000); return;
    }
    try { await dl.save({ filename, data }); } catch { toast("Backup was not saved."); }''',
    '''    o.market = [...S.market.values()];
    const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([JSON.stringify(o, null, 2)], { type: "application/json" })); a.download = `edge-ledger-backup-${today()}.json`;
    document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);''')
cut('''    const f = $("importFile").files[0]; if (!f) return;
    try {''', '''    $("importFile").value = "";''', '''    const f = $("importFile").files[0]; if (!f) return;
    toast("Reading the file…");
    try {
      const r = await importBackup(f);
      toast(`Brought in ${plural(r.trades, "trade")}${r.shots ? `, ${plural(r.shots, "screenshot")}` : ""}${r.news ? ` and ${plural(r.news, "news day")}` : ""}`);
      renderSettings();
    } catch (e) { toast(e?.name === "QuotaExceededError" ? "Your disk is full." : "That file isn't an Edge Ledger backup or export."); }
''')

rep('''    for (const t of fixes) { try { await backend.put("trades", t); fixed++; } catch {} }''',
    '''    // One save for each batch. If it fails, the trades stay in the journal and the notice at the top offers Try again.
    try { await backend.putMany("trades", fixes); } catch {}
    fixed = fixes.length;''')
rep('''    for (const t of list) { try { await backend.put("trades", t); ok++; } catch (e) { if (e?.code === "quota_exceeded") break; } }''',
    '''    try { await backend.putMany("trades", list); } catch {}
    ok = list.length;''')

# ---- tab memory key and boot ----
rep('''  initStorage();
})();''', '''  initStorage();
})();''')

# leftovers that must not survive
for bad in ["window.claude", "sampleFn", "/_blob/", "assets.upload", "localBackend", "makeDbBackend", 'S.mode === "cloud"']:
    if bad in s:
        sys.exit(f"leftover: {bad}")
OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
