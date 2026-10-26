#!/usr/bin/env python3
"""v11 -> v12: simpler dashboard, eye toggle, R/$ switch, structured daily journal, auto-fit screenshots, full-screen viewer."""
import pathlib, sys

HERE = pathlib.Path(__file__).parent
s = (HERE.parent / "v11-backup.html").read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:100]!r}")
    s = s.replace(a, b)

def cut(start, end, new):
    """Replace from `start` up to (not including) `end`."""
    global s
    if s.count(start) != 1: sys.exit(f"cut start not unique: {start[:80]!r}")
    i = s.index(start); j = s.index(end, i)
    s = s[:i] + new + s[j:]

# ================= CSS =================
rep('''.shot { position: relative; width: 150px; max-width: 100%; aspect-ratio: 16 / 10; border-radius: 8px; overflow: hidden; border: 1px solid var(--line); background: var(--sunk); }
.shot img { width: 100%; height: 100%; object-fit: cover; cursor: zoom-in; display: block; }''',
'''.shot { position: relative; min-height: 80px; border-radius: 10px; overflow: hidden; border: 1px solid var(--line); background: var(--sunk); }
.shot img { width: 100%; height: auto; cursor: zoom-in; display: block; }''')
rep('''.shots { display: flex; gap: 10px; flex-wrap: wrap; }''',
'''.shots { display: grid; grid-template-columns: minmax(0, 1fr); gap: 12px; }
.shots:empty { display: none; }
.shots.many { grid-template-columns: repeat(2, minmax(0, 1fr)); }''')
rep('''.lightbox { position: fixed; inset: 0; background: var(--scrim); z-index: 20; display: grid; place-items: center; padding: 16px; cursor: zoom-out; }
.lightbox img { max-width: 100%; max-height: 100%; border-radius: 8px; }''',
'''.lightbox { position: fixed; inset: 0; background: rgba(3, 6, 14, 0.94); z-index: 50; display: grid; place-items: center; padding: 0; cursor: zoom-out; }
.lightbox img { width: 100vw; height: 100vh; object-fit: contain; display: block; }
.lightbox .lb-btn { position: absolute; width: 46px; height: 46px; padding: 0; display: grid; place-items: center; font-size: 1.5rem; line-height: 1; background: rgba(12, 20, 38, 0.85); border-color: var(--line-strong); cursor: pointer; }
.lightbox .lb-close { top: 14px; right: 14px; }
.lightbox .lb-prev { left: 14px; top: calc(50% - 23px); }
.lightbox .lb-next { right: 14px; top: calc(50% - 23px); }
.lightbox .lb-count { position: absolute; bottom: 14px; left: 50%; transform: translateX(-50%); font-family: var(--font-mono); font-size: 0.8rem; color: var(--muted); background: rgba(12, 20, 38, 0.85); padding: 3px 10px; border-radius: 99px; }''')
rep('''.bullets .row { display: flex; gap: 6px; align-items: center; }
.bullets .row::before { content: "•"; font-size: 1.2rem; line-height: 1; color: var(--gain); flex: none; width: 10px; }''',
'''.bullets .row { display: flex; gap: 6px; align-items: flex-start; }
.bullets .row::before { content: "•"; font-size: 1.2rem; line-height: 1; color: var(--gain); flex: none; width: 10px; margin-top: 10px; }
.bullets textarea { min-height: 2.4em; resize: none; field-sizing: content; line-height: 1.45; }''')
rep('''.bullets.bad .row::before { color: var(--loss); }''', '''.bullets.bad .row::before { color: var(--warn); }''')

rep('''/* Phones: bottom dock + floating log button */''', '''/* v12: eye toggle, $/R switch, dashboard alert, structured daily journal */
.top-tools { display: flex; align-items: center; gap: 8px; }
.eye { display: inline-flex; align-items: center; gap: 8px; padding: 7px 10px; }
.eye span { display: none; }
.eye svg { width: 18px; height: 18px; flex: none; }
.eye[aria-pressed="true"] { border-color: var(--accent); color: var(--accent); }
.units button { padding: 7px 11px; font-family: var(--font-mono); }
body.hide-nums .gain:not(p), body.hide-nums .loss:not(p) { color: var(--fg) !important; text-shadow: none !important; }
.cal .d.traded { background: rgba(110, 168, 255, 0.1); border-color: rgba(110, 168, 255, 0.22); }
.cal .d .p.t { color: var(--muted); font-family: var(--font-body); font-size: 0.66rem; }
.alert { display: flex; align-items: center; gap: 10px 12px; flex-wrap: wrap; padding: 10px 14px; border-radius: 12px; border: 1px solid rgba(255, 193, 99, 0.35); background: var(--warn-soft); font-size: 0.9rem; }
.alert.bad { border-color: rgba(255, 107, 129, 0.4); background: var(--loss-soft); }
.alert .msg { flex: 1 1 240px; }
.day-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px 16px; flex-wrap: wrap; }
.day-head .big { font-family: var(--font-display); font-size: clamp(1.4rem, 4vw, 2rem); font-weight: 500; line-height: 1.1; }
.day-nav { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.day-nav input { width: auto; }
details.pre { padding: 0; }
details.pre > summary { list-style: none; cursor: pointer; display: flex; align-items: center; gap: 8px 12px; flex-wrap: wrap; padding: 16px 20px; }
details.pre > summary::-webkit-details-marker { display: none; }
details.pre .chev { width: 18px; height: 18px; flex: none; transition: transform 0.2s; }
details.pre[open] .chev { transform: rotate(180deg); }
details.pre .pre-body { padding: 0 20px 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr)); gap: 20px; }
.jgrid { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr); gap: 16px; align-items: start; }
.jcol { display: grid; gap: 16px; min-width: 0; }
.quick { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px 22px; }
.mini { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--line); }
.mini > div { padding: 10px 12px; border-radius: 12px; background: var(--sunk); display: grid; gap: 4px; }
.mini .v { font-family: var(--font-mono); font-size: 1.15rem; font-variant-numeric: tabular-nums; }
.panel.good { border-color: rgba(62, 224, 165, 0.25); }
.panel.bad { border-color: rgba(255, 193, 99, 0.25); }
details.more.panel { padding: 14px 18px; }
@media (max-width: 900px) { .jgrid { grid-template-columns: 1fr; } }
@media (max-width: 520px) { .shots.many { grid-template-columns: 1fr; } }

/* Phones: bottom dock + floating log button */''')

# ================= header tools =================
EYE_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12c0-1.5 3.5-7 9-7s9 5.5 9 7-3.5 7-9 7-9-5.5-9-7z"/><circle cx="12" cy="12" r="3"/></svg>'
rep('''    </nav>
    <button class="btn-primary" id="newTradeBtn">Log trade</button>''', f'''    </nav>
    <div class="top-tools">
      <div class="seg units" id="unitSeg" role="group" aria-label="Show results in"><button type="button" data-unit="usd" aria-pressed="true" title="Show results in dollars">$</button><button type="button" data-unit="r" aria-pressed="false" title="Show results in R">R</button></div>
      <button type="button" class="eye" id="eyeBtn" aria-pressed="false" aria-label="Hide numbers">{EYE_SVG}<span>Hide numbers</span></button>
    </div>
    <button class="btn-primary" id="newTradeBtn">Log trade</button>''')

# ================= dashboard =================
rep('''    <div class="panel" id="reviewPanel" hidden></div>''', '''    <div class="alert" id="dashAlert" role="status" hidden></div>
    <div class="panel" id="reviewPanel" hidden></div>''')
cut('''    <div class="grid2">
      <div class="panel">
        <div class="panel-head"><h2>Before you trade</h2>''', '''    <div class="grid2">
      <div class="panel">
        <div class="panel-head">
          <h2 id="calTitle">''', '')

# ================= insights: discipline moves here =================
rep('''    <div class="stats" id="insightStats"></div>
    <div class="grid2">''', '''    <div class="stats" id="insightStats"></div>
    <div class="grid2">
      <div class="panel">
        <div class="panel-head"><h2>Discipline score</h2><span class="label">Last 20 trading days</span></div>
        <div id="discipline"></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>What discipline is worth</h2><span class="label">Actual vs. without mistake trades</span></div>
        <div id="whatif"></div>
      </div>
    </div>
    <div class="grid2">''')

# ================= settings: rules, guardrails and prop money move here =================
rep('''  <section class="view" id="view-settings" hidden>
    <div class="grid2">''', '''  <section class="view" id="view-settings" hidden>
    <div class="grid2" id="rulesPanel">
      <div class="panel">
        <div class="panel-head"><h2>Challenge rules</h2><span class="pill" id="phasePill"></span></div>
        <div id="rules"></div>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>Today's guardrails</h2><span class="label">From your own rules</span></div>
        <div id="guards"></div>
      </div>
    </div>
    <div class="grid2">''')
rep('''    <div class="panel">
      <div class="panel-head"><h2>Your lists</h2></div>''', '''    <div class="panel">
      <div class="panel-head"><h2>Prop money</h2><span class="label">Fees in, payouts out, all accounts</span></div>
      <div id="propRoi"></div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>Your lists</h2></div>''')

