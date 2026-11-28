// Pay for a list of Telegraph questions on Solana devnet (x402 v2 "exact", routed /engine/v1/ask)
// and record every answer as it returns.
//
//   NODE_USE_ENV_PROXY=1 node bench/telegraph_jobs.mjs --jobs <jobs.json> --out <dir> [--max-spend 1.50]
//
// jobs.json: {"jobs": [{"key": "...", "intent": "...", "params": {...}, "miner": "<id, optional>"}]}; with a
// miner the call goes to /engine/v1/ask/<id>, otherwise to the ranked route. Each answer is appended to
// <dir>/calls.ndjson with the Solana transaction signature; a re-run skips recorded keys, so nothing
// is paid twice. Each payment is capped at $0.02 by the client; the run stops before exceeding
// --max-spend (counting $0.01 per call, the node's price). Reconcile on-chain with
// bench/solana_reconcile.py. Key: $SOLANA_KEY_FILE (default ~/.adversarialeval/solana-burner.json).
import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import { ExactSvmScheme } from "@x402/svm/exact/client";

const NODE = "https://devnode.telegraphprotocol.com";
const SOLANA_DEVNET = "solana:EtWTRABZaYq6iMfeYKouRu166VU2xqa1";
const DEVNET_USDC = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU";
const PRICE_USD = 0.01;

const { values: opt } = parseArgs({ options: {
  jobs: { type: "string" }, out: { type: "string" },
  "max-spend": { type: "string", default: "1.50" }, "dry-run": { type: "boolean", default: false },
} });
const jobs = JSON.parse(readFileSync(resolve(opt.jobs), "utf8")).jobs;
const outDir = resolve(opt.out);
mkdirSync(outDir, { recursive: true });
const callsFile = join(outDir, "calls.ndjson");
const done = new Set();
let spent = 0;
if (existsSync(callsFile)) for (const l of readFileSync(callsFile, "utf8").split("\n").filter(Boolean)) {
  const r = JSON.parse(l); done.add(r.key); if (r.paid) spent += PRICE_USD;
}
const maxSpend = Number(opt["max-spend"]);
const todo = jobs.filter((j) => !done.has(j.key));
console.log(`${jobs.length} jobs, ${done.size} recorded ($${spent.toFixed(2)}), ${todo.length} to run; cap $${maxSpend}`);
if (opt["dry-run"]) process.exit(0);

const keyFile = process.env.SOLANA_KEY_FILE || join(homedir(), ".adversarialeval", "solana-burner.json");
const signer = await createKeyPairSignerFromBytes(new Uint8Array(JSON.parse(readFileSync(keyFile, "utf8"))));
const pay = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [{ network: SOLANA_DEVNET, client: new ExactSvmScheme(signer) }],
  spendControls: { maxAmountPerPayment: false, allowedAssets: [
    { network: SOLANA_DEVNET, asset: DEVNET_USDC, maxAmountPerPayment: "20000" } ] },
});
console.log(`payer ${signer.address} (Solana devnet)`);
writeFileSync(join(outDir, "payer.json"), JSON.stringify({ payer: signer.address, network: SOLANA_DEVNET }) + "\n");
const decode = (v) => { if (!v) return null; try { return JSON.parse(Buffer.from(v, "base64").toString("utf8")); } catch { return v.slice(0, 500); } };

for (const j of todo) {
  if (spent + PRICE_USD > maxSpend + 1e-9) { console.log(`spending cap $${maxSpend} reached; ${todo.length - todo.indexOf(j)} jobs skipped`); break; }
  spent += PRICE_USD;
  const started = Date.now();
  let rec = { key: j.key, intent: j.intent, params: j.params, miner_asked: j.miner ?? "routed", at: new Date().toISOString() };
  try {
    const res = await pay(j.miner ? `${NODE}/engine/v1/ask/${j.miner}` : `${NODE}/engine/v1/ask`, { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ intent: j.intent, params: j.params }), signal: AbortSignal.timeout(120_000) });
    const text = await res.text();
    let body; try { body = JSON.parse(text); } catch { body = { raw: text.slice(0, 2000) }; }
    const payment = decode(res.headers.get("payment-response"));
    rec = { ...rec, http: res.status, wall_ms: Date.now() - started, paid: Boolean(payment?.success ?? payment?.transaction),
      solana_tx: payment?.transaction ?? null, receipt: decode(res.headers.get("x-telegraph-receipt")),
      miner_id: body.miner_id ?? null, miner: body.miner_name ?? null, result: body.result ?? null,
      cost_usd: body.cost_usd ?? null, error: body.error ?? null, message: body.message ?? null };
  } catch (e) {
    rec = { ...rec, http: null, wall_ms: Date.now() - started, paid: null, error: String(e?.message || e).slice(0, 300) };
  }
  if (!rec.paid) spent -= PRICE_USD;
  appendFileSync(callsFile, JSON.stringify(rec) + "\n");
  console.log(`${j.key.padEnd(44)} http=${rec.http} ${rec.result?.verdict ?? rec.error ?? ""} ${rec.solana_tx ? "tx " + rec.solana_tx.slice(0, 10) + "…" : ""}`);
}
