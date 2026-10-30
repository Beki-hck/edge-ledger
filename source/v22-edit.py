#!/usr/bin/env python3
"""v21 -> v22 (PC): My rules in Settings (daily limits + your own written rules, which are the journal's
"Before you trade" checklist), and a journaling logo (open journal with a rising line) on the header, folder screen and Chrome tab."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

# ---- logo ----
OLD_MARK = '<svg viewBox="0 0 24 24" fill="none" stroke="#061024" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l5-6 4 3 6-8"/><path d="M15 6h3v3"/></svg>'
MARK_PATHS = '<path d="M12 6.5C9.5 4.8 6 4.5 3 5.2v13.5c3-.7 6.5-.4 9 1.3 2.5-1.7 6-2 9-1.3V5.2c-3-.7-6.5-.4-9 1.3z"/><path d="M12 6.5V20"/><path d="M5.5 9h4M5.5 12h4M14.5 14l2-2.5 1.5 1.2 2-2.7"/>'
rep(OLD_MARK, f'<svg viewBox="0 0 24 24" fill="none" stroke="#061024" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{MARK_PATHS}</svg>', 2)
fav = ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
       "<stop offset='0' stop-color='#6ea8ff'/><stop offset='1' stop-color='#a78bfa'/></linearGradient></defs>"
       "<rect width='32' height='32' rx='8' fill='url(#g)'/><g transform='translate(4 4)' fill='none' stroke='#061024' stroke-width='2.1' "
       "stroke-linecap='round' stroke-linejoin='round'>" + MARK_PATHS.replace('"', "'") + "</g></svg>")
fav = fav.replace("#", "%23").replace("<", "%3C").replace(">", "%3E")
rep('<title>Edge Ledger</title>', f'<title>Edge Ledger</title>\n<link rel="icon" href="data:image/svg+xml,{fav}">')

# ---- My rules panel (Settings) ----
rep('''.keyrow input { flex: 1 1 220px; width: auto; }''', '''.keyrow input { flex: 1 1 220px; width: auto; }
.mr-row { display: flex; gap: 6px; align-items: flex-start; }
.mr-row .num, .mr-row button { margin-top: 7px; }
.mr-row .num { color: var(--muted); min-width: 1.4em; text-align: right; font-size: 0.85rem; }
.mr-row textarea { flex: 1 1 auto; width: auto; min-height: 2.4em; resize: none; field-sizing: content; line-height: 1.45; }
.mr-limits { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
.mr-limits .field { flex: 1 1 170px; }
#myRulesPanel { scroll-margin-top: 140px; }
.mr-row button { flex: none; }''')
rep('''        <div class="panel-head"><h2>Today's guardrails</h2><span class="label">From your own rules</span></div>''',
    '''        <div class="panel-head"><h2>Today's guardrails</h2><button type="button" class="btn-small" data-mr-goto>Edit my rules</button></div>''')
rep('''        <div id="guards"></div>
      </div>
    </div>
''', '''        <div id="guards"></div>
      </div>
    </div>
    <div class="panel" id="myRulesPanel">
      <div class="panel-head"><h2>My rules</h2><span class="label" id="mrAcct"></span></div>
      <div class="stack" style="gap:18px">
        <div class="stack">
          <span class="flabel">Daily limits</span>
          <div class="mr-limits">
            <div class="field"><label for="mrMaxTrades">Max trades per day</label><input id="mrMaxTrades" inputmode="numeric" placeholder="No limit"></div>
            <div class="field"><label for="mrMaxLosses">Stop after this many losses a day</label><input id="mrMaxLosses" inputmode="numeric" placeholder="1"></div>
            <div class="field"><label for="mrRisk">Risk per trade (%)</label><input id="mrRisk" inputmode="decimal" placeholder="0.5"></div>
            <button type="button" class="btn-primary" id="mrSave">Save limits</button>
          </div>
          <p class="calc">The dashboard counts your trades left from these, warns you when you hit one, and flags trades over the limit. Leave max trades empty for no limit.</p>
        </div>
        <div class="stack">
          <span class="flabel">My written rules: your "Before you trade" checklist in the journal</span>
          <div class="stack" id="mrList"></div>
          <form id="mrAdd" class="keyrow"><input id="mrNew" maxlength="300" placeholder="Add a rule, e.g. Only 2 trades a day" aria-label="New rule"><button type="submit">Add rule</button></form>
          <p class="calc">Click a rule to change its wording. Changes save when you click away or press Enter.</p>
        </div>
      </div>
    </div>
''')

# ---- rules data: written rules come from settings, the original six until edited ----
rep('''  const GATE = [''', '''  const DEFAULT_GATE = [''')
rep('''  // The dashboard shows one slim line, only when a rule needs attention.''', '''  const myRules = () => (Array.isArray(S.settings.myRules) ? S.settings.myRules : DEFAULT_GATE.map(([id, text]) => ({ id, text })));
  const gateIds = () => myRules().map((r) => r.id);
  // The dashboard shows one slim line, only when a rule needs attention.''')

# ---- journal checklist ----
rep('''  $("jChecks").innerHTML = GATE.map(([k, txt]) => `<label><input type="checkbox" id="j-${k}" value="${k}"><span>${esc(txt)}</span></label>`).join("");
''', '')
rep('''  const pickOne = (id, prefix, values, cur) =>''', '''  // Rebuilt only when the rules change; ticks already made stay ticked.
  let checksSig = null;
  function renderChecks() {
    const rules = myRules(), sig = JSON.stringify(rules);
    if (sig === checksSig) return;
    checksSig = sig;
    const on = new Set(checkedVals("jChecks"));
    $("jChecks").innerHTML = rules.length ? rules.map((r) => `<label><input type="checkbox" value="${esc(r.id)}" ${on.has(r.id) ? "checked" : ""}><span>${esc(r.text)}</span></label>`).join("")
      : `<span class="calc">No rules written yet. Add yours in Settings, under My rules.</span>`;
    updatePrePill();
  }
  const pickOne = (id, prefix, values, cur) =>''')
rep('''    const n = GATE.filter(([k]) => $("j-" + k).checked).length, st = num(document.querySelector("#jMood input:checked")?.value);
    const [c, txt] = st && st < 3 ? ["bad", "Sit out or half risk"] : n === GATE.length ? ["ok", "Ready to trade"] : ["warn", `${n} of ${GATE.length} checked`];''',
    '''    const ids = gateIds(), on = checkedVals("jChecks"), n = ids.filter((k) => on.includes(k)).length, st = num(document.querySelector("#jMood input:checked")?.value);
    const [c, txt] = st && st < 3 ? ["bad", "Sit out or half risk"] : !ids.length ? ["", "No checklist yet"] : n === ids.length ? ["ok", "Ready to trade"] : ["warn", `${n} of ${ids.length} checked`];''')
rep('''    GATE.forEach(([k]) => ($("j-" + k).checked = (g.checks || []).includes(k)));''',
    '''    renderChecks(); document.querySelectorAll("#jChecks input").forEach((c) => (c.checked = (g.checks || []).includes(c.value)));''')
# A rule deleted later keeps its tick on old days, so putting it back restores them.
rep('''checks: GATE.map(([k]) => k).filter((k) => $("j-" + k).checked), at: Date.now() };''',
    '''checks: [...((prev.gate || {}).checks || []).filter((k) => !gateIds().includes(k)), ...checkedVals("jChecks")], at: Date.now() };''')
rep('''${x.gate ? ` pre-trade-checks:${(x.gate.checks || []).length}/${GATE.length}` : ""}''',
    '''${x.gate && gateIds().length ? ` pre-trade-checks:${(x.gate.checks || []).filter((k) => gateIds().includes(k)).length}/${gateIds().length}` : ""}''')
rep('''      `ACCOUNT TOTALS: ${s.n} trades''', '''      `MY RULES: ${myRules().map((r) => r.text).join("; ") || "none written"}.`,
      `ACCOUNT TOTALS: ${s.n} trades''')
rep('''    if (!$("view-settings").hidden) renderSettings();
  }''', '''    if (!$("view-settings").hidden) renderSettings();
    renderChecks();
  }''')

# ---- Settings: My rules editor ----
rep('''    renderListEditor("listEmotions", "emotions", "Feelings", "Add a feeling");''', '''    renderMyRules();
    renderListEditor("listEmotions", "emotions", "Feelings", "Add a feeling");''')
rep('''  // ---------- settings: lists ----------''', '''  // ---------- settings: my rules ----------
  let mrLimitsSig = "", mrListSig = "", mrDelArmed = "";
  const mrLimitEls = ["mrMaxTrades", "mrMaxLosses", "mrRisk"];
  function renderMyRules(force) {
    const acc = activeAccount(), rules = myRules();
    $("mrAcct").textContent = `Limits for ${acc.name || "this account"}`;
    // Never overwrite what's being typed; refill when the account or its saved limits change.
    const lsig = JSON.stringify([acc.id, acc.maxTrades, acc.maxLosses, acc.riskPct]);
    if ((force || lsig !== mrLimitsSig) && !mrLimitEls.includes(document.activeElement?.id)) {
      mrLimitsSig = lsig;
      $("mrMaxTrades").value = +acc.maxTrades > 0 ? acc.maxTrades : "";
      $("mrMaxLosses").value = acc.maxLosses ? acc.maxLosses : "";
      $("mrRisk").value = +acc.riskPct > 0 ? acc.riskPct : "";
    }
    const sig = JSON.stringify([rules, mrDelArmed]);
    if ((force || sig !== mrListSig) && !document.activeElement?.matches("#mrList textarea")) {
      mrListSig = sig;
      $("mrList").innerHTML = rules.length ? rules.map((r, i) => `<div class="mr-row"><span class="num">${i + 1}.</span><textarea rows="1" maxlength="300" data-mr-edit="${esc(r.id)}" aria-label="Rule ${i + 1}">${esc(r.text)}</textarea>`
        + `<button type="button" class="btn-small" data-mr-up="${esc(r.id)}" ${i ? "" : "disabled"} aria-label="Move rule ${i + 1} up" title="Move up">↑</button>`
        + `<button type="button" class="btn-small btn-danger" data-mr-del="${esc(r.id)}">${mrDelArmed === r.id ? "Sure?" : "Delete"}</button></div>`).join("")
        : `<span class="calc">No written rules yet. Add your first one below.</span>`;
    }
  }
  const saveRules = (rules, msg) => saveSettings({ myRules: rules }).then((ok) => { mrDelArmed = ""; renderMyRules(true); renderChecks(); updatePrePill(); if (ok && msg) toast(msg); return ok; });
  $("mrAdd").addEventListener("submit", (e) => {
    e.preventDefault();
    const text = $("mrNew").value.trim().replace(/\\s+/g, " "); if (!text) { toast("Write the rule first."); return; }
    if (myRules().some((r) => r.text.toLowerCase() === text.toLowerCase())) { toast("You already have that rule."); return; }
    saveRules([...myRules(), { id: "r" + uid(), text }], "Rule added").then((ok) => { if (ok) $("mrNew").value = ""; $("mrNew").focus(); });
  });
  $("mrList").addEventListener("change", (e) => {
    const inp = e.target.closest("[data-mr-edit]"); if (!inp) return;
    const rules = myRules(), r = rules.find((x) => x.id === inp.dataset.mrEdit); if (!r) return;
    const text = inp.value.trim().replace(/\\s+/g, " ");
    if (!text) { inp.value = r.text; toast("A rule can't be empty. Use Delete to remove it."); return; }
    if (text === r.text) return;
    if (rules.some((x) => x !== r && x.text.toLowerCase() === text.toLowerCase())) { inp.value = r.text; toast("You already have that rule."); return; }
    saveRules(rules.map((x) => (x === r ? { ...x, text } : x)), "Rule saved");
  });
  $("mrList").addEventListener("keydown", (e) => {
    const inp = e.target.closest("[data-mr-edit]"); if (!inp) return;
    if (e.key === "Enter") { e.preventDefault(); inp.blur(); }
    if (e.key === "Escape") { inp.value = myRules().find((x) => x.id === inp.dataset.mrEdit)?.text ?? inp.value; inp.blur(); }
  });
  $("mrList").addEventListener("focusout", (e) => { if (e.target.matches("textarea")) setTimeout(() => renderMyRules(), 0); });
  $("mrList").addEventListener("click", (e) => {
    const up = e.target.closest("[data-mr-up]"), del = e.target.closest("[data-mr-del]"), rules = [...myRules()];
    if (up) {
      const i = rules.findIndex((x) => x.id === up.dataset.mrUp); if (i < 1) return;
      [rules[i - 1], rules[i]] = [rules[i], rules[i - 1]]; saveRules(rules);
    } else if (del) {
      const id = del.dataset.mrDel;
      if (mrDelArmed !== id) { mrDelArmed = id; renderMyRules(true); return; }
      saveRules(rules.filter((x) => x.id !== id), "Rule deleted");
    }
  });
  $("mrSave").addEventListener("click", async () => {
    const acc = activeAccount();
    if (!S.accounts.has(acc.id)) { toast("Add an account first, under Accounts."); return; }
    const t = $("mrMaxTrades").value.trim(), l = $("mrMaxLosses").value.trim(), r = $("mrRisk").value.trim();
    const maxTrades = t === "" ? 0 : num(t), maxLosses = l === "" ? "" : num(l), riskPct = r === "" ? 0 : num(r);
    if (!Number.isInteger(maxTrades) || maxTrades < 0 || maxTrades > 100) { toast("Max trades per day should be a whole number like 2. Leave it empty for no limit."); return; }
    if (maxLosses !== "" && (!Number.isInteger(maxLosses) || maxLosses < 1 || maxLosses > 100)) { toast("Losses a day should be a whole number from 1 up."); return; }
    if (riskPct == null || !(riskPct >= 0 && riskPct <= 100)) { toast("Risk per trade should be a percent, like 0.5."); return; }
    const a = { ...acc, maxTrades, maxLosses, riskPct };
    if (await persist(() => backend.put("accounts", a), "Limits saved")) { mrLimitsSig = ""; render(); }
  });
  mrLimitEls.forEach((id) => $(id).addEventListener("keydown", (e) => { if (e.key === "Enter") $("mrSave").click(); }));
  document.addEventListener("click", (e) => { if (e.target.closest("[data-mr-goto]")) $("myRulesPanel").scrollIntoView({ behavior: "smooth", block: "start" }); });

  // ---------- settings: lists ----------''')

import re
if re.search(r"(?<![A-Z_])GATE\b", s):
    sys.exit("a GATE use is left")
OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
