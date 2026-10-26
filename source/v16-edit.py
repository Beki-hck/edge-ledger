#!/usr/bin/env python3
"""v15 -> v16: the platform import merges trades you logged by hand with the same trades in the file."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

# ---- find hand-logged twins while reading the file ----
rep('''    let skipped = 0, dupes = 0;
    body.forEach((r, i) => {
      const side = String(col(r, "side")).toLowerCase()''', '''    let skipped = 0, dupes = 0;
    const already = [];
    body.forEach((r, i) => {
      const side = String(col(r, "side")).toLowerCase()''')
rep('''        if (old !== true && Math.abs((num(old.pnl) || 0) - pnl) > 0.005) fixes.push({ ...old, pnl: pnl.toFixed(2), size: String(num(col(r, "volume")) ?? old.size ?? ""), entry: String(num(col(r, "openPrice")) ?? old.entry ?? ""), exit: String(num(col(r, "closePrice")) ?? old.exit ?? "") });
        return;''', '''        if (old !== true && Math.abs((num(old.pnl) || 0) - pnl) > 0.005) fixes.push({ ...old, pnl: pnl.toFixed(2), size: String(num(col(r, "volume")) ?? old.size ?? ""), entry: String(num(col(r, "openPrice")) ?? old.entry ?? ""), exit: String(num(col(r, "closePrice")) ?? old.exit ?? "") });
        if (old !== true) already.push(fixes.find((f) => f.id === old.id) || old);
        return;''')
rep('''        followedPlan: null, mistakes: [], tags: [], screenshots: [], notes: "" });
    });
    return { trades: out, fixes, skipped, dupes };
  }''', '''        followedPlan: null, mistakes: [], tags: [], screenshots: [], notes: "" });
    });
    return { trades: out, fixes, skipped, dupes, merges: findTwins(mine.filter((t) => !t.extId && t.source !== "import"), out, already) };
  }
  // A trade you logged by hand and the same trade in the platform's file: same day, same market, same side of zero and
  // about the same P&L (a hand-typed number is often rounded). Closest pairs win, and each trade pairs once.
  const MARKET_FAMILY = [[/^(NAS|NDX|US100|USTEC|NQ$|MNQ$)/, "nq"], [/^(SPX|US500|SP500|USA500|ES$|MES$)/, "es"], [/^(US30|DJ|DOW|WS30|USA30|YM$|MYM$)/, "ym"],
    [/^(US2000|RUT|RTY$|M2K$)/, "rty"], [/^(GER|DE40|DAX)/, "dax"], [/^(UK100|FTSE)/, "ftse"], [/^(XAU|GOLD|GC$|MGC$)/, "gold"], [/^(XAG|SILVER|SI$)/, "silver"]];
  const marketKey = (sym) => { const u = cleanSymbol(sym).replace(/\\s+/g, ""); const f = MARKET_FAMILY.find(([re]) => re.test(u)); return f ? f[1] : u; };
  function findTwins(hand, fresh, already) {
    const pool = [...fresh.map((t) => ({ t, isNew: true })), ...already.map((t) => ({ t, isNew: false }))], pairs = [];
    hand.forEach((h) => {
      const hp = num(h.pnl); if (hp == null) return;
      pool.forEach((p) => {
        const pp = num(p.t.pnl) || 0, diff = Math.abs(hp - pp);
        if (p.t.id === h.id || p.t.date !== h.date || marketKey(p.t.instrument) !== marketKey(h.instrument) || Math.sign(hp) !== Math.sign(pp) || diff > Math.max(2, Math.abs(pp) * 0.1)) return;
        // Times only rank the pairs: you type yours in NY time and the file's time zone may not be set on the account.
        const a = nyMinutes(h), b = nyMinutes(p.t), gap = a != null && b != null ? Math.min(Math.abs(a - b), 1440 - Math.abs(a - b)) : null;
        pairs.push({ hand: h, imp: p.t, isNew: p.isNew, score: diff + (gap != null ? gap / 60 : 0.5) });
      });
    });
    // Pair as many trades as possible, then the closest: each day and market on its own, tried every way when it's small.
    const groups = new Map(); pairs.forEach((p) => { const k = `${p.hand.date}:${marketKey(p.hand.instrument)}`; groups.set(k, [...(groups.get(k) || []), p]); });
    const out = [];
    groups.forEach((list) => {
      const hands = [...new Set(list.map((p) => p.hand.id))];
      let best = { n: 0, score: 0, picks: [] }, steps = 0;
      const walk = (i, used, picks, score) => {
        if (++steps > 20000) return;
        if (i === hands.length) { if (picks.length > best.n || (picks.length === best.n && score < best.score)) best = { n: picks.length, score, picks: [...picks] }; return; }
        list.filter((p) => p.hand.id === hands[i] && !used.has(p.imp.id)).forEach((p) => { used.add(p.imp.id); picks.push(p); walk(i + 1, used, picks, score + p.score); picks.pop(); used.delete(p.imp.id); });
        walk(i + 1, used, picks, score);
      };
      walk(0, new Set(), [], 0);
      if (steps > 20000) { const uh = new Set(), ui = new Set(); best = { picks: [] }; [...list].sort((x, y) => x.score - y.score).forEach((p) => { if (uh.has(p.hand.id) || ui.has(p.imp.id)) return; uh.add(p.hand.id); ui.add(p.imp.id); best.picks.push(p); }); }
      out.push(...best.picks);
    });
    return out.sort((x, y) => sortKey(x.imp).localeCompare(sortKey(y.imp)));
  }
  // The file's facts (time, prices, lots, P&L) joined with what you wrote. Where both copies have something,
  // notes are joined, lists are combined, your stop, target and risk win, and an answer already on the trade stays.
  const TRADE_FACTS = ["extId", "source", "accountId", "date", "time", "instrument", "dir", "size", "entry", "exit", "pnl"];
  const HAND_WINS = ["stop", "target", "risk", "origStop"];
  const filled = (v) => v != null && v !== "" && !(Array.isArray(v) && !v.length);
  function mergeTwin(hand, imported, id) {
    const out = { ...imported };
    Object.keys(hand).forEach((k) => {
      const h = hand[k], o = out[k];
      if (TRADE_FACTS.includes(k) || k === "id" || k === "createdAt" || !filled(h)) return;
      if (!filled(o) || HAND_WINS.includes(k)) out[k] = h;
      else if (Array.isArray(h) && Array.isArray(o)) out[k] = [...new Set([...o, ...h])];
      else if (k === "notes" && String(o).trim() !== String(h).trim()) out[k] = `${String(o).trim()}\n\n${String(h).trim()}`;
    });
    return { ...out, id, mergedFrom: hand.id };
  }''')

# ---- preview: list the pairs, each with its own tick box ----
rep('''    const res = buildImport(); imp.result = res;
    const s = summarize(res.trades);''', '''    const res = buildImport(); imp.result = res;
    imp.skipMerge = imp.skipMerge || new Set();
    const merging = res.merges.filter((m) => !imp.skipMerge.has(m.hand.id)), mergedNew = new Set(merging.filter((m) => m.isNew).map((m) => m.imp.id));
    const adding = res.trades.filter((t) => !mergedNew.has(t.id));
    const mergedIds = new Set(merging.map((m) => m.imp.id)), fixesLeft = res.fixes.filter((f) => !mergedIds.has(f.id)).length;
    const s = summarize(adding);''')
rep('''    $("impPreview").innerHTML = `<div class="stack"><p>Found <strong>${res.trades.length}</strong> new trade${res.trades.length === 1 ? "" : "s"} for''', '''    const twins = res.merges.length ? `<div class="stack"><div class="section-label">Trades you logged by hand</div>
      <p class="calc">${res.merges.length === 1 ? "This trade looks like one" : `These ${res.merges.length} trades look like ones`} in the file. Merging keeps your review, feelings and notes, and takes the time, prices, lots and P&amp;L from the file, so nothing is counted twice. Untick a trade that's really a different one.</p>
      <div class="table-wrap"><table><thead><tr><th>Merge</th><th>Date</th><th>Market</th><th class="r">You logged</th><th class="r">In the file</th></tr></thead><tbody>${res.merges.map((m) => `<tr><td><input type="checkbox" data-merge="${esc(m.hand.id)}" aria-label="Merge the ${esc(m.hand.date)} ${esc(m.hand.instrument)} trade" ${imp.skipMerge.has(m.hand.id) ? "" : "checked"}></td><td class="num">${esc(m.imp.date)} ${esc(m.imp.time || "")}</td><td>${esc(m.imp.instrument)}${marketKey(m.hand.instrument) === marketKey(m.imp.instrument) && cleanSymbol(m.hand.instrument) !== cleanSymbol(m.imp.instrument) ? ` <span class="muted">(${esc(m.hand.instrument)})</span>` : ""}</td><td class="r num ${cls(num(m.hand.pnl))}">${money(num(m.hand.pnl))}</td><td class="r num ${cls(num(m.imp.pnl))}">${money(num(m.imp.pnl))}${m.isNew ? "" : ' <span class="muted">imported before</span>'}</td></tr>`).join("")}</tbody></table></div></div>` : "";
    const goLabel = [adding.length ? `Import ${plural(adding.length, "trade")}` : "", merging.length ? `merge ${merging.length}` : "", fixesLeft ? `fix ${fixesLeft}` : ""].filter(Boolean).join(", ").replace(/^./, (c) => c.toUpperCase());
    $("impPreview").innerHTML = `<div class="stack"><p>Found <strong>${res.trades.length}</strong> new trade${res.trades.length === 1 ? "" : "s"} for''')
rep('''      <p class="calc">Imported trades are marked "needs review". Open each one to add your playbook, feelings and notes. They count in your P&amp;L right away and in your discipline score once reviewed.</p>
      <div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="impGo">Import ${res.trades.length} trade${res.trades.length === 1 ? "" : "s"}${res.fixes.length ? ` and fix ${res.fixes.length}` : ""}</button></div>` : res.fixes.length ? `<div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="impGo">Fix ${res.fixes.length} trade${res.fixes.length === 1 ? "" : "s"}</button></div>` : `<p class="muted">Nothing to import. Check that the columns marked * are matched above.</p>`}</div>`;''', '''      <p class="calc">Imported trades are marked "needs review". Open each one to add your playbook, feelings and notes. They count in your P&amp;L right away and in your discipline score once reviewed.</p>` : ""}
      ${twins}
      ${goLabel ? `<div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="impGo">${goLabel}</button></div>` : res.merges.length ? `<p class="muted">Nothing new to import. Tick a trade above to merge it.</p>` : `<p class="muted">Nothing to import. Check that the columns marked * are matched above.</p>`}</div>`;''')
rep('''  $("impMapGrid").addEventListener("change", (e) => { const s = e.target.closest("[data-map]"); if (s) { imp.map[s.dataset.map] = +s.value; renderImport(); } });''', '''  $("impMapGrid").addEventListener("change", (e) => { const s = e.target.closest("[data-map]"); if (s) { imp.map[s.dataset.map] = +s.value; renderImport(); } });
  $("impPreview").addEventListener("change", (e) => { const c = e.target.closest("[data-merge]"); if (!c || !imp) return; c.checked ? imp.skipMerge.delete(c.dataset.merge) : imp.skipMerge.add(c.dataset.merge); renderImport(); });''')

# ---- saving: a merged trade replaces both ----
rep('''  async function doImport() {
    const list = imp?.result?.trades || [], fixes = imp?.result?.fixes || [];
    $("impGo").disabled = true; $("impGo").textContent = "Importing…";
    let ok = 0, fixed = 0;
    for (const t of fixes) { try { await backend.put("trades", t); fixed++; } catch {} }
    for (const t of list) { try { await backend.put("trades", t); ok++; } catch (e) { if (e?.code === "quota_exceeded") break; } }
    const fixMsg = fixed ? ` Corrected the P&L on ${plural(fixed, "earlier trade")}.` : "";
    toast(ok === list.length ? `Imported ${plural(ok, "trade")}.${fixMsg}${ok ? " Review them to add your notes." : ""}` : `Imported ${ok} of ${plural(list.length, "trade")}.${fixMsg} Storage may be full.`);''', '''  async function doImport() {
    const res = imp?.result || {}, skip = imp?.skipMerge || new Set();
    const merges = (res.merges || []).filter((m) => !skip.has(m.hand.id) && S.trades.has(m.hand.id));
    const mergedImp = new Set(merges.map((m) => m.imp.id));
    const list = (res.trades || []).filter((t) => !mergedImp.has(t.id)), fixes = (res.fixes || []).filter((t) => !mergedImp.has(t.id));
    $("impGo").disabled = true; $("impGo").textContent = "Importing…";
    let ok = 0, fixed = 0, merged = 0;
    for (const t of fixes) { try { await backend.put("trades", t); fixed++; } catch {} }
    // New in the file: your hand-logged trade takes the file's numbers. Imported before: the imported trade takes
    // what you wrote, and the hand-logged copy goes.
    for (const m of merges) {
      try {
        if (m.isNew) await backend.put("trades", mergeTwin(m.hand, m.imp, m.hand.id));
        else { await backend.put("trades", mergeTwin(m.hand, m.imp, m.imp.id)); await backend.del("trades", m.hand.id); }
        merged++;
      } catch {}
    }
    for (const t of list) { try { await backend.put("trades", t); ok++; } catch (e) { if (e?.code === "quota_exceeded") break; } }
    const fixMsg = fixed ? ` Corrected the P&L on ${plural(fixed, "earlier trade")}.` : "";
    const mergeMsg = merged ? ` Merged ${plural(merged, "trade")} you logged by hand.` : "";
    const allOk = ok === list.length && merged === merges.length;
    toast(allOk ? `Imported ${plural(ok, "trade")}.${mergeMsg}${fixMsg}${ok ? " Review them to add your notes." : ""}` : `Imported ${ok} of ${plural(list.length, "trade")}.${mergeMsg}${fixMsg} Not everything was saved; import the file again to finish.`);''')
rep('''    $("fPlan").value = "review"; showTab("trades"); renderTrades();''', '''    if (ok) $("fPlan").value = "review"; showTab("trades"); renderTrades();''')

# ---- trades tab: say when a filter is hiding trades ----
rep('''${pending && fp !== "review" ? ` · <a href="#" id="showPending">${pending} need review</a>` : ""}</p>` + tradeTable(list, false)
      : all.length ? `<p class="muted">No trades match these filters.</p>`''', '''${pending && fp !== "review" ? ` · <a href="#" id="showPending">${pending} need review</a>` : ""}${list.length < all.length ? ` · <a href="#" class="showAllTrades">filtered: show all ${all.length}</a>` : ""}</p>` + tradeTable(list, false)
      : all.length ? `<p class="muted">No trades match these filters. <a href="#" class="showAllTrades">Show all ${all.length}</a></p>`''')
rep('''    $("showPending")?.addEventListener("click", (e) => { e.preventDefault(); $("fPlan").value = "review"; renderTrades(); });''', '''    $("showPending")?.addEventListener("click", (e) => { e.preventDefault(); $("fPlan").value = "review"; renderTrades(); });
    $("tradeTable").querySelector(".showAllTrades")?.addEventListener("click", (e) => { e.preventDefault(); ["fInstrument", "fResult", "fPlan", "fTag"].forEach((id) => { $(id).value = ""; }); renderTrades(); });''')

rep('$("impPreview").innerHTML = `<div class="stack"><p>Found <strong>${res.trades.length}</strong> new trade${res.trades.length === 1 ? "" : "s"} for', '$("impPreview").innerHTML = `<div class="stack"><p>Found <strong>${adding.length}</strong> new trade${adding.length === 1 ? "" : "s"} for')
rep('${res.trades.length ? `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Symbol</th>', '${adding.length ? `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Symbol</th>')
rep('${res.trades.slice(0, 8).map((t) =>', '${adding.slice(0, 8).map((t) =>')
rep('${res.trades.length > 8 ? `<p class="calc">and ${res.trades.length - 8} more</p>` : ""}', '${adding.length > 8 ? `<p class="calc">and ${adding.length - 8} more</p>` : ""}')
rep('toast(allOk ? `Imported ${plural(ok, "trade")}.${mergeMsg}', 'toast(allOk ? `${ok || !merged ? `Imported ${plural(ok, "trade")}.` : ""}${mergeMsg}')

rep('import the file again to finish.`);', 'import the file again to finish.`).trim());')
rep('    toast(allOk ? `${ok || !merged', '    toast((allOk ? `${ok || !merged')

# ---- OneNote: a PDF picked by mistake gets the way forward, not just a no ----
rep('toast("Pick the .txt file with your notebook\'s text, not the PDF itself.");', 'toast("Edge Ledger reads the notebook as text. Pick OneNote journal.txt, or open the PDF in Chrome, press Ctrl+A then Ctrl+C, and paste it in the box below.", 9000); $("oneFile").value = "";')

rep('function toast(msg) { const t = $("toast"); t.textContent = msg; t.hidden = false; clearTimeout(toast.h); toast.h = setTimeout(() => (t.hidden = true), 2800); }', 'function toast(msg, ms = 2800) { const t = $("toast"); t.textContent = msg; t.hidden = false; clearTimeout(toast.h); toast.h = setTimeout(() => (t.hidden = true), ms); }')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
