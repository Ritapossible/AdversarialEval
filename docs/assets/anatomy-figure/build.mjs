// AdversarialEval anatomy: a dimple-key test bench.
//
// Concept -> object (Anatomy skill, step 3): an evaluator must tell a sound security answer
// from one that is plausible but wrong in ONE decisive fact. Two dimple keys look identical
// except for one dimple (the decisive fact). A shortcut judge compares length and outline,
// and can't tell them apart. The lock checks every pin. The wrong key sits in the channel, and
// pin 4 rides proud of the shear line (the one lit part), so the lock refuses.
//
// Size: Figure (one mechanism, ~60 parts, SVG only).
// Truth (step 2): every readout and caption number comes from MODEL below or from the
// project's verified reports.
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import * as k from "../../kit/iso-kit.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------- model (truth first)
const MODEL = {
  pins: 6,
  correct: [1.2, 2.4, 0.8, 3.0, 1.6, 2.0], // dimple depths the lock is keyed to
  wrong: [1.2, 2.4, 0.8, 0.3, 1.6, 2.0],   // identical except dimple 4 (the decisive fact)
  shear: 15,                               // shear-line height
  poolEligible: 81,                         // eval/reports/2026-11-14-pool-upload.md
  shortcut: "≈50%",                         // shortcut judges on the pool material
};
const decisive = MODEL.correct.findIndex((d, i) => d !== MODEL.wrong[i]);
const proud = +(MODEL.correct[decisive] - MODEL.wrong[decisive]).toFixed(1);

// ---------------------------------------------------------------- world plan
const W = 1000, H = 400;
const PLATE = { x: -150, y: -66, w: 300, d: 132, r: 9 };
const PLATE_H = 12, FOOT_H = 5;
const BLADE_T = 4;                                  // key thickness
const PIN_X = [18, 30, 42, 54, 66, 78];             // pin chambers along x
const PIN_R = 3;
const CH_Y = 18;                                    // channel centre line
const RETAINER_Z = 42;
const TRAY = { x: -138, y: -56, w: 112, d: 38, r: 4 };
const TRAY_H = 4;

const P = k.fitProjection(
  [...k.boxCorners(PLATE, -PLATE_H - FOOT_H, 0), [10, CH_Y, RETAINER_Z + 6], [140, 18, 34]],
  W, H, { pad: 10, azimuth: 60 },
);
const at = (p) => k.iso(p, P);
const S = (paths, style) => k.solidSvg(paths, style);
const L = (d, style) => k.lineSvg(d, style);
const D = (points, style) => k.dotsSvg(points, style);
const slab = (plan, z, h, steps = 4, bevel = 0.5) => k.slabOf(plan, z, h, P, steps, bevel);
const cyl = (x, y, r, z, h, steps = 28, bevel = 0) => k.cylinder(x, y, r, z, h, P, steps, bevel);
const halo = (plan, z, h, blur = 9) => `<path class="iso-halo" d="${k.haloOf(plan, z, h, P)}" style="filter:blur(${blur}px)"/>`;
const byDepth = (pts) => [...pts].sort((a, b) => k.depthOf([a[0], a[1], 0], P) - k.depthOf([b[0], b[1], 0], P));
const V = k.towardViewer(P);

function vcoil(cx, cy, z0, z1, r, turns) {
  const count = Math.round(turns * 24);
  const back = [], front = [];
  let run = [], near = null;
  for (let i = 0; i <= count; i++) {
    const s = i / count, a = s * turns * Math.PI * 2;
    const pt = at([cx + r * Math.cos(a), cy + r * Math.sin(a), z0 + (z1 - z0) * s]);
    const facing = Math.cos(a) * V[0] + Math.sin(a) * V[1] > 0;
    if (near === null) near = facing;
    if (facing !== near) { run.push(pt); (near ? front : back).push(k.pathOf(run)); run = [pt]; near = facing; continue; }
    run.push(pt);
  }
  if (run.length > 1) (near ? front : back).push(k.pathOf(run));
  return { back: back.join(""), front: front.join("") };
}

