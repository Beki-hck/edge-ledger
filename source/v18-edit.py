#!/usr/bin/env python3
"""v17 -> v18: bring in the pictures from a Notion export folder, each on its day in the journal."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

rep('''        <div id="notionPreview"></div>
      </div>''', '''        <div id="notionPreview"></div>
        <div class="stack" style="margin-top:8px;border-top:1px solid var(--line);padding-top:14px">
          <div class="section-label">Pictures from the Notion export</div>
          <p class="muted">Choose the unzipped export folder, the one with the .md pages and the image files. Each picture goes on its day in the journal, under Charts. Pictures already there are skipped, so you can run this again safely.</p>
          <div class="fields"><div class="field"><label for="notionPics">Choose the export folder</label><input type="file" id="notionPics" webkitdirectory multiple></div></div>
          <div id="notionPicsPreview"></div>
        </div>
      </div>''')

# online: one picture to the artifact's file store (the PC version has its own, in shots.js)
rep('''  function removeDayShot(i) { const date = loadedDay; if (!date) return; dayShots.splice(i, 1); renderDayShots(); saveDayShots(date, dayShots, "Screenshot removed"); }''', '''  function removeDayShot(i) { const date = loadedDay; if (!date) return; dayShots.splice(i, 1); renderDayShots(); saveDayShots(date, dayShots, "Screenshot removed"); }
  // For the old-journal picture import: one file stored, its id returned.
  const canStoreShots = () => !!assets;
  async function storeShot(file) {
    if (!assets || !imageFiles([file]).length) throw new Error("no_store");
    return (await assets.upload(file)).id;
  }''')

rep('''  // Which import the page shows: your platform's file, your OneNote notebook, or a Notion export.''', '''  // Notion pictures: the export folder has one .md page per row ("Date: April 1, 2025") linking its images,
  // which sit next to it. A picture is known by its contents, so the same image twice, or a second run, adds nothing.
  let notionPics = null;
  const PIC_TYPES = { png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", webp: "image/webp", gif: "image/gif" };
  const NOTION_IMG = /!\\[(?:[^\\[\\]\\n]|\\[[^\\]\\n]*\\])*\\]\\(/g;
  // The link after "](": up to the ")" that closes it, so "shot (1).png" stays whole; a "title" at the end is dropped.
  function imageLinks(text) {
    const out = [];
    for (const m of text.matchAll(NOTION_IMG)) {
      let j = m.index + m[0].length, depth = 0, raw = "";
      if (text[j] === "<") { const k = text.indexOf(">", j); if (k > 0) { out.push(text.slice(j + 1, k)); continue; } }
      for (; j < text.length; j++) { const c = text[j]; if (c === "\\n") break; if (c === "(") depth++; else if (c === ")") { if (!depth) break; depth--; } raw += c; }
      const link = raw.trim().replace(/\\s+"[^"]*"$/, "");
      if (link) out.push(link);
    }
    return out;
  }
  const relPath = (f) => String(f.webkitRelativePath || f.name).normalize("NFC");
  const picType = (f) => PIC_TYPES[String(f.name).split(".").pop().toLowerCase()] || "";
  async function picHash(f) { const b = new Uint8Array(await crypto.subtle.digest("SHA-256", await f.arrayBuffer())); return [...b.slice(0, 16)].map((x) => x.toString(16).padStart(2, "0")).join(""); }
  // Pictures still on the day. Older days kept only a list of hashes, so for those every hash counts.
  const dayPicHashes = (d) => { if (!d) return new Set(); if (d.shotHash) return new Set(Object.entries(d.shotHash).filter(([id]) => id.startsWith("old-") || (d.screenshots || []).includes(id)).map(([, h]) => h)); return new Set(d.shotHashes || []); };
  async function readNotionPics(files) {
    const byPath = new Map(files.map((f) => [relPath(f), f]));
    const pages = files.filter((f) => /\\.md$/i.test(f.name));
    const found = new Map(); let noDate = 0, missing = 0, odd = 0;
    for (const pg of pages) {
      const text = await pg.text();
      const links = imageLinks(text).filter((l) => !/^[a-z][a-z0-9+.-]*:/i.test(l));
      if (!links.length) continue;
      const order = $("notionDateOrder").value === "dmy" ? "dmy" : "mdy";
      const dt = [text.match(/^Date:[ \\t]*(\\S.*)$/m), text.match(/^#[ \\t]+(\\S.*)$/m)].map((m) => m && parseLooseDate(m[1], order)).find(Boolean) || null;
      if (!dt) { noDate += links.length; continue; }
      const dir = relPath(pg).split("/").slice(0, -1);
      for (const l of links) {
        let rel = l; try { rel = decodeURIComponent(l); } catch {}
        const parts = [...dir]; rel.normalize("NFC").split("/").forEach((p) => { if (p === "..") parts.pop(); else if (p && p !== ".") parts.push(p); });
        const f = byPath.get(parts.join("/"));
        if (!f) { missing++; continue; }
        if (!picType(f)) { odd++; continue; }
        found.set(dt.date, [...(found.get(dt.date) || []), f.type ? f : new File([f], f.name, { type: picType(f) })]);
      }
    }
    const days = []; let dup = 0;
    for (const [date, list] of [...found].sort((a, b) => a[0].localeCompare(b[0]))) {
      const have = dayPicHashes(S.days.get(date)), add = [];
      for (const f of list) { const h = await picHash(f); if (have.has(h)) { dup++; continue; } have.add(h); add.push({ file: f, hash: h }); }
      if (add.length) days.push({ date, add });
    }
    return { days, dup, noDate, missing, odd, pages: pages.length };
  }
  function renderNotionPics() {
    const r = notionPics, el = $("notionPicsPreview");
    if (!r) { el.innerHTML = ""; return; }
    const n = r.days.reduce((a, d) => a + d.add.length, 0), long = { month: "short", day: "numeric", year: "numeric" };
    const bits = [n ? `Found <strong>${plural(n, "picture")}</strong> for ${plural(r.days.length, "day")}, ${esc(fmtDay(r.days[0].date, long))}${r.days.length > 1 ? ` to ${esc(fmtDay(r.days[r.days.length - 1].date, long))}` : ""}.` : r.pages ? "No new pictures to bring in." : "That folder has no Notion pages (.md files). Choose the unzipped export folder.",
      r.dup ? `${plural(r.dup, "picture")} ${r.dup === 1 ? "is" : "are"} already in the journal or repeated on the same day, so ${r.dup === 1 ? "it's" : "they're"} skipped.` : "",
      r.missing ? `${plural(r.missing, "linked picture")} ${r.missing === 1 ? "isn't" : "aren't"} in the folder.` : "",
      r.noDate ? `${plural(r.noDate, "picture")} on pages without a date ${r.noDate === 1 ? "is" : "are"} left out.` : "",
      r.odd ? `${plural(r.odd, "file")} ${r.odd === 1 ? "isn't a" : "aren't"} PNG, JPG, WebP or GIF, so ${r.odd === 1 ? "it's" : "they're"} left out.` : ""].filter(Boolean).join(" ");
    el.innerHTML = `<div class="stack"><p>${bits}</p>${n ? canStoreShots() ? `<div class="actions" style="justify-content:flex-start"><button class="btn-primary" id="notionPicsGo">Bring in ${plural(n, "picture")}</button></div>` : `<p class="muted">Pictures can only be saved when the journal can store screenshots: open it from claude.ai while signed in, or connect your Edge Ledger folder.</p>` : ""}</div>`;
    $("notionPicsGo")?.addEventListener("click", importNotionPics);
  }
  let picsBusy = false;
  $("notionPics").addEventListener("change", async () => {
    const files = [...$("notionPics").files]; if (!files.length) return;
    if (picsBusy) { toast("Still saving the pictures. Choose the folder again once it's done."); return; }
    $("notionPicsPreview").innerHTML = `<p class="muted">Reading ${plural(files.length, "file")}…</p>`;
    try { notionPics = await readNotionPics(files); } catch { notionPics = null; $("notionPicsPreview").innerHTML = ""; toast("Couldn't read that folder. Choose the unzipped Notion export folder."); return; }
    renderNotionPics();
  });
  async function importNotionPics() {
    const r = notionPics; if (!r || picsBusy) return;
    picsBusy = true;
    try { await importPicsRun(r); } finally { picsBusy = false; $("notionPics").disabled = false; }
  }
  async function importPicsRun(r) {
    const btn = $("notionPicsGo"), total = r.days.reduce((a, d) => a + d.add.length, 0);
    btn.disabled = true; $("notionPics").disabled = true;
    let done = 0, daysDone = 0, failed = false, full = false, slow = false;
    for (const d of r.days) {
      const ids = [], hashes = [];
      const have = dayPicHashes(S.days.get(d.date));
      for (const { file, hash } of d.add) {
        if (have.has(hash)) continue;
        btn.textContent = `Saving ${done + ids.length + 1} of ${total}…`;
        try { ids.push(await storeShot(file, d.date)); hashes.push(hash); have.add(hash); }
        catch (e) { failed = true; if (e?.code === "quota_or_state" || e?.name === "QuotaExceededError") { full = true; break; } if (e?.code === "rate_limited") { slow = true; break; } }
      }
      if (ids.length) {
        // The day takes the pictures and remembers them, so a second run skips them.
        const prev = S.days.get(d.date) || {};
        const shotHash = { ...(prev.shotHash || Object.fromEntries((prev.shotHashes || []).map((h, i) => [`old-${i}`, h]))) };
        ids.forEach((id, i) => { shotHash[id] = hashes[i]; });
        const day = { ...prev, id: d.date, date: d.date, screenshots: [...(prev.screenshots || []), ...ids], shotHash, updatedAt: Date.now() };
        delete day.shotHashes;
        try { await backend.put("days", day); done += ids.length; daysDone++; } catch { failed = true; }
        if (loadedDay === d.date) { dayShots = [...day.screenshots]; renderDayShots(); }
      }
      if (full || slow) break;
    }
    toast(`Added ${plural(done, "picture")} to ${plural(daysDone, "day")} in the journal.${full ? " Storage is full, so the rest weren't saved." : slow ? " The picture store asked to slow down. Wait a minute, then choose the folder again to add the rest." : failed ? " Some couldn't be saved; choose the folder again to finish, and the ones already in are skipped." : ""}`, 7000);
    picsBusy = false; notionPics = null; $("notionPics").value = ""; $("notionPics").disabled = false; renderNotionPics();
  }
  // Which import the page shows: your platform's file, your OneNote notebook, or a Notion export.''')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