# ================= journal: daily page =================
CHEV = '<svg class="chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6"/></svg>'
GRADES_OPT = '<option value="">Not graded</option><option>S</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option>'
REST_OPT = '<option value="">Pick one</option><option>No A+ setup</option><option>High-impact news</option><option>Tired or emotional</option><option>Hit my weekly goal</option><option>Rule after losses</option><option>Holiday / thin market</option><option>Life</option>'
cut('''    <div class="grid2" id="jDaily">''', '''    <div class="grid2" id="jWeekly" hidden>''', f'''    <div class="stack" id="jDaily" style="gap:16px">
      <div class="day-head">
        <div><div class="big num" id="jDateBig"></div><div class="muted" id="jDateLong"></div></div>
        <div class="day-nav"><button type="button" id="jPrev" aria-label="Previous day">‹</button><button type="button" id="jToday">Today</button><button type="button" id="jNext" aria-label="Next day">›</button><input type="date" id="jDate" aria-label="Journal date"></div>
      </div>
      <form class="editor" id="dayForm" novalidate style="gap:16px">
        <details class="panel pre" id="jPre">
          <summary><h2>Pre-market</h2><span class="calc" style="margin-right:auto">Bias, plan and your before-you-trade check</span><span class="pill" id="jPrePill"></span>{CHEV}</summary>
          <div class="pre-body">
            <div class="stack" style="gap:14px">
              <div class="field"><span class="flabel">Bias</span><div class="chips" id="jBias" data-single></div></div>
              <div class="field"><label for="jPlan">Plan: levels, news, what I'm waiting for</label><textarea id="jPlan" placeholder="NQ: draw is PDL. Waiting for a sweep of the London low, then the 15m FVG to inverse."></textarea></div>
              <div class="field"><span class="flabel">How am I right now? (below 3 = sit out or half risk)</span><div class="mood" id="jMood"></div></div>
              <div class="field"><span class="flabel">Market that day</span><div class="market" id="jMarket"></div></div>
            </div>
            <div class="field"><span class="flabel">Before you trade</span><div class="checklist" id="jChecks"></div></div>
          </div>
        </details>
        <div class="jgrid">
          <div class="jcol">
            <div class="panel">
              <div class="quick">
                <div class="field"><span class="flabel">Market</span><div class="chips" id="jMarkets"></div></div>
                <div class="field"><span class="flabel">Result</span><div class="chips" id="jResult" data-single></div></div>
                <div class="field"><span class="flabel">Type</span><div class="chips" id="jKind" data-single></div></div>
                <div class="field"><span class="flabel">Importance</span><div class="chips" id="jImportance" data-single></div></div>
              </div>
              <div class="field" id="jNoTradeWhy" hidden style="margin-top:14px"><label for="jRestReason">Why I sat out</label><select id="jRestReason">{REST_OPT}</select></div>
              <div class="mini" id="jMini"></div>
              <p class="calc" style="margin-top:8px">P/L and RR fill in from the trades you logged on this day.</p>
            </div>
            <div class="panel">
              <div class="panel-head"><h2>Charts</h2></div>
              <div class="stack" id="jShotField" style="gap:12px">
                <div class="shots" id="jShots"></div>
                <div class="drop" id="jShotDrop">Press Ctrl+V (⌘V on a Mac) anywhere on this page to paste a screenshot, drop one here, or <label for="jShotFile" style="color:var(--accent);cursor:pointer;text-decoration:underline">choose a file</label>. It sizes itself to fit. Click it to see it full screen.<input type="file" id="jShotFile" accept="image/png,image/jpeg,image/webp,image/gif" multiple hidden></div>
              </div>
              <p class="calc" id="jShotOff" hidden>Screenshots need the journal opened from claude.ai while signed in.</p>
            </div>
          </div>
          <div class="jcol">
            <div class="panel"><div class="field"><h2 style="margin-bottom:6px"><label for="jThoughts">Thoughts</label></h2><textarea id="jThoughts" style="min-height:190px" placeholder="What happened today, why you took it, how it felt."></textarea></div></div>
            <div class="panel">
              <h2 style="margin-bottom:12px">How I felt</h2>
              <div class="field"><span class="flabel">Before</span><div class="chips" id="jFeelBefore"></div></div>
              <div class="field" style="margin-top:12px"><span class="flabel">After</span><div class="chips" id="jFeelAfter"></div></div>
            </div>
            <div class="panel good"><h2 style="margin-bottom:10px">Good things I did</h2><div class="bullets" id="jGood"></div><div style="margin-top:8px"><button type="button" class="btn-small" data-add-bullet="jGood">+ Add a point</button></div></div>
            <div class="panel bad"><h2 style="margin-bottom:10px">Bad things I did</h2><div class="bullets bad" id="jBad"></div><div style="margin-top:8px"><button type="button" class="btn-small" data-add-bullet="jBad">+ Add a point</button></div></div>
            <details class="more panel" id="jMoreBox">
              <summary>Grade, news and lesson (optional)</summary>
              <div class="stack" style="gap:12px">
                <div class="field"><label for="jGrade">Grade the day</label><select id="jGrade">{GRADES_OPT}</select></div>
                <div class="field"><span class="flabel">Red-folder news and headlines that moved the market</span><div class="chips" id="jNews"></div></div>
                <div class="field"><label for="jNewsNotes">News notes: times, actual vs forecast, how price reacted</label><input id="jNewsNotes" placeholder="CPI 0.4% vs 0.3% expected, NAS100 dumped 150 pts at 8:30 ET"></div>
                <div class="field"><label for="jLesson">One lesson to carry forward</label><input id="jLesson"></div>
              </div>
            </details>
            <div class="actions"><button type="submit" class="btn-primary">Save day</button></div>
          </div>
        </div>
      </form>
      <div class="panel">
        <div class="panel-head"><h2>Past entries</h2></div>
        <div id="dayList"></div>
      </div>
    </div>
''')

# ================= lightbox markup =================
rep('''<div class="lightbox" id="lightbox" hidden><img id="lightboxImg" alt="Trade chart"></div>''',
'''<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="Chart full screen" hidden><img id="lightboxImg" alt="Chart full screen"><button type="button" class="lb-btn lb-close" id="lbClose" aria-label="Close full screen">×</button><button type="button" class="lb-btn lb-prev" id="lbPrev" aria-label="Previous chart">‹</button><button type="button" class="lb-btn lb-next" id="lbNext" aria-label="Next chart">›</button><span class="lb-count" id="lbCount"></span></div>''')

# ================= JS: helpers (hide numbers, R mode) =================
rep('''  const money = (n, sign = true) => { if (n == null || !Number.isFinite(n)) return "–"; const s =''',
'''  // Eye toggle in the header: every money and R figure shows as dots and loses its green/red.
  let hideNums = false;
  const MASK = "•••";
  const money = (n, sign = true) => { if (n == null || !Number.isFinite(n)) return "–"; if (hideNums) return MASK; const s =''')
rep('''  const cls = (n) => (n > 0 ? "gain" : n < 0 ? "loss" : "");''', '''  const cls = (n) => (hideNums ? "" : n > 0 ? "gain" : n < 0 ? "loss" : "");''')
rep('''  const fmtR = (x) => (x == null ? "–" : (x > 0 ? "+" : "") + x.toFixed(2) + "R");''',
'''  const fmtRraw = (x) => (x == null ? "–" : (x > 0 ? "+" : "") + x.toFixed(2) + "R");
  const fmtR = (x) => (x != null && hideNums ? MASK : fmtRraw(x));
  // The $ / R switch in the header: totals show as dollars or as the sum of each trade's R.
  const inR = () => S.settings.units === "r";
  const plOf = (s) => (inR() ? s.netR : s.net);
  const pl = (s) => (inR() ? fmtR(s.netR) : money(s.net));''')
rep('''      avgR: mean(rs), planRate:''', '''      avgR: mean(rs), netR: rs.length ? rs.reduce((a, b) => a + b, 0) : null, planRate:''')

# ================= JS: render =================
rep('''    renderDash(list, acc); renderReview(list); renderGate(acc, list);''', '''    renderTopTools(); renderDash(list, acc); renderAlert(acc, list); renderReview(list); renderGate(acc, list);''')
rep('''  $("acctSelect").addEventListener("change", () => { saveSettings({ activeAccountId: $("acctSelect").value }); render(); });''',
'''  $("acctSelect").addEventListener("change", () => { saveSettings({ activeAccountId: $("acctSelect").value }); render(); });
  const EYE_ON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12c0-1.5 3.5-7 9-7s9 5.5 9 7-3.5 7-9 7-9-5.5-9-7z"/><circle cx="12" cy="12" r="3"/></svg>';
  const EYE_OFF = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3l18 18"/><path d="M10.6 5.1A10.6 10.6 0 0 1 12 5c5.5 0 9 5.5 9 7a11.7 11.7 0 0 1-2.6 3.4M6.6 6.6C4.2 8.1 3 10.6 3 12c0 1.5 3.5 7 9 7a9.6 9.6 0 0 0 4.4-1"/><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"/></svg>';
  function renderTopTools() {
    const unit = inR() ? "r" : "usd";
    document.querySelectorAll("#unitSeg [data-unit]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.unit === unit)));
    const eb = $("eyeBtn"), label = hideNums ? "Show numbers" : "Hide numbers";
    if (eb.getAttribute("aria-pressed") !== String(hideNums) || !eb.dataset.drawn) { eb.innerHTML = (hideNums ? EYE_OFF : EYE_ON) + `<span>${hideNums ? "Numbers hidden" : "Hide numbers"}</span>`; eb.dataset.drawn = "1"; }
    eb.setAttribute("aria-pressed", String(hideNums)); eb.setAttribute("aria-label", label); eb.title = label;
    document.body.classList.toggle("hide-nums", hideNums);
  }
  $("eyeBtn").addEventListener("click", () => {
    hideNums = !hideNums;
    try { localStorage.setItem(LS_KEY + "-hide", hideNums ? "1" : "0"); } catch {}
    render();
  });
  $("unitSeg").addEventListener("click", (e) => {
    const b = e.target.closest("[data-unit]"); if (!b) return;
    const units = b.dataset.unit === "r" ? "r" : "";
    if ((S.settings.units || "") === units) return;
    saveSettings({ units }); render();
    if (units === "r" && !accountTrades().some((t) => rOf(t) != null)) toast("R needs a risk on each trade, or a risk % on the account in Settings.");
  });''')