// ---------------------------------------------------------------- base
function base() {
  const out = [halo(PLATE, -PLATE_H - FOOT_H, PLATE_H)];
  for (const [x, y] of byDepth(k.corners(PLATE, 24))) {
    out.push(S(cyl(x, y, 7.5, -PLATE_H - FOOT_H, 1.6), { tone: "lo" }));
    out.push(S(cyl(x, y, 5.8, -PLATE_H - FOOT_H + 1.6, FOOT_H - 1.6), { tone: "mid" }));
  }
  out.push(S(k.slabOf(PLATE, -PLATE_H, PLATE_H, P, 8, 1.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(PLATE, 5), 0, P), { tone: "lo" }));
  const screws = k.corners(PLATE, 11);
  out.push(L(screws.map(([x, y]) => k.ring(x, y, 2.3, 0, P, 16)).join(""), { tone: "lo" }));
  out.push(D(screws.map(([x, y]) => at([x, y, 0])), { size: 0.5 }));
  // ruler strip along the front edge
  const strip = { x: -46, y: PLATE.y + PLATE.d - 15, w: 184, d: 7, r: 1 };
  out.push(S(slab(strip, 0, 0.6, 3, 0), { tone: "lo", crease: "none" }));
  const t = k.topTicks(strip.x + 4, strip.x + strip.w - 4, 4, 5, strip.y + 0.8, 0.6, [2, 3.8], P);
  out.push(L(t.minor, { tone: "lo" }), L(t.major, { tone: "mid" }));
  out.push(D([at([strip.x + 2, strip.y + 3.5, 0.6]), at([strip.x + strip.w - 2, strip.y + 3.5, 0.6])], { size: 0.45 }));
  // label plate, front left: three rule lines stand for printed text
  const label = { x: 66, y: -56, w: 74, d: 22, r: 2 };
  out.push(S(slab(label, 0, 0.8, 3, 0.2), { tone: "mid", crease: "none" }));
  out.push(L([5, 10, 15].map((dy, i) => k.lineOnTop([label.x + 6, label.y + dy + 1], [label.x + (i === 2 ? 40 : 60), label.y + dy + 1], 0.8, P)).join(""), { tone: "lo", free: "both" }));
  out.push(D([at([label.x + 3, label.y + 3, 0.8]), at([label.x + label.w - 3, label.y + label.d - 3, 0.8])], { size: 0.45 }));
  return out.join("");
}

// ---------------------------------------------------------------- a dimple key lying flat
function key({ bowX, y, bladeTo, z, depths, lit = false }) {
  const out = [];
  const bow = { x: bowX - 13, y: y - 13, w: 26, d: 26, r: 11 };
  out.push(halo(bow, z, BLADE_T, 5));
  out.push(S(slab(bow, z, BLADE_T, 10, 0.6), { tone: "hi", crease: "lo" }));
  out.push(L(k.ring(bowX - 4, y, 3.6, z + BLADE_T, P, 24), { tone: "mid" }));       // key-ring hole
  out.push(L(k.planOutline(k.insetPlan(bow, 3), z + BLADE_T, P, 10), { tone: "faint" }));
  const shoulder = { x: bowX + 12, y: y - 7, w: 6, d: 14, r: 1 };
  out.push(S(slab(shoulder, z, BLADE_T, 3, 0.4), { tone: "hi", crease: "lo" }));
  const blade = { x: bowX + 17, y: y - 5, w: bladeTo - (bowX + 17), d: 10, r: 1.4 };
  out.push(S(slab(blade, z, BLADE_T, 3, 0.4), { tone: "hi", crease: "lo" }));
  out.push(L(k.lineOnTop([blade.x + 1, y - 3.2], [blade.x + blade.w - 2, y - 3.2], z + BLADE_T, P), { tone: "faint" }));
  // dimples: deeper dimple, wider cone
  const dx = PIN_X.map((px) => px - (MODEL.pinsOffset || 0));
  depths.forEach((d, i) => {
    const x = blade.x + 8 + i * 12;
    const top = z + BLADE_T;
    out.push(L(k.ring(x, y + 1.2, 1.1 + d * 0.75, top, P, 20), { tone: "mid" }));
    out.push(L(k.ring(x, y + 1.2, 0.5 + d * 0.3, top, P, 14), { tone: "lo" }));
  });
  return out.join("");
}

