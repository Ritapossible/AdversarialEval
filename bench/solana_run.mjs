// Solana use case 3 run: Telegraph SECURITY_REVIEW answers paid per call in USDC on Solana devnet
// (x402 v2 "exact", the protocol Pay.sh speaks), three paid arms on the same frozen cases.
//
//   node bench/solana_run.mjs --cases mind/solana-test-v2/cases.json --out bench/out/solana-v2 [--max-spend 1.00] [--dry-run]
//
// Arms (mind/solana-test-v2/RULE.md):
//   listing   the provider an agent picks from the node's public listing: the first miner listed for
//             SECURITY_REVIEW_GENERAL (fixed in the rule), asked directly, answer trusted
//   ranked    Telegraph's ranked route (/engine/v1/ask), answer trusted
//   verified  the ranked answer checked free by Verified Ask; only if proven wrong or unusable, one
//             re-ask of the benchmark's best miner, also paid on Solana; then PASS / BLOCK / FLAG
// (The fourth arm, the frontier model alone, is the Dependency.Guard Mind; see the rule.)
//
// Every paid call is appended to <out>/calls.ndjson as soon as it returns, with the Solana
// transaction signature from the payment response; a re-run skips recorded calls, so nothing is
// paid twice. Spending: each call is capped at $0.02 by the payment client, and the run stops before
// exceeding --max-spend (counting $0.01 per call, the price the node asks; settled amounts are
// checked on-chain by bench/solana_reconcile.py).
// Key: $SOLANA_KEY_FILE (default ~/.adversarialeval/solana-burner.json), never from the repo.
// Set NODE_USE_ENV_PROXY=1 behind an HTTPS proxy.
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import { ExactSvmScheme } from "@x402/svm/exact/client";

const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(HERE, "..");
const NODE = "https://devnode.telegraphprotocol.com";
const INTENT = "SECURITY_REVIEW_GENERAL";
export const SOLANA_DEVNET = "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1";
export const DEVNET_USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"; // Circle's devnet USDC, as the node asks
export const LISTING_MINER = { id: "9002", name: "TxLens" };      // first listed for the intent (rule)
export const FALLBACK_MINER = { id: "20260828", name: "a1-preflight" }; // benchmark's best miner (rounds 2-4)
const PRICE_USD = 0.01;

const { values: opt } = parseArgs({ options: {
  cases: { type: "string", default: join(ROOT, "mind", "solana-test-v2", "cases.json") },
  out: { type: "string", default: join(HERE, "out", "solana-v2") },
  "max-spend": { type: "string", default: "1.00" },
  "dry-run": { type: "boolean", default: false },
} });

const cases = JSON.parse(readFileSync(resolve(opt.cases), "utf8")).cases;
const outDir = resolve(opt.out);
mkdirSync(outDir, { recursive: true });
const callsFile = join(outDir, "calls.ndjson");
const done = new Map();
if (existsSync(callsFile)) for (const l of readFileSync(callsFile, "utf8").split("\n").filter(Boolean)) {
  const r = JSON.parse(l); done.set(`${r.case}|${r.arm}`, r);
}
const maxSpend = Number(opt["max-spend"]);
let spent = [...done.values()].filter((r) => r.paid).length * PRICE_USD;
console.log(`${cases.length} cases; ${done.size} calls recorded ($${spent.toFixed(2)}); cap $${maxSpend}`);
if (opt["dry-run"]) process.exit(0);

const keyFile = process.env.SOLANA_KEY_FILE || join(homedir(), ".adversarialeval", "solana-burner.json");
const signer = await createKeyPairSignerFromBytes(new Uint8Array(JSON.parse(readFileSync(keyFile, "utf8"))));
const pay = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [{ network: SOLANA_DEVNET, client: new ExactSvmScheme(signer) }],
  spendControls: { maxAmountPerPayment: false, allowedAssets: [
    { network: SOLANA_DEVNET, asset: DEVNET_USDC, maxAmountPerPayment: "20000" } ] },
});
console.log(`payer ${signer.address} (Solana devnet)`);

const decode = (v) => { if (!v) return null; try { return JSON.parse(Buffer.from(v, "base64").toString("utf8")); } catch { return v.slice(0, 500); } };

