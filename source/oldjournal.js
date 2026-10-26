  // ---------- import: old journal (OneNote pages, Notion CSV) ----------
  // OneNote: the text of the notebook printed to PDF. Each page holds one day: the table row (market ticks are lost,
  // the P/L, RR and RRx cells come out as loose numbers), then Thoughts, Good things I did, Bad things I did, and the date.
  const ON_WEEKDAY = /(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})/;
  const MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"];
  const ON_MARKETS = ["ES", "NQ", "Dow", "Gold", "Silver"];
  const ON_SECTIONS = { "thoughts": "thoughts", "good things i did": "good", "bad things i did": "bad" };
  const BULLET = "•●▪◦·‣⁃\\-–";
  const isBullet = (l) => new RegExp(`^[${BULLET}]$`).test(l);
  const bulletText = (l) => { const m = l.match(new RegExp(`^[${BULLET}]\\s+(.*)$`)); return m ? m[1] : null; };
  const SHORT_DATE = /^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})(?!\d)(.*)$/;
  const validYmd = (y, mo, d) => { const dt = new Date(+y, +mo - 1, +d, 12); return dt.getFullYear() === +y && dt.getMonth() === +mo - 1 && dt.getDate() === +d ? `${y}-${pad(mo)}-${pad(d)}` : null; };
  const shortYmd = (m) => (m ? validYmd(m[3].length === 2 ? "20" + m[3] : m[3], m[1], m[2]) : null);
  // A line that is only the long date, maybe after the typed short date: not a date mentioned in the notes.
  const onDateLine = (l) => { const w = l.match(ON_WEEKDAY); if (!w || l.slice(w.index + w[0].length).trim()) return null; const pre = l.slice(0, w.index).trim(); return !pre || SHORT_DATE.test(pre) ? w : null; };
  function onDateOf(lines) {
    // The page date: the long "Tuesday, July 15, 2025" line OneNote prints, with the date typed on the page
    // (7/15/2025 and any title) just above it. Read from the bottom, since that's where the PDF text puts it.
    for (let i = lines.length - 1; i >= 0; i--) {
      const w = onDateLine(lines[i]); if (!w) continue;
      const date = validYmd(w[4], MONTHS.indexOf(w[2].toLowerCase()) + 1, w[3]); if (!date) continue;
      const same = lines[i].slice(0, w.index).trim(), prev = i > 0 ? lines[i - 1].trim() : "";
      const short = same.match(SHORT_DATE) || (!same && prev.match(SHORT_DATE));
      const skip = new Set([i]); if (!same && short) skip.add(i - 1);
      const typed = shortYmd(short);
      return { date, title: short ? short[4].trim() : "", typed: typed && typed !== date ? typed : "", skip };
    }
    for (let i = lines.length - 1; i >= 0; i--) {
      const m = lines[i].trim().match(SHORT_DATE), date = shortYmd(m);
      if (date) return { date, title: m[4].trim(), typed: "", skip: new Set([i]) };
    }
    return null;
  }
  // Splits the text into pages. The PDF footer ("Trading Journal1 Page 12") ends each page: a line ending in
  // "Page <n>" whose start repeats on at least three lines, so a note that happens to end "on Page 2" isn't one.
  function onPages(text) {
    const lines = String(text).replace(/^﻿/, "").replace(/\r\n?/g, "\n").split("\n");
    const FOOT = /^\s*(\S.{0,60}?)\s+Page\s+(\d{1,4})\s*$/, seen = new Map();
    lines.forEach((l) => { const m = l.match(FOOT); if (m) seen.set(m[1], [...(seen.get(m[1]) || []), +m[2]]); });
    // A footer repeats on every PDF page and counts up from 1; a note that ends "on Page 2" does neither.
    const feet = new Set([...seen].filter(([, n]) => n.length >= 3 || n.every((x, i) => x === i + 1)).map(([k]) => k));
    if (feet.size) {
      const pages = []; let cur = [];
      lines.forEach((l) => { const m = l.match(FOOT); if (m && feet.has(m[1])) { pages.push(cur); cur = []; } else cur.push(l); });
      pages.push(cur);
      return pages;
    }
    // No footers (pasted text): a page ends at each long date line.
    const out = []; let cur = [];
    lines.forEach((l) => { cur.push(l); if (onDateLine(l)) { out.push(cur); cur = []; } });
    if (cur.some((l) => l.trim())) out.push(cur);
    return out;
  }
  const NUM_TOKEN = /^[-−–+]?\$?\d[\d.,]*$/;
  function onParsePage(raw, startSec) {
    const lines = raw.map((l) => l.replace(/\s+$/, ""));
    const head = lines.findIndex((l) => /^\s*Market\s+Win\s+Lose\b/i.test(l));
    const dt = onDateOf(lines);
    const page = { date: dt?.date || "", title: dt?.title || "", typed: dt?.typed || "", nums: [], thoughts: [], good: [], bad: [], hasHead: head >= 0 };
    const skip = new Set(dt ? dt.skip : []);
    let i = head >= 0 ? head + 1 : 0;
    if (head >= 0) {
      skip.add(head);
      // Market names (ES, NQ, Dow, Gold, Silver), then the row of numbers, then the importance labels 1 2 3.
      while (i < lines.length && ON_MARKETS.some((m) => m.toLowerCase() === lines[i].trim().toLowerCase())) skip.add(i++);
      const tok = (lines[i] || "").trim().split(/\s+/).filter(Boolean);
      if (tok.length && tok.every((t) => NUM_TOKEN.test(t) && num(t) != null)) {
        let vals = tok.map((t) => num(t));
        if (vals[vals.length - 1] === 1 && (lines[i + 1] || "").trim() === "2") vals = vals.slice(0, -1);
        page.nums = vals; skip.add(i++);
      }
      if ((lines[i] || "").trim() === "2") skip.add(i++);
      if ((lines[i] || "").trim() === "3") skip.add(i++);
    }
    // Text before the first heading belongs to Thoughts, except a bare date typed on the page.
    let sec = startSec || "thoughts", buf = [];
    const flush = () => { const t = buf.map((s) => s.trim()).filter(Boolean).join(" ").replace(/\s{2,}/g, " ").trim(); if (t) page[sec].push(t); buf = []; };
    for (let k = head >= 0 ? head : 0; k < lines.length; k++) {
      if (skip.has(k)) continue;
      const l = lines[k].trim();
      if (!l) continue;
      const s = ON_SECTIONS[l.toLowerCase()];
      if (s) { flush(); sec = s; continue; }
      if (/^\d{1,2}\/\d{1,2}\/\d{2,4}$/.test(l)) continue;
      if (isBullet(l)) { flush(); continue; }
      const b = bulletText(l);
      if (b != null) { flush(); buf.push(b); flush(); continue; }
      buf.push(l);
    }
    flush();
    page.lastSec = sec;
    return page;
  }
  // The loose numbers become P/L, RR, RRx. A first number that's a whole number under 10 could be dollars or RR, so it's flagged.
  function onNumbers(nums, firstIs) {
    const out = { pnl: null, rr: null, rrx: null, unsure: false };
    if (!nums.length) return out;
    const a = nums[0];
    out.unsure = Number.isInteger(a) && a > 0 && a < 10;
    const asRR = firstIs ? firstIs === "rr" : out.unsure && nums.length === 1;
    if (asRR) { out.rr = a; out.rrx = nums[1] ?? null; }
    else { out.pnl = a; out.rr = nums[1] ?? null; out.rrx = nums[2] ?? null; }
    return out;
  }
  // Which market a day's trade was on, read from the thoughts. Ticks in the Market column don't survive the PDF.
  const MKT_RE = { ES: /\bES\b/g, NQ: /\bNQ\b/g, Dow: /\b(?:Dow|YM|US30)\b/gi, Gold: /\b(?:gold|XAU(?:USD)?)\b/gi, Silver: /\b(?:silver|XAG(?:USD)?)\b/gi };
  function onGuessMarket(text) {
    const t = String(text);
    const took = t.match(/\b(?:took|entered|entry|traded|trade|went|got in|shorted|longed|position)\b[^.,]{0,40}?\bon\s+(ES|NQ|Dow|YM|US30|gold|silver)\b/i);
    if (took) { const k = took[1].toLowerCase(); return k === "es" ? "ES" : k === "nq" ? "NQ" : k === "gold" ? "Gold" : k === "silver" ? "Silver" : "Dow"; }
    const counts = ON_MARKETS.map((m) => [m, (t.match(MKT_RE[m]) || []).length]).sort((x, y) => y[1] - x[1]);
    return counts[0][1] ? counts[0][0] : "";
  }
  const NO_TRADE_RE = /\bno trades?\b|\bdidn'?t (?:take|trade|enter|participate)\b|\bdid not (?:take|trade)\b|\bsat out\b|\bstayed out\b|\bcalled it a day\b|\bdecided not to trade\b/i;
  const NEWS_WORDS = [["FOMC", /\bfomc\b|\bpowell|\bpowel/i], ["CPI", /\bcpi\b/i], ["PPI", /\bppi\b/i], ["NFP", /\bnfp\b/i], ["Trump", /\btrump\b/i], ["Fed Chair", /\bfed chair\b|\bjackson hole\b/i], ["Geopolitics", /\bUN speech\b/i]];
  // The symbol each OneNote market becomes, preferring the one already used in this journal.
  function onSymbol(m) {
    const used = new Set([...S.trades.values()].map((t) => String(t.instrument || "").toUpperCase()));
    const opts = { ES: ["US500", "SPX500", "SP500", "US500CASH"], NQ: ["NAS100", "US100", "USTEC", "NAS100CASH"], Dow: ["US30", "DJ30", "WS30", "US30CASH"], Gold: ["XAUUSD", "GOLD"], Silver: ["XAGUSD", "SILVER"] }[m];
    return opts ? opts.find((o) => used.has(o)) || opts[m === "ES" ? 1 : 0] : m;
  }
  function onParse(text) {
    const byDate = new Map();
    let last = null, undated = 0;
    onPages(text).forEach((raw) => {
      if (!raw.some((l) => l.trim())) return;
      const head = raw.some((l) => /^\s*Market\s+Win\s+Lose\b/i.test(l)), dated = !!onDateOf(raw);
      // A page with no date and no table is the overflow of the page before it, and carries on in the same section.
      const p = onParsePage(raw, !head && !dated && last ? last.lastSec : "");
      if (!p.date) {
        if (!p.hasHead && last && (p.thoughts.length || p.good.length || p.bad.length)) { last.thoughts.push(...p.thoughts); last.good.push(...p.good); last.bad.push(...p.bad); last.lastSec = p.lastSec; }
        else if (p.thoughts.length || p.good.length || p.bad.length || p.nums.length) undated++;
        return;
      }
      const prev = byDate.get(p.date);
      if (prev) { // the same date on two pages: keep both pages' notes and numbers
        prev.thoughts.push(...p.thoughts); prev.good.push(...p.good); prev.bad.push(...p.bad);
        if (p.title && !prev.title.includes(p.title)) prev.title = [prev.title, p.title].filter(Boolean).join(" · ");
        if (p.nums.length) { if (prev.nums.length) prev.extra.push(p.nums); else prev.nums = p.nums; }
        prev.typed = prev.typed || p.typed; prev.lastSec = p.lastSec;
        last = prev; return;
      }
      p.extra = []; byDate.set(p.date, p); last = p;
    });
    return { days: [...byDate.values()].sort((a, b) => a.date.localeCompare(b.date)), undated };
  }
  const dayHasWords = (d) => !!(d && (String(d.thoughts ?? d.review ?? "").trim() || (d.good || []).some(Boolean) || (d.bad || []).some(Boolean)));
  // Anything you entered yourself makes the day yours: the import then only fills what's empty.
  const dayTouched = (d) => !!(d && (dayHasWords(d) || String(d.plan || "").trim() || d.result || d.noTrade || (d.markets || []).length || d.mood || d.bias || d.kind || d.importance
    || String(d.lesson || "").trim() || d.grade || (d.news || []).length || String(d.newsNotes || "").trim() || (d.screenshots || []).length || d.gate || (d.feelBefore || []).length || (d.feelAfter || []).length));
  // done: brought in before. notion: a Notion note sits on the day, and the page joins it. merge: you started the day
  // but wrote nothing, so the page's words go in and your choices stay. yours: you wrote the day, so only its trade can come in.
  function onDayStatus(date) {
    const d = S.days.get(date);
    if (!d) return "new";
    if (d.importedFrom === "onenote" || d.onenoteMerged) return "done";
    if (d.importedFrom === "notion") return "notion";
    if (dayHasWords(d)) return "yours";
    return dayTouched(d) ? "merge" : "new";
  }
  const onTradesLogged = (date) => [...S.trades.values()].some((t) => t.date === date && t.source !== "onenote");
  const onTradeDone = (date) => [...S.trades.values()].some((t) => t.extId === `onenote:${date}:0`);
  function onRefreshRow(row) {
    row.status = onDayStatus(row.date); row.tradeDone = onTradeDone(row.date); row.hasTrades = onTradesLogged(row.date);
  }
  // Turns parsed pages into rows for the review table. Row choices (include, P/L or RR, result, market) live on the row.
  function onRows(parsed) {
    return parsed.days.map((p) => {
      const words = [p.title, ...p.thoughts, ...p.good, ...p.bad].join(" ");
      const thoughts = [p.title ? `Page title: ${p.title}` : "", p.thoughts.join("\n\n")].filter(Boolean).join("\n\n");
      const row = { date: p.date, pageDate: p.date, typed: p.typed, title: p.title, thoughts, good: p.good, bad: p.bad, nums: p.nums, extra: p.extra, firstIs: "", market: onGuessMarket(words), resultSet: false,
        empty: !p.thoughts.length && !p.good.length && !p.bad.length && !p.nums.length && !p.extra.length, autoNoTrade: NO_TRADE_RE.test(words) };
      row.news = NEWS_WORDS.filter(([, re]) => re.test(p.title)).map(([n]) => n);
      row.importance = /\b(?:v\.?\s?imp|very imp|important|imp|check me|mark the day)\b/i.test(p.title) ? "3" : "";
      onRefreshRow(row);
      onRowNumbers(row);
      row.addTrade = !row.hasTrades;
      row.include = canInclude(row);
      return row;
    });
  }
  const hasPnl = (r) => r.pnl != null || r.extraPnls.length > 0;
  const newTrade = (r) => hasPnl(r) && !r.tradeDone && r.addTrade;
  // A day already in the journal can still add its trade; otherwise there's nothing new to bring in.
  const canInclude = (r) => !r.empty && (["new", "merge", "notion"].includes(r.status) || newTrade(r));
  function onRowNumbers(row) {
    const n = onNumbers(row.nums, row.firstIs);
    row.pnl = n.pnl; row.rr = n.rr; row.rrx = n.rrx; row.unsure = n.unsure;
    row.extraPnls = row.extra.map((x) => onNumbers(x, "")).filter((x) => x.pnl != null);
    if (!row.resultSet) { const t = row.pnl != null ? row.pnl + row.extraPnls.reduce((a, e) => a + e.pnl, 0) : row.extraPnls.length ? row.extraPnls.reduce((a, e) => a + e.pnl, 0) : null; row.result = t == null ? (row.autoNoTrade ? "No trade" : "") : t > 0 ? "Win" : t < 0 ? "Loss" : "BE"; }
  }
  const oneRec = { rows: [], undated: 0, filter: "all" };
  const PAST_ACCOUNT = "Past trades (old journal)";
  function importAccountOptions(sel) {
    const accs = accountsSorted(), past = accs.find((a) => a.importTarget);
    sel.innerHTML = (past ? "" : `<option value="__new">New account: ${esc(PAST_ACCOUNT)}</option>`) + accs.map((a) => `<option value="${esc(a.id)}">${esc(a.name || "Account")}</option>`).join("");
    sel.value = past ? past.id : "__new";
  }
  // The past trades go in their own closed account by default, so old results don't count against a live challenge.
  async function importAccountId(sel) {
    const pick = sel?.value || "__new";
    if (pick !== "__new" && S.accounts.has(pick)) return pick;
    const past = [...S.accounts.values()].find((a) => a.importTarget); if (past) return past.id;
    const acc = { ...ACCOUNT_DEFAULTS, id: "past-trades", name: PAST_ACCOUNT, firm: "", preset: "custom", status: "closed", startBalance: 100000, startDate: "", targetPct: 0, dailyLossPct: 0, maxLossPct: 0, riskPct: 0, maxTrades: 0, maxLosses: "", importTarget: true, payouts: [] };
    S.accounts.set(acc.id, acc); // so a retry right after a failed save finds it
    await backend.put("accounts", acc);
    return acc.id;
  }
  async function putAll(coll, list) { if (list.length) await backend.putMany(coll, list); }
  const onPnls = (r) => (newTrade(r) ? [...(r.pnl != null ? [{ pnl: r.pnl, rr: r.rr, rrx: r.rrx }] : []), ...r.extraPnls] : []);
  function oneSummary(shown) {
    const take = oneRec.rows.filter((r) => r.include && canInclude(r));
    const trades = take.reduce((a, r) => a + onPnls(r).length, 0);
    const days = take.filter((r) => ["new", "merge", "notion"].includes(r.status)).length;
    const net = take.reduce((a, r) => a + onPnls(r).reduce((x, e) => x + e.pnl, 0), 0);
    return { days, trades, net, check: oneRec.rows.filter((r) => r.include && canInclude(r) && r.unsure && !r.firstIs).length };
  }
  const ON_STATUS = { new: "", merge: '<span class="pill info">Adds to your day</span>', notion: '<span class="pill info">Joins a Notion note</span>', done: '<span class="pill ok">Already brought in</span>', yours: '<span class="pill info">You wrote this day</span>' };
  const plainAmt = (a) => `${a < 0 ? "−" : ""}$${Math.abs(a)}`;
  function oneShown() { return oneRec.rows.map((r, i) => [r, i]).filter(([r]) => oneRec.filter === "all" || (oneRec.filter === "check" ? r.unsure && !r.firstIs && r.include && canInclude(r) : oneRec.filter === "date" ? !!r.typed : hasPnl(r))); }
  function renderOneNote() {
    const rows = oneRec.rows, el = $("oneReview"), keep = $("oneAcct")?.value;
    if (!rows.length) { el.innerHTML = ""; return; }
    const s = oneSummary(), count = (st) => rows.filter((r) => r.status === st).length, done = count("done"), yours = count("yours"), empty = rows.filter((r) => r.empty).length;
    const dates = rows.filter((r) => r.typed).length, logged = rows.filter((r) => r.hasTrades && hasPnl(r) && !r.tradeDone).length;
    const shown = oneShown(), selectable = shown.filter(([r]) => canInclude(r));
    const mOpts = (cur) => `<option value="">Not sure (NQ)</option>` + ON_MARKETS.map((m) => `<option ${m === cur ? "selected" : ""}>${m}</option>`).join("");
    const rOpts = (cur) => ["", ...DAY_RESULTS].map((v) => `<option value="${esc(v)}" ${v === cur ? "selected" : ""}>${v || "Not set"}</option>`).join("");
    const firstOpts = (r) => (r.unsure && !r.firstIs ? `<option value="" selected>Check: ${esc(plainAmt(r.nums[0]))} or ${esc(r.nums[0])} RR?</option>` : "") + [["pnl", `${plainAmt(r.nums[0])} P/L`], ["rr", `${r.nums[0]} RR`]].map(([k, l]) => `<option value="${k}" ${r.firstIs === k || (!r.firstIs && !r.unsure && (r.pnl == null ? "rr" : "pnl") === k) ? "selected" : ""}>${esc(l)}</option>`).join("");
    el.innerHTML = `<div class="stack">
      <p>Found <strong>${plural(rows.length, "day")}</strong> from ${esc(fmtDay(rows[0].date, { month: "short", day: "numeric", year: "numeric" }))} to ${esc(fmtDay(rows[rows.length - 1].date, { month: "short", day: "numeric", year: "numeric" }))}.
        ${done ? ` ${done} already brought in.` : ""}${yours ? ` ${yours} ${yours === 1 ? "is a day" : "are days"} you already wrote in Edge Ledger, so your words stay.` : ""}${empty ? ` ${empty} empty ${empty === 1 ? "page is" : "pages are"} left out.` : ""}${oneRec.undated ? ` ${oneRec.undated} ${oneRec.undated === 1 ? "page has" : "pages have"} no date and ${oneRec.undated === 1 ? "is" : "are"} left out.` : ""}${logged ? ` ${plural(logged, "day")} already ${logged === 1 ? "has" : "have"} trades logged, so ${logged === 1 ? "its" : "their"} P/L isn't added unless you tick it.` : ""}</p>
      ${s.check ? `<p class="alert" style="margin:0"><span class="msg"><strong>${plural(s.check, "day")} to check.</strong> The PDF loses which box was ticked, so a small whole number like 4 could be $4 or 4 RR. Pick which it is in the First number column. Until you do, a lone number counts as RR.</span></p>` : ""}
      ${dates ? `<p class="calc" style="margin:0">On ${plural(dates, "page")} the date you typed differs from OneNote's page date. Those use OneNote's date; pick the other one in the Day column if it's wrong.</p>` : ""}
      <div class="filters"><div class="seg" role="group" aria-label="Which days to show">${[["all", "All days"], ["trades", "Days with P/L"], ["check", `To check (${s.check})`], ...(dates ? [["date", `Dates (${dates})`]] : [])].map(([k, l]) => `<button type="button" data-one-filter="${k}" aria-pressed="${oneRec.filter === k}">${l}</button>`).join("")}</div></div>
      <div class="table-wrap" style="max-height:62vh;overflow:auto"><table><thead><tr><th><input type="checkbox" id="oneAll" aria-label="Tick every day shown" ${selectable.length && selectable.every(([r]) => r.include) ? "checked" : ""} ${selectable.length ? "" : "disabled"}></th><th>Day</th><th>First number</th><th class="r">P/L</th><th class="r">RR</th><th>Result</th><th>Market</th><th>What it says</th></tr></thead><tbody>
      ${shown.map(([r, i]) => {
        const p = hasPnl(r) ? [...(r.pnl != null ? [r.pnl] : []), ...r.extraPnls.map((e) => e.pnl)] : [];
        const pnl = p.length ? p.reduce((a, b) => a + b, 0) : null;
        const on = r.include && canInclude(r);
        return `<tr data-one="${i}"${on ? "" : ' style="opacity:.55"'}>
          <td><input type="checkbox" data-one-inc aria-label="Bring in ${esc(r.date)}" ${on ? "checked" : ""} ${canInclude(r) ? "" : "disabled"}></td>
          <td class="num">${r.typed ? `<select data-one-date aria-label="Date of this page" style="width:auto">${[r.pageDate, r.typed].map((d) => `<option value="${d}" ${d === r.date ? "selected" : ""}>${esc(fmtDay(d, { weekday: "short", month: "short", day: "numeric", year: "2-digit" }))}${d === r.pageDate ? " (OneNote)" : " (typed)"}</option>`).join("")}</select>` : esc(fmtDay(r.date, { weekday: "short", month: "short", day: "numeric", year: "2-digit" }))}<br>${ON_STATUS[r.status]}${r.tradeDone ? ' <span class="pill ok">Trade in</span>' : ""}</td>
          <td>${r.nums.length ? `<select data-one-first aria-label="What the first number on ${esc(r.date)} is" style="width:auto">${firstOpts(r)}</select>` : '<span class="muted">–</span>'}</td>
          <td class="r num ${cls(pnl)}">${pnl == null ? "–" : money(pnl)}${p.length > 1 ? `<br><span class="calc">${p.length} pages</span>` : ""}${pnl != null && r.hasTrades && !r.tradeDone ? `<br><label class="calc" style="white-space:nowrap"><input type="checkbox" data-one-add ${r.addTrade ? "checked" : ""}> Add it (trades already logged)</label>` : ""}</td>
          <td class="r num">${r.rr == null ? "–" : esc(r.rr)}${r.rrx != null ? ` <span class="muted">/ ${esc(r.rrx)}</span>` : ""}</td>
          <td><select data-one-result aria-label="Result on ${esc(r.date)}" style="width:auto">${rOpts(r.result)}</select></td>
          <td>${pnl != null ? `<select data-one-market aria-label="Market on ${esc(r.date)}" style="width:auto">${mOpts(r.market)}</select>` : '<span class="muted">–</span>'}</td>
          <td style="white-space:normal;min-width:260px;max-width:460px"><span class="clamp muted" style="font-size:.85rem">${esc(r.thoughts || r.good[0] || r.bad[0] || "Empty page")}</span>${r.good.length || r.bad.length ? `<span class="calc">${plural(r.good.length, "good point")} · ${plural(r.bad.length, "bad point")}</span>` : ""}</td></tr>`;
      }).join("") || `<tr><td colspan="8" class="muted">No days here.</td></tr>`}
      </tbody></table></div>
      <div class="field" style="max-width:420px"><label for="oneAcct">Put the trades in</label><select id="oneAcct"></select><span class="calc">A separate closed account keeps old results out of your live challenge numbers. Pick it in the account menu at the top to see their stats.</span></div>
      <div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="oneGo" ${s.days || s.trades ? "" : "disabled"}>Bring in ${plural(s.days, "day")} and ${plural(s.trades, "trade")}</button><span class="calc">Net ${money(s.net)}. Running this again later skips anything already brought in.</span></div>
    </div>`;
    importAccountOptions($("oneAcct")); if (keep && [...$("oneAcct").options].some((o) => o.value === keep)) $("oneAcct").value = keep;
  }
  $("oneReview").addEventListener("change", (e) => {
    const tr = e.target.closest("tr[data-one]");
    if (e.target.id === "oneAll") { oneShown().forEach(([r]) => { if (canInclude(r)) r.include = e.target.checked; }); renderOneNote(); return; }
    if (!tr) return;
    const r = oneRec.rows[+tr.dataset.one];
    if (e.target.matches("[data-one-inc]")) r.include = e.target.checked;
    else if (e.target.matches("[data-one-first]")) { r.firstIs = e.target.value; onRowNumbers(r); }
    else if (e.target.matches("[data-one-result]")) { r.result = e.target.value; r.resultSet = true; }
    else if (e.target.matches("[data-one-market]")) r.market = e.target.value;
    else if (e.target.matches("[data-one-add]")) { r.addTrade = e.target.checked; if (r.addTrade) r.include = true; }
    else if (e.target.matches("[data-one-date]")) { r.date = e.target.value; onRefreshRow(r); r.addTrade = !r.hasTrades; r.include = canInclude(r); }
    else return;
    renderOneNote();
  });
  $("oneReview").addEventListener("click", (e) => {
    const f = e.target.closest("[data-one-filter]"); if (f) { oneRec.filter = f.dataset.oneFilter; renderOneNote(); return; }
    if (e.target.closest("#oneGo")) oneImport();
  });
  async function readOneNote() {
    let text = $("onePaste").value;
    const f = $("oneFile").files[0];
    if (!text.trim() && f) {
      if (/\.pdf$/i.test(f.name) || f.type === "application/pdf") { toast("Pick the .txt file with your notebook's text, not the PDF itself."); return; }
      text = await f.text();
    }
    if (!text.trim()) { toast("Choose your notebook's text file or paste its text first."); return; }
    const parsed = onParse(text);
    if (!parsed.days.length) { oneRec.rows = []; renderOneNote(); toast("Couldn't find any dated pages in that text."); return; }
    oneRec.rows = onRows(parsed); oneRec.undated = parsed.undated; oneRec.filter = "all";
    renderOneNote();
  }
  $("oneRead").addEventListener("click", readOneNote);
  $("oneFile").addEventListener("change", () => { $("onePaste").value = ""; readOneNote(); });
  async function oneImport() {
    const btn = $("oneGo"); btn.disabled = true; btn.textContent = "Bringing them in…";
    try {
      // Check again against what's saved now: a retry after a failed save must not add anything twice.
      oneRec.rows.forEach(onRefreshRow);
      const take = oneRec.rows.filter((r) => r.include && canInclude(r));
      const accountId = take.some((r) => onPnls(r).length) ? await importAccountId($("oneAcct")) : "";
      const days = new Map(), trades = [], now = Date.now(), perDate = new Map();
      take.forEach((r) => {
        const pnls = onPnls(r);
        pnls.forEach((n) => {
          const k = perDate.get(r.date) || 0; perDate.set(r.date, k + 1);
          trades.push({ id: `onenote-${r.date}-${k}`, extId: `onenote:${r.date}:${k}`, accountId, source: "onenote", createdAt: now, date: r.date, time: "", instrument: onSymbol(r.market || "NQ"), dir: "",
            session: "", setup: "", size: "", entry: "", exit: "", stop: "", target: "", risk: "", pnl: n.pnl.toFixed(2), followedPlan: null, mistakes: [], tags: [], screenshots: [],
            notes: [`From your OneNote journal${pnls.length > 1 ? `, page ${k + 1} of this day` : ""}. The P/L is the day's number from the table.`, n.rr != null ? `RR ${n.rr}${n.rrx != null ? `, RRx ${n.rrx}` : ""}.` : "", r.market ? "" : "Market not found in the notes, so it's set to NQ."].filter(Boolean).join(" ") });
        });
        if (!["new", "merge", "notion"].includes(r.status)) return;
        const prev = days.get(r.date) || S.days.get(r.date) || {}, again = days.has(r.date);
        const joinText = (a, b) => [String(a || "").trim(), b].filter(Boolean).join("\n\n");
        const thoughts = again || r.status === "notion" ? joinText(prev.thoughts, r.thoughts) : r.thoughts;
        const traded = pnls.length || r.tradeDone;
        days.set(r.date, { ...prev, id: r.date, date: r.date, thoughts, good: [...(again || r.status === "notion" ? prev.good || [] : []), ...r.good], bad: [...(again || r.status === "notion" ? prev.bad || [] : []), ...r.bad],
          markets: (prev.markets || []).length ? prev.markets : traded && r.market ? [r.market] : [],
          result: prev.result || r.result, noTrade: prev.result ? !!prev.noTrade : r.result === "No trade", restReason: prev.restReason || "",
          importance: prev.importance || r.importance, news: [...new Set([...(prev.news || []), ...r.news])],
          ...(r.status === "notion" ? { onenoteMerged: true } : { importedFrom: "onenote" }), updatedAt: now });
      });
      await putAll("trades", trades); await putAll("days", [...days.values()]);
      const accName = S.accounts.get(accountId)?.name || PAST_ACCOUNT;
      toast(`Brought in ${plural(days.size, "day")} and ${plural(trades.length, "trade")}.${trades.length && accountId !== activeAccount().id ? ` Pick "${accName}" in the account menu to see the trades.` : ""}`);
      oneRec.rows = []; $("onePaste").value = ""; $("oneFile").value = ""; renderOneNote();
      showTab("journal");
    } catch (e) {
      toast(e?.code === "quota_exceeded" ? "Storage is full. Not everything was saved." : "Couldn't save everything. Click Bring in again; anything already saved is skipped.");
      oneRec.rows.forEach(onRefreshRow); renderOneNote();
    }
  }

  // Notion: a database exported as CSV (Markdown & CSV export). Columns are matched like the platform import.
  function parseCsv(text) {
    const s = String(text).replace(/^﻿/, ""), rows = []; let row = [], cur = "", q = false;
    const first = s.split(/\r?\n/, 1)[0], delim = [",", ";", "\t"].map((d) => [d, first.split(d).length]).sort((a, b) => b[1] - a[1])[0][0];
    for (let i = 0; i < s.length; i++) {
      const c = s[i];
      if (q) { if (c === '"' && s[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; continue; }
      if (c === '"' && !cur.trim()) { q = true; cur = ""; }
      else if (c === delim) { row.push(cur.trim()); cur = ""; }
      else if (c === "\n" || c === "\r") { if (c === "\r" && s[i + 1] === "\n") i++; row.push(cur.trim()); cur = ""; if (row.some((x) => x)) rows.push(row); row = []; }
      else cur += c;
    }
    row.push(cur.trim()); if (row.some((x) => x)) rows.push(row);
    return rows;
  }
  const NOTION_FIELDS = [
    ["date", "Date", true, ["date", "day", "tradedate", "entrydate", "dateopened", "opened", "created", "createdtime", "time"]],
    ["pnl", "P/L ($)", false, ["pnl", "pl", "netpl", "netpnl", "profit", "profitloss", "net", "netprofit", "realizedpnl", "realizedpl"]],
    ["result", "Win / loss", false, ["result", "outcome", "winloss", "wl"]],
    ["win", "Win box (W)", false, ["w", "win", "won", "winner"]],
    ["loss", "Loss box (L)", false, ["l", "loss", "lost", "loser"]],
    ["mock", "Mock / backtest / BE box", false, ["mockbacktestbetrades", "mockbacktestbe", "mockbtbe", "mock", "backtest", "papertrade"]],
    ["instrument", "Market / symbol", false, ["market", "instrument", "symbol", "pair", "asset", "ticker", "index"]],
    ["dir", "Long / short", false, ["direction", "side", "position", "longshort", "bias", "type"]],
    ["rr", "RR", false, ["rr", "riskreward", "rmultiple", "r", "rratio"]],
    ["rrx", "RRx", false, ["rrx", "rrgot", "rrexit", "realizedrr", "rrachieved"]],
    ["risk", "Risk level", false, ["risklevel", "risk", "riskpercent"]],
    ["importance", "Importance", false, ["importance", "priority"]],
    ["setup", "Setup", false, ["setup", "strategy", "model", "playbook", "entrymodel"]],
    ["session", "Session", false, ["session", "killzone", "kz"]],
    ["feelings", "Feelings", false, ["emotions", "emotion", "feelings", "feeling", "mood", "psychology", "mindset"]],
    ["mistakes", "Mistakes", false, ["mistakes", "mistake", "errors", "error"]],
    ["tags", "Tags", false, ["tags", "tag", "confluences", "confluence"]],
    ["title", "Title", false, ["name", "title", "trade"]],
    ["notes", "Notes", false, ["notes", "note", "thoughts", "comments", "comment", "review", "description", "journal", "lessons", "lesson"]],
  ];
  const normN = (h) => String(h).toLowerCase().replace(/[^a-z]/g, "");
  // A text column filled with dates (Notion sometimes keeps a date in a "Strategy" property) isn't matched as text.
  const mostlyDates = (rows, i) => { const v = rows.slice(1).map((r) => r[i]).filter((x) => String(x || "").trim()); return v.length > 0 && v.filter((x) => parseLooseDate(x, "mdy")).length / v.length > 0.5; };
  function guessNotionMap(header, rows) {
    const norm = header.map(normN), used = new Set(), map = {};
    const textOnly = new Set(["setup", "session", "instrument", "dir", "feelings", "mistakes", "tags", "title", "notes"]);
    NOTION_FIELDS.forEach(([key, , , names]) => {
      const free = (i) => !used.has(i) && !(textOnly.has(key) && mostlyDates(rows, i));
      let idx = -1;
      for (const n of names) { idx = norm.findIndex((h, i) => h === n && free(i)); if (idx >= 0) break; }
      if (idx < 0) for (const n of names) { if (n.length < 4) continue; idx = norm.findIndex((h, i) => h.includes(n) && free(i)); if (idx >= 0) break; }
      if (idx >= 0) { map[key] = idx; used.add(idx); }
    });
    return map;
  }
  // Dates as Notion writes them ("July 15, 2025 9:30 AM", "2025/07/15", "15/07/2025"), the start of a range when there is one.
  function parseLooseDate(v, order) {
    const s = String(v || "").split(/\s*(?:→|->)\s*/)[0].trim();
    if (!s) return null;
    const tm = s.match(/(\d{1,2}):(\d{2})\s*([AaPp][Mm])?/);
    const iso = s.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})$/i);
    if (iso) { const d = new Date(s); if (!isNaN(d)) return { date: `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`, time: `${pad(d.getHours())}:${pad(d.getMinutes())}` }; }
    let time = "";
    if (tm) { let h = +tm[1]; if (tm[3]) { const pm = /p/i.test(tm[3]); if (h === 12) h = pm ? 12 : 0; else if (pm) h += 12; } if (h < 24 && +tm[2] < 60) time = `${pad(h)}:${tm[2]}`; }
    let m = s.match(/\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)/);
    if (m) { const d = validYmd(m[1], m[2], m[3]); return d ? { date: d, time } : null; }
    m = s.match(/\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b/);
    if (m) { const mo = MONTHS.findIndex((x) => x.startsWith(m[1].toLowerCase().slice(0, 3))); const d = mo >= 0 ? validYmd(m[3], mo + 1, m[2]) : null; if (d) return { date: d, time }; }
    m = s.match(/\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b/);
    if (m) { const mo = MONTHS.findIndex((x) => x.startsWith(m[2].toLowerCase().slice(0, 3))); const d = mo >= 0 ? validYmd(m[3], mo + 1, m[1]) : null; if (d) return { date: d, time }; }
    m = s.match(/\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2}|\d{4})\b/);
    if (m) { const y = m[3].length === 2 ? "20" + m[3] : m[3]; const d = order === "dmy" ? validYmd(y, m[2], m[1]) : validYmd(y, m[1], m[2]); return d ? { date: d, time } : null; }
    return null;
  }
  const yes = (v) => /^(yes|true|y|x|✓|✔|1|checked)$/i.test(String(v || "").trim());
  const splitList = (v) => String(v || "").split(/\s*[,;]\s*/).map((x) => x.trim()).filter(Boolean);
  // Same date, numbers and text: the same id, so importing the file twice (or its _all twin) adds nothing new.
  // Two identical rows are told apart by their order in the file.
  const hashRow = (r) => { let h = 2166136261; for (const c of r.join("\u0001")) { h ^= c.codePointAt(0); h = Math.imul(h, 16777619); } return (h >>> 0).toString(36); };
  let notion = null;
  function buildNotion() {
    const { rows, map } = notion, body = rows.slice(1), col = (r, k) => (map[k] != null && map[k] >= 0 ? r[map[k]] ?? "" : "");
    const order = $("notionDateOrder").value === "auto" ? (body.some((r) => { const m = String(col(r, "date")).match(/^(\d{1,2})[-/.](\d{1,2})[-/.]/); return m && +m[1] > 12; }) ? "dmy" : "mdy") : $("notionDateOrder").value;
    const extIds = new Set([...S.trades.values()].map((t) => t.extId).filter(Boolean));
    const fallback = $("notionInstr").value || "NAS100";
    const trades = [], notes = new Map(), seen = new Map(); let skipped = 0, dupes = 0, noPnl = 0;
    body.forEach((r) => {
      const dt = parseLooseDate(col(r, "date"), order);
      if (!dt) { skipped++; return; }
      const said = String(col(r, "result")).trim().toLowerCase();
      const res = map.win >= 0 && yes(col(r, "win")) ? "win" : map.loss >= 0 && yes(col(r, "loss")) ? "loss"
        : /^(w|win|won|winner|green|tp)$/.test(said) ? "win" : /^(l|loss|lost|lose|losing|loser|red|sl)$/.test(said) ? "loss" : /^(be|b\/e|breakeven|break ?even)$/.test(said) ? "be" : "";
      const isMock = yes(col(r, "mock"));
      let pnl = num(col(r, "pnl"));
      if (pnl != null && pnl > 0 && res === "loss") pnl = -pnl; // a loss written as a positive number
      const rrx = num(col(r, "rrx")), risk = num(col(r, "risk")), imp = String(col(r, "importance")).trim();
      const facts = [res === "win" ? "Win" : res === "loss" ? "Loss" : res === "be" ? "BE" : "", isMock ? "Mock / backtest / BE" : "", String(col(r, "instrument")).trim(), String(col(r, "dir")).trim()].filter(Boolean).join(" · ");
      const extra = [num(col(r, "rr")) != null ? `RR ${num(col(r, "rr"))}` : "", rrx != null ? `RRx ${rrx}` : "", risk != null ? `risk level ${risk}` : "", imp ? `importance ${imp}` : ""].filter(Boolean).join(", ");
      const text = [col(r, "title"), col(r, "notes")].map((x) => String(x).trim()).filter(Boolean);
      if (pnl == null && res === "be") pnl = 0;
      // Mock, backtest and breakeven rows stay out of your P/L unless you ask for them, and become notes on the day instead.
      if (pnl == null || (isMock && !$("notionMock").checked)) {
        noPnl++;
        if (text.length || facts) { const cur = notes.get(dt.date) || []; cur.push([[facts, pnl != null ? money(pnl) : "", extra].filter(Boolean).join(" · "), ...text].filter(Boolean).join("\n")); notes.set(dt.date, cur); }
        return;
      }
      const key = hashRow(NOTION_FIELDS.map(([k]) => String(col(r, k)).trim())), nth = (seen.get(key) || 0) + 1; seen.set(key, nth);
      const extId = `notion:${key}${nth > 1 ? ":" + nth : ""}`;
      if (extIds.has(extId)) { dupes++; return; }
      extIds.add(extId);
      const dirRaw = String(col(r, "dir")).toLowerCase(), feel = splitList(col(r, "feelings"));
      trades.push({ id: `notion-${key}${nth > 1 ? "-" + nth : ""}`, extId, source: "notion", createdAt: Date.now(), date: dt.date, time: dt.time, instrument: cleanSymbol(col(r, "instrument")) || fallback,
        dir: /short|sell|bear/.test(dirRaw) ? "Short" : /long|buy|bull/.test(dirRaw) ? "Long" : "", session: String(col(r, "session")).trim(), setup: String(col(r, "setup")).trim(),
        size: "", entry: "", exit: "", stop: "", target: "", risk: "", pnl: pnl.toFixed(2), followedPlan: null, feelingsBefore: feel, feelingsAfter: [], emotionBefore: feel[0] || "", emotionAfter: "",
        mistakes: splitList(col(r, "mistakes")), tags: [...splitList(col(r, "tags")), ...(isMock ? ["Mock / backtest / BE"] : [])], screenshots: [], notes: [...text, extra ? `From Notion: ${extra}.` : ""].filter(Boolean).join("\n") });
    });
    const noteOn = (d) => !dayHasWords(d) || (d.importedFrom === "onenote" && !d.notionMerged);
    const isDone = (d) => d && (d.importedFrom === "notion" || d.notionMerged);
    const kept = [...notes.entries()].filter(([date]) => !isDone(S.days.get(date)) && noteOn(S.days.get(date)));
    const dayNotes = kept.map(([date, list]) => ({ date, text: list.join("\n\n") }));
    const noteDone = [...notes.entries()].filter(([date]) => isDone(S.days.get(date))).reduce((a, [, l]) => a + l.length, 0);
    return { trades, dayNotes, dayNoteRows: kept.reduce((a, [, l]) => a + l.length, 0), noteDone, skipped, dupes, noPnl };
  }
  function renderNotion() {
    if (!notion) return;
    $("notionMap").hidden = false;
    const opts = (k) => `<option value="-1">Not in file</option>` + notion.header.map((h, i) => `<option value="${i}" ${notion.map[k] === i ? "selected" : ""}>${esc(h || `Column ${i + 1}`)}</option>`).join("");
    $("notionMapGrid").innerHTML = NOTION_FIELDS.map(([k, label, req]) => `<div class="field"><label for="nmap-${k}">${esc(label)}${req ? " *" : ""}</label><select id="nmap-${k}" data-nmap="${k}">${opts(k)}</select></div>`).join("");
    const res = buildNotion(); notion.result = res;
    const s = summarize(res.trades);
    const noPl = !(notion.map.pnl >= 0);
    $("notionPreview").innerHTML = `<div class="stack">${noPl ? `<p><strong>No P/L column is matched.</strong> Pick it in "P/L ($)" above, or every row is saved as a note instead of a trade.</p>` : ""}<p>Found <strong>${plural(res.trades.length, "new trade")}</strong>, net <span class="num ${cls(s.net)}">${money(s.net)}</span>.${res.dupes ? ` ${res.dupes} already brought in.` : ""}${res.noteDone ? ` ${plural(res.noteDone, "note")} already in the journal.` : ""}${res.dayNotes.length ? ` ${plural(res.dayNoteRows, "row")} without a P/L${$("notionMock").checked ? "" : " or marked mock, backtest or BE"} will be saved as notes on ${plural(res.dayNotes.length, "day")} in the journal.` : ""}${res.noPnl - res.dayNoteRows - res.noteDone > 0 ? ` ${plural(res.noPnl - res.dayNoteRows - res.noteDone, "row")} without a P/L ${res.noPnl - res.dayNoteRows - res.noteDone === 1 ? "is" : "are"} left out, because ${res.noPnl - res.dayNoteRows - res.noteDone === 1 ? "its day already has" : "their days already have"} notes or ${res.noPnl - res.dayNoteRows - res.noteDone === 1 ? "it is" : "they are"} empty.` : ""}${res.skipped ? ` ${plural(res.skipped, "row")} had no date I could read.` : ""}</p>
      ${res.trades.length ? `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Market</th><th>Side</th><th>Setup</th><th class="r">P/L</th><th>Notes</th></tr></thead><tbody>${res.trades.slice(0, 10).map((t) => `<tr><td class="num">${esc(t.date)} ${esc(t.time)}</td><td>${esc(t.instrument)}</td><td>${esc(t.dir || "–")}</td><td>${esc(t.setup || "–")}</td><td class="r num ${cls(num(t.pnl))}">${money(num(t.pnl))}</td><td style="white-space:normal;max-width:360px"><span class="clamp muted" style="font-size:.85rem">${esc(t.notes || "–")}</span></td></tr>`).join("")}</tbody></table></div>${res.trades.length > 10 ? `<p class="calc">and ${res.trades.length - 10} more</p>` : ""}` : ""}
      ${res.trades.length || res.dayNotes.length ? `<div class="field" style="max-width:420px"><label for="notionAcct">Put the trades in</label><select id="notionAcct"></select></div>
      <div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="notionGo">Bring in ${plural(res.trades.length, "trade")}${res.dayNotes.length ? ` and ${plural(res.dayNotes.length, "note")}` : ""}</button></div>` : `<p class="muted">Nothing to bring in. Check that Date and P/L are matched above.</p>`}</div>`;
    if ($("notionAcct")) importAccountOptions($("notionAcct"));
    $("notionGo")?.addEventListener("click", notionImport);
  }
  $("notionMapGrid").addEventListener("change", (e) => { const s = e.target.closest("[data-nmap]"); if (s) { notion.map[s.dataset.nmap] = +s.value; renderNotion(); } });
  ["notionDateOrder", "notionInstr", "notionMock"].forEach((id) => $(id).addEventListener("change", () => notion && renderNotion()));
  $("notionFile").addEventListener("change", async () => {
    const f = $("notionFile").files[0]; if (!f) return;
    if (/\.zip$/i.test(f.name)) { toast("Unzip the Notion export first, then pick the .csv file inside."); $("notionFile").value = ""; return; }
    const rows = parseCsv(await f.text());
    if (rows.length < 2) { notion = null; $("notionMap").hidden = true; $("notionPreview").innerHTML = ""; toast("Couldn't find any rows in that file."); return; }
    notion = { rows, header: rows[0], map: guessNotionMap(rows[0], rows) };
    renderNotion();
  });
  async function notionImport() {
    const btn = $("notionGo"); btn.disabled = true; btn.textContent = "Bringing them in…";
    try {
      const res = buildNotion(), now = Date.now();
      const accountId = res.trades.length ? await importAccountId($("notionAcct")) : "";
      const trades = res.trades.map((t) => ({ ...t, accountId }));
      const days = res.dayNotes.map(({ date, text }) => {
        const prev = S.days.get(date) || {};
        return dayHasWords(prev) ? { ...prev, thoughts: [String(prev.thoughts ?? prev.review ?? "").trim(), text].filter(Boolean).join("\n\n"), notionMerged: true, updatedAt: now }
          : { ...prev, id: date, date, thoughts: text, importedFrom: "notion", updatedAt: now };
      });
      await putAll("trades", trades); await putAll("days", days);
      const accName = S.accounts.get(accountId)?.name || PAST_ACCOUNT;
      toast(`Brought in ${plural(trades.length, "trade")}${days.length ? ` and ${plural(days.length, "note")}` : ""}.${trades.length && accName && accountId !== activeAccount().id ? ` Pick "${accName}" in the account menu to see them.` : ""}`);
      notion = null; $("notionMap").hidden = true; $("notionPreview").innerHTML = ""; $("notionFile").value = "";
      showTab(trades.length ? "trades" : "journal");
    } catch (e) { toast(e?.code === "quota_exceeded" ? "Storage is full. Not everything was saved." : "Couldn't save everything. Try again; anything already brought in is skipped."); renderNotion(); }
  }
  // Which import the page shows: your platform's file, your OneNote notebook, or a Notion export.
  function setImportMode(mode) {
    ["platform", "onenote", "notion"].forEach((m) => { $("imp-" + m).hidden = m !== mode; });
    document.querySelectorAll("#impModes [data-imp-mode]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.impMode === mode)));
  }
  $("impModes").addEventListener("click", (e) => { const b = e.target.closest("[data-imp-mode]"); if (b) setImportMode(b.dataset.impMode); });
  document.addEventListener("click", (e) => { const b = e.target.closest("[data-open-import]"); if (b) { showTab("import"); setImportMode(b.dataset.openImport); } });
  $("notionInstr").innerHTML = INSTRUMENTS.map((s) => `<option>${esc(s)}</option>`).join("");