// ---------------------------------------------------------------- tray holding the sound key
function tray() {
  const out = [halo(TRAY, 0, TRAY_H, 6)];
  out.push(S(slab(TRAY, 0, TRAY_H, 4, 0.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(TRAY, 3), TRAY_H, P, 4), { tone: "faint" }));
  out.push(D(k.corners(TRAY, 4).map(([x, y]) => at([x, y, TRAY_H])), { size: 0.45 }));
  out.push(key({ bowX: TRAY.x + 18, y: TRAY.y + 20, bladeTo: TRAY.x + TRAY.w - 8, z: TRAY_H, depths: MODEL.correct }));
  return out.join("");
}

// ---------------------------------------------------------------- channel and lock body
const END_A = { x: 2, y: 2, w: 8, d: 32, r: 1.5 };
const END_B = { x: 94, y: 2, w: 8, d: 32, r: 1.5 };
const WALL_BACK = { x: 10, y: 2, w: 84, d: 5, r: 0.8 };
const WALL_FRONT = { x: 10, y: 29, w: 84, d: 5, r: 0.8 };
const RAIL_BACK = { x: -30, y: 6, w: 32, d: 4, r: 0.8 };
const RAIL_FRONT = { x: -30, y: 26, w: 32, d: 4, r: 0.8 };

function rails() {
  const out = [];
  for (const r of [RAIL_BACK]) {
    out.push(S(slab(r, 0, 6, 3, 0.4), { tone: "mid" }));
    out.push(D([at([r.x + 4, r.y + 2, 6]), at([r.x + r.w - 4, r.y + 2, 6])], { size: 0.4 }));
  }
  return out.join("");
}
function railFront() {
  const r = RAIL_FRONT;
  return S(slab(r, 0, 6, 3, 0.4), { tone: "mid" }) + D([at([r.x + 4, r.y + 2, 6]), at([r.x + r.w - 4, r.y + 2, 6])], { size: 0.4 })
    + L(k.topTicks(r.x + 6, r.x + r.w - 6, 6, 3, r.y + 0.6, 6, [1.2, 2.4], P).minor, { tone: "lo" });
}

function endBlock(b) {
  const out = [];
  out.push(S(slab(b, 0, RETAINER_Z, 4, 0.6), { tone: "mid" }));
  out.push(L(k.planOutline(k.insetPlan(b, 1.6), RETAINER_Z, P, 4), { tone: "faint" }));
  // engraved shear line wraps the block at the shear height
  out.push(L(k.sideSeam(b, MODEL.shear, P, 4), { tone: "lo" }));
  out.push(D([at([b.x + b.w / 2, b.y + 5, RETAINER_Z]), at([b.x + b.w / 2, b.y + b.d - 5, RETAINER_Z])], { size: 0.45 }));
  return out.join("");
}

function wall(w, height) {
  return S(slab(w, 0, height, 3, 0.4), { tone: "mid" }) + L(k.sideSeam(w, MODEL.shear, P, 3), { tone: "lo" });
}

const pinBottom = (i) => BLADE_T - MODEL.wrong[i];
const pinLength = (i) => MODEL.shear - BLADE_T + MODEL.correct[i];  // keyed for the sound key
function pinsAndSprings() {
  const out = [];
  const order = PIN_X.map((x, i) => i).sort((a, b) => k.depthOf([PIN_X[a], CH_Y, 0], P) - k.depthOf([PIN_X[b], CH_Y, 0], P));
  for (const i of order) {
    const x = PIN_X[i];
    const z0 = pinBottom(i), top = z0 + pinLength(i);
    const isLit = i === decisive;
    const spring = vcoil(x, CH_Y, top + 1.6, RETAINER_Z, 2.4, 5);
    out.push(L(spring.back, { tone: "lo" }));
    out.push(S(cyl(x, CH_Y, PIN_R, z0, top - z0, 24, 0.3), { tone: "hi", crease: "none", lit: isLit }));
    out.push(S(cyl(x, CH_Y, PIN_R + 0.5, top, 1.6, 24, 0.3), { tone: "hi", crease: "lo", lit: isLit })); // driver cap
    out.push(L(spring.front, { tone: isLit ? "mid" : "mid" }));
  }
  return out.join("");
}

