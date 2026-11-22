// Send one message to the Dependency.Guard Mind and save its reply (used for the "Mind alone" arm).
//
//   node mind/connector/ask_mind.mjs --mind <mindId> --out mind/evidence/<name>.json < message.txt
//
// The Minds Builder key comes from the session proxy (or MINDS_BUILDER_API_KEY).
import { readFileSync, writeFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { createMindsClient } from "@animocabrands/minds-client-lib";

const { values: opt } = parseArgs({ options: {
  mind: { type: "string" }, out: { type: "string" }, alias: { type: "string", default: "dependency-guard" },
  timeout: { type: "string", default: "300000" } } });
if (!opt.mind || !opt.out) throw new Error("--mind and --out are required");
const text = readFileSync(0, "utf8").trim();
const client = createMindsClient({ builderApiKey: process.env.MINDS_BUILDER_API_KEY || "proxy-injected" });
await client.ensureConversation(opt.alias, opt.mind);
const after = await client.getLatestHistoryFingerprint(opt.alias);
const sentAt = new Date().toISOString();
await client.sendMessage({ alias: opt.alias, messageText: text });
const out = await client.waitForReply({ alias: opt.alias, timeoutMs: Number(opt.timeout), afterFingerprint: after, sentMessageText: text });
const reply = out.timedOut ? null : out.reply.messageText;
writeFileSync(opt.out, JSON.stringify({ mind: opt.mind, alias: opt.alias, sent_at: sentAt, sent: text, reply,
  replied_at: new Date().toISOString() }, null, 1) + "\n");
console.log(reply ?? "(no reply within the timeout)");
