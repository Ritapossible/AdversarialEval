#!/usr/bin/env python3
"""Build a phone-friendly review page for the pool candidates (audit item U2).

    python tools/review_page.py            # -> data/private/review/review.html (git-ignored)
    python tools/review_pool.py apply-code --reviewer "<name>" --code "<code from the page>"

The page shows one pair at a time with Approve / Reject buttons and an optional note, keeps
progress in the browser where it can, and gives the reviewer a short decision code to paste
back. The code is applied with tools/review_pool.py apply-code, which records the reviewer
by name. It lives under data/private/ because it contains the pool rows: never publish it.
"""
from __future__ import annotations

import csv
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT  # noqa: E402

SHEET = ROOT / "data" / "private" / "review" / "pool_review.csv"
OUT = ROOT / "data" / "private" / "review" / "review.html"

KIND_HELP = {
    "F2-in": ("The version IS affected; the wrong answer says it's safe.",
              "Open the source link. Check that the pinned version is inside the advisory's affected range, "
              "and that the fix version in the correct answer matches the advisory's patched version."),
    "F2-out": ("The version is already patched; the wrong answer says it's vulnerable.",
               "Open the source link. Check that the advisory's patched version is the pinned version or lower."),
    "F7": ("Same facts, but the wrong answer's fields contradict each other.",
           "Check that the correct answer's verdict, count and issue list agree, and the wrong one's don't."),
    "F1": ("The wrong answer cites a real advisory for a different package.",
           "Open the source link and check it is the advisory the question describes."),
}


def main() -> int:
    rows = list(csv.DictReader(SHEET.open(newline="")))
    data = [{"id": r["row_id"][:12], "kind": r["kind"], "src": r["source_url"], "prompt": r["prompt"],
             "good": r["chosen"], "bad": r["rejected"], "flaw": r["flaw_note"]} for r in rows]
    page = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")) \
                   .replace("__HELP__", json.dumps(KIND_HELP).replace("</", "<\\/")) \
                   .replace("__N__", html.escape(str(len(data))))
    OUT.write_text(page)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(data)} pairs)")
    return 0


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Pool review</title>
<style>
:root { --bg:#f2f4f7; --card:#fff; --ink:#17212b; --muted:#5a6573; --line:#d6dce3;
  --good:#1d7550; --good-soft:#e3f3ea; --bad:#b42318; --bad-soft:#fde8e6; --accent:#2d4bd0;
  --mono: ui-monospace, Menlo, Consolas, monospace; }