# dashboard tiles and calendar
rep('''      statTile("Balance", money(balance, false), "", `${money(s.net)} since start`),''', '''      statTile("Balance", money(balance, false), "", `${pl(s)} since start`),''')
rep('''    renderCalendar(byDay);
    const recent''', '''    renderCalendar(list);
    const recent''')

# ================= alert + guardrails =================
cut('''  // ---------- pre-trade gate and guardrails ----------''', '''    // Guardrails
''', '''  // ---------- pre-trade check (journal) and guardrails (Settings) ----------
  const GATE = [
    ["news", "No NFP, CPI or FOMC today or tomorrow, and no Fed or Trump speech in my window"],
    ["window", "It's NY AM, not lunch, and not right before a new 15m or 1H candle"],
    ["ath", "I'm not shorting into all-time highs"],
    ["setup", "Sweep → SMT → structure break → 5m OB/FVG, and the candle has closed"],
    ["risk", "Same risk as always. No full port, no adding while red"],
    ["be", "Breakeven only at my written rule, not because I'm nervous"],
  ];
  // The dashboard shows one slim line, only when a rule needs attention. The full rules live in Settings.
  function dashAlerts(acc, list) {
    if (acc.status && acc.status !== "active") return [];
    const td = today(), tdTrades = list.filter((t) => t.date === td), net = summarize(list).net, bal0 = +acc.startBalance || 0;
    const todayPnl = tdTrades.reduce((a, t) => a + (num(t.pnl) || 0), 0), lossesToday = tdTrades.filter((t) => num(t.pnl) < 0).length;
    const maxL = +acc.maxLosses || 1, maxT = +acc.maxTrades || 0, dailyLim = bal0 * (+acc.dailyLossPct || 0) / 100, maxLim = bal0 * (+acc.maxLossPct || 0) / 100, r1 = plannedRisk(acc);
    const out = [];
    if (maxLim > 0 && -net >= maxLim) out.push(["bad", "This account has reached its max-loss floor."]);
    if (dailyLim > 0 && -todayPnl >= dailyLim) out.push(["bad", "You've hit today's daily loss limit. Done trading."]);
    else if (lossesToday >= maxL) out.push(["bad", `You've hit your ${maxL}-loss rule for today. Done trading.`]);
    else if (maxT && tdTrades.length > maxT) out.push(["bad", "You're over your trade limit for today."]);
    else if (maxT && tdTrades.length === maxT) out.push(["warn", "You've used all your trades for today."]);
    else if (dailyLim > 0 && -todayPnl >= dailyLim * 0.6) out.push(["warn", "You've used most of today's daily loss room."]);
    if (maxLim > 0 && -net < maxLim) {
      const room = maxLim + Math.min(0, net), left = r1 > 0 ? Math.floor(room / r1) : null;
      if (left != null ? left <= 3 : -net >= maxLim * 0.6) out.push(["warn", left != null ? `Only ${left} full loss${left === 1 ? "" : "es"} left above the max-loss floor. Consider half risk.` : "You're close to the max-loss floor. Consider half risk."]);
    }
    return out;
  }
  function renderAlert(acc, list) {
    const el = $("dashAlert"), all = dashAlerts(acc, list), top = all[0];
    let dismissed = ""; try { dismissed = localStorage.getItem(LS_KEY + "-alert-" + acc.id) || ""; } catch {}
    const key = top ? `${today()}|${acc.id}|${top[1]}` : "";
    el.hidden = !top || dismissed === key;
    if (el.hidden) return;
    el.className = "alert " + (top[0] === "bad" ? "bad" : "");
    el.innerHTML = `<span class="msg"><strong>${esc(top[1])}</strong>${all.length > 1 ? ` <span class="muted">and ${all.length - 1} more</span>` : ""}</span><button type="button" class="btn-small" data-goto-settings>See rules</button><button type="button" class="btn-small" id="alertX" aria-label="Hide this for today">×</button>`;
    $("alertX").onclick = () => { try { localStorage.setItem(LS_KEY + "-alert-" + acc.id, key); } catch {} el.hidden = true; };
  }
  function renderGate(acc, list) {
    const td = today();
''')
rep('''  $("gateForm").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const td = today(), d = S.days.get(td) || { id: td, date: td };
    const gate = { state: num(document.querySelector("#gState input:checked")?.value), checks: GATE.map(([k]) => k).filter((k) => $("g-" + k).checked), index: $("gIndex").value.trim(), at: Date.now() };
    if (!gate.state) { toast("Rate how you feel first."); return; }
    persist(() => backend.put("days", { ...d, id: td, date: td, mood: d.mood ?? gate.state, gate, updatedAt: Date.now() }), gateVerdict(gate)[1]);
  });
''', '')
rep('''    if (!t.fee && !t.paid) { $("propRoi").innerHTML = `<div class="empty-state"><h3>No fees or payouts recorded</h3><span>Add each challenge fee and payout in Settings › Accounts to see whether prop trading is paying you.</span><button data-goto-settings>Open accounts</button></div>`; return; }''',
'''    if (!t.fee && !t.paid) { $("propRoi").innerHTML = `<div class="empty-state"><h3>No fees or payouts recorded</h3><span>Add each challenge fee and payout to an account above to see whether prop trading is paying you.</span></div>`; return; }''')

# equity chart: neutral when hidden
rep('''    const ticks = [lo + padv, (lo + hi) / 2, hi - padv], last = pts[pts.length - 1], up = last >= start, col = up ? "var(--gain)" : "var(--loss)";''',
'''    const ticks = [lo + padv, (lo + hi) / 2, hi - padv], last = pts[pts.length - 1], up = last >= start, col = hideNums ? "var(--accent)" : up ? "var(--gain)" : "var(--loss)";''')
rep('''text-anchor="end">${Math.round(v).toLocaleString("en-US")}</text>`).join("")}''', '''text-anchor="end">${hideNums ? "" : Math.round(v).toLocaleString("en-US")}</text>`).join("")}''')

# calendar
rep('''  function renderCalendar(byDay) {
    const y = calMonth.getFullYear(), m = calMonth.getMonth();''', '''  const calR = (v) => { if (v == null) return "–"; const a = Math.abs(v); return a < 0.05 ? "0R" : (v > 0 ? "+" : "−") + a.toFixed(1) + "R"; };
  function renderCalendar(list) {
    const byDay = dailyPnl(list), byDayR = new Map();
    list.forEach((t) => { const r = rOf(t); if (r != null) byDayR.set(t.date, (byDayR.get(t.date) || 0) + r); });
    const y = calMonth.getFullYear(), m = calMonth.getMonth();''')
rep('''    let monthNet = 0;
    const evList = [];''', '''    let monthNet = 0, monthR = null;
    const evList = [];''')
rep('''      if (p != null) monthNet += p;''', '''      if (p != null) monthNet += p;
      const pr = byDayR.get(key); if (pr != null) monthR = (monthR || 0) + pr;
      const v = inR() ? pr : p;''')
rep('''      const c = p == null ? (day.noTrade ? "rest" : "") : p > 0 ? "pos" : p < 0 ? "neg" : "";''',
'''      const c = p == null ? (day.noTrade ? "rest" : "") : hideNums ? "traded" : v > 0 ? "pos" : v < 0 ? "neg" : "";''')
rep('''${p != null ? `<span class="p ${cls(p)}">${calAmt(p)}</span>` : day.noTrade''', '''${p != null ? (hideNums ? `<span class="p t">traded</span>` : `<span class="p ${cls(v)}">${inR() ? calR(v) : calAmt(p)}</span>`) : day.noTrade''')
rep('''Month net: <span class="num ${cls(monthNet)}">${money(monthNet)}</span>''', '''Month net: <span class="num ${cls(inR() ? monthR : monthNet)}">${inR() ? fmtR(monthR) : money(monthNet)}</span>''')
rep('''  $("calPrev").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() - 1); renderCalendar(dailyPnl(accountTrades())); });
  $("calNext").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() + 1); renderCalendar(dailyPnl(accountTrades())); });''',
'''  $("calPrev").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() - 1); renderCalendar(accountTrades()); });
  $("calNext").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() + 1); renderCalendar(accountTrades()); });''')

# hidden numbers: breakeven cost, account list, breakdown bars
rep('''<span class="v loss">${withPr ? given.toFixed(1) + "R" : "–"}</span>''', '''<span class="v loss">${withPr ? (hideNums ? MASK : given.toFixed(1) + "R") : "–"}</span>''')
rep('''· $${(+a.startBalance || 0).toLocaleString("en-US")} ·''', '''· ${money(+a.startBalance || 0, false)} ·''')

