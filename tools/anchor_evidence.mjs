// Anchor the signed evidence manifest on Solana devnet, and verify an anchor.
//
//   NODE_PATH=bench/node_modules NODE_USE_ENV_PROXY=1 node tools/anchor_evidence.mjs anchor   # owner: one memo transaction
//   NODE_PATH=bench/node_modules node tools/anchor_evidence.mjs verify                         # anyone: the latest anchor matches
//
// `anchor` writes one Memo-program transaction whose text is the SHA-256 of evidence/MANIFEST.json and
// of its Ed25519 signature (evidence/MANIFEST.sig), with the file count and git commit. The transaction's
// block time then shows the evidence existed, unchanged, no later than that moment. The record is
// appended to evidence/ANCHORS.json. `verify` fetches the latest anchored transaction from Solana, reads
// its memo and checks it against the current manifest and signature. The fee payer is the Solana burner
// key ($SOLANA_KEY_FILE, default ~/.adversarialeval/solana-burner.json), which needs a little devnet SOL.
import { createHash } from "node:crypto";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(join(ROOT, "bench", "package.json"));
const kit = require("@solana/kit");
const RPC_URL = process.env.SOLANA_RPC || "https://api.devnet.solana.com";
const MEMO_PROGRAM = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr";
const EV = join(ROOT, "evidence");
const ANCHORS = join(EV, "ANCHORS.json");
const sha = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");

function memoText() {
  const manifest = JSON.parse(readFileSync(join(EV, "MANIFEST.json"), "utf8"));
  const files = Object.keys(manifest.files || {}).length;
  return { text: `AdversarialEval evidence v1 manifest_sha256=${sha(join(EV, "MANIFEST.json"))} sig_sha256=${sha(join(EV, "MANIFEST.sig"))} files=${files} commit=${String(manifest.commit || "").slice(0, 12)}`,
           files, manifestCommit: manifest.commit };
}

async function anchor() {
  const { text, files, manifestCommit } = memoText();
  const keyFile = process.env.SOLANA_KEY_FILE || join(homedir(), ".adversarialeval", "solana-burner.json");
  const signer = await kit.createKeyPairSignerFromBytes(new Uint8Array(JSON.parse(readFileSync(keyFile, "utf8"))));
  const rpc = kit.createSolanaRpc(RPC_URL);
  const lamports = (await rpc.getBalance(signer.address).send()).value;
  if (lamports < 10_000n) throw new Error(`fee payer ${signer.address} has ${lamports} lamports; get devnet SOL at https://faucet.solana.com`);
  const { value: blockhash } = await rpc.getLatestBlockhash().send();
  const ix = { programAddress: kit.address(MEMO_PROGRAM),
               accounts: [{ address: signer.address, role: kit.AccountRole.READONLY_SIGNER, signer }],
               data: new TextEncoder().encode(text) };
  const msg = kit.pipe(kit.createTransactionMessage({ version: 0 }),
    (m) => kit.setTransactionMessageFeePayerSigner(signer, m),
    (m) => kit.setTransactionMessageLifetimeUsingBlockhash(blockhash, m),
    (m) => kit.appendTransactionMessageInstruction(ix, m));
  const tx = await kit.signTransactionMessageWithSigners(msg);
  const sig = kit.getSignatureFromTransaction(tx);
  await rpc.sendTransaction(kit.getBase64EncodedWireTransaction(tx), { encoding: "base64", preflightCommitment: "confirmed" }).send();
  let st = null;
  for (let i = 0; i < 40 && !(st && st.confirmationStatus && st.confirmationStatus !== "processed"); i++) {
    await new Promise((r) => setTimeout(r, 1500));
    st = (await rpc.getSignatureStatuses([sig]).send()).value[0];
  }
  if (!st || st.err) throw new Error(`not confirmed: ${JSON.stringify(st)}`);
  const commit = spawnSync("git", ["rev-parse", "HEAD"], { cwd: ROOT, encoding: "utf8" }).stdout.trim();
  const rec = { network: "solana-devnet", tx: sig, slot: Number(st.slot), memo: text, files, manifest_commit: manifestCommit,
                repo_commit_when_anchored: commit, anchored_at: new Date().toISOString(), payer: signer.address,
                explorer: `https://explorer.solana.com/tx/${sig}?cluster=devnet` };
  const all = existsSync(ANCHORS) ? JSON.parse(readFileSync(ANCHORS, "utf8")) : [];
  all.push(rec);
  writeFileSync(ANCHORS, JSON.stringify(all, null, 1) + "\n");
  console.log(JSON.stringify(rec, null, 1));
}

async function verifyCmd() {
  const all = JSON.parse(readFileSync(ANCHORS, "utf8"));
  const last = all[all.length - 1];
  const rpc = kit.createSolanaRpc(RPC_URL);
  const tx = await rpc.getTransaction(last.tx, { encoding: "json", maxSupportedTransactionVersion: 0, commitment: "confirmed" }).send();
  if (!tx || tx.meta?.err) throw new Error(`anchor transaction ${last.tx} not found or failed`);
  const logs = (tx.meta?.logMessages || []).join("\n");
  const onchain = (logs.match(/Memo \(len \d+\): "(.*)"/) || [])[1];
  const now = memoText().text;
  const ok = onchain === last.memo && onchain === now;
  console.log(JSON.stringify({ tx: last.tx, block_time: tx.blockTime ? new Date(Number(tx.blockTime) * 1000).toISOString() : null,
    memo_onchain: onchain, matches_record: onchain === last.memo, matches_current_manifest: onchain === now }, null, 1));
  if (!ok) process.exit(1);
}

const cmd = process.argv[2];
if (cmd === "anchor") await anchor();
else if (cmd === "verify") await verifyCmd();
else { console.error("usage: node tools/anchor_evidence.mjs anchor|verify"); process.exit(2); }
