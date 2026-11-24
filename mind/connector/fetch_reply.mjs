// Complete an ask_mind.mjs record when the Mind's first reply was only a progress note.
//
//   node mind/connector/fetch_reply.mjs --file mind/evidence/<name>.json [--expect 21]
//
// Reads the conversation history, takes the Mind's messages sent after the recorded `sent_at`,
// and picks the first one with at least --expect lines of the form "<purl> | PASS|BLOCK|FLAG".
// The earlier reply is kept as `interim_reply`; `reply` and `replied_at` are replaced. Nothing is
// written if no complete answer is there yet.
import { readFileSync, writeFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { createMindsClient } from "@animocabrands/minds-client-lib";

const { values: opt } = parseArgs({ options: { file: { type: "string" }, expect: { type: "string", default: "1" } } });
if (!opt.file) throw new Error("--file is required");
const rec = JSON.parse(readFileSync(opt.file, "utf8"));
const expect = Number(opt.expect);
const LINE = /pkg:[a-z]+\/\S+?@[^\s|`<]+\s*`?\s*\|\s*\**\s*(PASS|BLOCK|FLAG)\b/g;

const client = createMindsClient({ builderApiKey: process.env.MINDS_BUILDER_API_KEY || "proxy-injected" });
await client.ensureConversation(rec.alias, rec.mind);
const history = await client.getHistory(rec.alias);
const sentAt = Date.parse(rec.sent_at);
// senderType 0 or 2 is the Mind, 1 the human (minds-client-lib MessageRecord)
const fromMind = history.filter((m) => m.senderType !== 1 && Date.parse(m.createdAt ?? 0) >= sentAt)
  .sort((a, b) => Date.parse(a.createdAt) - Date.parse(b.createdAt));
const text = (m) => m.messageText ?? "";
const full = fromMind.find((m) => (text(m).match(LINE) || []).length >= expect);
if (!full) {
  console.log(`no complete answer yet (${fromMind.length} Mind message(s) since ${rec.sent_at})`);
  process.exit(2);
}
if (rec.reply && rec.reply !== text(full)) rec.interim_reply = rec.reply;
rec.reply = text(full);
rec.replied_at = new Date(Date.parse(full.createdAt)).toISOString();
writeFileSync(opt.file, JSON.stringify(rec, null, 1) + "\n");
console.log(`complete answer saved (${(rec.reply.match(LINE) || []).length} decision lines, replied ${rec.replied_at})`);
