// Dependency Guard connector: one paid Telegraph answer per package, a free check, a decision,
// then the evidence goes to the Dependency.Guard Mind, which writes the report and remembers it.
//
//   node mind/connector/guard.mjs --mind <mindId> pkg:npm/minimist@1.2.5 pkg:npm/minimist@1.2.8
//   node mind/connector/guard.mjs --mind <mindId> --manifest package.json
//   ... --no-mind          run the checks only, don't message the Mind
//   ... --max-spend 0.10   stop buying once this much USD has been spent (default 0.10)
//
// Keys are never read from the repo: the session's network proxy adds the Anjoman key for
// backend.telegraphprotocol.com and the Minds Builder key for api.build.hellominds.ai. Elsewhere,
// set ANJOMAN_API_KEY and MINDS_BUILDER_API_KEY in the environment.
//
// Policy (Telegraph's guidance: no 3x buying by default): ask the ranked route once per package.
// Re-ask one different provider only when the free check proves the first answer wrong or it has
// no usable verdict. Every run is written to mind/evidence/<timestamp>.json with receipts.
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..", "..");
const ANJOMAN = "https://backend.telegraphprotocol.com";
const INTENT = "SECURITY_REVIEW_GENERAL";
// Re-ask target: the most accurate miner in our benchmark (rounds 2 to 4, 83% pooled).
const FALLBACK_MINER = { id: "20260828", name: "a1-preflight" };
const VULNERABLE = new Set(["Insecure", "Needs changes"]);

const { values: opt, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    mind: { type: "string" },
    manifest: { type: "string" },
    "no-mind": { type: "boolean", default: false },
    "max-spend": { type: "string", default: "0.10" },
    alias: { type: "string", default: "dependency-guard" },
  },
});

// ---------- inputs ----------
function purlsFromManifest(path) {
  const text = readFileSync(path, "utf8");
  if (path.endsWith(".json")) {
    const pj = JSON.parse(text);
    const deps = { ...(pj.dependencies || {}), ...(pj.devDependencies || {}) };
    return Object.entries(deps).flatMap(([n, v]) => {
      const m = String(v).match(/^[\^~=v]*(\d+\.\d+\.\d+[\w.+-]*)$/);
      return m ? [`pkg:npm/${n}@${m[1]}`] : [];  // ranges without one exact version are skipped
    });
  }
  return text.split("\n").flatMap((l) => {
    const m = l.trim().match(/^([A-Za-z0-9_.\-]+)==([\w.+-]+)$/);
    return m ? [`pkg:pypi/${m[1].toLowerCase()}@${m[2]}`] : [];
  });
}
const targets = [...positionals, ...(opt.manifest ? purlsFromManifest(opt.manifest) : [])];
if (!targets.length) throw new Error("give purls or --manifest");
for (const t of targets) if (!/^pkg:[a-z]+\/.+@[^@\s]+$/.test(t)) throw new Error(`not an exact purl: ${t}`);
const maxSpend = Number(opt["max-spend"]);

// ---------- Telegraph through Anjoman ----------
const anjomanHeaders = { "Content-Type": "application/json",
  ...(process.env.ANJOMAN_API_KEY ? { Authorization: `Bearer ${process.env.ANJOMAN_API_KEY}` } : {}) };

async function ask(target, minerId) {
  const url = minerId ? `${ANJOMAN}/engine/ask/${minerId}` : `${ANJOMAN}/engine/ask`;
  const started = Date.now();
  try {
    const res = await fetch(url, { method: "POST", headers: anjomanHeaders, signal: AbortSignal.timeout(120_000),
      body: JSON.stringify({ intent: INTENT, params: { target } }) });
    const body = await res.json().catch(() => ({}));
    const r = body.result || {};
    return { http: res.status, ms: Date.now() - started, miner: r.miner_name ?? null, miner_id: r.miner_id ?? null,
      result: r.result ?? null, cost_usd: r.cost_usd_total ?? r.cost_usd ?? 0, receipt: body.receipt ?? null,
      signal_hash: r.signal_hash ?? null, error: body.error ?? body.message ?? null };
  } catch (e) {
    return { http: null, ms: Date.now() - started, result: null, cost_usd: 0, receipt: null, error: String(e?.message || e) };
  }
}

// ---------- the free check ----------
function check(target, result) {
  const p = spawnSync("python3", ["-m", "verify", "--target", target], { cwd: ROOT, input: JSON.stringify(result ?? null), encoding: "utf8" });
  if (p.status !== 0) return { label: "unavailable", checks: [{ name: "verify", status: "skip", detail: (p.stderr || "").slice(-300) }] };
  return JSON.parse(p.stdout);
}

function decide(label, result) {
  const vulnerable = VULNERABLE.has(result?.verdict) && (result?.vulnerability_count ?? 0) >= 1;
  if (label === "verified") return vulnerable ? "BLOCK" : "PASS";
  if (label === "unconfirmed") return "FLAG";
  return null;  // contradicted, invalid or unavailable: re-ask once, then FLAG
}