async function call(c, arm, minerId) {
  const key = `${c.id}|${arm}`;
  if (done.has(key)) return done.get(key);
  if (spent + PRICE_USD > maxSpend + 1e-9) throw new Error(`spending cap $${maxSpend} reached`);
  spent += PRICE_USD; // reserved before sending
  const url = minerId ? `${NODE}/engine/v1/ask/${minerId}` : `${NODE}/engine/v1/ask`;
  const started = Date.now();
  let rec = { case: c.id, arm, target: c.target, miner_asked: minerId ?? "routed", at: new Date().toISOString() };
  try {
    const res = await pay(url, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent: INTENT, params: { target: c.target } }), signal: AbortSignal.timeout(90_000) });
    const text = await res.text();
    let body; try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 2000) }; }
    const payment = decode(res.headers.get("payment-response"));
    rec = { ...rec, http: res.status, wall_ms: Date.now() - started, paid: Boolean(payment?.success ?? payment?.transaction),
      payment, solana_tx: payment?.transaction ?? null, receipt: decode(res.headers.get("x-telegraph-receipt")),
      miner_id: body.miner_id ?? minerId ?? null, miner: body.miner_name ?? null, result: body.result ?? null,
      cost_usd: body.cost_usd ?? null, signal_hash: body.signal_hash ?? null, error: body.error ?? null, message: body.message ?? null };
  } catch (e) {
    rec = { ...rec, http: null, wall_ms: Date.now() - started, paid: null, error: String(e?.message || e).slice(0, 300) };
  }
  if (!rec.paid) spent -= PRICE_USD; // an unpaid failure costs nothing; on-chain reconciliation confirms
  appendFileSync(callsFile, JSON.stringify(rec) + "\n");
  done.set(key, rec);
  console.log(`${c.id.padEnd(40)} ${arm.padEnd(8)} http=${rec.http} ${rec.result?.verdict ?? rec.error ?? ""} ${rec.solana_tx ? "tx " + rec.solana_tx.slice(0, 12) + "…" : ""}`);
  return rec;
}

function check(target, result) {
  const p = spawnSync("python3", ["-m", "verify", "--target", target], { cwd: ROOT, input: JSON.stringify(result ?? null), encoding: "utf8" });
  if (p.status !== 0) return { label: "unavailable", checks: [{ name: "verify", status: "skip", detail: (p.stderr || "").slice(-300) }] };
  try { return JSON.parse(p.stdout); } catch { return { label: "unavailable", checks: [] }; }
}
const VULN = new Set(["Insecure", "Needs changes"]);
function decide(label, r) {
  if (label === "verified") return VULN.has(r?.verdict) && (r?.vulnerability_count ?? 0) >= 1 ? "BLOCK" : "PASS";
  if (label === "unconfirmed" || label === "unavailable") return "FLAG";
  return null;
}

const decisions = [];
try {
  for (const c of cases) {
    const listing = await call(c, "listing", LISTING_MINER.id);
    const ranked = await call(c, "ranked");
    let v = check(c.target, ranked.result);
    const steps = [{ from: "ranked", label: v.label, checks: v.checks }];
    let d = decide(v.label, ranked.result);
    if (!d && String(ranked.miner_id) !== FALLBACK_MINER.id) {
      const re = await call(c, "reask", FALLBACK_MINER.id);
      v = check(c.target, re.result);
      steps.push({ from: "reask", label: v.label, checks: v.checks });
      d = decide(v.label, re.result);
    }
    decisions.push({ case: c.id, target: c.target, listing_verdict: listing.result?.verdict ?? null,
      ranked_verdict: ranked.result?.verdict ?? null, verified_decision: d || "FLAG", steps });
  }
} finally {
  writeFileSync(join(outDir, "decisions.json"), JSON.stringify({ at: new Date().toISOString(), cases: opt.cases,
    repo_commit: spawnSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).stdout.trim(),
    payer: signer.address, network: SOLANA_DEVNET, listing_miner: LISTING_MINER, fallback_miner: FALLBACK_MINER,
    spent_usd_by_count: Math.round(spent * 100) / 100, decisions }, null, 1) + "\n");
  console.log(`\n${decisions.length} cases decided; about $${spent.toFixed(2)} spent (reconcile on-chain with bench/solana_reconcile.py)`);
}