# trades summary line
rep('''${plural(s.n, "trade")} · net <span class="num ${cls(s.net)}">${money(s.net)}</span> · win rate''', '''${plural(s.n, "trade")} · net <span class="num ${cls(plOf(s))}">${pl(s)}</span> · win rate''')

# breakdown and heat table
rep('''    const entries = [...groups.entries()].map(([k, list]) => [k, summarize(list)]).sort(opt.order ? (a, b) => opt.order.indexOf(a[0]) - opt.order.indexOf(b[0]) : (a, b) => b[1].net - a[1].net);
    if (!entries.length) { el.innerHTML = `<p class="muted">Not enough trades yet.</p>`; return; }
    const max = Math.max(...entries.map(([, s]) => Math.abs(s.net)), 1);
    el.innerHTML = `<div class="breakdown">${entries.map(([k, s]) => {
      const w = (Math.abs(s.net) / max) * 50, left = s.net >= 0 ? 50 : 50 - w;
      return `<div class="brow"><span title="${esc(k)}">${esc(k)}</span><div class="track"><span class="mid"></span><i style="left:${left}%;width:${w}%;background:${s.net >= 0 ? "var(--gain)" : "var(--loss)"}"></i></div><span class="meta"><span class="${cls(s.net)}">${money(s.net)}</span>''',
'''    const val = (s) => plOf(s) || 0;
    const entries = [...groups.entries()].map(([k, list]) => [k, summarize(list)]).sort(opt.order ? (a, b) => opt.order.indexOf(a[0]) - opt.order.indexOf(b[0]) : (a, b) => val(b[1]) - val(a[1]));
    if (!entries.length) { el.innerHTML = `<p class="muted">Not enough trades yet.</p>`; return; }
    const max = Math.max(...entries.map(([, s]) => Math.abs(val(s))), inR() ? 0.01 : 1);
    el.innerHTML = `<div class="breakdown">${entries.map(([k, s]) => {
      const v = val(s), w = hideNums ? 0 : (Math.abs(v) / max) * 50, left = v >= 0 ? 50 : 50 - w;
      return `<div class="brow"><span title="${esc(k)}">${esc(k)}</span><div class="track"><span class="mid"></span><i style="left:${left}%;width:${w}%;background:${hideNums ? "var(--accent)" : v >= 0 ? "var(--gain)" : "var(--loss)"}"></i></div><span class="meta"><span class="${cls(plOf(s))}">${pl(s)}</span>''')
rep('''    const max = Math.max(1, ...cells.flatMap(([, cs]) => cs.map((x) => Math.abs(x.net))));
    cells.sort((a, b) => summarize(rows.get(b[0])).net - summarize(rows.get(a[0])).net);''',
'''    const hv = (x) => plOf(x) || 0;
    const max = Math.max(inR() ? 0.01 : 1, ...cells.flatMap(([, cs]) => cs.map((x) => Math.abs(hv(x)))));
    cells.sort((a, b) => hv(summarize(rows.get(b[0]))) - hv(summarize(rows.get(a[0]))));''')
rep('''style="background:color-mix(in srgb, ${x.net >= 0 ? "var(--gain)" : "var(--loss)"} ${Math.round(8 + (Math.abs(x.net) / max) * 40)}%, transparent)" title="${plural(x.n, "trade")}, win rate ${fmtPct(x.winRate)}"><span class="${cls(x.net)}">${money(x.net)}</span>''',
'''style="background:color-mix(in srgb, ${hideNums ? "var(--accent)" : hv(x) >= 0 ? "var(--gain)" : "var(--loss)"} ${hideNums ? 10 : Math.round(8 + (Math.abs(hv(x)) / max) * 40)}%, transparent)" title="${plural(x.n, "trade")}, win rate ${fmtPct(x.winRate)}"><span class="${cls(plOf(x))}">${pl(x)}</span>''')

# playbook cards
rep('''<div class="kv"><div><span class="label">Net</span><span class="v ${cls(s.net)}">${list.length ? money(s.net) : "–"}</span></div>''', '''<div class="kv"><div><span class="label">Net</span><span class="v ${cls(plOf(s))}">${list.length ? pl(s) : "–"}</span></div>''')
rep('''`<div class="calc">All rules met: <span class="num ${cls(sf.net)}">${money(sf.net)}</span> over ${full.length} · Rules missed: <span class="num ${cls(sp.net)}">${money(sp.net)}</span> over ${part.length}</div>`''',
'''`<div class="calc">All rules met: <span class="num ${cls(plOf(sf))}">${pl(sf)}</span> over ${full.length} · Rules missed: <span class="num ${cls(plOf(sp))}">${pl(sp)}</span> over ${part.length}</div>`''')

# weekly
rep('''      statTile("Net", money(s.net), cls(s.net), plural(s.n, "trade")), statTile("Win rate", fmtPct(s.winRate)),''', '''      statTile("Net", pl(s), cls(plOf(s)), plural(s.n, "trade")), statTile("Win rate", fmtPct(s.winRate)),''')
rep('''<span class="num ${cls(s.net)}">${s.n ? money(s.net) : ""}</span>''', '''<span class="num ${cls(plOf(s))}">${s.n ? pl(s) : ""}</span>''')

# coach: never send masked values
rep('''avg R ${fmtR(s.avgR)}, discipline score''', '''avg R ${fmtRraw(s.avgR)}, discipline score''')
rep('''mood:${x.mood || "?"} sleep:${x.sleep || "?"} bias:${x.bias || "-"} plan:"${(x.plan || "").slice(0, 200)}" review:"${(x.review || "").slice(0, 300)}" lesson:"${x.lesson || ""}"`''',
'''mood:${x.mood || "?"} bias:${x.bias || "-"}${x.result ? ` result:${x.result}` : ""}${x.kind ? ` type:${x.kind}` : ""}${(x.markets || []).length ? ` markets:${x.markets.join("/")}` : ""}${x.gate ? ` pre-trade-checks:${(x.gate.checks || []).length}/${GATE.length}` : ""}${(x.feelBefore || []).length ? ` felt-before:${x.feelBefore.join("/")}` : ""}${(x.feelAfter || []).length ? ` felt-after:${x.feelAfter.join("/")}` : ""} plan:"${(x.plan || "").slice(0, 200)}" thoughts:"${(x.thoughts ?? x.review ?? "").slice(0, 400).replace(/\\s+/g, " ")}"${(x.good || []).length ? ` did-well:"${x.good.join("; ").slice(0, 300)}"` : ""}${(x.bad || []).length ? ` did-badly:"${x.bad.join("; ").slice(0, 300)}"` : ""} lesson:"${x.lesson || ""}"`''')

# ================= bullets: sentences, Enter adds the next one =================
rep('''  const bulletRow = (id, v) => `<div class="row"><input value="${esc(v)}" aria-label="${id === "tGood" ? "Good thing I did" : "Bad thing I did"}" maxlength="200"><button type="button" data-rm-bullet aria-label="Remove this point">×</button></div>`;
  const bulletValues = (id) => [...$(id).querySelectorAll("input")].map((i) => i.value.trim()).filter(Boolean);
  function addBullet(id) { $(id).insertAdjacentHTML("beforeend", bulletRow(id, "")); $(id).lastElementChild.querySelector("input").focus(); }''',
'''  const bulletRow = (id, v) => `<div class="row"><textarea rows="1" aria-label="${/Good$/.test(id) ? "Good thing I did" : "Bad thing I did"}" maxlength="600">${esc(v)}</textarea><button type="button" data-rm-bullet aria-label="Remove this point">×</button></div>`;
  const bulletValues = (id) => [...$(id).querySelectorAll("textarea")].map((i) => i.value.trim()).filter(Boolean);
  function addBullet(id, after) {
    if (after) { after.insertAdjacentHTML("afterend", bulletRow(id, "")); after.nextElementSibling.querySelector("textarea").focus(); }
    else { $(id).insertAdjacentHTML("beforeend", bulletRow(id, "")); $(id).lastElementChild.querySelector("textarea").focus(); }
  }''')
rep('''  ["tGood", "tBad"].forEach((id) => $(id).addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.target.tagName !== "INPUT") return;
    e.preventDefault(); // Enter adds the next point instead of saving the trade
    if (e.target.value.trim()) addBullet(id);
  }));''',
'''  ["tGood", "tBad", "jGood", "jBad"].forEach((id) => $(id).addEventListener("keydown", (e) => {
    if (e.target.tagName !== "TEXTAREA") return;
    const row = e.target.closest(".row");
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); if (e.target.value.trim()) addBullet(id, row); return; } // Enter starts the next point
    if (e.key === "Backspace" && !e.target.value && $(id).children.length > 1) { // Backspace on an empty point removes it
      e.preventDefault(); const prev = row.previousElementSibling || row.nextElementSibling; row.remove(); const ta = prev?.querySelector("textarea"); if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); }
      if (id[0] === "j") dayDirty = true;
    }
  }));''')

