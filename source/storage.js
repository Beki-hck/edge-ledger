  // ---------- storage: a folder on this computer ----------
  // Everything lives in one folder the trader picks: journal.json (all trades, journal entries, accounts, playbooks,
  // settings), screenshots/ (chart images as normal files), news/ (the market log, one file per day) and backups/
  // (one copy of journal.json per day, newest 30 kept). Chrome remembers the folder between visits.
  const LS_KEY = "edge-ledger-desktop";
  const JOURNAL = "journal.json";
  let dir = null, shotsDir = null, newsDir = null, backupsDir = null;
  let pendingDrops = []; // screenshot files to delete once the journal saves
  let lastDiskStamp = 0, pendingWrites = 0, saveChain = Promise.resolve(), saveError = null, backupDay = "";

  const idb = {
    open() {
      return new Promise((res, rej) => {
        const r = indexedDB.open("edge-ledger", 1);
        r.onupgradeneeded = () => r.result.createObjectStore("kv");
        r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
      });
    },
    async get(key) { const db = await idb.open(); return new Promise((res, rej) => { const q = db.transaction("kv").objectStore("kv").get(key); q.onsuccess = () => res(q.result); q.onerror = () => rej(q.error); }); },
    async set(key, val) { const db = await idb.open(); return new Promise((res, rej) => { const tx = db.transaction("kv", "readwrite"); tx.objectStore("kv").put(val, key); tx.oncomplete = () => res(); tx.onerror = () => rej(tx.error); }); },
  };

  async function writeFile(dirH, name, data) {
    const fh = await dirH.getFileHandle(name, { create: true });
    const w = await fh.createWritable();
    try { await w.write(data); await w.close(); } catch (e) { try { await w.abort(); } catch {} throw e; }
    return fh;
  }
  async function readText(dirH, name) {
    try { return await (await (await dirH.getFileHandle(name)).getFile()).text(); }
    catch (e) { if (e?.name === "NotFoundError") return null; throw e; }
  }
  async function fileStamp(dirH, name) {
    try { const f = await (await dirH.getFileHandle(name)).getFile(); return f.lastModified + ":" + f.size; } catch { return ""; }
  }
  async function removeFile(dirH, name) { try { await dirH.removeEntry(name); return true; } catch { return false; } }

  function snapshot() {
    const o = { app: "edge-ledger", version: 3, savedAt: new Date().toISOString(), settings: S.settings };
    COLLS.forEach((c) => (o[c] = [...S[c].values()]));
    return o;
  }
  function loadSnapshot(j) {
    COLLS.forEach((c) => (S[c] = new Map((Array.isArray(j[c]) ? j[c] : []).filter((x) => x && (x.id || x.date)).map((x) => { if (c === "days" && !x.id) x.id = x.date; if (c === "days" && !x.date) x.date = x.id; return [x.id, x]; }))));
    S.settings = j.settings && typeof j.settings === "object" ? j.settings : {};
    if (S.accounts.size === 0) {
      const legacy = S.settings.startBalance ? S.settings : {};
      S.accounts.set("main", { ...ACCOUNT_DEFAULTS, ...pickAccount(legacy), id: "main" });
    }
  }

  // Keeps one copy of the journal per day before the first change of that day, and the newest 30 copies.
  async function dailyBackup() {
    const day = today();
    if (backupDay === day) return;
    const name = `journal-${day}.json`;
    if ((await readText(backupsDir, name)) == null) {
      const current = await readText(dir, JOURNAL);
      if (!current) return; // nothing to back up yet; try again on the next save
      try { JSON.parse(current); } catch { return; } // never keep a damaged file as a backup
      await writeFile(backupsDir, name, current);
      const names = [];
      for await (const [n, h] of backupsDir.entries()) if (h.kind === "file" && /^journal-\d{4}-\d{2}-\d{2}\.json$/.test(n)) names.push(n);
      names.sort().slice(0, Math.max(0, names.length - 30)).forEach((n) => removeFile(backupsDir, n));
    }
    backupDay = day;
  }
  async function writeJournal() {
    await dailyBackup();
    await writeFile(dir, JOURNAL, JSON.stringify(snapshot(), null, 1));
    lastDiskStamp = await fileStamp(dir, JOURNAL);
  }
  // Writes are queued so two quick changes never interleave; each write saves the whole current journal.
  function queueSave() {
    pendingWrites++;
    const p = (saveChain = saveChain.then(writeJournal, writeJournal)).then(
      () => { pendingWrites--; if (saveError) { saveError = null; showNotice(""); } if (pendingDrops.length) dropShots(pendingDrops.splice(0)); },
      (e) => { pendingWrites--; saveError = e; showSaveError(e); throw saveErr(e); });
    return p;
  }
  function saveErr(e) { const err = new Error("save failed"); err.code = e?.name === "QuotaExceededError" ? "quota_exceeded" : e?.name === "NotAllowedError" ? "no_permission" : "save_failed"; return err; }
  function showSaveError(e) {
    const msg = e?.name === "NotAllowedError" ? "Edge Ledger lost permission to save in your folder." : e?.name === "QuotaExceededError" ? "Your disk is full, so the last change wasn't saved." : "The last change couldn't be saved to your folder.";
    showNotice(`${msg} <button class="btn-small" id="retrySave">Try again</button>`, true);
  }
  function showNotice(html, isHtml) { const n = $("storageNotice"); n.hidden = !html; if (isHtml) n.innerHTML = html; else n.textContent = html; }
  document.addEventListener("click", async (e) => {
    if (!e.target.closest("#retrySave")) return;
    if (dir && (await dir.queryPermission({ mode: "readwrite" })) !== "granted") { try { await dir.requestPermission({ mode: "readwrite" }); } catch {} }
    queueSave().then(() => toast("Saved"), () => {});
  });
  window.addEventListener("beforeunload", (e) => { if (pendingWrites > 0) { e.preventDefault(); e.returnValue = ""; } });

  const folderBackend = {
    async put(coll, obj) { S[coll].set(obj.id, obj); render(); await queueSave(); },
    async putMany(coll, list) { list.forEach((o) => S[coll].set(o.id, o)); render(); await queueSave(); },
    async del(coll, id) { S[coll].delete(id); render(); await queueSave(); },
    async saveSettings(s) { S.settings = s; render(); await queueSave(); },
  };
  function pickAccount(o) { const out = {}; ["firm", "preset", "startBalance", "startDate", "targetPct", "dailyLossPct", "maxLossPct", "riskPct", "maxTrades"].forEach((k) => { if (o[k] !== undefined && o[k] !== "") out[k] = o[k]; }); return out; }

  // Reads journal.json. A file that can't be read is set aside (never overwritten) and the newest backup is used.
  async function loadJournal() {
    const text = await readText(dir, JOURNAL);
    if (text == null) { loadSnapshot({}); await writeJournal(); return "new"; }
    try { loadSnapshot(JSON.parse(text)); lastDiskStamp = await fileStamp(dir, JOURNAL); return "ok"; }
    catch {
      await writeFile(dir, `journal-unreadable-${Date.now()}.json`, text);
      const names = [];
      for await (const [n, h] of backupsDir.entries()) if (h.kind === "file" && /^journal-\d{4}-\d{2}-\d{2}\.json$/.test(n)) names.push(n);
      for (const n of names.sort().reverse()) { try { loadSnapshot(JSON.parse(await readText(backupsDir, n))); await writeJournal(); return "restored:" + n; } catch {} }
      loadSnapshot({}); await writeJournal(); return "unreadable";
    }
  }
  async function loadNews() {
    const m = new Map();
    for await (const [n, h] of newsDir.entries()) {
      if (h.kind !== "file" || !/^\d{4}-\d{2}-\d{2}\.json$/.test(n)) continue;
      try { const d = JSON.parse(await (await h.getFile()).text()); if (d && typeof d === "object") m.set(n.slice(0, 10), cleanNewsDoc(d, n.slice(0, 10), d)); } catch {}
    }
    S.market = m;
  }
  async function saveNewsDay(doc) {
    await writeFile(newsDir, doc.date + ".json", JSON.stringify(doc, null, 1));
    S.market.set(doc.date, doc);
  }

  // If the journal file changed on disk (another computer through a synced folder), reload it.
  async function checkDiskChanges() {
    if (!dir || pendingWrites > 0 || document.hidden) return;
    try {
      const stamp = await fileStamp(dir, JOURNAL);
      if (stamp && lastDiskStamp && stamp !== lastDiskStamp && pendingWrites === 0) {
        const text = await readText(dir, JOURNAL);
        loadSnapshot(JSON.parse(text)); lastDiskStamp = stamp; await loadNews(); render(); toast("Loaded changes from your folder");
      }
    } catch {}
  }
  window.addEventListener("focus", checkDiskChanges);
  document.addEventListener("visibilitychange", checkDiskChanges);

  // ---------- folder gate ----------
  const testDir = () => window.EDGE_TEST_DIR || null;
  function gate(state, extra = "", note = "") {
    const g = $("gate");
    g.hidden = !state;
    if (!state) return;
    const body = {
      unsupported: `<h2>Open Edge Ledger in Chrome or Edge</h2><p>Edge Ledger saves your journal as files in a folder on this computer. Only Chrome and Microsoft Edge on a computer can do that.</p><p class="calc">Right-click the Edge Ledger file, choose Open with, then Google Chrome.</p>`,
      first: `<h2>Welcome to Edge Ledger</h2><p>Pick the folder where your journal will live. Your trades, journal entries and chart screenshots are saved there as normal files, and nothing leaves this computer.</p>
        <ol class="calc" style="margin:0;padding-left:1.2em;display:grid;gap:4px"><li>Click <strong>Choose my folder</strong>.</li><li>Make a new folder, for example <strong>Edge Ledger Data</strong> inside Documents, and select it.</li><li>When Chrome asks, allow Edge Ledger to save changes. Choose <strong>Allow on every visit</strong> if it offers that.</li></ol>
        <div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="gatePick">Choose my folder</button></div>
        <p class="calc">Moving from Edge Ledger online? Pick a new empty folder here first. Then, in Settings, use <strong>Restore or move in from a file</strong> with the .zip you exported.</p>`,
      reconnect: `<h2>Welcome back</h2><p>Chrome needs your OK to open your journal folder${extra ? ` <strong>${esc(extra)}</strong>` : ""} again.</p>
        ${note ? `<p class="loss">${esc(note)}</p>` : ""}
        <div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="gateReconnect">Open my journal</button><button id="gatePick">Use a different folder</button></div>`,
      locked: `<h2>Edge Ledger is already open</h2><p>It's open in another tab or window. Close the other one, then reload this page, so two copies never save over each other.</p><div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="gateReload">Reload</button></div>`,
      error: `<h2>Couldn't open your folder</h2><p>${esc(extra || "Chrome blocked access to that folder.")}</p><p class="calc">Chrome doesn't allow some folders, like Documents or Desktop themselves. Make a new folder inside them and pick that one.</p><div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="gatePick">Choose a folder</button></div>`,
    }[state];
    $("gateBody").innerHTML = body;
  }
  $("gate").addEventListener("click", async (e) => {
    if (e.target.closest("#gatePick")) pickFolder();
    else if (e.target.closest("#gateReconnect")) {
      let h = null;
      try { h = await idb.get("dir"); if (h && (await h.requestPermission({ mode: "readwrite" })) === "granted") return openFolder(h); } catch {}
      if (h) gate("reconnect", h.name, "Chrome didn't give permission. Click Open my journal again and choose Allow, or pick the folder again.");
      else gate("first");
    } else if (e.target.closest("#gateReload")) location.reload();
  });
  async function pickFolder() {
    let h;
    try { h = await window.showDirectoryPicker({ id: "edge-ledger", mode: "readwrite", startIn: "documents" }); }
    catch (e) { if (e?.name === "AbortError") return; gate("error", e?.message); return; }
    try { await idb.set("dir", h); } catch {}
    openFolder(h);
  }
  // Settings > Use a different folder. An empty folder can take a copy of the current journal.
  async function switchFolder() {
    let h;
    try { h = await window.showDirectoryPicker({ id: "edge-ledger", mode: "readwrite", startIn: "documents" }); }
    catch (e) { if (e?.name !== "AbortError") toast("Chrome couldn't open that folder. Make a new folder inside Documents and pick that one."); return; }
    try { if (dir && (await h.isSameEntry(dir))) { toast("That's the folder you're already using."); return; } } catch {}
    let has = true;
    try { has = (await readText(h, JOURNAL)) != null; } catch { toast("Chrome couldn't read that folder."); return; }
    if (!has && (S.trades.size || S.days.size || S.weeks?.size || S.playbooks.size)) {
      if (confirm(`"${h.name}" has no journal yet.\n\nOK: copy your current journal, screenshots and news log into it.\nCancel: start a new, empty journal there.`)) {
        try {
          await saveChain.catch(() => {});
          for (const [sub, from] of [["screenshots", shotsDir], ["news", newsDir]]) {
            const to = await h.getDirectoryHandle(sub, { create: true });
            for await (const [n, fh] of from.entries()) if (fh.kind === "file") await writeFile(to, n, await fh.getFile());
          }
          await writeFile(h, JOURNAL, JSON.stringify(snapshot(), null, 1));
        } catch (e) { toast(e?.name === "QuotaExceededError" ? "Your disk is full, so the copy stopped. Edge Ledger stayed on your current folder." : "The copy didn't finish, so Edge Ledger stayed on your current folder."); return; }
      }
    }
    try { await idb.set("dir", h); } catch {}
    openFolder(h);
  }
  async function openFolder(h) {
    try {
      dir = h; backupDay = ""; lastDiskStamp = 0;
      shotUrls.forEach((u) => URL.revokeObjectURL(u)); shotUrls.clear(); S.ff = new Map();
      shotsDir = await dir.getDirectoryHandle("screenshots", { create: true });
      newsDir = await dir.getDirectoryHandle("news", { create: true });
      backupsDir = await dir.getDirectoryHandle("backups", { create: true });
      const res = await loadJournal();
      await loadNews();
      backend = folderBackend; S.mode = "folder";
      gate(null); render();
      if (res === "new") toast(`Your journal is saved in ${dir.name}`);
      else if (res.startsWith("restored:")) showNotice(`Your journal file couldn't be read, so Edge Ledger set it aside and opened your backup from ${res.slice(17, 27)}.`);
      else if (res === "unreadable") showNotice("Your journal file couldn't be read and there was no backup. It was set aside in your folder, and a fresh journal was started.");
      afterOpen();
    } catch (e) {
      dir = null;
      gate("error", e?.name === "NotAllowedError" ? "Chrome didn't give permission to save in that folder." : (e?.message || "Something went wrong opening that folder."));
    }
  }
  async function initStorage() {
    const t = testDir();
    if (t) return openFolder(await t);
    if (!window.showDirectoryPicker || !window.indexedDB) return gate("unsupported");
    // One open copy at a time, so two tabs never overwrite each other's changes.
    if (navigator.locks) {
      const got = await new Promise((res) => navigator.locks.request("edge-ledger-folder", { ifAvailable: true }, (lock) => { res(!!lock); return lock ? new Promise(() => {}) : undefined; }));
      if (!got) return gate("locked");
    }
    let h = null;
    try { h = await idb.get("dir"); } catch {}
    if (!h) return gate("first");
    let perm = "prompt";
    try { perm = await h.queryPermission({ mode: "readwrite" }); } catch {}
    if (perm === "granted") return openFolder(h);
    gate("reconnect", h.name);
  }
  async function persist(fn, okMsg) {
    try { await fn(); if (okMsg) toast(okMsg); return true; }
    catch (e) { toast(e?.code === "quota_exceeded" ? "Your disk is full. Free up space, then try again." : e?.code === "no_permission" ? "Edge Ledger lost permission to your folder. Use Try again at the top." : "Couldn't save to your folder. Use Try again at the top."); return false; }
  }
  const saveSettings = (patch) => { S.settings = { ...S.settings, ...patch }; return persist(() => backend.saveSettings(S.settings)); };