function retainer() {
  const bar = { x: 2, y: CH_Y - 6, w: 100, d: 12, r: 1.4 };
  const out = [S(slab(bar, RETAINER_Z, 4, 3, 0.5), { tone: "mid" })];
  out.push(D(PIN_X.map((x) => at([x, CH_Y, RETAINER_Z + 4])), { size: 0.45 }));
  out.push(L(PIN_X.map((x) => k.ring(x, CH_Y, 2.2, RETAINER_Z + 4, P, 16)).join(""), { tone: "lo" }));
  return out.join("");
}

// ---------------------------------------------------------------- turn knob (refuses)
const HOUSING = { x: 102, y: 0, w: 40, d: 36, r: 3 };
function knob() {
  const out = [];
  out.push(S(slab(HOUSING, 0, 22, 5, 0.6), { tone: "mid" }));
  const c = [HOUSING.x + 20, HOUSING.y + 18];
  const ticks = k.radialTicks(c[0], c[1], 13.5, 24, 6, 22, [1.2, 2.6], P);
  out.push(L(ticks.minor, { tone: "lo" }), L(ticks.major, { tone: "mid" }));
  out.push(L(k.ring(c[0], c[1], 11.4, 22, P, 48), { tone: "faint" }));
  out.push(S(cyl(c[0], c[1], 9, 22, 7, 40, 0.5), { tone: "hi", crease: "lo" }));
  out.push(L(k.knurl(c[0], c[1], 9, 23, 29, 54, P, 0.3), { tone: "lo" }));
  out.push(S(slab({ x: c[0] - 1.6, y: c[1] - 8, w: 3.2, d: 16, r: 1 }, 29, 2.2, 3, 0.3), { tone: "hi", crease: "lo" })); // grip bar, at zero
  out.push(D([at([c[0], c[1], 31.2])], { size: 0.55, tone: "hi" }));
  out.push(D([at([HOUSING.x + 4, HOUSING.y + 4, 22]), at([HOUSING.x + 36, HOUSING.y + 4, 22]), at([HOUSING.x + 36, HOUSING.y + 32, 22]), at([HOUSING.x + 4, HOUSING.y + 32, 22])], { size: 0.45 }));
  out.push(L(k.sideSeam(HOUSING, 8, P, 5), { tone: "faint" }));
  return out.join("");
}

// ---------------------------------------------------------------- assemble back to front
const svg = k.figureSvg({
  width: W,
  height: H,
  label:
    "A dimple-key test bench. Two keys look identical but for one dimple. The wrong key sits in the channel under six spring-loaded pins; pin 4 rides proud of the engraved shear line, so the turn knob stays locked. The sound key rests in a tray.",
  body: [
    base(),
    tray(),
    rails(),
    endBlock(END_A),
    wall(WALL_BACK, 20),
    key({ bowX: -50, y: CH_Y, bladeTo: 96, z: 0, depths: MODEL.wrong }),
    pinsAndSprings(),
    wall(WALL_FRONT, 9),
    railFront(),
    endBlock(END_B),
    retainer(),
    knob(),
  ],
});