# ================= screenshots (online). The desktop build swaps this whole section for shots.js =================
cut('''  // screenshots
''', '''  // ---------- playbooks ----------''', '''  // screenshots: trades keep theirs in t.screenshots, journal days in d.screenshots (asset ids)
  const shotUrl = (id) => "/_blob/" + id;
  const shotTile = (id, i, rm) => `<div class="shot"><img src="${esc(shotUrl(id))}" alt="Chart screenshot ${i + 1}" data-i="${i}"><button type="button" ${rm}="${i}" aria-label="Remove screenshot">Remove</button></div>`;
  function renderShots() {
    $("tShots").classList.toggle("many", formShots.length > 1);
    $("tShots").innerHTML = formShots.map((id, i) => shotTile(id, i, "data-rm")).join("");
  }
  function renderDayShots() {
    $("jShots").classList.toggle("many", dayShots.length > 1);
    $("jShots").innerHTML = dayShots.map((id, i) => shotTile(id, i, "data-rm-day")).join("");
  }
  // Full-screen viewer: click outside or press Esc to close, arrows to move between charts.
  let lbList = [], lbAt = 0;
  function openLightbox(list, i) { lbList = list; lbAt = i; showLb(); $("lightbox").hidden = false; $("lbClose").focus(); }
  function showLb() {
    $("lightboxImg").src = lbList[lbAt] || "";
    const many = lbList.length > 1; $("lbPrev").hidden = !many; $("lbNext").hidden = !many; $("lbCount").hidden = !many;
    $("lbCount").textContent = `${lbAt + 1} / ${lbList.length}`;
  }
  const stepLb = (d) => { if (lbList.length > 1) { lbAt = (lbAt + d + lbList.length) % lbList.length; showLb(); } };
  function closeLb() { if ($("lightbox").hidden) return; $("lightbox").hidden = true; $("lightboxImg").removeAttribute("src"); document.activeElement?.blur(); }
  $("lightbox").addEventListener("click", (e) => { if (e.target.closest("#lbPrev")) stepLb(-1); else if (e.target.closest("#lbNext")) stepLb(1); else closeLb(); });
  document.addEventListener("keydown", (e) => {
    if ($("lightbox").hidden) return;
    if (e.key === "Escape") closeLb(); else if (e.key === "ArrowLeft") stepLb(-1); else if (e.key === "ArrowRight") stepLb(1); else return;
    e.preventDefault();
  });
  $("tShots").addEventListener("click", (e) => {
    const rm = e.target.closest("[data-rm]"); if (rm) { formShots.splice(+rm.dataset.rm, 1); renderShots(); return; }
    const img = e.target.closest("img[data-i]"); if (img) openLightbox(formShots.map(shotUrl), +img.dataset.i);
  });
  $("jShots").addEventListener("click", (e) => {
    const rm = e.target.closest("[data-rm-day]");
    if (rm) { if (rm.dataset.armed) removeDayShot(+rm.dataset.rmDay); else { rm.dataset.armed = "1"; rm.textContent = "Click again to remove"; setTimeout(() => { if (rm.isConnected) { delete rm.dataset.armed; rm.textContent = "Remove"; } }, 3000); } return; }
    const img = e.target.closest("img[data-i]"); if (img) openLightbox(dayShots.map(shotUrl), +img.dataset.i);
  });
  const imageFiles = (files) => [...files].filter((f) => /^image\\/(png|jpeg|webp|gif)$/.test(f.type));
  const shotError = (e) => toast(e?.code === "quota_or_state" ? "Screenshot storage is full." : e?.code === "unsupported_type" ? "That image type isn't supported." : "Couldn't upload the screenshot.");
  async function uploadShots(files) {
    if (!assets) return;
    const imgs = imageFiles(files);
    if (!imgs.length) { toast("Use a PNG, JPG, WebP or GIF image."); return; }
    for (const f of imgs) {
      toast("Uploading screenshot…");
      try { const r = await assets.upload(f); formShots.push(r.id); renderShots(); toast("Screenshot added. Save the trade to keep it."); }
      catch (e) { shotError(e); }
    }
  }
  // Journal charts are saved with the day as soon as they're added, so nothing is lost if you move to another day.
  async function addDayShots(files) {
    if (!assets) return;
    const imgs = imageFiles(files);
    if (!imgs.length) { toast("Use a PNG, JPG, WebP or GIF image."); return; }
    const date = loadedDay || today();
    for (const f of imgs) {
      toast("Uploading screenshot…");
      let id; try { id = (await assets.upload(f)).id; } catch (e) { shotError(e); continue; }
      if (loadedDay === date) { dayShots.push(id); renderDayShots(); }
      const list = loadedDay === date ? dayShots : [...((S.days.get(date) || {}).screenshots || []), id];
      await saveDayShots(date, list, "Screenshot saved");
    }
  }
  function removeDayShot(i) { const date = loadedDay; if (!date) return; dayShots.splice(i, 1); renderDayShots(); saveDayShots(date, dayShots, "Screenshot removed"); }
  $("shotFile").addEventListener("change", () => { uploadShots($("shotFile").files); $("shotFile").value = ""; });
  $("jShotFile").addEventListener("change", () => { addDayShots($("jShotFile").files); $("jShotFile").value = ""; });
  [["shotDrop", uploadShots], ["jShotDrop", addDayShots]].forEach(([id, fn]) => {
    const drop = $(id);
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); fn(e.dataTransfer.files); });
  });
  document.addEventListener("paste", (e) => {
    if (!assets) return;
    const files = [...(e.clipboardData?.files || [])].filter((f) => f.type.startsWith("image/"));
    if (!files.length) return;
    if (e.target.closest?.("input, textarea") && e.clipboardData.getData("text/plain")) return; // pasting text into a box stays a text paste
    if (!$("view-editor").hidden) { e.preventDefault(); uploadShots(files); }
    else if (!$("view-journal").hidden && !$("jDaily").hidden) { e.preventDefault(); addDayShots(files); }
  });

''')

