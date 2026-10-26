#!/usr/bin/env python3
"""v20 -> v21 (PC): a trade shows the charts saved on its day in the journal (the old OneNote/Notion pictures live there)."""
import pathlib, sys

SRC = pathlib.Path(sys.argv[1]); OUT = pathlib.Path(sys.argv[2])
s = SRC.read_text()

def rep(a, b, n=1):
    global s
    c = s.count(a)
    if c != n:
        sys.exit(f"expected {n} match(es), found {c}: {a[:90]!r}")
    s = s.replace(a, b)

rep('''              <div class="shots" id="tShots"></div>''', '''              <div class="shots" id="tShots"></div>
              <div class="stack" id="tDayShotsWrap" hidden><span class="flabel">From this day in the journal</span><div class="shots" id="tDayShots"></div></div>''')

# Trades list: the picture mark also shows when the trade's day has charts.
rep('''shots = (t.screenshots || []).length ? ` <span class="muted" title="Has screenshots">▣</span>` : "";''',
    '''shots = (t.screenshots || []).length || (S.days.get(t.date)?.screenshots || []).length ? ` <span class="muted" title="Has screenshots">▣</span>` : "";''')

rep('''    discardShots(); formShots = [...(t?.screenshots || [])]; shotsOriginal = [...formShots]; renderShots();''',
    '''    discardShots(); formShots = [...(t?.screenshots || [])]; shotsOriginal = [...formShots]; renderShots(); renderTradeDayShots();''')
rep('''  $("tDate").addEventListener("change", updateMarket);''', '''  $("tDate").addEventListener("change", () => { updateMarket(); renderTradeDayShots(); });''')

rep('''  const renderShots = () => fillShots($("tShots"), formShots, "data-rm");''', '''  const renderShots = () => fillShots($("tShots"), formShots, "data-rm");
  // The day's journal charts, shown on the trade to look at. They stay on the day: nothing here can remove them.
  let tradeDayShots = [];
  function renderTradeDayShots() {
    const d = $("tDate").value;
    tradeDayShots = d ? [...(S.days.get(d)?.screenshots || [])] : [];
    $("tDayShotsWrap").hidden = !tradeDayShots.length;
    fillShots($("tDayShots"), tradeDayShots, "data-day-view");
    $("tDayShots").querySelectorAll("button").forEach((b) => b.remove());
  }
  $("tDayShots").addEventListener("click", (e) => { const img = e.target.closest("img[data-i]"); if (img) openLightbox(tradeDayShots, +img.dataset.i); });''')

OUT.write_text(s)
print("wrote", OUT, len(s), "bytes")