// ---------------------------------------------------------------- page sized for X (16:9)
const PALETTE = `
.iso[data-theme="light"]{
  --anatomy-page:#f7f6ff;--anatomy-card:#ffffff;--anatomy-text:#4a4566;--anatomy-strong:#1f1b33;--anatomy-muted:#7d77a0;
  --anatomy-paper:#ffffff;--anatomy-face:#f6f4ff;--anatomy-top:#f6f4ff;
  --anatomy-shade-0:#c9c0ef;--anatomy-shade-1:#d6cff5;--anatomy-shade-2:#e2ddf9;--anatomy-shade-3:#eceafe;
  --anatomy-lit-top:#c4b2ff;--anatomy-lit-shade:#a98ff5;
  --anatomy-hi:#2b2146;--anatomy-mid:#9370db;--anatomy-lo:#b6a5e6;--anatomy-faint:#ddd5f6;--anatomy-lit:#5b2fc9;
  --anatomy-halo:#9370db;--anatomy-halo-opacity:.22;--anatomy-dot:#4b3a85;
}`;
const swatch = (color, w = 1.4) => `<svg viewBox="0 0 18 10"><path d="M1 5 L9 1 L17 5 L9 9 Z" style="fill:none;stroke:${color};stroke-width:${w};stroke-linejoin:round"/></svg>`;
const page = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>AdversarialEval anatomy</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@1&family=JetBrains+Mono:wght@500;700&display=swap">
<style>${k.ISO_CSS}${PALETTE}
*{box-sizing:border-box;margin:0}
body{width:1600px;height:900px;overflow:hidden;background:var(--anatomy-page);font-family:"Instrument Sans",system-ui,sans-serif;color:var(--anatomy-text)}
.wrap{height:900px;padding:22px 26px 20px;display:grid;grid-template-rows:auto 1fr auto auto;gap:14px}
header{display:flex;justify-content:space-between;align-items:center}
.brand{display:flex;align-items:center;gap:14px}
.mark{width:46px;height:46px;border:2px solid #4b3a85;border-radius:12px;display:grid;place-items:center;background:#fff}
.name{font:600 38px/1 "Instrument Sans",sans-serif;letter-spacing:-.02em;color:var(--anatomy-strong)}
.name i{font:italic 400 42px/1 "Instrument Serif",serif;color:#5b2fc9;letter-spacing:0}
.tagline{font-size:21px;color:var(--anatomy-muted)}
.tagline b{color:var(--anatomy-strong);font-weight:600}
.card .iso-plate{height:100%;padding:44px 26px;border-radius:18px;box-shadow:0 0 0 1.5px #ddd5f6, 0 20px 50px -34px rgba(91,47,201,.4);display:flex;align-items:center}
.card{min-height:0}
.card .iso-plate>.iso-stage,.card .iso-plate>div:not(.iso-plate-corners){width:100%}
.card .iso-plate-corner{font-size:15px}
.card .iso-plate-corner[data-corner="title"]{color:#4b3a85}
.card .iso-figure{margin:0;height:100%}
.legend{display:flex;gap:34px;font-size:18px;color:var(--anatomy-text);padding:0 6px}
.legend span{display:inline-flex;align-items:center;gap:9px}
.legend svg{width:20px;height:12px}
.foot{display:flex;justify-content:space-between;font:500 16px/1 "JetBrains Mono",monospace;color:var(--anatomy-muted);padding:0 6px}
.foot b{color:#4b3a85;font-weight:700}
</style></head>
<body class="iso" data-theme="light"><div class="wrap">
<header>
  <div class="brand"><div class="mark"><svg width="26" height="26" viewBox="0 0 26 26"><path d="M4 8h10M4 13h7M4 18h10" stroke="#4b3a85" stroke-width="2.2" stroke-linecap="round"/><circle cx="19" cy="13" r="4" fill="#5b2fc9"/></svg></div>
  <div class="name">Adversarial<i>Eval</i></div></div>
  <div class="tagline">Rewards security answers that <b>survive scrutiny</b>, not ones that sound right</div>
</header>
<div class="card">${k.plateHtml({
  fig: "Fig 1",
  title: "Anatomy of an AdversarialEval check",
  hint: "Two keys, one dimple apart",
  readout: `pin ${decisive + 1} proud ${proud} · wrong key refused`,
  keys: [], caption: "",
  body: `<div class="iso-stage">${svg}</div>`,
})}</div>
<div class="legend">
  <span>${swatch("#5b2fc9", 1.8)} Pin ${decisive + 1}: the one decisive fact, checked</span>
  <span>${swatch("#9370db")} Tray key: the sound answer</span>
  <span>${swatch("#b6a5e6")} Lock key: plausible, one fact wrong</span>
</div>
<div class="foot"><span>${MODEL.poolEligible} pairs live in the Telegraph testnet pool · shortcut judges ${MODEL.shortcut}</span><b>github.com/Ritapossible/AdversarialEval</b></div>
</div></body></html>`;
writeFileSync(join(HERE, "adversarialeval-anatomy.html"), page);
console.log("wrote adversarialeval-anatomy.html; decisive pin", decisive + 1, "proud", proud);