# ================= journal: daily =================
cut('''  // ---------- journal: daily ----------''', '''  function renderDayList() {''', '''  // ---------- journal: daily ----------
  const BIAS = ["Bullish", "Bearish", "Neutral / range"], DAY_MARKETS = ["ES", "NQ", "Dow", "Gold", "Silver"], DAY_RESULTS = ["Win", "Loss", "BE", "No trade"], DAY_KINDS = ["Live", "Mock", "Backtest"], DAY_IMPORTANCE = ["1", "2", "3"];
  $("jMood").innerHTML = MOODS.map((m, i) => `<label><input type="radio" name="mood" id="mood${i + 1}" value="${i + 1}">${m}</label>`).join("");
  $("jChecks").innerHTML = GATE.map(([k, txt]) => `<label><input type="checkbox" id="j-${k}" value="${k}"><span>${esc(txt)}</span></label>`).join("");
  let loadedDay = null, dayShots = [], dayDirty = false;
  const checkedVals = (id) => [...document.querySelectorAll(`#${id} input:checked`)].map((c) => c.value);
  const pickOne = (id, prefix, values, cur) => ($(id).innerHTML = chipList(prefix, values, cur ? [cur] : []));
  // Chip groups marked data-single hold one choice; clicking the chosen chip again clears it.
  document.addEventListener("change", (e) => {
    const g = e.target.closest?.("[data-single]");
    if (g && e.target.checked) g.querySelectorAll("input").forEach((i) => { if (i !== e.target) i.checked = false; });
    if (e.target.closest?.("#jResult")) syncNoTrade();
  });
  const syncNoTrade = () => ($("jNoTradeWhy").hidden = checkedVals("jResult")[0] !== "No trade");
  function updatePrePill() {
    const n = GATE.filter(([k]) => $("j-" + k).checked).length, st = num(document.querySelector("#jMood input:checked")?.value);
    const [c, txt] = st && st < 3 ? ["bad", "Sit out or half risk"] : n === GATE.length ? ["ok", "Ready to trade"] : ["warn", `${n} of ${GATE.length} checked`];
    $("jPrePill").className = "pill " + c; $("jPrePill").textContent = txt;
  }
  $("jPre").addEventListener("change", updatePrePill);
  $("jPre").addEventListener("toggle", () => { try { localStorage.setItem(LS_KEY + "-pre", $("jPre").open ? "1" : "0"); } catch {} });
  function loadDay(date, soft) {
    if (soft && loadedDay === date) { updateDayPnl(date); $("jMarket").innerHTML = marketHtml(date); return; }
    if (dayDirty && loadedDay) saveDay(true); // never throw away typed text when the page reloads the form
    loadedDay = date; $("jDate").value = date; dayDirty = false;
    const d = S.days.get(date) || {}, g = d.gate || {}, L = lists();
    $("jDateBig").textContent = fmtDay(date, { month: "2-digit", day: "2-digit", year: "numeric" });
    $("jDateLong").textContent = fmtDay(date, { weekday: "long", month: "long", day: "numeric", year: "numeric" }) + (date === today() ? " · today" : "");
    const mood = d.mood ?? g.state;
    document.querySelectorAll("#jMood input").forEach((r) => (r.checked = String(mood) === r.value));
    pickOne("jBias", "jb", BIAS, d.bias === "No trade day" ? "" : d.bias || "");
    $("jPlan").value = d.plan ?? "";
    GATE.forEach(([k]) => ($("j-" + k).checked = (g.checks || []).includes(k)));
    $("jMarkets").innerHTML = chipList("jm", DAY_MARKETS, d.markets || []);
    pickOne("jResult", "jr", DAY_RESULTS, d.result || (d.noTrade || d.bias === "No trade day" ? "No trade" : ""));
    pickOne("jKind", "jk", DAY_KINDS, d.kind || "");
    pickOne("jImportance", "ji", DAY_IMPORTANCE, d.importance ? String(d.importance) : "");
    $("jRestReason").value = d.restReason || ""; syncNoTrade();
    $("jThoughts").value = d.thoughts ?? d.review ?? "";
    $("jFeelBefore").innerHTML = chipList("jfb", L.emotions, d.feelBefore || []);
    $("jFeelAfter").innerHTML = chipList("jfa", L.emotions, d.feelAfter || []);
    renderBullets("jGood", (d.good || []).length ? d.good : [""]); renderBullets("jBad", (d.bad || []).length ? d.bad : [""]);
    $("jGrade").value = d.grade || ""; $("jLesson").value = d.lesson ?? "";
    $("jNews").innerHTML = chipList("nw", L.news, d.news || []); $("jNewsNotes").value = d.newsNotes || "";
    $("jMoreBox").open = !!(d.grade || d.lesson || (d.news || []).length || d.newsNotes);
    dayShots = [...(d.screenshots || [])]; renderDayShots();
    $("jMarket").innerHTML = marketHtml(date);
    updatePrePill(); updateDayPnl(date);
  }
  function updateDayPnl(date) {
    const list = accountTrades().filter((t) => t.date === date), s = summarize(list), prs = list.map(plannedR).filter((x) => x != null);
    const tile = (label, v, c = "") => `<div><span class="label">${label}</span><span class="v ${c}">${v}</span></div>`;
    $("jMini").innerHTML = [
      tile("P/L", list.length ? money(s.net) : "–", cls(s.net)),
      tile("RR planned", prs.length ? `${mean(prs).toFixed(1)}R` : "–"),
      tile("RR got", fmtR(s.netR), cls(s.netR)),
      tile("Trades", String(list.length)),
    ].join("");
  }
  // Saves the screenshots list straight onto the day (the rest of the form saves with Save day).
  function saveDayShots(date, list, okMsg) {
    const d = { ...(S.days.get(date) || {}), id: date, date, screenshots: [...list], updatedAt: Date.now() };
    S.days.set(date, d);
    return persist(() => backend.put("days", d), okMsg);
  }
  function saveDay(quiet) {
    const date = loadedDay || today(), prev = S.days.get(date) || {}, result = checkedVals("jResult")[0] || "";
    const gate = { ...(prev.gate || {}), state: num(document.querySelector("#jMood input:checked")?.value), checks: GATE.map(([k]) => k).filter((k) => $("j-" + k).checked), at: Date.now() };
    const d = { ...prev, id: date, date, mood: gate.state, bias: checkedVals("jBias")[0] || "", plan: $("jPlan").value.trim(),
      markets: checkedVals("jMarkets"), result, kind: checkedVals("jKind")[0] || "", importance: checkedVals("jImportance")[0] || "",
      noTrade: result === "No trade", restReason: result === "No trade" ? $("jRestReason").value : "",
      thoughts: $("jThoughts").value.trim(), feelBefore: checkedVals("jFeelBefore"), feelAfter: checkedVals("jFeelAfter"), good: bulletValues("jGood"), bad: bulletValues("jBad"),
      grade: $("jGrade").value, lesson: $("jLesson").value.trim(), news: checkedVals("jNews"), newsNotes: $("jNewsNotes").value.trim(), screenshots: [...dayShots], updatedAt: Date.now() };
    if (prev.gate || gate.state || gate.checks.length) d.gate = gate; // only days where the pre-trade check was used carry one
    if (prev.thoughts == null) delete d.review; // the old review text now lives in Thoughts
    dayDirty = false;
    S.days.set(date, d);
    if (!quiet && d.noTrade && [...S.trades.values()].some((t) => t.date === date)) toast("Heads up: you have trades logged on this day.");
    return persist(() => backend.put("days", d), quiet ? `Saved ${fmtDay(date)}` : "Day saved");
  }
  // Moving to another day, or leaving the journal, saves what you typed first.
  const goDay = (date) => { if (dayDirty) saveDay(true); loadDay(date); };
  $("jDate").addEventListener("change", () => goDay($("jDate").value || today()));
  $("jPrev").addEventListener("click", () => goDay(addDays(loadedDay || today(), -1)));
  $("jNext").addEventListener("click", () => goDay(addDays(loadedDay || today(), 1)));
  $("jToday").addEventListener("click", () => goDay(today()));
  $("dayForm").addEventListener("input", () => (dayDirty = true));
  $("dayForm").addEventListener("change", (e) => { if (e.target.id !== "jDate") dayDirty = true; });
  $("dayForm").addEventListener("click", (e) => { if (e.target.closest("[data-rm-bullet]")) dayDirty = true; });
  $("dayForm").addEventListener("submit", (ev) => { ev.preventDefault(); saveDay(false); });
  window.addEventListener("beforeunload", (e) => { if (dayDirty) { e.preventDefault(); e.returnValue = ""; } });
''')
rep('''    const days = [...S.days.values()].sort((a, b) => b.date.localeCompare(a.date)), byDay = dailyPnl(accountTrades());
    $("dayList").innerHTML = days.length ? `<div class="list">${days.map((d) => {
      const p = byDay.get(d.date);
      return `<div class="item click" tabindex="0" data-date="${esc(d.date)}"><div class="rule-row"><strong class="num">${esc(fmtDay(d.date, { weekday: "short", month: "short", day: "numeric", year: "numeric" }))}</strong><span>${d.noTrade ? '<span class="pill warn">Rest day</span> ' : ""}${d.grade ? `<span class="pill info">Grade ${esc(d.grade)}</span> ` : ""}${d.mood ? `<span class="pill">${esc(MOODS[d.mood - 1])}</span>` : ""} ${p != null ? `<span class="num ${cls(p)}">${money(p)}</span>` : ""}</span></div>${d.lesson ? `<span class="clamp"><strong>Lesson:</strong> ${esc(d.lesson)}</span>` : d.review ? `<span class="clamp muted">${esc(d.review)}</span>` : d.plan ? `<span class="clamp muted">${esc(d.plan)}</span>` : ""}</div>`;''',
'''    const days = [...S.days.values()].sort((a, b) => b.date.localeCompare(a.date)), byDay = groupBy(accountTrades(), (t) => t.date);
    $("dayList").innerHTML = days.length ? `<div class="list">${days.map((d) => {
      const p = byDay.has(d.date) ? summarize(byDay.get(d.date)) : null, text = d.thoughts || d.review;
      return `<div class="item click" tabindex="0" data-date="${esc(d.date)}"><div class="rule-row"><strong class="num">${esc(fmtDay(d.date, { weekday: "short", month: "short", day: "numeric", year: "numeric" }))}</strong><span>${d.noTrade ? '<span class="pill warn">Rest day</span> ' : d.result ? `<span class="pill">${esc(d.result)}</span> ` : ""}${d.grade ? `<span class="pill info">Grade ${esc(d.grade)}</span> ` : ""}${d.mood ? `<span class="pill">${esc(MOODS[d.mood - 1])}</span>` : ""}${(d.screenshots || []).length ? ` <span class="muted" title="Has charts">▣</span>` : ""} ${p ? `<span class="num ${cls(plOf(p))}">${pl(p)}</span>` : ""}</span></div>${d.lesson ? `<span class="clamp"><strong>Lesson:</strong> ${esc(d.lesson)}</span>` : text ? `<span class="clamp muted">${esc(text)}</span>` : d.plan ? `<span class="clamp muted">${esc(d.plan)}</span>` : ""}</div>`;''')
rep('''      const go = () => { loadDay(el.dataset.date); window.scrollTo(0, 0); };
      el.addEventListener("click", go); el.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
    });
  }

  // ---------- journal: weekly ----------''', '''      const go = () => { goDay(el.dataset.date); window.scrollTo(0, 0); };
      el.addEventListener("click", go); el.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });
    });
  }

  // ---------- journal: weekly ----------''')
rep('''  function setJournalMode(week) {
''', '''  function setJournalMode(week) {
    if (week && dayDirty) saveDay(true);
''')

# tabs: leaving the journal saves the open day
rep('''  function showTab(tab) {
    if (tab !== "editor") reviewMode = false;''', '''  function showTab(tab) {
    if (dayDirty && tab !== "journal" && !$("view-journal").hidden) saveDay(true);
    if (tab !== "editor") reviewMode = false;''')

# ================= storage init: journal charts need assets online =================
rep('''    $("shotField").hidden = !assets; $("shotOff").hidden = !!assets;''', '''    $("shotField").hidden = !assets; $("shotOff").hidden = !!assets;
    $("jShotField").hidden = !assets; $("jShotOff").hidden = !!assets;''')

# ================= export for desktop: day charts too =================
rep('''      const ids = [...new Set(o.trades.flatMap((t) => t.screenshots || []))], files = [];''', '''      const ids = [...new Set([...o.trades, ...o.days].flatMap((t) => t.screenshots || []))], files = [];''')

# ================= boot =================
rep('''  // ---------- boot ----------
  $("jDate").value = today();''', '''  // ---------- boot ----------
  $("jDate").value = today();
  try { hideNums = localStorage.getItem(LS_KEY + "-hide") === "1"; $("jPre").open = localStorage.getItem(LS_KEY + "-pre") === "1"; } catch {}''')

