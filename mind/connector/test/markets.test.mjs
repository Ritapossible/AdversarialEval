import { test } from "node:test";
import assert from "node:assert/strict";
process.argv[1] = "not-main";
const { decide, normOutcome, proxyProblem, ruleSentence, shouldAsk } = await import("../markets.mjs");

test("normOutcome reads outcome or resolved_yes", () => {
  assert.equal(normOutcome({ outcome: "YES" }), "yes");
  assert.equal(normOutcome({ resolved_yes: false }), "no");
  assert.equal(normOutcome(null), "unresolved");
});

test("settles only from the named source; overrules a disagreeing paid answer", () => {
  const c = { contract: { kind: "binance" }, source_outcome: "no", evidence: { extreme: 62006 } };
  assert.deepEqual(decide("yes", c).decision, "SETTLE NO");
  assert.equal(decide("yes", c).dispute, true);
  assert.equal(decide("no", c).dispute, false);
  assert.equal(decide("unresolved", c).decision, "SETTLE NO");
});

test("no source in the rules: HOLD, never settle on a paid answer alone", () => {
  const c = { contract: null, source_outcome: "unresolved", evidence: {} };
  assert.equal(decide("yes", c).decision, "HOLD");
  assert.equal(decide("unresolved", { contract: { kind: "binance" }, source_outcome: "unresolved", evidence: { why: "x" } }).decision, "HOLD");
});

test("pays only where the rules name a checkable source", () => {
  assert.equal(shouldAsk({ contract: { kind: "binance" } }), true);
  assert.equal(shouldAsk({ contract: null }), false);
  assert.equal(shouldAsk({ contract: null }, true), true);
});

test("ruleSentence keeps the first sentence of the market's rules", () => {
  assert.equal(ruleSentence("This market resolves YES if X. Otherwise NO."), "This market resolves YES if X.");
  assert.equal(ruleSentence(null), "");
});

test("refuses to start behind a proxy without NODE_USE_ENV_PROXY (every ask would be a 401)", () => {
  assert.match(proxyProblem({ HTTPS_PROXY: "http://proxy:3128" }), /NODE_USE_ENV_PROXY/);
  assert.equal(proxyProblem({ HTTPS_PROXY: "http://proxy:3128", NODE_USE_ENV_PROXY: "1" }), null);
  assert.equal(proxyProblem({ HTTPS_PROXY: "http://proxy:3128", ANJOMAN_API_KEY: "k" }), null);
  assert.equal(proxyProblem({}), null);
});
