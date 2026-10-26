  // screenshots: image files in the screenshots/ folder; a trade or journal day keeps their file names
  const shotUrls = new Map();
  let shotsAdded = new Set(), shotsOriginal = [], shotSession = 0;
  // A file is only deleted when no saved trade or journal day still points at it.
  const shotInUse = (name) => [...S.trades.values(), ...S.days.values()].some((t) => (t.screenshots || []).includes(name));
  function dropShots(names) { names.forEach((n) => { if (shotsDir && !shotInUse(n)) { removeFile(shotsDir, n); shotUrls.delete(n); } }); }
  async function shotSrc(name) {
    if (shotUrls.has(name)) return shotUrls.get(name);
    try { const f = await (await shotsDir.getFileHandle(name)).getFile(); const u = URL.createObjectURL(f); shotUrls.set(name, u); return u; }
    catch { return ""; }
  }
  function fillShots(el, names, rm) {
    el.classList.toggle("many", names.length > 1);
    el.innerHTML = names.map((name, i) => `<div class="shot" data-shot="${esc(name)}"><img alt="Chart screenshot ${i + 1}" data-i="${i}" hidden><span class="calc shot-missing" hidden>Image file not found</span><button type="button" ${rm}="${i}" aria-label="Remove screenshot">Remove</button></div>`).join("");
    el.querySelectorAll("[data-shot]").forEach(async (tile) => {
      const src = shotsDir ? await shotSrc(tile.dataset.shot) : "";
      const img = tile.querySelector("img");
      if (src) { img.src = src; img.hidden = false; } else tile.querySelector(".shot-missing").hidden = false;
    });
  }
  const renderShots = () => fillShots($("tShots"), formShots, "data-rm");
  const renderDayShots = () => fillShots($("jShots"), dayShots, "data-rm-day");
  // Full-screen viewer: click outside or press Esc to close, arrows to move between charts.
  let lbList = [], lbAt = 0;
  async function openLightbox(names, i) {
    lbList = await Promise.all(names.map((n) => shotSrc(n)));
    lbAt = i; showLb(); $("lightbox").hidden = false; $("lbClose").focus();
  }
  function showLb() {
    if (lbList[lbAt]) $("lightboxImg").src = lbList[lbAt]; else $("lightboxImg").removeAttribute("src");
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
    const img = e.target.closest("img[data-i]"); if (img) openLightbox(formShots, +img.dataset.i);
  });
  $("jShots").addEventListener("click", (e) => {
    const rm = e.target.closest("[data-rm-day]");
    if (rm) { if (rm.dataset.armed) removeDayShot(+rm.dataset.rmDay); else { rm.dataset.armed = "1"; rm.textContent = "Click again to remove"; setTimeout(() => { if (rm.isConnected) { delete rm.dataset.armed; rm.textContent = "Remove"; } }, 3000); } return; }
    const img = e.target.closest("img[data-i]"); if (img) openLightbox(dayShots, +img.dataset.i);
  });
  const SHOT_EXT = { "image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "image/gif": "gif" };
  const shotName = (date, label, type) => `${date}-${(label || "chart").toUpperCase().replace(/[^A-Z0-9]+/g, "") || "CHART"}-${uid()}.${SHOT_EXT[type]}`;
  const shotWriteError = (e) => toast(e?.name === "QuotaExceededError" ? "Your disk is full." : "Couldn't save the screenshot to your folder.");
  async function uploadShots(files) {
    if (!shotsDir) return;
    const imgs = [...files].filter((f) => SHOT_EXT[f.type]);
    if (!imgs.length) { toast("Use a PNG, JPG, WebP or GIF image."); return; }
    const sess = shotSession;
    for (const f of imgs) {
      const name = shotName($("tDate").value || today(), $("tInstrument").value.trim(), f.type);
      try {
        await writeFile(shotsDir, name, f);
        if (sess !== shotSession) { removeFile(shotsDir, name); return; } // the editor closed while this was saving
        formShots.push(name); shotsAdded.add(name); renderShots(); toast("Screenshot added. Save the trade to keep it."); }
      catch (e) { shotWriteError(e); }
    }
  }
  // Journal charts are saved with the day as soon as they're added, so nothing is lost if you move to another day.
  async function addDayShots(files) {
    if (!shotsDir) return;
    const imgs = [...files].filter((f) => SHOT_EXT[f.type]);
    if (!imgs.length) { toast("Use a PNG, JPG, WebP or GIF image."); return; }
    const date = loadedDay || today();
    for (const f of imgs) {
      const name = shotName(date, "day", f.type);
      try { await writeFile(shotsDir, name, f); } catch (e) { shotWriteError(e); continue; }
      if (loadedDay === date) { dayShots.push(name); renderDayShots(); }
      const list = loadedDay === date ? dayShots : [...((S.days.get(date) || {}).screenshots || []), name];
      await saveDayShots(date, list, "Screenshot saved");
    }
  }
  // For the old-journal picture import: one file saved to the screenshots folder, its name returned.
  const canStoreShots = () => !!shotsDir;
  async function storeShot(file, date) {
    if (!shotsDir || !SHOT_EXT[file.type]) throw new Error("no_store");
    const name = shotName(date, "notion", file.type);
    await writeFile(shotsDir, name, file);
    return name;
  }
  function removeDayShot(i) {
    const date = loadedDay; if (!date) return;
    const [name] = dayShots.splice(i, 1); renderDayShots();
    saveDayShots(date, dayShots, "Screenshot removed").then((ok) => { if (ok) dropShots([name]); else pendingDrops.push(name); });
  }
  // Called once the trade is saved: files the trade no longer uses are deleted from the folder.
  function commitShots(removed) { dropShots(removed); }
  // Called when the editor closes without saving: images added in this edit are deleted again.
  function discardShots() {
    shotSession++;
    dropShots([...shotsAdded]);
    shotsAdded = new Set();
  }
  $("shotFile").addEventListener("change", () => { uploadShots($("shotFile").files); $("shotFile").value = ""; });
  $("jShotFile").addEventListener("change", () => { addDayShots($("jShotFile").files); $("jShotFile").value = ""; });
  [["shotDrop", uploadShots], ["jShotDrop", addDayShots]].forEach(([id, fn]) => {
    const drop = $(id);
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); fn(e.dataTransfer.files); });
  });
  document.addEventListener("paste", (e) => {
    if (!shotsDir) return;
    const files = [...(e.clipboardData?.files || [])].filter((f) => f.type.startsWith("image/"));
    if (!files.length) return;
    if (e.target.closest?.("input, textarea") && e.clipboardData.getData("text/plain")) return; // pasting text into a box stays a text paste
    if (!$("view-editor").hidden) { e.preventDefault(); uploadShots(files); }
    else if (!$("view-journal").hidden && !$("jDaily").hidden) { e.preventDefault(); addDayShots(files); }
  });
