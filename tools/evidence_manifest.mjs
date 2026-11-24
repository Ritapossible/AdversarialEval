// Signed evidence manifest: a changed result fails verification.
//
//   node tools/evidence_manifest.mjs sign     # owner only: hash every evidence file, sign the list
//   node tools/evidence_manifest.mjs verify   # anyone (and CI): every signed file still matches
//
// Evidence = the tracked files under eval/reports/, bench/out/, mind/evidence/ and data/test/.
// `sign` writes evidence/MANIFEST.json (path -> SHA-256, plus the git commit it was made at) and
// evidence/MANIFEST.sig (Ed25519 signature over the manifest bytes). The private key never enters
// the repo: $EVIDENCE_KEY_FILE (default ~/.adversarialeval/evidence-signing.pem), created on the
// first `sign`. Its public half is committed as evidence/signing-key.pub.
// `verify` fails if the signature doesn't match the public key, or if any file listed in the
// manifest is missing or its bytes changed. Files added after signing are listed as "not yet
// signed" without failing; the owner re-signs when publishing new evidence. Node built-ins only.
import { createHash, createPrivateKey, createPublicKey, generateKeyPairSync, sign, verify } from "node:crypto";
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DIR = join(ROOT, "evidence");
const MANIFEST = join(DIR, "MANIFEST.json"), SIG = join(DIR, "MANIFEST.sig"), PUB = join(DIR, "signing-key.pub");
const SCOPE = ["eval/reports", "bench/out", "mind/evidence", "data/test"];

const git = (...a) => execFileSync("git", a, { cwd: ROOT, encoding: "utf8" });
const tracked = () => git("ls-files", "-z", "--", ...SCOPE).split("\0").filter(Boolean).sort();
const sha256 = (p) => createHash("sha256").update(readFileSync(join(ROOT, p))).digest("hex");

function signCmd() {
  const keyFile = process.env.EVIDENCE_KEY_FILE || join(homedir(), ".adversarialeval", "evidence-signing.pem");
  if (!existsSync(keyFile)) {
    const { privateKey } = generateKeyPairSync("ed25519");
    mkdirSync(dirname(keyFile), { recursive: true });
    writeFileSync(keyFile, privateKey.export({ type: "pkcs8", format: "pem" }), { mode: 0o600 });
  }
  const priv = createPrivateKey(readFileSync(keyFile));
  const pubPem = createPublicKey(priv).export({ type: "spki", format: "pem" });
  if (existsSync(PUB) && readFileSync(PUB, "utf8") !== pubPem) throw new Error("key file doesn't match evidence/signing-key.pub");
  const files = Object.fromEntries(tracked().map((p) => [p, sha256(p)]));
  const manifest = { schema: 1, signed_at: new Date().toISOString(), at_commit: git("rev-parse", "HEAD").trim(),
    scope: SCOPE, algorithm: "ed25519 over the exact bytes of MANIFEST.json; files hashed with SHA-256", files };
  const bytes = Buffer.from(JSON.stringify(manifest, null, 1) + "\n");
  mkdirSync(DIR, { recursive: true });
  writeFileSync(MANIFEST, bytes);
  writeFileSync(SIG, sign(null, bytes, priv).toString("base64") + "\n");
  writeFileSync(PUB, pubPem);
  console.log(`signed ${Object.keys(files).length} evidence files`);
}

function verifyCmd() {
  const bytes = readFileSync(MANIFEST);
  const ok = verify(null, bytes, createPublicKey(readFileSync(PUB)), Buffer.from(readFileSync(SIG, "utf8").trim(), "base64"));
  if (!ok) { console.error("signature does not match the manifest"); process.exit(1); }
  const { files, signed_at } = JSON.parse(bytes);
  const bad = Object.entries(files).filter(([p, h]) => !existsSync(join(ROOT, p)) || sha256(p) !== h).map(([p]) => p);
  const unsigned = tracked().filter((p) => !(p in files));
  console.log(`signature OK (signed ${signed_at}); ${Object.keys(files).length - bad.length}/${Object.keys(files).length} signed files unchanged`);
  if (unsigned.length) console.log(`${unsigned.length} evidence file(s) added after signing, not yet signed: ${unsigned.slice(0, 5).join(", ")}${unsigned.length > 5 ? ", ..." : ""}`);
  if (bad.length) { console.error(`changed or missing since signing:\n  ${bad.join("\n  ")}`); process.exit(1); }
}

const cmd = process.argv[2];
if (cmd === "sign") signCmd(); else if (cmd === "verify") verifyCmd();
else { console.error("usage: node tools/evidence_manifest.mjs sign|verify"); process.exit(2); }