// ---------- run ----------
const run = { at: new Date().toISOString(), intent: INTENT, policy: "one ranked ask; re-ask one other provider only if the free check proves it wrong",
  max_spend_usd: maxSpend, packages: [] };
let spent = 0;
for (const target of targets) {
  const pkg = { target, attempts: [] };
  run.packages.push(pkg);
  if (spent + 0.01 > maxSpend + 1e-9) { pkg.decision = "NOT CHECKED"; pkg.reason = `spending cap $${maxSpend} reached`; continue; }
  let a = await ask(target);
  spent += Number(a.cost_usd) || 0;
  let v = check(target, a.result);
  pkg.attempts.push({ ...a, label: v.label, checks: v.checks });
  let d = decide(v.label, a.result);
  if (!d && spent + 0.01 <= maxSpend + 1e-9 && String(a.miner_id) !== FALLBACK_MINER.id) {
    a = await ask(target, FALLBACK_MINER.id);
    spent += Number(a.cost_usd) || 0;
    v = check(target, a.result);
    pkg.attempts.push({ ...a, label: v.label, checks: v.checks, reask: true });
    d = decide(v.label, a.result);
  }
  pkg.decision = d || "FLAG";
  const last = pkg.attempts.at(-1);
  pkg.reason = d ? `${last.label}: ${last.result?.verdict}, ${last.result?.vulnerability_count} known` :
    `not verified after ${pkg.attempts.length} answer(s): ${last.checks.filter((c) => c.status === "fail").map((c) => c.detail).join("; ") || last.label}`;
  console.log(`${pkg.decision.padEnd(6)} ${target}  (${pkg.reason})`);
}
run.spent_usd = Math.round(spent * 100) / 100;
run.receipts = run.packages.flatMap((p) => p.attempts.map((x) => x.receipt?.receipt_hash).filter(Boolean));

// ---------- hand the evidence to the Mind ----------
function evidenceMessage() {
  const lines = run.packages.map((p) => {
    const tries = p.attempts.map((x) => `${x.miner ?? "no miner"}: ${x.result?.verdict ?? "no verdict"} (count ${x.result?.vulnerability_count ?? "n/a"}; issues ${JSON.stringify(x.result?.issues ?? [])}) -> Verified Ask "${x.label}"${x.checks?.filter((c) => c.status !== "pass").map((c) => ` [${c.status}: ${c.detail}]`).join("") ?? ""}; $${x.cost_usd}; receipt ${x.receipt?.receipt_hash ?? "none"}`);
    return `- ${p.target}: proposed ${p.decision}\n    ${tries.join("\n    ")}`;
  });
  return [
    "Dependency check request. Evidence was gathered by your connector: one paid SECURITY_REVIEW_GENERAL answer per package from Telegraph (Anjoman), each checked free by Verified Ask against OSV, deps.dev and rubygems.org.",
    "Rules: verified + Secure = PASS; verified + vulnerable = BLOCK; unconfirmed, or not verified after one re-ask = FLAG for a person. Don't invent facts beyond the evidence.",
    "",
    ...lines,
    "",
    `Total spent: $${run.spent_usd}. Receipts: ${run.receipts.join(", ") || "none"}.`,
    "Please reply with: one line per package (decision and reason, naming the advisories for any BLOCK), anything you would overrule and why, the total cost, and what you'll remember about these versions for future alerts.",
  ].join("\n");
}

if (!opt["no-mind"]) {
  if (!opt.mind) throw new Error("--mind <mindId> is required unless --no-mind");
  const { createMindsClient } = await import("@animocabrands/minds-client-lib");
  const client = createMindsClient({ builderApiKey: process.env.MINDS_BUILDER_API_KEY || "proxy-injected" });
  await client.ensureConversation(opt.alias, opt.mind);
  const after = await client.getLatestHistoryFingerprint(opt.alias);
  const text = evidenceMessage();
  await client.sendMessage({ alias: opt.alias, messageText: text });
  run.mind = { id: opt.mind, alias: opt.alias, sent: text };
  const out = await client.waitForReply({ alias: opt.alias, timeoutMs: 180_000, afterFingerprint: after, sentMessageText: text });
  run.mind.reply = out.timedOut ? null : out.reply.messageText;
  console.log(out.timedOut ? "\n(the Mind did not reply within 3 minutes; check its chat)" : `\n--- Dependency.Guard ---\n${out.reply.messageText}`);
}

const outDir = join(ROOT, "mind", "evidence");
mkdirSync(outDir, { recursive: true });
const file = join(outDir, `${run.at.replace(/[:.]/g, "-")}.json`);
writeFileSync(file, JSON.stringify(run, null, 1) + "\n");
console.log(`\nspent $${run.spent_usd}; run saved to ${file.replace(ROOT + "/", "")}`);