# v13 (2026-10-19): writing boxes use the full page width and grow with the text
rep('''textarea { min-height: 80px; resize: vertical; }''', '''textarea { min-height: 80px; resize: vertical; field-sizing: content; }
textarea.line { min-height: 2.6em; line-height: 1.45; }
#impPaste { field-sizing: fixed; }''')
rep('''details.pre .pre-body { padding: 0 20px 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr)); gap: 20px; }''',
'''details.pre .pre-body { padding: 0 20px 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 380px), 1fr)); gap: 20px; }
details.pre .pre-body .plan { grid-column: 1 / -1; }
details.pre .pre-body > .stack { align-content: start; }
textarea.line { resize: none; }
.bullets .row button { margin-top: 3px; }
#tSetupField { grid-column: span 2; }
@media (max-width: 380px) { #tSetupField { grid-column: 1 / -1; } }''')
# Pre-market: the plan box spans the whole card under bias/mood and the checklist
rep('''              <div class="field"><label for="jPlan">Plan: levels, news, what I'm waiting for</label><textarea id="jPlan" placeholder="NQ: draw is PDL. Waiting for a sweep of the London low, then the 15m FVG to inverse."></textarea></div>
''', "")
rep('''            <div class="field"><span class="flabel">Before you trade</span><div class="checklist" id="jChecks"></div></div>
''', '''            <div class="field"><span class="flabel">Before you trade</span><div class="checklist" id="jChecks"></div></div>
            <div class="field plan"><label for="jPlan">Plan: levels, news, what I'm waiting for</label><textarea id="jPlan" placeholder="NQ: draw is PDL. Waiting for a sweep of the London low, then the 15m FVG to inverse."></textarea></div>
''')
# Daily journal: tags and feelings side by side, every writing box full width below
OLD_JBLOCK = '        <div class="jgrid">\n          <div class="jcol">\n            <div class="panel">\n              <div class="quick">\n                <div class="field"><span class="flabel">Market</span><div class="chips" id="jMarkets"></div></div>\n                <div class="field"><span class="flabel">Result</span><div class="chips" id="jResult" data-single></div></div>\n                <div class="field"><span class="flabel">Type</span><div class="chips" id="jKind" data-single></div></div>\n                <div class="field"><span class="flabel">Importance</span><div class="chips" id="jImportance" data-single></div></div>\n              </div>\n              <div class="field" id="jNoTradeWhy" hidden style="margin-top:14px"><label for="jRestReason">Why I sat out</label><select id="jRestReason"><option value="">Pick one</option><option>No A+ setup</option><option>High-impact news</option><option>Tired or emotional</option><option>Hit my weekly goal</option><option>Rule after losses</option><option>Holiday / thin market</option><option>Life</option></select></div>\n              <div class="mini" id="jMini"></div>\n              <p class="calc" style="margin-top:8px">P/L and RR fill in from the trades you logged on this day.</p>\n            </div>\n            <div class="panel">\n              <div class="panel-head"><h2>Charts</h2></div>\n              <div class="stack" id="jShotField" style="gap:12px">\n                <div class="shots" id="jShots"></div>\n                <div class="drop" id="jShotDrop">Press Ctrl+V (⌘V on a Mac) anywhere on this page to paste a screenshot, drop one here, or <label for="jShotFile" style="color:var(--accent);cursor:pointer;text-decoration:underline">choose a file</label>. It sizes itself to fit. Click it to see it full screen.<input type="file" id="jShotFile" accept="image/png,image/jpeg,image/webp,image/gif" multiple hidden></div>\n              </div>\n              <p class="calc" id="jShotOff" hidden>Screenshots need the journal opened from claude.ai while signed in.</p>\n            </div>\n          </div>\n          <div class="jcol">\n            <div class="panel"><div class="field"><h2 style="margin-bottom:6px"><label for="jThoughts">Thoughts</label></h2><textarea id="jThoughts" style="min-height:190px" placeholder="What happened today, why you took it, how it felt."></textarea></div></div>\n            <div class="panel">\n              <h2 style="margin-bottom:12px">How I felt</h2>\n              <div class="field"><span class="flabel">Before</span><div class="chips" id="jFeelBefore"></div></div>\n              <div class="field" style="margin-top:12px"><span class="flabel">After</span><div class="chips" id="jFeelAfter"></div></div>\n            </div>\n            <div class="panel good"><h2 style="margin-bottom:10px">Good things I did</h2><div class="bullets" id="jGood"></div><div style="margin-top:8px"><button type="button" class="btn-small" data-add-bullet="jGood">+ Add a point</button></div></div>\n            <div class="panel bad"><h2 style="margin-bottom:10px">Bad things I did</h2><div class="bullets bad" id="jBad"></div><div style="margin-top:8px"><button type="button" class="btn-small" data-add-bullet="jBad">+ Add a point</button></div></div>\n            <details class="more panel" id="jMoreBox">\n              <summary>Grade, news and lesson (optional)</summary>\n              <div class="stack" style="gap:12px">\n                <div class="field"><label for="jGrade">Grade the day</label><select id="jGrade"><option value="">Not graded</option><option>S</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option></select></div>\n                <div class="field"><span class="flabel">Red-folder news and headlines that moved the market</span><div class="chips" id="jNews"></div></div>\n                <div class="field"><label for="jNewsNotes">News notes: times, actual vs forecast, how price reacted</label><input id="jNewsNotes" placeholder="CPI 0.4% vs 0.3% expected, NAS100 dumped 150 pts at 8:30 ET"></div>\n                <div class="field"><label for="jLesson">One lesson to carry forward</label><input id="jLesson"></div>\n              </div>\n            </details>\n            <div class="actions"><button type="submit" class="btn-primary">Save day</button></div>\n          </div>\n        </div>\n'
NEW_JBLOCK = '        <div class="jgrid">\n            <div class="panel">\n              <div class="quick">\n                <div class="field"><span class="flabel">Market</span><div class="chips" id="jMarkets"></div></div>\n                <div class="field"><span class="flabel">Result</span><div class="chips" id="jResult" data-single></div></div>\n                <div class="field"><span class="flabel">Type</span><div class="chips" id="jKind" data-single></div></div>\n                <div class="field"><span class="flabel">Importance</span><div class="chips" id="jImportance" data-single></div></div>\n              </div>\n              <div class="field" id="jNoTradeWhy" hidden style="margin-top:14px"><label for="jRestReason">Why I sat out</label><select id="jRestReason"><option value="">Pick one</option><option>No A+ setup</option><option>High-impact news</option><option>Tired or emotional</option><option>Hit my weekly goal</option><option>Rule after losses</option><option>Holiday / thin market</option><option>Life</option></select></div>\n              <div class="mini" id="jMini"></div>\n              <p class="calc" style="margin-top:8px">P/L and RR fill in from the trades you logged on this day.</p>\n            </div>\n            <div class="panel">\n              <h2 style="margin-bottom:12px">How I felt</h2>\n              <div class="field"><span class="flabel">Before</span><div class="chips" id="jFeelBefore"></div></div>\n              <div class="field" style="margin-top:12px"><span class="flabel">After</span><div class="chips" id="jFeelAfter"></div></div>\n            </div>\n        </div>\n        <div class="panel"><div class="field"><h2 style="margin-bottom:6px"><label for="jThoughts">Thoughts</label></h2><textarea id="jThoughts" style="min-height:190px" placeholder="What happened today, why you took it, how it felt."></textarea></div></div>\n        <div class="panel good"><h2 style="margin-bottom:10px">Good things I did</h2><div class="bullets" id="jGood"></div><div style="margin-top:8px"><button type="button" class="btn-small" data-add-bullet="jGood">+ Add a point</button></div></div>\n        <div class="panel bad"><h2 style="margin-bottom:10px">Bad things I did</h2><div class="bullets bad" id="jBad"></div><div style="margin-top:8px"><button type="button" class="btn-small" data-add-bullet="jBad">+ Add a point</button></div></div>\n        <div class="panel">\n          <div class="panel-head"><h2>Charts</h2></div>\n          <div class="stack" id="jShotField" style="gap:12px">\n            <div class="shots" id="jShots"></div>\n            <div class="drop" id="jShotDrop">Press Ctrl+V (⌘V on a Mac) anywhere on this page to paste a screenshot, drop one here, or <label for="jShotFile" style="color:var(--accent);cursor:pointer;text-decoration:underline">choose a file</label>. It sizes itself to fit. Click it to see it full screen.<input type="file" id="jShotFile" accept="image/png,image/jpeg,image/webp,image/gif" multiple hidden></div>\n          </div>\n          <p class="calc" id="jShotOff" hidden>Screenshots need the journal opened from claude.ai while signed in.</p>\n        </div>\n        <details class="more panel" id="jMoreBox">\n          <summary>Grade, news and lesson (optional)</summary>\n          <div class="fields" style="margin-top:4px">\n            <div class="field"><label for="jGrade">Grade the day</label><select id="jGrade"><option value="">Not graded</option><option>S</option><option>A</option><option>B</option><option>C</option><option>D</option><option>F</option></select></div>\n            <div class="field wide"><span class="flabel">Red-folder news and headlines that moved the market</span><div class="chips" id="jNews"></div></div>\n            <div class="field wide"><label for="jNewsNotes">News notes: times, actual vs forecast, how price reacted</label><textarea class="line" id="jNewsNotes" rows="1" placeholder="CPI 0.4% vs 0.3% expected, NAS100 dumped 150 pts at 8:30 ET"></textarea></div>\n            <div class="field wide"><label for="jLesson">One lesson to carry forward</label><textarea class="line" id="jLesson" rows="1"></textarea></div>\n          </div>\n        </details>\n        <div class="actions"><button type="submit" class="btn-primary">Save day</button></div>\n'
rep(OLD_JBLOCK, NEW_JBLOCK)
rep('''<div class="field"><span class="flabel">Good things I did</span><div class="bullets" id="tGood">''', '''<div class="field wide"><span class="flabel">Good things I did</span><div class="bullets" id="tGood">''')
rep('''<div class="field"><span class="flabel">Bad things I did</span><div class="bullets bad" id="tBad">''', '''<div class="field wide"><span class="flabel">Bad things I did</span><div class="bullets bad" id="tBad">''')
rep('''<input id="wFocus">''', '''<textarea class="line" id="wFocus" rows="1"></textarea>''')

