#!/usr/bin/env python3
"""v21 -> v22 (PC): watchlist earnings (looked up with Claude about once a week, shown on the session they move),
FOMC 2027 dates and minutes, ECB and BoE rate decisions, index rebalances, and a "next session" line on the dashboard."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

# ---- styles and markup ----
rep('.pill.info { color: var(--accent); }', '.pill.info { color: var(--accent); }\n.pill.earn { color: var(--accent-2); }')
rep('''        <div class="chips-row" id="todayChips"></div>''', '''        <div class="chips-row" id="todayChips"></div>
        <div class="sub" id="todayNext" style="margin-top:12px;font-size:.88rem"></div>''')
rep('''        <div class="tag-editor" id="listNews"></div>''', '''        <div class="tag-editor" id="listNews"></div>
        <div class="tag-editor" id="listEarnings"></div>''')
rep('''A coach answer costs a few cents, and a day's news log costs roughly 10 to 30 cents.</p>''',
    '''A coach answer costs a few cents, a day's news log costs roughly 10 to 30 cents, and the weekly earnings lookup costs a few cents.</p>''')
rep('''          <p class="calc" id="sFFInfo"></p>''', '''          <p class="calc" id="sFFInfo"></p>
          <label class="switch" for="sEarn"><input type="checkbox" id="sEarn"><span>Look up earnings dates for my watchlist about once a week</span></label>
          <div class="actions" style="justify-content:flex-start"><button type="button" class="btn-small" id="sEarnNow">Look up earnings now</button></div>
          <p class="calc" id="sEarnInfo"></p>''')

# ---- state and lists ----
rep('const S = { ff: new Map(), ffStatus: "",', 'const S = { ff: new Map(), ffStatus: "", earn: new Map(), earnFile: null, earnBusy: false, earnTried: "",')
rep('''    news: ["CPI", "PPI", "NFP", "FOMC", "Fed Chair", "PCE", "GDP", "Retail sales", "Jobless claims", "ISM / PMI", "JOLTS", "Consumer confidence", "Trump", "Geopolitics", "War", "ECB", "BoE"],
  };''', '''    news: ["CPI", "PPI", "NFP", "FOMC", "Fed Chair", "PCE", "GDP", "Retail sales", "Jobless claims", "ISM / PMI", "JOLTS", "Consumer confidence", "Trump", "Geopolitics", "War", "ECB", "BoE"],
    earnings: ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "AVGO", "NFLX", "UNH", "GS", "JPM", "HD", "CAT", "V"],
  };''')
rep('''news: S.settings.news || DEFAULT_LISTS.news });''', '''news: S.settings.news || DEFAULT_LISTS.news, earnings: S.settings.earnings || DEFAULT_LISTS.earnings });''')
rep('''    const key = f.dataset.listAdd, v = $("add-" + key).value.trim(); if (!v) return;''',
    '''    const key = f.dataset.listAdd, raw = $("add-" + key).value.trim(), v = key === "earnings" ? raw.toUpperCase() : raw; if (!v) return;''')

# ---- computed calendar: FOMC 2027 + minutes, ECB, BoE, rebalances ----
# 2027 FOMC dates are the Fed's tentative schedule (each is confirmed at the meeting before it).
rep('''"2026-10-28", "2026-12-09"]);''', '''"2026-10-28", "2026-12-09",
    "2027-01-27", "2027-03-17", "2027-04-28", "2027-06-09", "2027-07-28", "2027-09-15", "2027-10-27", "2027-12-08"]);
  // Rate decision days (the press conference day for the ECB; BoE dates are its provisional schedule).
  const ECB = new Set(["2026-02-05", "2026-03-19", "2026-04-30", "2026-06-11", "2026-07-23", "2026-09-10", "2026-10-29", "2026-12-17",
    "2027-02-04", "2027-03-18", "2027-04-29", "2027-06-10", "2027-07-22", "2027-09-09", "2027-10-28", "2027-12-16"]);
  const BOE = new Set(["2026-02-05", "2026-03-19", "2026-04-30", "2026-06-18", "2026-07-30", "2026-09-17", "2026-11-05", "2026-12-17",
    "2027-02-04", "2027-03-18", "2027-04-29", "2027-06-17", "2027-07-29", "2027-09-16", "2027-11-04", "2027-12-16"]);''')
rep('''      add(ymd(last), [2, 5, 8, 11].includes(m) ? "Quarter-end" : "Month-end", "flow");
    }''', '''      add(ymd(last), [2, 5, 8, 11].includes(m) ? "Quarter-end" : "Month-end", "flow");
      if ([2, 5, 8, 11].includes(m)) add(opex, "S&P 500 quarterly rebalance", "flow");
      if (m === 11) add(opex, "Nasdaq-100 annual reconstitution", "flow");
    }
    // Russell: fourth Friday of June, and from 2026 also the second Friday of December. Both at the close.
    add(nthWeekday(y, 5, 5, 4), "Russell reconstitution", "flow");
    if (y >= 2026) add(nthWeekday(y, 11, 5, 2), "Russell reconstitution", "flow");''')
rep('''    FOMC.forEach((d) => d.startsWith(String(y)) && add(d, "FOMC rate decision", "news"));''',
    '''    FOMC.forEach((d) => d.startsWith(String(y)) && add(d, "FOMC rate decision", "news"));
    FOMC.forEach((d) => { const mn = addDays(d, 21); if (mn.startsWith(String(y))) add(mn, "FOMC minutes", "news"); });
    ECB.forEach((d) => d.startsWith(String(y)) && add(d, "ECB rate decision", "news"));
    BOE.forEach((d) => d.startsWith(String(y)) && add(d, "BoE rate decision", "news"));''')

# ---- earnings labels: a report after the close (AMC) belongs to the next trading day, the session it moves ----
rep('''  function dayLabels(date) {
    const d = S.days.get(date) || {};
    return [...new Set([...marketEvents(date).map((e) => shortEvent(e.name)), ...autoNews(date), ...(d.news || [])])];
  }''', '''  const isTradingDay = (d) => { const w = dateObj(d).getDay(); return w > 0 && w < 6 && !marketEvents(d).some((e) => e.name.startsWith("US holiday")); };
  const nextTradingDay = (d) => { let x = addDays(d, 1); while (!isTradingDay(x)) x = addDays(x, 1); return x; };
  const earnLabels = (date) => (S.earn.get(date) || []).map((e) => `${e.ticker} earnings`);
  const earnDetail = (e) => `${e.ticker} earnings${e.timing === "AMC" ? ` (after the ${fmtDay(e.date, { weekday: "short" })} close)` : e.timing === "BMO" ? " (before the open)" : ""}${e.confirmed ? "" : ", expected"}`;
  function dayLabels(date) {
    const d = S.days.get(date) || {};
    return [...new Set([...marketEvents(date).map((e) => shortEvent(e.name)), ...autoNews(date), ...earnLabels(date), ...(d.news || [])])];
  }''')
rep('''.concat(news.map((n) => `<span class="pill bad">${esc(n)}</span>`));
    const auto = autoMarketHtml(date);''', '''.concat((S.earn.get(date) || []).map((e) => `<span class="pill earn">${esc(earnDetail(e))}</span>`), news.map((n) => `<span class="pill bad">${esc(n)}</span>`));
    const auto = autoMarketHtml(date);''')

# ---- dashboard: earnings chips and the next session's events ----
rep('''      ...events.filter((e) => !(S.ff.get(day) || []).some((f) => f.tag === e)).map((e) => `<span class="pill warn">⚑ ${esc(e)}</span>`),
    ].join("");
    tickClock();''', '''      ...(S.earn.get(day) || []).map((e) => `<span class="pill earn">⚑ ${esc(earnDetail(e))}</span>`),
      ...events.filter((e) => !(S.ff.get(day) || []).some((f) => f.tag === e) && !earnLabels(day).includes(e)).map((e) => `<span class="pill warn">⚑ ${esc(e)}</span>`),
    ].join("");
    const nx = nextTradingDay(day), nff = S.ff.get(nx) || [];
    const nItems = [...nff.map((e) => `${e.time ? e.time.replace(" ET", "") + " " : ""}${e.name}`), ...(S.earn.get(nx) || []).map(earnDetail),
      ...dayLabels(nx).filter((e) => !nff.some((f) => f.tag === e) && !earnLabels(nx).includes(e))];
    const ffGap = !S.settings.ffOff && S.ff.size && nx > [...S.ff.keys()].sort().pop();
    $("todayNext").textContent = `Next session, ${fmtDay(nx, { weekday: "long", month: "short", day: "numeric" })}: ${nItems.length ? nItems.join(" · ") : "nothing scheduled"}${ffGap ? ". Red-folder times show once ForexFactory posts that week." : ""}`;
    tickClock();''')

# ---- earnings lookup ----
rep('''shotUrls.clear(); S.ff = new Map();''', '''shotUrls.clear(); S.ff = new Map(); S.earn = new Map(); S.earnFile = null; S.earnTried = "";''')
rep('''  setInterval(() => { if (!document.hidden) autoLogNews(); }, 15 * 60e3);
  function afterOpen() { loadFF(); autoLogNews(); }''', r'''  setInterval(() => { if (!document.hidden) { autoLogNews(); autoEarnings(); } }, 15 * 60e3);

  // ---------- earnings: the watchlist's report dates, looked up with Claude about once a week ----------
  // news/earnings.json keeps every report found, so past days keep their label for Insights. Each lookup replaces
  // what it found inside its own window (today plus three weeks).
  const EARN_FILE = "earnings.json", EARN_DAYS = 21, EARN_EVERY = 5 * 864e5;
  function applyEarnings() {
    S.earn = new Map();
    (S.earnFile?.items || []).forEach((e) => {
      const day = e.timing === "AMC" ? nextTradingDay(e.date) : e.date;
      if (!S.earn.has(day)) S.earn.set(day, []);
      S.earn.get(day).push(e);
    });
  }
  async function loadEarnings() {
    if (!newsDir) return;
    let f = null;
    try { f = JSON.parse((await readText(newsDir, EARN_FILE)) || "null"); } catch {}
    S.earnFile = Array.isArray(f?.items) ? f : null;
    applyEarnings(); render();
  }
  const EARN_PROMPT = (from, to, tickers) => `Find the quarterly earnings report dates between ${from} and ${to} (inclusive) for these US companies: ${tickers.join(", ")}. Use web search: company investor relations pages, Nasdaq, Yahoo Finance, Zacks, Earnings Whispers.
For each company that reports in that window, give the report date (America/New_York), whether it reports before the US open (BMO) or after the close (AMC), and whether the company has confirmed the date. Leave out companies that don't report in the window. Never guess: leave timing empty if you can't find it, and leave a company out if you can't find a date.
Answer with only one JSON object, no other text: {"items":[{"ticker":"NVDA","date":"YYYY-MM-DD","timing":"AMC","confirmed":true}]}`;
  async function fetchEarnings(manual) {
    if (!apiKey()) { if (manual) toast("Add your Claude API key in Settings first."); return false; }
    const tickers = lists().earnings;
    if (S.earnBusy || !newsDir || !tickers.length) return false;
    S.earnBusy = true; renderDesktopSettings();
    const from = today(), to = addDays(from, EARN_DAYS);
    try {
      const tools = [{ type: "web_search_20260209", name: "web_search", max_uses: 8 }];
      let messages = [{ role: "user", content: EARN_PROMPT(from, to, tickers) }], msg = null;
      for (let i = 0; i < 4; i++) {
        msg = await callClaude({ max_tokens: 8000, output_config: { effort: "low" }, tools, messages });
        if (msg.stop_reason !== "pause_turn") break;
        messages = [...messages, { role: "assistant", content: msg.content }];
      }
      const text = (msg.content || []).filter((b) => b.type === "text").map((b) => b.text).join("");
      let raw;
      try { raw = JSON.parse(text.slice(text.indexOf("{"), text.lastIndexOf("}") + 1)); } catch { throw Object.assign(new Error("no json"), { code: "api_error" }); }
      const found = (Array.isArray(raw?.items) ? raw.items : [])
        .map((e) => ({ ticker: String(e?.ticker || "").trim().toUpperCase(), date: String(e?.date || ""), timing: ["BMO", "AMC"].includes(e?.timing) ? e.timing : "", confirmed: e?.confirmed === true }))
        .filter((e, i, a) => tickers.includes(e.ticker) && /^\d{4}-\d{2}-\d{2}$/.test(e.date) && e.date >= from && e.date <= to && a.findIndex((x) => x.ticker === e.ticker && x.date === e.date) === i);
      const kept = (S.earnFile?.items || []).filter((e) => e.date < from);
      S.earnFile = { fetchedAt: Date.now(), from, to, tickers: [...tickers], items: [...kept, ...found].sort((x, y) => x.date.localeCompare(y.date)) };
      await writeFile(newsDir, EARN_FILE, JSON.stringify(S.earnFile, null, 1));
      applyEarnings();
      if (manual) toast(found.length ? `Found ${plural(found.length, "earnings report")} in the next 3 weeks` : "No watchlist earnings in the next 3 weeks");
      return true;
    } catch (e) { if (manual) toast(e?.message === "no json" ? "Claude's answer couldn't be read. Try again." : claudeErrorText(e?.code)); return false; }
    finally { S.earnBusy = false; render(); renderDesktopSettings(); }
  }
  // Looks up again when the last lookup is 5 days old or the watchlist changed. A failed try waits for the next visit.
  async function autoEarnings() {
    if (S.settings.earnOff || !apiKey() || S.earnBusy || !newsDir) return;
    const t = lists().earnings.join(",");
    const stale = !S.earnFile || Date.now() - (S.earnFile.fetchedAt || 0) > EARN_EVERY || (S.earnFile.tickers || []).join(",") !== t;
    if (!stale || S.earnTried === t) return;
    S.earnTried = t; await fetchEarnings(false);
  }
  function afterOpen() { loadFF(); loadEarnings().then(autoEarnings); autoLogNews(); }''')

# ---- settings ----
rep('''    renderListEditor("listNews", "news", "News types", "Add a news type");''', '''    renderListEditor("listNews", "news", "News types", "Add a news type");
    renderListEditor("listEarnings", "earnings", "Earnings watchlist", "Add a ticker, e.g. AMD");''')
rep('''    $("sFF").checked = !S.settings.ffOff;''', '''    $("sFF").checked = !S.settings.ffOff;
    $("sEarn").checked = !S.settings.earnOff; $("sEarn").disabled = !k; $("sEarnNow").disabled = !k || S.earnBusy;
    const upcoming = (S.earnFile?.items || []).filter((e) => e.date >= today()).length;
    $("sEarnInfo").textContent = !k ? "Needs your Claude API key." : S.earnBusy ? "Claude is looking up earnings dates…"
      : S.earnFile ? `Last looked up ${fmtDay(ymd(new Date(S.earnFile.fetchedAt)))}: ${plural(upcoming, "upcoming report")}. A report after the close shows on the next session. Edit the tickers under Your lists.` : "Not looked up yet.";''')
rep('''  $("sFF").addEventListener("change",''', '''  $("sEarn").addEventListener("change", () => saveSettings({ earnOff: !$("sEarn").checked }).then(() => { renderDesktopSettings(); autoEarnings(); }));
  $("sEarnNow").addEventListener("click", () => fetchEarnings(true));
  $("sFF").addEventListener("change",''')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
