#!/usr/bin/env python3
"""v16 -> v17: move trades from one account to another (for an import that went into the wrong account)."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

rep('''          <button id="importBtn">Import trades</button>
        </div>
      </div>
      <div id="tradeTable"></div>
    </div>''', '''          <button id="importBtn">Import trades</button>
          <button type="button" id="moveBtn">Move trades</button>
        </div>
      </div>
      <div id="tradeTable"></div>
    </div>
    <div class="panel" id="movePanel" hidden>
      <div class="panel-head"><h2>Move trades</h2><button type="button" id="moveClose">Close</button></div>
      <div class="stack">
        <p class="muted">Moves trades from <strong id="mvFromAcct"></strong> to another account. Their notes, reviews and screenshots go with them.</p>
        <div class="fields">
          <div class="field"><label for="mvSource">Which trades</label><select id="mvSource"><option value="">All trades</option><option value="import">Imported from a platform</option><option value="hand">Logged by hand</option><option value="onenote">From OneNote</option><option value="notion">From Notion</option></select></div>
          <div class="field"><label for="mvStart">From</label><input type="date" id="mvStart"></div>
          <div class="field"><label for="mvEnd">To</label><input type="date" id="mvEnd"></div>
          <div class="field"><label for="mvTarget">Move them to</label><select id="mvTarget"></select></div>
        </div>
        <div id="mvPreview"></div>
      </div>
    </div>''')

rep('''  $("importBtn").addEventListener("click", () => { showTab("import"); setImportMode("platform"); });''', '''  $("importBtn").addEventListener("click", () => { showTab("import"); setImportMode("platform"); });

  // ---------- move trades between accounts ----------
  const sourceOf = (t) => (t.source === "import" || t.source === "onenote" || t.source === "notion" ? t.source : t.extId ? "import" : "hand");
  // A platform import's id carries its account, so a later import of the same file into the new account knows it's there.
  const movedExt = (t, from, to) => (t.extId && t.extId.startsWith(from + ":") ? to + t.extId.slice(from.length) : t.extId);
  const mvPick = () => {
    const acc = activeAccount(), src = $("mvSource").value, a = $("mvStart").value, b = $("mvEnd").value;
    return [...S.trades.values()].filter((t) => accOf(t) === acc.id && (!src || sourceOf(t) === src) && (!a || t.date >= a) && (!b || t.date <= b)).sort((x, y) => sortKey(x).localeCompare(sortKey(y)));
  };
  function mvRange() {
    const acc = activeAccount(), src = $("mvSource").value;
    const dates = [...S.trades.values()].filter((t) => accOf(t) === acc.id && (!src || sourceOf(t) === src)).map((t) => t.date).filter(Boolean).sort();
    $("mvStart").value = dates[0] || ""; $("mvEnd").value = dates[dates.length - 1] || "";
  }
  function openMove() {
    const acc = activeAccount(), others = accountsSorted().filter((a) => a.id !== acc.id);
    if (!others.length) { toast("Add a second account in Settings first."); return; }
    $("mvFromAcct").textContent = acc.name || "this account"; $("mvFromAcct").dataset.id = acc.id;
    $("mvTarget").innerHTML = others.map((a) => `<option value="${esc(a.id)}">${esc(a.name || "Account")}${a.status && a.status !== "active" ? ` (${esc(a.status)})` : ""}</option>`).join("");
    $("mvTarget").value = (others.find((a) => a.status === "active" && !a.importTarget) || others[0]).id;
    // In the old-journal account, platform imports are the ones that most likely went there by mistake.
    $("mvSource").value = acc.importTarget && [...S.trades.values()].some((t) => accOf(t) === acc.id && sourceOf(t) === "import") ? "import" : "";
    mvRange(); $("movePanel").hidden = false; renderMove(); $("movePanel").scrollIntoView({ block: "nearest" });
  }
  let moving = false;
  function renderMove() {
    if ($("movePanel").hidden || moving) return;
    const acc = activeAccount(), to = S.accounts.get($("mvTarget").value), list = mvPick();
    if ($("mvFromAcct").dataset.id !== acc.id) { $("movePanel").hidden = true; return; } // the account at the top changed
    if (!to) { $("mvPreview").innerHTML = ""; return; }
    const there = new Set([...S.trades.values()].filter((t) => accOf(t) === to.id && t.extId).map((t) => t.extId));
    const dupes = list.filter((t) => t.extId && there.has(movedExt(t, acc.id, to.id))), s = summarize(list);
    $("mvPreview").innerHTML = list.length ? `<div class="stack"><p><strong>${plural(list.length, "trade")}</strong> from ${esc(fmtDay(list[0].date, { month: "short", day: "numeric", year: "numeric" }))} to ${esc(fmtDay(list[list.length - 1].date, { month: "short", day: "numeric", year: "numeric" }))}, net <span class="num ${cls(s.net)}">${money(s.net)}</span>.${dupes.length ? ` ${plural(dupes.length, "trade")} ${dupes.length === 1 ? "is" : "are"} already in ${esc(to.name)}, so ${dupes.length === 1 ? "that copy is" : "those copies are"} folded into ${dupes.length === 1 ? "it" : "them"}: anything you wrote on ${dupes.length === 1 ? "it" : "them"} here is kept.` : ""}</p>
      <div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="mvGo">${[list.length > dupes.length ? `Move ${plural(list.length - dupes.length, "trade")} to ${esc(to.name || "Account")}` : "", dupes.length ? `${list.length > dupes.length ? "fold in" : "Fold in"} ${dupes.length} ${dupes.length === 1 ? "copy" : "copies"}` : ""].filter(Boolean).join(", ")}</button></div></div>` : `<p class="muted">No trades in ${esc(acc.name || "this account")} match.</p>`;
    $("mvGo")?.addEventListener("click", doMove);
  }
  async function doMove() {
    const acc = activeAccount(), to = S.accounts.get($("mvTarget").value), list = mvPick(); if (!to || !list.length) return;
    $("mvGo").disabled = true; $("mvGo").textContent = "Moving…";
    const there = new Set([...S.trades.values()].filter((t) => accOf(t) === to.id && t.extId).map((t) => t.extId));
    const twinOf = new Map([...S.trades.values()].filter((t) => accOf(t) === to.id && t.extId).map((t) => [t.extId, t]));
    const dupes = list.filter((t) => t.extId && twinOf.has(movedExt(t, acc.id, to.id))), go = list.filter((t) => !dupes.includes(t));
    const early = to.startDate ? list.filter((t) => t.date < to.startDate).length : 0;
    moving = true;
    try {
      if (go.length) await backend.putMany("trades", go.map((t) => ({ ...t, accountId: to.id, extId: movedExt(t, acc.id, to.id) })));
      // A copy the other account already has: what you wrote on it joins that copy, then it goes.
      if (dupes.length) await backend.putMany("trades", dupes.map((t) => { const twin = twinOf.get(movedExt(t, acc.id, to.id)); return { ...mergeTwin(t, twin, twin.id), mergedFrom: twin.mergedFrom || "" }; }));
      for (const t of dupes) await backend.del("trades", t.id);
      moving = false; $("movePanel").hidden = true;
      toast([go.length ? `Moved ${plural(go.length, "trade")} to ${to.name || "the other account"}.` : "", dupes.length ? `Folded ${dupes.length} ${dupes.length === 1 ? "copy" : "copies"} into the ones ${to.name || "it"} already had.` : "",
        early ? `${plural(early, "trade")} ${early === 1 ? "is" : "are"} before its start date (${to.startDate}), so ${early === 1 ? "it's" : "they're"} hidden there until you change the start date in Settings.` : go.length ? "Pick it in the account menu to see them." : ""].filter(Boolean).join(" "), 8000);
    } catch (e) { moving = false; toast("Couldn't move everything. Click Move again; trades already moved won't move twice."); renderMove(); }
  }
  $("moveBtn").addEventListener("click", openMove);
  $("moveClose").addEventListener("click", () => { $("movePanel").hidden = true; });
  $("mvSource").addEventListener("change", () => { mvRange(); renderMove(); });
  ["mvStart", "mvEnd", "mvTarget"].forEach((id) => $(id).addEventListener("change", renderMove));''')

# keep the preview current when trades or the account change
rep('''    renderTopTools(); renderDash(list, acc);''', '''    if (typeof renderMove === "function") renderMove();
    renderTopTools(); renderDash(list, acc);''')

# an import preview is for one account: switching accounts re-reads it for the new one
rep('$("acctSelect").addEventListener("change", () => { saveSettings({ activeAccountId: $("acctSelect").value }); render(); });', '$("acctSelect").addEventListener("change", () => { saveSettings({ activeAccountId: $("acctSelect").value }); render(); if (imp) renderImport(); });')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
