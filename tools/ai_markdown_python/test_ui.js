"use strict";

const assert = require("node:assert/strict");
const ui = require("../../apps/spl_ai_markdown_python/appserver/static/js/ai_markdown_python_002.js");
const fs = require("node:fs");
const source = fs.readFileSync(require.resolve("../../apps/spl_ai_markdown_python/appserver/static/js/ai_markdown_python_002.js"), "utf8");
const vendor = fs.readFileSync("apps/spl_ai_markdown_python/appserver/static/vendor/purify_noamd_001.js", "utf8");

assert.equal(ui.APP_ID, "spl_ai_markdown_python");
assert.equal(ui.normalizeRowCap(200), 200);
assert.equal(ui.normalizeRowCap(999999), 100);
assert.deepEqual(ui.resolveTimeRange("last_24h", "", ""), { earliest: "-24h", latest: "now" });
assert.deepEqual(ui.resolveTimeRange("custom", "-2h", "now"), { earliest: "-2h", latest: "now" });
assert.throws(() => ui.resolveTimeRange("custom", "", "now"));
assert.equal(ui.validateField("answer_2"), "answer_2");
for (const field of ["_raw", "bad field", "x|collect", "a.b", ""]) assert.throws(() => ui.validateField(field));
assert.equal(ui.composeSearch("| makeresults", ""), "| makeresults\n| aimarkdown");
assert.equal(ui.composeSearch("index=main", "answer_2"), "index=main\n| aimarkdown field=answer_2");
assert.deepEqual(ui.detectRiskyCommands("| makeresults | stats count"), []);
assert.deepEqual(ui.detectRiskyCommands("| makeresults | outputlookup x.csv"), ["outputlookup"]);
assert.deepEqual(ui.detectRiskyCommands('| makeresults | eval x="| collect index=x"'), []);
assert.deepEqual(ui.detectRiskyCommands("| makeresults | ```comment | collect index=x``` stats count"), []);
assert.deepEqual(ui.detectRiskyCommands("| makeresults | ```note``` collect index=x"), ["collect"]);

const options = ui.createSearchOptions("| makeresults", "", "-15m", "now", 200, "owner-7");
assert.equal(options.search, "| makeresults\n| aimarkdown");
assert.equal(options.earliest_time, "-15m");
assert.equal(options.latest_time, "now");
assert.equal(options.count, 200);
assert.equal(options.preview, false);
assert.equal(options.autostart, false);
assert.equal(options.id, "ai_markdown_python_owner-7");

assert.equal(ui.isCurrentGeneration({ generation: 3 }, 3), true);
assert.equal(ui.isCurrentGeneration({ generation: 4 }, 3), false);
assert.equal(source.includes("root.require(["), false);
assert.equal(source.includes("require([\"splunkjs/mvc/searchmanager\""), true);
assert.equal(vendor.includes("window.define = undefined"), true);
assert.equal(vendor.includes("window.define = savedDefine"), true);

let purifierCalls = 0;
const target = { innerHTML: "unsafe" };
const purifier = { sanitize(value, config) { purifierCalls += 1; assert.equal(value, "<p>safe</p><img src=x>"); assert.equal(config.USE_PROFILES.html, true); return "<p>safe</p>"; } };
ui.insertSanitizedHtml(target, "<p>safe</p><img src=x>", purifier);
assert.equal(purifierCalls, 1);
assert.equal(target.innerHTML, "<p>safe</p>");
assert.throws(() => ui.insertSanitizedHtml(target, "<p>x</p>", null));

console.log("ai_markdown_python JavaScript unit checks passed");