# v13 deep-check fixes
rep(""".bullets .row button { margin-top: 3px; }""", """.bullets .row button { margin-top: 3px; }
.bullets { grid-template-columns: minmax(0, 1fr); }
.bullets .row { min-width: 0; }
textarea { overflow-wrap: anywhere; }
.clamp, #wLessons li { overflow-wrap: anywhere; white-space: pre-line; }
@supports not (field-sizing: content) { textarea.line { resize: vertical; min-height: 4.4em; } .bullets textarea { resize: vertical; } }""")
rep("""#tSetupField { grid-column: span 2; }
@media (max-width: 380px) { #tSetupField { grid-column: 1 / -1; } }""", """@media (min-width: 400px) { #tSetupField { grid-column: span 2; } }""")
rep(""".jcol { display: grid; gap: 16px; min-width: 0; }
""", "")
# coach: every journal field stays on one line so each day is one line of the prompt
rep("""${x.newsNotes ? `newsNotes:"${x.newsNotes.slice(0, 160)}" ` : ""}""", """${x.newsNotes ? `newsNotes:"${oneLine(x.newsNotes, 160)}" ` : ""}""")
rep("""plan:"${(x.plan || "").slice(0, 200)}" thoughts:"${(x.thoughts ?? x.review ?? "").slice(0, 400).replace(/\\s+/g, " ")}"${(x.good || []).length ? ` did-well:"${x.good.join("; ").slice(0, 300)}"` : ""}${(x.bad || []).length ? ` did-badly:"${x.bad.join("; ").slice(0, 300)}"` : ""} lesson:"${x.lesson || ""}\"""",
    """plan:"${oneLine(x.plan, 200)}" thoughts:"${oneLine(x.thoughts ?? x.review, 400)}"${(x.good || []).length ? ` did-well:"${oneLine(x.good.join("; "), 300)}"` : ""}${(x.bad || []).length ? ` did-badly:"${oneLine(x.bad.join("; "), 300)}"` : ""} lesson:"${oneLine(x.lesson, 300)}\"""")
rep("""`MY WEEKLY REVIEW: grade ${week.grade || "-"}; went well: ${week.well || "-"}; went wrong: ${week.wrong || "-"}; focus: ${week.focus || "-"}`""",
    """`MY WEEKLY REVIEW: grade ${week.grade || "-"}; went well: ${oneLine(week.well, 600) || "-"}; went wrong: ${oneLine(week.wrong, 600) || "-"}; focus: ${oneLine(week.focus, 300) || "-"}`""")
rep("""  async function askCoach(preset) {""", """  function oneLine(v, n) { return String(v ?? "").replace(/\\s+/g, " ").trim().slice(0, n); }
  async function askCoach(preset) {""")
# weekly review: typed text is saved when you change week, switch to Daily or leave the journal
rep("""  let curWeek = weekStart(today()), loadedWeek = null;
  function setJournalMode(week) {
    if (week && dayDirty) saveDay(true);""", """  let curWeek = weekStart(today()), loadedWeek = null, weekDirty = false;
  function setJournalMode(week) {
    if (week && dayDirty) saveDay(true);
    if (!week && weekDirty) saveWeek(true);""")
rep("""    curWeek = ws; loadedWeek = ws;
    const w = S.weeks.get(ws) || {};""", """    if (weekDirty && loadedWeek) saveWeek(true);
    curWeek = ws; loadedWeek = ws; weekDirty = false;
    const w = S.weeks.get(ws) || {};""")
rep("""  $("weekForm").addEventListener("submit", (ev) => {
    ev.preventDefault();
    const w = { id: curWeek, grade: $("wGrade").value, well: $("wWell").value.trim(), wrong: $("wWrong").value.trim(), focus: $("wFocus").value.trim(), updatedAt: Date.now() };
    persist(() => backend.put("weeks", w), "Weekly review saved");
  });""", """  function saveWeek(quiet) {
    const id = loadedWeek || curWeek;
    const w = { ...(S.weeks.get(id) || {}), id, grade: $("wGrade").value, well: $("wWell").value.trim(), wrong: $("wWrong").value.trim(), focus: $("wFocus").value.trim(), updatedAt: Date.now() };
    weekDirty = false; S.weeks.set(id, w); renderWeekList();
    return persist(() => backend.put("weeks", w), "Weekly review saved");
  }
  $("weekForm").addEventListener("input", () => (weekDirty = true));
  $("weekForm").addEventListener("change", () => (weekDirty = true));
  $("weekForm").addEventListener("submit", (ev) => { ev.preventDefault(); saveWeek(false); });""")
rep("""    if (dayDirty && tab !== "journal" && !$("view-journal").hidden) saveDay(true);""", """    if (dayDirty && tab !== "journal" && !$("view-journal").hidden) saveDay(true);
    if (weekDirty && tab !== "journal" && !$("view-journal").hidden) saveWeek(true);""")
rep("""window.addEventListener("beforeunload", (e) => { if (dayDirty) {""", """window.addEventListener("beforeunload", (e) => { if (dayDirty || weekDirty) {""")

# previews: blank lines collapse so the 2-line preview shows text
for a in ['${esc(p.description)}</p>', '${esc(d.lesson)}</span>', '${esc(text)}</span>', '${esc(d.plan)}</span>', '${esc(w.focus)}</span>', '${esc(x.lesson)}</li>']:
    v = a[6:a.index(")")]
    rep(a, a.replace(f"esc({v})", f"esc(tight({v}))"))
rep("""  function oneLine(v, n) {""", """  function tight(v) { return String(v ?? "").replace(/\\n\\s*\\n+/g, "\\n"); }
  function oneLine(v, n) {""")
rep("""return persist(() => backend.put("weeks", w), "Weekly review saved");
  }""", """return persist(() => backend.put("weeks", w), quiet ? `Saved week of ${fmtDay(id, { month: "short", day: "numeric" })}` : "Weekly review saved");
  }""")

# v14 (2026-10-20): Instrument is a real dropdown (the typed list only showed matches, so it looked broken)
rep("""<div class="field"><label for="tInstrument">Instrument</label><input id="tInstrument" list="instrumentList" placeholder="NAS100" required></div>""",
    """<div class="field"><label for="tInstrumentPick">Instrument</label><select id="tInstrumentPick"></select><input id="tInstrument" aria-label="Instrument symbol" placeholder="Type the symbol, e.g. NAS100" hidden></div>""")
rep("""<datalist id="instrumentList">
  <option>NAS100</option><option>US30</option><option>SPX500</option><option>GER40</option><option>UK100</option><option>JPN225</option><option>US2000</option><option>FRA40</option><option>AUS200</option><option>HK50</option><option>XAUUSD</option>
</datalist>
""", "")
rep("""    Object.entries(F).forEach(([k, el]) => ($(el).value = t ? t[k] ?? "" : defaults[k] ?? ""));
""", """    Object.entries(F).forEach(([k, el]) => ($(el).value = t ? t[k] ?? "" : defaults[k] ?? ""));
    syncInstrumentPick();
""")
rep("""  function openEditor(id) {""", """  // Instrument dropdown: your usual indices plus anything you've logged before; "Other" lets you type a new one.
  const INSTRUMENTS = ["NAS100", "US30", "SPX500", "GER40", "UK100", "JPN225", "US2000", "FRA40", "AUS200", "HK50", "XAUUSD"];
  function syncInstrumentPick() {
    const cur = $("tInstrument").value.trim(), pick = $("tInstrumentPick");
    const used = [...new Set([...S.trades.values()].map((t) => String(t.instrument || "").trim()).filter((s) => s && !INSTRUMENTS.includes(s)))].sort();
    pick.innerHTML = [...INSTRUMENTS, ...used].map((s) => `<option>${esc(s)}</option>`).join("") + `<option value="__other">Other (type it)</option>`;
    pick.value = cur && [...INSTRUMENTS, ...used].includes(cur) ? cur : "__other";
    $("tInstrument").hidden = pick.value !== "__other";
  }
  $("tInstrumentPick").addEventListener("change", () => {
    const v = $("tInstrumentPick").value, box = $("tInstrument");
    box.hidden = v !== "__other";
    box.value = v === "__other" ? "" : v;
    if (v === "__other") box.focus();
    box.dispatchEvent(new Event("input", { bubbles: true }));
  });
  function openEditor(id) {""")

out = HERE / "trading-journal.html"
out.write_text(s)
print("wrote", out, len(s))
