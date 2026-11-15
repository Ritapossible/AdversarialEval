// Paid SECURITY_REVIEW benchmark runner (rule: bench/RULE.md).
//
//   NODE_USE_ENV_PROXY=1 node bench/run.mjs --dry-run      # plan only, no payment
//   NODE_USE_ENV_PROXY=1 node bench/run.mjs                # pay and record
//
// Key: read from $BENCH_KEY_FILE (default ~/.adversarialeval/burner.key), never from the repo.
// Output: one JSON line per call in bench/out/calls.ndjson. Finished (case, target) pairs are
// skipped on a re-run, so a restart never pays twice for the same pair.
import { readFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { privateKeyToAccount } from "viem/accounts";
import { wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm";

const HERE = dirname(fileURLToPath(import.meta.url));
const NODE = "https://devnode.telegraphprotocol.com";
const INTENT = "SECURITY_REVIEW_GENERAL";
const SEPOLIA = "eip155:11155111";
const TEST_USDC = "0xcc194e1a843B658526D0D5C431f670028582Ae17";
const MAX_CALLS = 91;
const dry = process.argv.includes("--dry-run");

const cases = JSON.parse(readFileSync(join(HERE, "cases.json"), "utf8")).cases;
const audit = JSON.parse(readFileSync(join(HERE, "..", "eval", "reports", "raw", "2026-11-15-miner-audit.json"), "utf8"));
const miners = audit.miners.filter((m) => m.callable.length).map((m) => ({ id: m.id, slug: m.slug, rank: m.rank }));
const targets = [{ id: "routed", slug: "auto-routed", rank: null }, ...miners];

const outDir = join(HERE, "out");
mkdirSync(outDir, { recursive: true });
const outFile = join(outDir, "calls.ndjson");
const done = new Set();
let paidSoFar = 0;
if (existsSync(outFile)) {
  for (const line of readFileSync(outFile, "utf8").split("\n").filter(Boolean)) {
    const r = JSON.parse(line);
    done.add(`${r.case}|${r.miner_id}`);
    paidSoFar += 1; // every recorded attempt counts against the cap, paid or not
  }
}

const plan = [];
for (const c of cases) for (const t of targets) if (!done.has(`${c.id}|${t.id}`)) plan.push({ c, t });
console.log(`${cases.length} cases x ${targets.length} targets; ${done.size} done, ${plan.length} to go; cap ${MAX_CALLS}`);
if (done.size + plan.length > MAX_CALLS) throw new Error("plan exceeds the call cap in RULE.md");
if (dry) { for (const p of plan) console.log(`  ${p.c.id} -> ${p.t.slug}`); process.exit(0); }

const keyFile = process.env.BENCH_KEY_FILE || join(homedir(), ".adversarialeval", "burner.key");
const account = privateKeyToAccount(readFileSync(keyFile, "utf8").trim());
const payFetch = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [{ network: SEPOLIA, client: new ExactEvmScheme(account) }],
  spendControls: { maxAmountPerPayment: false, allowedAssets: [{ network: SEPOLIA, asset: TEST_USDC, maxAmountPerPayment: "20000" }] },
});
console.log(`payer ${account.address}`);

function decodeB64Json(v) {
  if (!v) return null;
  try { return JSON.parse(Buffer.from(v, "base64").toString("utf8")); } catch { return v.slice(0, 500); }
}

for (const { c, t } of plan) {
  const url = t.id === "routed" ? `${NODE}/engine/v1/ask` : `${NODE}/engine/v1/ask/${t.id}`;
  const started = Date.now();
  let rec = { case: c.id, miner_id: t.id, miner: t.slug, rank: t.rank, target: c.target, at: new Date().toISOString() };
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
      receipt: decodeB64Json(res.headers.get("x-telegraph-receipt")),
      payment_response: decodeB64Json(res.headers.get("payment-response")),
      routed_miner: body.miner_id ?? null, routed_name: body.miner_name ?? null,
      result: body.result ?? null, field_status: body.field_status ?? null, result_shape: body.result_shape ?? null,
      cost_usd: body.cost_usd ?? null, duration_ms: body.duration_ms ?? null, signal_hash: body.signal_hash ?? null,
      error: body.error ?? null, message: body.message ?? null, warnings: body.warnings ?? null };
  } catch (e) {
    rec = { ...rec, http: null, wall_ms: Date.now() - started, error: String(e?.message || e).slice(0, 300) };
  }
  appendFileSync(outFile, JSON.stringify(rec) + "\n");
  paidSoFar += 1;
  console.log(`${c.id.padEnd(16)} ${t.slug.padEnd(30)} http=${rec.http} ${rec.result?.verdict ?? rec.error ?? ""}`);
  if (paidSoFar >= MAX_CALLS) { console.log("call cap reached"); break; }
  await new Promise((r) => setTimeout(r, 1000));
}
