  // ---------- Claude API (coach and news), with the trader's own API key ----------
  const KEY_LS = "edge-ledger-claude-key";
  const MODEL = "claude-opus-5-5";
  const apiKey = () => { try { return localStorage.getItem(KEY_LS) || ""; } catch { return ""; } };
  function apiError(status, body) {
    const e = new Error(body?.error?.message || `HTTP ${status}`);
    e.code = status === 401 || status === 403 ? "bad_key" : status === 429 ? "rate_limited" : status === 529 || status >= 500 ? "overloaded" : status === 400 && /credit|billing|balance/i.test(e.message) ? "no_credit" : "api_error";
    return e;
  }
  // One Messages API call. With onText, the answer streams in and onText gets the text so far.
  async function callClaude(body, { signal, onText } = {}) {
    const send = async (useFallbacks) => fetch("https://api.anthropic.com/v1/messages", {
      method: "POST", signal,
      headers: {
        "content-type": "application/json", "x-api-key": apiKey(), "anthropic-version": "2023-06-01",
        "anthropic-dangerous-direct-browser-access": "true",
        ...(useFallbacks ? { "anthropic-beta": "server-side-fallback-2026-07-01" } : {}),
      },
      body: JSON.stringify({ model: MODEL, ...body, ...(useFallbacks ? { fallbacks: "default" } : {}), ...(onText ? { stream: true } : {}) }),
    });
    let res;
    try { res = await send(true); }
    catch (e) { if (e?.name === "AbortError") throw Object.assign(new Error("cancelled"), { code: "cancelled" }); throw Object.assign(new Error("offline"), { code: "offline" }); }
    if (res.status === 400) {
      const b = await res.clone().json().catch(() => null);
      if (/fallback|anthropic-beta/i.test(b?.error?.message || "")) res = await send(false);
    }
    if (!res.ok) throw apiError(res.status, await res.json().catch(() => null));
    if (!onText) return res.json();
    // Server-sent events: collect the text blocks and the stop reason.
    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "", text = "", stop = null;
    try {
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let i;
        while ((i = buf.indexOf("\n\n")) >= 0) {
          const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
          const data = chunk.split("\n").filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim()).join("");
          if (!data) continue;
          let ev; try { ev = JSON.parse(data); } catch { continue; }
          if (ev.type === "content_block_delta" && ev.delta?.type === "text_delta") { text += ev.delta.text; onText(text); }
          else if (ev.type === "message_delta" && ev.delta?.stop_reason) stop = ev.delta.stop_reason;
          else if (ev.type === "error") throw Object.assign(new Error(ev.error?.message || "stream error"), { code: ev.error?.type === "overloaded_error" ? "overloaded" : "api_error", text });
        }
      }
    } catch (e) {
      if (e?.name === "AbortError") throw Object.assign(new Error("cancelled"), { code: "cancelled", text });
      throw Object.assign(e, { text: e.text ?? text });
    }
    return { text, stop };
  }
  const claudeErrorText = (c) => ({
    bad_key: "Your Claude API key wasn't accepted. Check it in Settings.",
    no_credit: "Your Claude API account is out of credit. Add credit at console.anthropic.com.",
    rate_limited: "Claude's API is rate limiting your key. Wait a minute and try again.",
    overloaded: "Claude is busy right now. Try again in a minute.",
    offline: "Couldn't reach Claude. Check your internet connection.",
  }[c] || "Claude couldn't answer. Try again.");

  // ---------- market news: ForexFactory calendar + optional Claude news log ----------
  // The ForexFactory weekly feed lists scheduled releases with forecast and previous (no actual).
  // Red-folder (High impact) USD releases are kept. It's fetched at most every 6 hours and cached in news/.
  const FF_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json";
  const NEWS_TAGS = ["CPI", "PPI", "NFP", "ADP", "FOMC", "Fed Chair", "PCE", "GDP", "Retail sales", "Jobless claims", "ISM / PMI", "JOLTS", "Consumer confidence", "Trump", "Geopolitics", "War", "ECB", "BoE"];
  function tagFor(title) {
    const t = title.toLowerCase();
    return /\badp\b/.test(t) ? "ADP" : /\bcpi\b/.test(t) ? "CPI" : /\bppi\b/.test(t) ? "PPI" : /non-farm|nonfarm|unemployment rate|average hourly/.test(t) ? "NFP"
      : /fomc|federal funds|fed interest/.test(t) ? "FOMC" : /powell|fed chair/.test(t) ? "Fed Chair" : /\bpce\b/.test(t) ? "PCE" : /\bgdp\b/.test(t) ? "GDP" : /retail sales/.test(t) ? "Retail sales"
      : /jobless|unemployment claims/.test(t) ? "Jobless claims" : /\bism\b|\bpmi\b/.test(t) ? "ISM / PMI" : /jolts/.test(t) ? "JOLTS" : /consumer confidence|consumer sentiment/.test(t) ? "Consumer confidence" : "";
  }
  const etParts = (iso) => {
    const d = new Date(iso); if (isNaN(d)) return null;
    const p = Object.fromEntries(new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).formatToParts(d).map((x) => [x.type, x.value]));
    return { date: `${p.year}-${p.month}-${p.day}`, time: `${p.hour}:${p.minute}` };
  };
  function applyFF(list) {
    const m = new Map();
    (Array.isArray(list) ? list : []).forEach((e) => {
      if (!e || e.country !== "USD" || String(e.impact).toLowerCase() !== "high") return;
      const et = etParts(e.date); if (!et) return;
      if (!m.has(et.date)) m.set(et.date, []);
      m.get(et.date).push({ time: et.time === "00:00" ? "" : `${et.time} ET`, name: String(e.title || ""), tag: tagFor(String(e.title || "")), impact: "high", forecast: String(e.forecast || ""), previous: String(e.previous || "") });
    });
    m.forEach((v) => v.sort((a, b) => a.time.localeCompare(b.time)));
    m.forEach((v, k) => S.ff.set(k, v));
  }
  async function loadFF() {
    if (S.settings.ffOff || !newsDir) return;
    let cached = null;
    try { cached = JSON.parse((await readText(newsDir, "forexfactory-week.json")) || "null"); } catch {}
    if (cached?.events) applyFF(cached.events);
    for await (const [n, h] of newsDir.entries()) {
      if (h.kind === "file" && /^forexfactory-\d{4}-\d{2}-\d{2}\.json$/.test(n)) { try { applyFF(JSON.parse(await (await h.getFile()).text()).events); } catch {} }
    }
    if (cached?.fetchedAt && Date.now() - cached.fetchedAt < 6 * 3600e3) { render(); return; }
    try {
      const res = await fetch(FF_URL, { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const events = await res.json();
      if (!Array.isArray(events)) throw new Error("bad feed");
      applyFF(events);
      await writeFile(newsDir, "forexfactory-week.json", JSON.stringify({ fetchedAt: Date.now(), events }));
      // Keep each week's red-folder list so past days keep their scheduled events. The file is named after the
      // feed's first day, so every fetch of the same week lands in the same file.
      const kept = events.filter((e) => e?.country === "USD" && String(e.impact).toLowerCase() === "high");
      const first = events.map((e) => etParts(e?.date)?.date).filter(Boolean).sort()[0];
      if (first && kept.length) await writeFile(newsDir, `forexfactory-${first}.json`, JSON.stringify({ fetchedAt: Date.now(), events: kept }));
      S.ffStatus = "ok";
    } catch { S.ffStatus = "failed"; }
    render();
  }

  const NEWS_PROMPT = (date) => `You log market-moving news for an ICT day trader of US stock indices (NAS100, US30, SPX500, GER40). Research ${date} (America/New_York date) with web search and report only what matters:
- ForexFactory red-folder (high-impact) USD releases: CPI, Core CPI, PPI, NFP, unemployment rate, average hourly earnings, ADP, Core PCE, GDP, Retail Sales, ISM PMIs, JOLTS, CB Consumer Confidence, UoM sentiment, unemployment claims, FOMC statement/rate/press conference/minutes, Fed Chair speeches. Give actual, forecast and previous, and release time ET. Drop medium and low impact releases. Add EUR or GBP red-folder releases only if they visibly moved GER40 or UK100.
- Anything Trump said, posted or announced that moved indices (tariffs, the Fed, trade deals, war), with time ET if known.
- Geopolitics and war news that moved indices or oil (strikes, attacks, escalation, ceasefires).
- Closing % change for the Dow, S&P 500 and Nasdaq, plus DAX if easy.
Never guess a number: leave a field out if you can't confirm it. If US markets were closed that day, say so in the summary with an empty events list. If nothing qualified, say it was a quiet day.
Answer with only one JSON object, no other text, in this shape:
{"date":"${date}","summary":"1-2 plain sentences on what drove indices","moves":{"Dow":"+0.4%","S&P 500":"-0.2%","Nasdaq":"+0.1%"},"events":[{"time":"08:30 ET","name":"CPI m/m (Sep)","tag":"CPI","actual":"0.3%","forecast":"0.2%","previous":"0.4%","note":"optional, how indices reacted"}],"sources":["url"]}
tag must be one of: ${NEWS_TAGS.join(", ")}. Trump and geopolitical items go in events with the headline as name and no actual/forecast/previous.`;
  // Keeps only the fields Edge Ledger shows, trimmed, with https links only. Used for Claude's answers and for any
  // news file read from disk or brought in from a backup.
  function cleanNewsDoc(raw, date, stored = null) {
    const s = (v, n = 400) => (v == null ? "" : String(v).slice(0, n));
    const moves = {};
    if (raw?.moves && typeof raw.moves === "object") Object.entries(raw.moves).slice(0, 6).forEach(([k, v]) => { if (v != null && v !== "") moves[s(k, 30)] = s(v, 20); });
    const events = (Array.isArray(raw?.events) ? raw.events : []).slice(0, 25).filter((e) => e && e.name).map((e) => {
      const o = { time: s(e.time, 20), name: s(e.name, 300), tag: NEWS_TAGS.includes(e.tag) ? e.tag : "", impact: stored && ["medium", "low"].includes(e.impact) ? e.impact : "high" };
      ["actual", "forecast", "previous", "note"].forEach((k) => { if (e[k] != null && e[k] !== "") o[k] = s(e[k], k === "note" ? 400 : 40); });
      return o;
    });
    const sources = (Array.isArray(raw?.sources) ? raw.sources : []).map((u) => s(u, 500)).filter((u) => /^https:\/\//.test(u)).slice(0, 8);
    return { date, summary: s(raw?.summary, 600), moves, events, sources, updatedAt: stored ? s(stored.updatedAt, 40) : today(), by: stored ? (stored.by === "claude" ? "claude" : "") : "claude" };
  }
  let newsBusy = null;
  async function fetchNewsDay(date) {
    if (!apiKey()) { toast("Add your Claude API key in Settings first."); return false; }
    if (newsBusy) return false;
    newsBusy = date; render();
    try {
      const tools = [{ type: "web_search_20260209", name: "web_search", max_uses: 8 }];
      let messages = [{ role: "user", content: NEWS_PROMPT(date) }], msg = null;
      for (let i = 0; i < 4; i++) {
        msg = await callClaude({ max_tokens: 16000, output_config: { effort: "medium" }, tools, messages });
        if (msg.stop_reason !== "pause_turn") break;
        messages = [...messages, { role: "assistant", content: msg.content }];
      }
      if (msg.stop_reason === "refusal") throw Object.assign(new Error("refused"), { code: "api_error" });
      const text = (msg.content || []).filter((b) => b.type === "text").map((b) => b.text).join("");
      const a = text.indexOf("{"), b = text.lastIndexOf("}");
      if (a < 0 || b < a) throw Object.assign(new Error("no json"), { code: "api_error" });
      let raw;
      try { raw = JSON.parse(text.slice(a, b + 1)); } catch { throw Object.assign(new Error("no json"), { code: "api_error" }); }
      const doc = cleanNewsDoc(raw, date);
      await saveNewsDay(doc);
      toast(`Market news logged for ${fmtDay(date)}`);
      return true;
    } catch (e) { toast(e?.message === "no json" ? "Claude's answer couldn't be read. Try again." : claudeErrorText(e?.code)); return false; }
    finally { newsBusy = null; render(); }
  }
  // Optional: after the US close on weekdays, log today's news once. A day that fails is tried at most twice per session.
  const autoTries = new Map();
  async function autoLogNews() {
    if (!S.settings.autoNews || !apiKey() || newsBusy) return;
    const n = nyNow();
    if (["Sat", "Sun"].includes(n.weekday) || n.hours < 16.5) return;
    if (S.market.has(n.date) || marketEvents(n.date).some((e) => e.name.startsWith("US holiday")) || (autoTries.get(n.date) || 0) >= 2) return;
    autoTries.set(n.date, (autoTries.get(n.date) || 0) + 1);
    await fetchNewsDay(n.date);
  }
  setInterval(() => { if (!document.hidden) autoLogNews(); }, 15 * 60e3);
  function afterOpen() { loadFF(); autoLogNews(); }
