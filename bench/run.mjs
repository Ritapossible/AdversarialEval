// Paid SECURITY_REVIEW benchmark runner.
//
//   node bench/run.mjs --cases bench/cases-v2.json --audit <audit.json> --out bench/out/round-2 [--concurrency 4] [--dry-run]
//
// Defaults reproduce round 1 (bench/RULE.md): cases.json, the 2026-11-15 audit, bench/out.
// Each target (miner or auto-routed) runs its cases one at a time; up to --concurrency targets run
// at once, so no miner gets parallel calls. One attempt per (case, target); a re-run skips every
// recorded pair, so a restart never pays twice. The call cap is cases x targets.
// Key: $BENCH_KEY_FILE (default ~/.adversarialeval/burner.key), never from the repo.
// Set NODE_USE_ENV_PROXY=1 when behind an HTTPS proxy.
import { readFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";
import { privateKeyToAccount } from "viem/accounts";
import { wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm";

const HERE = dirname(fileURLToPath(import.meta.url));
const NODE = "https://devnode.telegraphprotocol.com";
const INTENT = "SECURITY_REVIEW_GENERAL";
const SEPOLIA = "eip155:11155111";
// Sepolia USDC assets the node has offered: the open-mint test token (until 2026-11-16) and Circle's
// USDC (from 2026-11-17, rule v2 amendment 2). Pay in whichever the node asks for, capped at $0.02.
const SEPOLIA_USDC = ["0xcc194e1a843B658526D0D5C431f670028582Ae17", "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"];
// From 2026-11-20 the node offers exact payment only on Base Sepolia (Circle USDC) and Solana.
const BASE_SEPOLIA = "eip155:84532";
const BASE_SEPOLIA_USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e";

const { values: opt } = parseArgs({
  options: {
    cases: { type: "string", default: join(HERE, "cases.json") },
    audit: { type: "string", default: join(HERE, "..", "eval", "reports", "raw", "2026-11-15-miner-audit.json") },
    out: { type: "string", default: join(HERE, "out") },
    concurrency: { type: "string", default: "1" },
    "dry-run": { type: "boolean", default: false },
  },
});

const cases = JSON.parse(readFileSync(resolve(opt.cases), "utf8")).cases;
const audit = JSON.parse(readFileSync(resolve(opt.audit), "utf8"));
const miners = audit.miners.filter((m) => m.callable.length).map((m) => ({ id: m.id, slug: m.slug, rank: m.rank, score: m.score }));
const targets = [{ id: "routed", slug: "auto-routed", rank: null, score: null }, ...miners];
const cap = cases.length * targets.length;

const outDir = resolve(opt.out);
mkdirSync(outDir, { recursive: true });
const outFile = join(outDir, "calls.ndjson");
const done = new Set();
if (existsSync(outFile)) {
  for (const line of readFileSync(outFile, "utf8").split("\n").filter(Boolean)) {
    const r = JSON.parse(line);
    done.add(`${r.case}|${r.miner_id}`);
  }
}
const queues = targets.map((t) => ({ t, todo: cases.filter((c) => !done.has(`${c.id}|${t.id}`)) }));
const remaining = queues.reduce((n, q) => n + q.todo.length, 0);
console.log(`${cases.length} cases x ${targets.length} targets = cap ${cap}; ${done.size} recorded, ${remaining} to go`);
if (done.size + remaining > cap) throw new Error("plan exceeds the call cap");
if (opt["dry-run"]) {
  for (const q of queues) console.log(`  ${q.t.slug.padEnd(32)} rank=${q.t.rank ?? "-"} ${q.todo.length} calls`);
  process.exit(0);
}

const keyFile = process.env.BENCH_KEY_FILE || join(homedir(), ".adversarialeval", "burner.key");
const account = privateKeyToAccount(readFileSync(keyFile, "utf8").trim());
const payFetch = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [{ network: SEPOLIA, client: new ExactEvmScheme(account) }, { network: BASE_SEPOLIA, client: new ExactEvmScheme(account) }],
  spendControls: { maxAmountPerPayment: false, allowedAssets: [
    ...SEPOLIA_USDC.map((asset) => ({ network: SEPOLIA, asset, maxAmountPerPayment: "20000" })),
    { network: BASE_SEPOLIA, asset: BASE_SEPOLIA_USDC, maxAmountPerPayment: "20000" },
  ] },
});
console.log(`payer ${account.address}`);

const decode = (v) => {
  if (!v) return null;
  try { return JSON.parse(Buffer.from(v, "base64").toString("utf8")); } catch { return v.slice(0, 500); }
};

async function call(c, t) {
  const url = t.id === "routed" ? `${NODE}/engine/v1/ask` : `${NODE}/engine/v1/ask/${t.id}`;
  const started = Date.now();
  let rec = { case: c.id, miner_id: t.id, miner: t.slug, rank: t.rank, node_score: t.score, target: c.target, at: new Date().toISOString() };
  try {
    const res = await payFetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent: INTENT, params: { target: c.target } }),
      signal: AbortSignal.timeout(90_000),
    });
    const text = await res.text();
    let body; try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 2000) }; }
    rec = { ...rec, http: res.status, wall_ms: Date.now() - started,
      receipt: decode(res.headers.get("x-telegraph-receipt")),
      payment_response: decode(res.headers.get("payment-response")),
      routed_miner: body.miner_id ?? null, routed_name: body.miner_name ?? null,
      result: body.result ?? null, field_status: body.field_status ?? null, result_shape: body.result_shape ?? null,
      cost_usd: body.cost_usd ?? null, duration_ms: body.duration_ms ?? null, signal_hash: body.signal_hash ?? null,
      error: body.error ?? null, message: body.message ?? null, warnings: body.warnings ?? null };
  } catch (e) {
    rec = { ...rec, http: null, wall_ms: Date.now() - started, error: String(e?.message || e).slice(0, 300) };
  }
  appendFileSync(outFile, JSON.stringify(rec) + "\n");
  console.log(`${c.id.padEnd(38)} ${t.slug.padEnd(30)} http=${rec.http} ${rec.result?.verdict ?? rec.error ?? ""}`);
}

async function worker(pool) {
  for (let q = pool.shift(); q; q = pool.shift()) {
    for (const c of q.todo) {
      await call(c, q.t);
      await new Promise((r) => setTimeout(r, 1000));
    }
  }
}
const pool = queues.filter((q) => q.todo.length);
const n = Math.max(1, Math.min(Number(opt.concurrency) || 1, pool.length));
await Promise.all(Array.from({ length: n }, () => worker(pool)));
console.log("round complete");