@media (prefers-color-scheme: dark) { :root { --bg:#10151b; --card:#18202a; --ink:#e6ebf0; --muted:#98a3b0;
  --line:#2b3644; --good:#5cc79b; --good-soft:#12301f; --bad:#f8766c; --bad-soft:#3a1714; --accent:#8aa0ff; color-scheme: dark; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.5 system-ui, -apple-system, Segoe UI, sans-serif;
  padding: 12px max(14px, env(safe-area-inset-left)) 120px max(14px, env(safe-area-inset-right)); }
.wrap { max-width: 760px; margin: 0 auto; display: grid; gap: 12px; }
h1 { font-size: 1.3rem; margin: 4px 0 0; }
.muted { color: var(--muted); font-size: .9rem; margin: 0; }
.bar { display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; }
.prog { font: 600 .85rem var(--mono); }
.card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; display:grid; gap:10px; }
.lbl { font: 600 .72rem var(--mono); letter-spacing:.06em; text-transform:uppercase; color:var(--muted); }
pre { margin:0; white-space:pre-wrap; overflow-wrap:anywhere; font: .88rem/1.5 var(--mono); }
.ans { border-radius:10px; padding:10px 12px; border:2px solid; }
.ans.good { border-color:var(--good); background:var(--good-soft); }
.ans.bad { border-color:var(--bad); background:var(--bad-soft); }
.help { font-size:.92rem; }
a { color: var(--accent); overflow-wrap:anywhere; }
textarea, input { width:100%; font: 15px system-ui, sans-serif; padding:8px; border-radius:8px; border:1px solid var(--line); background:var(--card); color:var(--ink); }
.btns { display:grid; grid-template-columns: 1fr 1fr; gap:10px; }
button { font: 600 1rem system-ui, sans-serif; padding: 14px; border-radius: 10px; border: 0; cursor: pointer; }
.approve { background: var(--good); color: #fff; } .reject { background: var(--bad); color: #fff; }
.nav { display:flex; gap:8px; } .nav button { flex:1; background: var(--line); color: var(--ink); padding:10px; }
.chip { font: 600 .8rem var(--mono); padding: 4px 8px; border-radius: 999px; }
.chip.a { background: var(--good-soft); color: var(--good); } .chip.r { background: var(--bad-soft); color: var(--bad); }
.done { display:grid; gap:10px; }
</style></head><body><div class="wrap">
<h1>Pool review: __N__ pairs</h1>
<p class="muted">For each pair: is the green answer correct, and is the red answer wrong for the stated reason? Approve only if both hold and nothing is misleading. Unsure? Reject with a note. Your progress is kept in this browser where possible, and the code at the bottom always holds every decision so far.</p>
<div class="bar"><span class="prog" id="prog"></span><span id="state"></span></div>
<div class="card" id="card">
  <div><div class="lbl" id="kind"></div><div class="help" id="help"></div></div>
  <div><div class="lbl">Question</div><pre id="prompt"></pre></div>
  <div class="ans good"><div class="lbl">Answer marked CORRECT</div><pre id="good"></pre></div>
  <div class="ans bad"><div class="lbl">Answer marked WRONG</div><pre id="bad"></pre></div>
  <div><div class="lbl">Why the wrong answer is wrong</div><div id="flaw"></div></div>
  <div><div class="lbl">Source to check</div><a id="src" target="_blank" rel="noopener"></a><div class="muted" id="check"></div></div>
  <input id="note" placeholder="Note (optional; say why if rejecting)">
  <div class="btns"><button class="approve" id="ok">Approve</button><button class="reject" id="no">Reject</button></div>
  <div class="nav"><button id="prev">← Back</button><button id="skip">Skip →</button></div>
</div>
<div class="card done">
  <div class="lbl">Your decision code: copy everything below and paste it to Claude</div>
  <textarea id="code" rows="5" readonly></textarea>
  <button id="copy" style="background:var(--ink);color:var(--bg)">Copy code</button>
  <p class="muted" id="copied"></p>
</div>
</div>
<script>
var D = __DATA__, H = __HELP__, KEY = "pool-review-v1", dec = {}, i = 0;
try { dec = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
function $(x){ return document.getElementById(x); }
function save(){ try { localStorage.setItem(KEY, JSON.stringify(dec)); } catch (e) {} code(); }
function code(){
  var parts = [];
  D.forEach(function(r){ var d = dec[r.id]; if (d) parts.push(r.id + ":" + d.v + (d.n ? ":" + d.n.replace(/[;\n]/g, ",") : "")); });
  $("code").value = parts.join(";");
  var a = 0, r = 0; for (var k in dec) { if (dec[k].v === "a") a++; else r++; }
  $("state").innerHTML = '<span class="chip a">' + a + ' approved</span> <span class="chip r">' + r + ' rejected</span>';
}
function show(){
  var r = D[i], d = dec[r.id];
  $("prog").textContent = "Pair " + (i + 1) + " of " + D.length + (d ? (d.v === "a" ? " · approved" : " · rejected") : "");
  $("kind").textContent = r.kind; $("help").textContent = (H[r.kind] || ["", ""])[0];
  $("check").textContent = (H[r.kind] || ["", ""])[1];
  $("prompt").textContent = r.prompt; $("good").textContent = r.good; $("bad").textContent = r.bad;
  $("flaw").textContent = r.flaw; $("src").href = r.src; $("src").textContent = r.src;
  $("note").value = d && d.n ? d.n : "";
  window.scrollTo(0, 0);
}
function decide(v){
  dec[D[i].id] = { v: v, n: $("note").value.trim() }; save();
  var nxt = -1; for (var k = 1; k <= D.length; k++) { var j = (i + k) % D.length; if (!dec[D[j].id]) { nxt = j; break; } }
  if (nxt >= 0) { i = nxt; show(); } else { $("prog").textContent = "All " + D.length + " pairs decided. Copy the code below."; $("code").scrollIntoView(); }
}
$("ok").onclick = function(){ decide("a"); };
$("no").onclick = function(){ decide("r"); };
$("prev").onclick = function(){ i = (i - 1 + D.length) % D.length; show(); };
$("skip").onclick = function(){ i = (i + 1) % D.length; show(); };
$("copy").onclick = function(){
  var t = $("code").value;
  function sel(){ $("code").select(); $("copied").textContent = "Selected: copy it with your phone's Copy option."; }
  try { navigator.clipboard.writeText(t).then(function(){ $("copied").textContent = "Copied."; }, sel); } catch (e) { sel(); }
};
for (var k = 0; k < D.length; k++) { if (!dec[D[k].id]) { i = k; break; } }
code(); show();
</script></body></html>"""

if __name__ == "__main__":
    sys.exit(main())
