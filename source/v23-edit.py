#!/usr/bin/env python3
"""v22 -> v23 (PC): one filter bar that drives the dashboard numbers, calendar, recent trades, trade log, equity
curve and every Insights panel (period, month in any year, year, custom dates, instrument, direction, session,
playbook, result, plan, playbook rules, weekday, NY time of day, trade # of the day, feelings, mistakes, tags,
grades, flags, conviction, source), plus a month-by-year grid and a same-month-across-years comparison in Insights.
Live risk numbers (balance, today's limits, discipline, review queue) always use every trade."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

# ---- CSS ----
rep('''.filters select { width: auto; }''', '''.filters select { width: auto; }
.fbar { display: grid; gap: 10px; padding: 12px 14px; margin-top: 20px; }
.fbar + section.view { margin-top: 16px; }
.fbar-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.fbar-row select, .fbar-row input { width: auto; }
.fbar-row .fsum { margin-left: auto; }
.fbar-more { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 165px), 1fr)); gap: 10px; padding-top: 4px; }
.fbar-more label { display: grid; gap: 4px; font-size: 0.78rem; font-weight: 600; color: var(--muted); }
.fbar-more select { width: 100%; }
.fchips { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.fchip { display: inline-flex; align-items: center; font-size: 0.82rem; padding: 2px 2px 2px 10px; border: 1px solid var(--accent); border-radius: 99px; background: rgba(110,168,255,0.12); }
.fchip button { border: 0; background: none; padding: 0 8px; color: var(--muted); font-size: 1rem; line-height: 1.2; }
.fon { color: var(--accent); }
.mby td.c { cursor: pointer; min-width: 92px; }
.mby td.c.sel, .mby th.sel { outline: 2px solid var(--accent); outline-offset: -2px; }
.mby .lnk { border: 0; background: none; padding: 0; color: var(--fg); font: inherit; font-weight: 600; cursor: pointer; text-decoration: underline dotted var(--muted); text-underline-offset: 3px; }
.mby tfoot td { border-top: 1px solid var(--line-strong); }
.mcmp td, .mcmp th { white-space: nowrap; }''')

# ---- shared filter bar (above Dashboard, Trades and Insights) ----
OPT = lambda pairs: "".join(f'<option value="{v}">{t}</option>' for v, t in pairs)
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
more = [
    ("fInstrument", "Instrument", [("", "All instruments")]),
    ("fDir", "Direction", [("", "Long and short"), ("Long", "Long"), ("Short", "Short"), ("none", "Not set")]),
    ("fSession", "Session", [("", "Any session")]),
    ("fSetup", "Playbook / model", [("", "Any playbook")]),
    ("fResult", "Result", [("", "Wins and losses"), ("win", "Wins"), ("loss", "Losses"), ("be", "Breakeven / scratched")]),
    ("fPlan", "Plan", [("", "Any plan adherence"), ("yes", "Followed plan"), ("no", "Broke plan"), ("review", "Needs review")]),
    ("fRules", "Playbook rules", [("", "Any"), ("all", "All rules met"), ("some", "Some rules missed"), ("none", "No checklist")]),
    ("fWeekday", "Day of the week", [("", "Any day"), ("1", "Monday"), ("2", "Tuesday"), ("3", "Wednesday"), ("4", "Thursday"), ("5", "Friday"), ("0", "Sunday"), ("6", "Saturday")]),
    ("fTod", "Time of day (NY)", [("", "Any time"), ("asia", "Asia / overnight (18:00–2:00)"), ("london", "London (2:00–7:00)"), ("pre", "Before the open (7:00–9:30)"), ("am", "AM session (9:30–11:00)"), ("lunch", "Lunch (11:00–13:30)"), ("pm", "PM session (13:30–16:00)"), ("late", "After the close (16:00–18:00)"), ("none", "No time logged")]),
    ("fNth", "Trade # of the day", [("", "Any"), ("1", "1st trade"), ("2", "2nd trade"), ("3", "3rd or later")]),
    ("fFeel", "Feeling before", [("", "Any feeling")]),
    ("fFeelAfter", "Feeling after", [("", "Any feeling")]),
    ("fMistake", "Mistake", [("", "Any"), ("any", "Any mistake tagged"), ("none", "No mistakes")]),
    ("fTag", "Tag", [("", "Any tag")]),
    ("fGrade", "Trade grade", [("", "Any grade")] + [(g, g) for g in "SABCDF"] + [("none", "Not graded")]),
    ("fDayGrade", "Day grade", [("", "Any grade")] + [(g, g) for g in "SABCDF"] + [("none", "Not graded")]),
    ("fFlag", "Rule-break flags", [("", "Any"), ("any", "Any flag caught"), ("clean", "Clean (no flag)"), ("Revenge", "Revenge"), ("Over trade limit", "Over trade limit"), ("After", "After the loss stop"), ("Flipped", "Flipped direction"), ("Scratched", "Scratched at breakeven")]),
    ("fConv", "Conviction", [("", "Any"), ("low", "1–3 low"), ("mid", "4–6 medium"), ("high", "7–8 high"), ("top", "9–10 A+"), ("none", "Not set")]),
    ("fSource", "Where it came from", [("", "Anywhere"), ("hand", "Logged by hand"), ("import", "Imported from a platform"), ("onenote", "OneNote"), ("notion", "Notion")]),
]
more_html = "\n".join(f'        <label>{lab}<select id="{i}">{OPT(o)}</select></label>' for i, lab, o in more)
rep('''  <!-- DASHBOARD -->''', f'''  <!-- FILTERS: shared by Dashboard, Trades and Insights -->
  <div class="panel fbar" id="fbar">
    <div class="fbar-row">
      <select id="fPeriod" aria-label="Time period"><option value="">All time</option><option value="week">This week</option><option value="month">This month</option><option value="lastmonth">Last month</option><option value="30">Last 30 days</option><option value="90">Last 90 days</option><option value="year">This year</option><option value="lastyear">Last year</option><option value="custom">Pick dates…</option></select>
      <span class="fbar-row" id="fCustom" hidden><input type="date" id="fFrom" aria-label="From date"><span class="muted">to</span><input type="date" id="fTo" aria-label="To date"></span>
      <select id="fMonth" aria-label="Month, in any year"><option value="">Any month</option>{"".join(f'<option value="{n}">{m} (every year)</option>' for n, m in enumerate(MONTHS, 1))}</select>
      <select id="fYear" aria-label="Year"><option value="">Any year</option></select>
      <button type="button" class="btn-small" id="fMoreBtn" aria-expanded="false" aria-controls="fMore">More filters</button>
      <span class="calc fsum" id="fSum"></span>
    </div>
    <div class="fbar-more" id="fMore" hidden>
{more_html}
    </div>
    <div class="fchips" id="fChips" hidden></div>
  </div>

  <!-- DASHBOARD -->''')

rep('''          <select id="fInstrument" aria-label="Filter by instrument"><option value="">All instruments</option></select>
          <select id="fResult" aria-label="Filter by result"><option value="">Wins and losses</option><option value="win">Wins</option><option value="loss">Losses</option></select>
          <select id="fPlan" aria-label="Filter by plan"><option value="">Any plan adherence</option><option value="yes">Followed plan</option><option value="no">Broke plan</option><option value="review">Needs review</option></select>
          <select id="fTag" aria-label="Filter by tag"><option value="">Any tag</option></select>
''', '')

# ---- Insights: month by year + same month across years ----
rep('''    <div class="stats" id="insightStats"></div>
''', '''    <div class="stats" id="insightStats"></div>
    <div class="panel" id="mcmpPanel">
      <div class="panel-head"><h2 id="mcmpTitle">This month across your years</h2><span class="label">Pick a month in the filter bar to change it</span></div>
      <div id="mcmp"></div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>Month by year</h2><span class="label">Click a cell to filter to it</span></div>
      <p class="calc" style="margin-bottom:10px">Every month you traded, side by side by year. Uses all your filters except the dates, so you can compare across years.</p>
      <div class="table-wrap" id="mby"></div>
    </div>
''')

# ---- JS: filter engine (before render) ----
rep('''  // ---------- render ----------
  function render() {
    renderAccountSelect();
    const acc = activeAccount(), list = accountTrades(acc);
    FLAGS = new Map(); S.accounts.forEach((a) => tradeFlags(accountTrades(a)).forEach((v, k) => FLAGS.set(k, v)));
    if (typeof renderMove === "function") renderMove();
    renderTopTools(); renderDash(list, acc); renderAlert(acc, list); renderReview(list); renderGate(acc, list); renderTrades(); renderPlaybooks(); renderDayList(); renderWeek(); renderWeekList(); renderInsights(list); fillDatalists();''',
'''  // ---------- shared filters ----------
  // One bar drives the dashboard numbers, calendar, recent trades, trade log and Insights. Live risk (balance,
  // today's limits, discipline, review queue) always counts every trade. Filters reset when the app is reopened.
  const FMORE = ["fInstrument", "fDir", "fSession", "fSetup", "fResult", "fPlan", "fRules", "fWeekday", "fTod", "fNth", "fFeel", "fFeelAfter", "fMistake", "fTag", "fGrade", "fDayGrade", "fFlag", "fConv", "fSource"];
  const FDATE = ["fPeriod", "fMonth", "fYear"];
  const FNAMES = { fPeriod: "Period", fMonth: "Month", fYear: "Year", fInstrument: "Instrument", fDir: "Direction", fSession: "Session", fSetup: "Playbook", fResult: "Result", fPlan: "Plan", fRules: "Rules", fWeekday: "Day", fTod: "Time", fNth: "Trade #", fFeel: "Feeling before", fFeelAfter: "Feeling after", fMistake: "Mistake", fTag: "Tag", fGrade: "Trade grade", fDayGrade: "Day grade", fFlag: "Flags", fConv: "Conviction", fSource: "From" };
  const MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const fv = (id) => $(id).value;
  const filterActive = () => [...FDATE, ...FMORE].some((id) => fv(id) && !(id === "fPeriod" && fv(id) === "custom" && !fv("fFrom") && !fv("fTo")));
  function periodRange(p) {
    const td = today(), y = +td.slice(0, 4), m = +td.slice(5, 7);
    const mEnd = (yy, mm) => ymd(new Date(yy, mm, 0));
    if (p === "week") return [addDays(td, -((dateObj(td).getDay() + 6) % 7)), addDays(td, 6 - ((dateObj(td).getDay() + 6) % 7))];
    if (p === "month") return [`${y}-${pad(m)}-01`, mEnd(y, m)];
    if (p === "lastmonth") { const yy = m === 1 ? y - 1 : y, mm = m === 1 ? 12 : m - 1; return [`${yy}-${pad(mm)}-01`, mEnd(yy, mm)]; }
    if (p === "30" || p === "90") return [addDays(td, 1 - +p), td];
    if (p === "year") return [`${y}-01-01`, `${y}-12-31`];
    if (p === "lastyear") return [`${y - 1}-01-01`, `${y - 1}-12-31`];
    if (p === "custom") { let a = fv("fFrom"), b = fv("fTo"); if (a && b && a > b) [a, b] = [b, a]; return [a, b]; }
    return ["", ""];
  }
  function todOf(t) {
    const h = nyHour(t); if (h == null) return "none";
    return h < 2 || h >= 18 ? "asia" : h < 7 ? "london" : h < 9.5 ? "pre" : h < 11 ? "am" : h < 13.5 ? "lunch" : h < 16 ? "pm" : "late";
  }
  const convBand = (t) => { const c = convOf(t); return c == null ? "none" : c <= 3 ? "low" : c <= 6 ? "mid" : c <= 8 ? "high" : "top"; };
  // Trade # of the day counts every trade that day, so filtering doesn't renumber them.
  function nthMap(list) {
    const m = new Map(), by = groupBy(list, (t) => t.date);
    by.forEach((ts) => [...ts].sort((a, b) => (a.time || "").localeCompare(b.time || "")).forEach((t, i) => m.set(t.id, String(Math.min(i + 1, 3)))));
    return m;
  }
  // keepDates: ignore the period, month and year (the month-by-year grid compares across them).
  function applyFilter(list, keepDates) {
    const f = Object.fromEntries([...FDATE, ...FMORE].map((id) => [id, fv(id)]));
    if (!Object.values(f).some(Boolean)) return list;
    const [from, to] = keepDates ? ["", ""] : periodRange(f.fPeriod), nth = f.fNth ? nthMap(list) : null;
    const realFlags = (t) => flagsOf(t).filter((x) => !x.startsWith("Scratched"));
    return list.filter((t) => {
      const d = t.date || "", p = num(t.pnl), mis = t.mistakes || [];
      if (!keepDates && ((from && d < from) || (to && d > to) || (f.fMonth && +d.slice(5, 7) !== +f.fMonth) || (f.fYear && d.slice(0, 4) !== f.fYear))) return false;
      if (f.fInstrument && t.instrument !== f.fInstrument) return false;
      if (f.fDir && (f.fDir === "none" ? !!t.dir : t.dir !== f.fDir)) return false;
      if (f.fSession && t.session !== f.fSession) return false;
      if (f.fSetup && setupName(t) !== f.fSetup) return false;
      if (f.fResult && !(f.fResult === "win" ? p > 0 : f.fResult === "loss" ? p < 0 : p === 0 || isScratch(t))) return false;
      if (f.fPlan && !(f.fPlan === "review" ? !reviewed(t) : f.fPlan === "yes" ? t.followedPlan === true : t.followedPlan === false)) return false;
      if (f.fRules && !(f.fRules === "none" ? !t.rulesTotal : t.rulesTotal && ((t.rulesChecked || []).length >= t.rulesTotal) === (f.fRules === "all"))) return false;
      if (f.fWeekday && dateObj(d).getDay() !== +f.fWeekday) return false;
      if (f.fTod && todOf(t) !== f.fTod) return false;
      if (nth && nth.get(t.id) !== f.fNth) return false;
      if (f.fFeel && !feelsOf(t, "before").includes(f.fFeel)) return false;
      if (f.fFeelAfter && !feelsOf(t, "after").includes(f.fFeelAfter)) return false;
      if (f.fMistake && !(f.fMistake === "any" ? mis.length : f.fMistake === "none" ? !mis.length : mis.includes(f.fMistake))) return false;
      if (f.fTag && !(t.tags || []).includes(f.fTag)) return false;
      if (f.fGrade && (t.grade || "none") !== f.fGrade) return false;
      if (f.fDayGrade && ((S.days.get(d) || {}).grade || "none") !== f.fDayGrade) return false;
      if (f.fFlag && !(f.fFlag === "any" ? realFlags(t).length : f.fFlag === "clean" ? !realFlags(t).length : flagsOf(t).some((x) => x.startsWith(f.fFlag)))) return false;
      if (f.fConv && convBand(t) !== f.fConv) return false;
      if (f.fSource && sourceOf(t) !== f.fSource) return false;
      return true;
    });
  }
  function fillSel(id, values, label) {
    const sel = $(id), cur = sel.value, fixed = [...sel.options].filter((o) => o.dataset.fixed != null || o.value === "" || ["any", "none"].includes(o.value));
    const vals = [...new Set([...values, ...(cur && !fixed.some((o) => o.value === cur) ? [cur] : [])])].filter(Boolean).sort((a, b) => String(a).localeCompare(String(b)));
    const head = fixed.map((o) => `<option value="${esc(o.value)}" data-fixed>${esc(o.value === "" ? label : o.textContent)}</option>`).join("");
    sel.innerHTML = head + vals.map((v) => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
    sel.value = cur;
  }
  function renderFilterBar(all, shown) {
    fillSel("fInstrument", all.map((t) => t.instrument), "All instruments");
    fillSel("fSession", all.map((t) => t.session), "Any session");
    fillSel("fSetup", all.map(setupName), "Any playbook");
    fillSel("fFeel", all.flatMap((t) => feelsOf(t, "before")), "Any feeling");
    fillSel("fFeelAfter", all.flatMap((t) => feelsOf(t, "after")), "Any feeling");
    fillSel("fMistake", all.flatMap((t) => t.mistakes || []), "Any");
    fillSel("fTag", all.flatMap((t) => t.tags || []), "Any tag");
    const ySel = $("fYear"), yCur = ySel.value, years = [...new Set([today().slice(0, 4), ...all.map((t) => (t.date || "").slice(0, 4)).filter((y) => /^\\d{4}$/.test(y)), ...(yCur ? [yCur] : [])])].sort().reverse();
    ySel.innerHTML = `<option value="">Any year</option>` + years.map((y) => `<option>${y}</option>`).join(""); ySel.value = yCur;
    $("fCustom").hidden = fv("fPeriod") !== "custom";
    const on = filterActive(), nMore = FMORE.filter((id) => fv(id)).length;
    $("fMoreBtn").textContent = nMore ? `More filters (${nMore})` : "More filters";
    $("fMoreBtn").classList.toggle("fon", !!nMore);
    const chips = [...FDATE, ...FMORE].filter((id) => fv(id)).map((id) => {
      let txt = $(id).selectedOptions[0]?.textContent || fv(id);
      if (id === "fPeriod" && fv(id) === "custom") { const [a, b] = periodRange("custom"); if (!a && !b) return ""; const fd = (x) => fmtDay(x, { month: "short", day: "numeric", year: "numeric" }); txt = `${a ? fd(a) : "start"} – ${b ? fd(b) : "today"}`; }
      if (id === "fMonth") txt = txt.replace(" (every year)", fv("fYear") ? "" : " · every year");
      return `<span class="fchip">${esc(FNAMES[id])}: ${esc(txt)}<button type="button" data-fclear="${id}" aria-label="Remove ${esc(FNAMES[id])} filter">×</button></span>`;
    }).filter(Boolean);
    $("fChips").hidden = !on;
    $("fChips").innerHTML = chips.join("") + (chips.length > 1 ? `<button type="button" class="btn-small" data-fclear="all">Clear all</button>` : "");
    $("fSum").innerHTML = on ? `<span class="fon">Showing ${shown} of ${plural(all.length, "trade")}</span>` : `All ${plural(all.length, "trade")}`;
  }
  function clearFilters(quiet) {
    [...FDATE, ...FMORE, "fFrom", "fTo"].forEach((id) => { $(id).value = ""; });
    if (!quiet) render();
  }
  function onFilter(e) {
    const id = e?.target?.id;
    // Picking a period clears a clashing month/year pick, and the other way round, so the result is never empty by accident.
    if (id === "fPeriod" && fv("fPeriod") && fv("fPeriod") !== "custom") { $("fMonth").value = ""; $("fYear").value = ""; }
    if ((id === "fMonth" || id === "fYear") && fv(id)) { $("fPeriod").value = ""; }
    const m = +fv("fMonth"), y = +fv("fYear"), p = fv("fPeriod");
    if (m && y) calMonth = new Date(y, m - 1, 1);
    else if (p === "month" || p === "lastmonth") { const [a] = periodRange(p); calMonth = new Date(+a.slice(0, 4), +a.slice(5, 7) - 1, 1); }
    render();
  }
  [...FDATE, ...FMORE, "fFrom", "fTo"].forEach((id) => $(id).addEventListener("change", onFilter));
  $("fMoreBtn").addEventListener("click", () => { const open = $("fMore").hidden; $("fMore").hidden = !open; $("fMoreBtn").setAttribute("aria-expanded", String(open)); });
  $("fChips").addEventListener("click", (e) => {
    const b = e.target.closest("[data-fclear]"); if (!b) return;
    if (b.dataset.fclear === "all") { clearFilters(); return; }
    $(b.dataset.fclear).value = ""; if (b.dataset.fclear === "fPeriod") { $("fFrom").value = ""; $("fTo").value = ""; }
    render();
  });

  // ---------- render ----------
  function render() {
    renderAccountSelect();
    const acc = activeAccount(), full = accountTrades(acc);
    FLAGS = new Map(); S.accounts.forEach((a) => tradeFlags(accountTrades(a)).forEach((v, k) => FLAGS.set(k, v)));
    const list = applyFilter(full);
    if (typeof renderMove === "function") renderMove();
    renderFilterBar(full, list.length);
    renderTopTools(); renderDash(list, acc, full); renderAlert(acc, full); renderReview(full); renderGate(acc, full); renderTrades(); renderPlaybooks(); renderDayList(); renderWeek(); renderWeekList(); renderInsights(list); renderMonthYear(full); fillDatalists();''')

# ---- dashboard: filtered tiles, live risk on every trade ----
rep('''  function renderDash(list, acc) {
    const s = summarize(list), bal0 = +acc.startBalance || 0, balance = bal0 + s.net, dsc = discipline(list, acc);
    $("dashStats").innerHTML = [
      statTile("Balance", money(balance, false), "", `${pl(s)} since start`),
      statTile("Win rate", fmtPct(s.winRate), "", `${s.wins}W · ${s.losses}L`),
      statTile("Profit factor", fmtPf(s.pf), s.pf != null && s.pf !== Infinity ? (s.pf >= 1 ? "gain" : "loss") : ""),
      statTile("Avg R", fmtR(s.avgR), cls(s.avgR)),
      statTile("Avg win : avg loss", s.avgWin != null && s.avgLoss ? `${(s.avgWin / -s.avgLoss).toFixed(2)} : 1` : "–", s.avgWin != null && s.avgLoss ? (s.avgWin >= -s.avgLoss ? "gain" : "loss") : "", s.avgWin != null && s.avgLoss ? `${money(s.avgWin, false)} vs ${money(-s.avgLoss, false)}` : ""),
      statTile("Discipline", dsc.score == null ? "–" : String(dsc.score), scoreCls(dsc.score), "out of 100"),
    ].join("");

    const td = today(), byDay = dailyPnl(list), todayPnl = byDay.get(td) || 0, todayTrades = list.filter((t) => t.date === td).length;''',
'''  function renderDash(list, acc, full = list) {
    const s = summarize(full), fs = summarize(list), bal0 = +acc.startBalance || 0, balance = bal0 + s.net, dsc = discipline(full, acc), on = filterActive();
    $("dashStats").innerHTML = [
      on ? statTile("Net P&L (filtered)", pl(fs), cls(plOf(fs)), `${plural(fs.n, "trade")} · balance ${money(balance, false)}`) : statTile("Balance", money(balance, false), "", `${pl(s)} since start`),
      statTile("Win rate", fmtPct(fs.winRate), "", `${fs.wins}W · ${fs.losses}L`),
      statTile("Profit factor", fmtPf(fs.pf), fs.pf != null && fs.pf !== Infinity ? (fs.pf >= 1 ? "gain" : "loss") : ""),
      statTile("Avg R", fmtR(fs.avgR), cls(fs.avgR)),
      statTile("Avg win : avg loss", fs.avgWin != null && fs.avgLoss ? `${(fs.avgWin / -fs.avgLoss).toFixed(2)} : 1` : "–", fs.avgWin != null && fs.avgLoss ? (fs.avgWin >= -fs.avgLoss ? "gain" : "loss") : "", fs.avgWin != null && fs.avgLoss ? `${money(fs.avgWin, false)} vs ${money(-fs.avgLoss, false)}` : ""),
      statTile("Discipline", dsc.score == null ? "–" : String(dsc.score), scoreCls(dsc.score), on ? "out of 100 · all trades" : "out of 100"),
    ].join("");

    const td = today(), byDay = dailyPnl(full), todayPnl = byDay.get(td) || 0, todayTrades = full.filter((t) => t.date === td).length;''')
rep('''    renderToday(acc, list, { todayPnl, todayTrades, dailyLim, maxT, dsc });
    renderDiscipline(dsc);
    renderProp();
    renderWhatIf(list, bal0, maxLim, target);''', '''    renderToday(acc, full, { todayPnl, todayTrades, dailyLim, maxT, dsc });
    renderDiscipline(dsc);
    renderProp();
    // Filtered: the curve is the running P&L of those trades from zero, with no floor or target lines.
    if (on) renderWhatIf(list, 0, null, 0); else renderWhatIf(list, bal0, maxLim, target);''')
rep('''    $("recent").innerHTML = recent.length ? tradeTable(recent, true) : emptyState("Nothing logged yet", "Log each trade you take, or import your history from the Trades tab.", true);''',
    '''    $("recent").innerHTML = recent.length ? tradeTable(recent, true) : full.length ? `<p class="muted">No trades match your filters.</p>` : emptyState("Nothing logged yet", "Log each trade you take, or import your history from the Trades tab.", true);''')
rep('''    if (!list.length) { $("whatif").innerHTML = emptyState("Nothing to compare yet", "Once you tag mistakes on your trades, this shows your results with those trades taken out.", false); return; }''',
    '''    if (!list.length) { $("whatif").innerHTML = maxLim == null ? `<p class="muted">No trades match your filters.</p>` : emptyState("Nothing to compare yet", "Once you tag mistakes on your trades, this shows your results with those trades taken out.", false); return; }''')
rep('''      ${equityChart(list, bal0, bal0 - maxLim, target > 0 ? bal0 + target : null, bad.length ? list.map((t) => (isMistake(t) ? 0 : num(t.pnl) || 0)) : null)}
      <div class="legend"><span><i style="border-color:var(--gain)"></i>Actual balance</span>''',
    '''      ${equityChart(list, bal0, maxLim == null ? -Infinity : bal0 - maxLim, target > 0 ? bal0 + target : null, bad.length ? list.map((t) => (isMistake(t) ? 0 : num(t.pnl) || 0)) : null)}
      <div class="legend"><span><i style="border-color:var(--gain)"></i>${maxLim == null ? "Running P&amp;L of the filtered trades" : "Actual balance"}</span>''')

# ---- trade log uses the shared bar ----
rep('''    const all = accountTrades().reverse();
    const fill = (sel, values, label) => { const cur = sel.value; sel.innerHTML = `<option value="">${label}</option>` + values.map((v) => `<option ${v === cur ? "selected" : ""}>${esc(v)}</option>`).join(""); };
    fill($("fInstrument"), [...new Set(all.map((t) => t.instrument).filter(Boolean))].sort(), "All instruments");
    fill($("fTag"), [...new Set(all.flatMap((t) => t.tags || []))].sort(), "Any tag");
    const fi = $("fInstrument").value, fr = $("fResult").value, fp = $("fPlan").value, ft = $("fTag").value;
    const list = all.filter((t) => (!fi || t.instrument === fi) && (!fr || (fr === "win" ? num(t.pnl) > 0 : num(t.pnl) < 0))
      && (!fp || (fp === "review" ? !reviewed(t) : fp === "yes" ? t.followedPlan === true : t.followedPlan === false)) && (!ft || (t.tags || []).includes(ft)));''',
    '''    const all = accountTrades().reverse(), list = applyFilter(all), fp = fv("fPlan");''')
rep('''    $("showPending")?.addEventListener("click", (e) => { e.preventDefault(); $("fPlan").value = "review"; renderTrades(); });
    $("tradeTable").querySelector(".showAllTrades")?.addEventListener("click", (e) => { e.preventDefault(); ["fInstrument", "fResult", "fPlan", "fTag"].forEach((id) => { $(id).value = ""; }); renderTrades(); });''',
    '''    $("showPending")?.addEventListener("click", (e) => { e.preventDefault(); clearFilters(true); $("fPlan").value = "review"; render(); });
    $("tradeTable").querySelector(".showAllTrades")?.addEventListener("click", (e) => { e.preventDefault(); clearFilters(); });''')
rep('''  ["fInstrument", "fResult", "fPlan", "fTag"].forEach((id) => $(id).addEventListener("change", renderTrades));
  $("calPrev").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() - 1); renderCalendar(accountTrades()); });
  $("calNext").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() + 1); renderCalendar(accountTrades()); });''',
    '''  $("calPrev").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() - 1); renderCalendar(applyFilter(accountTrades())); });
  $("calNext").addEventListener("click", () => { calMonth.setMonth(calMonth.getMonth() + 1); renderCalendar(applyFilter(accountTrades())); });''')
rep('''  $("emoTagMode").addEventListener("change", () => renderEmoTag(accountTrades(activeAccount())));''',
    '''  $("emoTagMode").addEventListener("change", () => renderEmoTag(applyFilter(accountTrades(activeAccount()))));''')
rep('''    if (ok) $("fPlan").value = "review"; showTab("trades"); renderTrades();''',
    '''    if (ok) { clearFilters(true); $("fPlan").value = "review"; } showTab("trades"); render();''')

# ---- filter bar shows on Dashboard, Trades and Insights ----
rep('''    document.querySelectorAll("section.view").forEach((v) => (v.hidden = v.id !== "view-" + tab));''',
    '''    document.querySelectorAll("section.view").forEach((v) => (v.hidden = v.id !== "view-" + tab));
    $("fbar").hidden = !["dash", "trades", "insights"].includes(tab);''')

# ---- month by year grid + same month across years ----
rep('''  function prevWeekday(s) {''', '''  // Month by year: rows are months, columns are years. Ignores the date filters so every year shows.
  function renderMonthYear(full) {
    const base = applyFilter(full, true), el = $("mby");
    if (!base.length) { el.innerHTML = `<p class="muted">${full.length ? "No trades match your other filters." : "Log some trades to fill this grid."}</p>`; renderMonthCompare(base); return; }
    const cells = groupBy(base, (t) => (t.date || "").slice(0, 7)), years = [...new Set(base.map((t) => (t.date || "").slice(0, 4)))].filter((y) => /^\\d{4}$/.test(y)).sort();
    const hv = (x) => plOf(x) || 0, sm = new Map([...cells].map(([k, ts]) => [k, summarize(ts)]));
    const max = Math.max(inR() ? 0.01 : 1, ...[...sm.values()].map((x) => Math.abs(hv(x))));
    const selM = +fv("fMonth"), selY = fv("fYear");
    const td = (x, attrs, sel) => (x && x.n ? `<td class="c${sel ? " sel" : ""}" ${attrs} style="background:color-mix(in srgb, ${hideNums ? "var(--accent)" : hv(x) >= 0 ? "var(--gain)" : "var(--loss)"} ${hideNums ? 10 : Math.round(8 + Math.min(1, Math.abs(hv(x)) / max) * 40)}%, transparent)" title="${plural(x.n, "trade")} · win rate ${fmtPct(x.winRate)} · avg ${fmtRraw(x.avgR)}"><span class="${cls(plOf(x))}">${pl(x)}</span><small>${x.n}t · ${fmtPct(x.winRate)} · ${fmtR(x.avgR)}</small></td>` : `<td class="c muted"${sel ? ' style="outline:2px solid var(--accent);outline-offset:-2px"' : ""}>–</td>`);
    const rows = MONTH_NAMES.map((name, i) => {
      const mm = pad(i + 1);
      if (!years.some((y) => sm.has(`${y}-${mm}`))) return "";
      return `<tr><td><button type="button" class="lnk" data-mby-month="${i + 1}" title="${name} in every year">${name.slice(0, 3)}</button></td>${years.map((y) => td(sm.get(`${y}-${mm}`), `data-mby="${y}-${i + 1}"`, selM === i + 1 && (!selY || selY === y))).join("")}</tr>`;
    }).join("");
    const tot = years.map((y) => { const x = summarize(base.filter((t) => t.date.startsWith(y))); return td(x, `data-mby-year="${y}"`, !selM && selY === y); }).join("");
    el.innerHTML = `<table class="heat mby"><thead><tr><th>Month</th>${years.map((y) => `<th class="${!selM && selY === y ? "sel" : ""}">${y}</th>`).join("")}</tr></thead><tbody>${rows}</tbody><tfoot><tr><td><strong>Year</strong></td>${tot}</tr></tfoot></table>`;
    renderMonthCompare(base);
  }
  // The chosen month (or this month) in every year you traded it.
  function renderMonthCompare(base) {
    const now = today(), m = +fv("fMonth") || +now.slice(5, 7), name = MONTH_NAMES[m - 1], el = $("mcmp");
    $("mcmpTitle").textContent = `${name} across your years`;
    const inMonth = base.filter((t) => +(t.date || "").slice(5, 7) === m), by = groupBy(inMonth, (t) => t.date.slice(0, 4));
    const years = [...by.keys()].sort();
    if (!years.length) { el.innerHTML = `<p class="muted">No ${name} trades${filterActive() ? " match your other filters" : " yet"}.</p>`; return; }
    let prev = null;
    const rows = years.map((y) => {
      const ts = by.get(y), x = summarize(ts), days = [...dailyPnl(ts).values()], v = plOf(x);
      const green = days.filter((p) => p > 0).length, cur = `${y}-${pad(m)}` === now.slice(0, 7);
      const diff = prev == null || v == null ? null : v - prev; prev = v;
      const fmtD = (d) => (d == null ? "–" : inR() ? fmtR(d) : money(d));
      return `<tr><td><button type="button" class="lnk" data-mby="${y}-${m}">${y}</button>${cur ? ' <span class="muted">so far</span>' : ""}</td><td class="r num">${x.n}</td><td class="r num ${cls(v)}">${pl(x)}</td><td class="r num">${fmtPct(x.winRate)}</td><td class="r num ${cls(x.avgR)}">${fmtR(x.avgR)}</td><td class="r num">${fmtPf(x.pf)}</td><td class="r num">${green}/${days.length}</td><td class="r num ${cls(diff)}">${fmtD(diff)}</td></tr>`;
    }).join("");
    el.innerHTML = `<div class="table-wrap"><table class="mcmp"><thead><tr><th>Year</th><th class="r">Trades</th><th class="r">Net</th><th class="r">Win rate</th><th class="r">Avg R</th><th class="r">Profit factor</th><th class="r">Green days</th><th class="r">vs year before</th></tr></thead><tbody>${rows}</tbody></table></div>
      <p class="calc" style="margin-top:8px">Uses your other filters, so you can compare, say, ${name} NY AM trades year on year. Click a year to filter everything to that ${name}.</p>`;
  }
  document.addEventListener("click", (e) => {
    const c = e.target.closest("[data-mby],[data-mby-month],[data-mby-year]"); if (!c) return;
    const d = c.dataset;
    $("fPeriod").value = ""; $("fFrom").value = ""; $("fTo").value = "";
    if (d.mby) { const [y, m] = d.mby.split("-"); $("fMonth").value = m; $("fYear").value = y; }
    else if (d.mbyMonth) { $("fMonth").value = d.mbyMonth; $("fYear").value = ""; }
    else { $("fMonth").value = ""; $("fYear").value = d.mbyYear; }
    onFilter();
  });
  function prevWeekday(s) {''')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
