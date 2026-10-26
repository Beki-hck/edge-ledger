  // ---------- reading .zip files (the export from Edge Ledger online) ----------
  async function readZip(blob) {
    const buf = new Uint8Array(await blob.arrayBuffer()), dv = new DataView(buf.buffer);
    let eocd = -1;
    for (let i = buf.length - 22; i >= Math.max(0, buf.length - 65557); i--) if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    if (eocd < 0) throw new Error("not a zip");
    const count = dv.getUint16(eocd + 10, true);
    let p = dv.getUint32(eocd + 16, true);
    const dec = new TextDecoder(), out = new Map();
    for (let n = 0; n < count; n++) {
      if (dv.getUint32(p, true) !== 0x02014b50) throw new Error("bad zip");
      const method = dv.getUint16(p + 10, true), csize = dv.getUint32(p + 20, true), nlen = dv.getUint16(p + 28, true), xlen = dv.getUint16(p + 30, true), clen = dv.getUint16(p + 32, true), off = dv.getUint32(p + 42, true);
      const name = dec.decode(buf.subarray(p + 46, p + 46 + nlen));
      p += 46 + nlen + xlen + clen;
      if (name.endsWith("/")) continue;
      const start = off + 30 + dv.getUint16(off + 26, true) + dv.getUint16(off + 28, true);
      const raw = buf.subarray(start, start + csize);
      out.set(name, async () => {
        if (method === 0) return new Blob([raw]);
        if (method === 8) return new Response(new Blob([raw]).stream().pipeThrough(new DecompressionStream("deflate-raw"))).blob();
        throw new Error("unsupported zip compression");
      });
    }
    return out;
  }
  // Brings in a backup (.json) or an export from Edge Ledger online (.zip, with screenshots). Existing entries with the same id are updated.
  async function importBackup(file) {
    let j, entries = null;
    if (/\.zip$/i.test(file.name) || file.type.includes("zip")) {
      entries = await readZip(file);
      const main = entries.get("edge-ledger-export.json") || entries.get("journal.json");
      if (!main) throw new Error("bad");
      j = JSON.parse(await (await main()).text());
    } else j = JSON.parse(await file.text());
    if (!j || !Array.isArray(j.trades)) throw new Error("bad");
    if (!Array.isArray(j.accounts) && j.settings?.startBalance) j.accounts = [{ ...ACCOUNT_DEFAULTS, ...pickAccount(j.settings), id: "main" }];
    // Screenshots: write each image file, then point trades and journal days at the file names.
    const rename = {};
    let shots = 0;
    if (entries) {
      for (const [path, get] of entries) {
        const m = path.match(/^screenshots\/([^/]+\.(png|jpe?g|webp|gif))$/i);
        if (!m) continue;
        await writeFile(shotsDir, m[1], await get()); shotUrls.delete(m[1]); shots++;
        rename[m[1].replace(/\.[^.]+$/, "")] = m[1];
      }
      Object.entries(j.screenshotFiles || {}).forEach(([id, p]) => { const f = String(p).split("/").pop(); if (f) rename[id] = f; });
    }
    const count = {};
    for (const c of COLLS) for (const x of Array.isArray(j[c]) ? j[c] : []) {
      if (!x || typeof x !== "object") continue;
      if (c === "days" && !x.id) x.id = x.date;
      if (c === "days" && !x.date) x.date = x.id;
      if (!x.id) continue;
      if (c === "trades" || c === "days") x.screenshots = (Array.isArray(x.screenshots) ? x.screenshots : []).map((s) => rename[s] || s);
      S[c].set(x.id, x);
      count[c] = (count[c] || 0) + 1;
    }
    if (j.settings && typeof j.settings === "object") {
      const { emotions, mistakes, tags, news, activeAccountId, name } = j.settings;
      S.settings = { ...S.settings, ...(emotions && { emotions }), ...(mistakes && { mistakes }), ...(tags && { tags }), ...(news && { news }), ...(activeAccountId && { activeAccountId }), ...(name && !S.settings.name && { name }) };
    }
    let news = 0;
    for (const d of Array.isArray(j.market) ? j.market : []) {
      if (d && typeof d === "object" && /^\d{4}-\d{2}-\d{2}$/.test(d.date || "") && !S.market.has(d.date)) { await saveNewsDay(cleanNewsDoc(d, d.date, d)); news++; }
    }
    await queueSave(); render();
    return { trades: count.trades || 0, shots, news };
  }
