import { test } from "node:test";
import assert from "node:assert/strict";
process.argv[1] = "not-main";
const { decide, normOutcome } = await import("../markets.mjs");

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
