/* AI Markdown Python 0.1.0 — Author: G0TH3R */
(function (root) {
  "use strict";

  const APP_ID = "spl_ai_markdown_python";
  const ALLOWED_CAPS = [25, 50, 100, 200];
  const TIME_PRESETS = {
    last_15m: { earliest: "-15m", latest: "now" },
    last_60m: { earliest: "-60m", latest: "now" },
    last_4h: { earliest: "-4h", latest: "now" },
    last_24h: { earliest: "-24h", latest: "now" },
    last_7d: { earliest: "-7d@d", latest: "now" },
    all_time: { earliest: "0", latest: "now" }
  };
  const RISKY_COMMANDS = ["collect", "delete", "dump", "map", "mcollect", "meventcollect", "outputcsv", "outputlookup", "run", "sendalert", "sendemail", "runshellscript", "script", "tscollect"];

  function normalizeRowCap(value) {
    const parsed = Number.parseInt(value, 10);
    return ALLOWED_CAPS.includes(parsed) ? parsed : 100;
  }

  function resolveTimeRange(preset, earliest, latest) {
    if (preset !== "custom" && TIME_PRESETS[preset]) return Object.assign({}, TIME_PRESETS[preset]);
    const from = String(earliest || "").trim();
    const to = String(latest || "").trim();
    if (!from || !to) throw new Error("Custom earliest and latest values are required.");
    return { earliest: from.slice(0, 80), latest: to.slice(0, 80) };
  }

  function validateField(value) {
    const field = String(value || "").trim();
    if (field === "auto") return "";
    if (!/^[A-Za-z][A-Za-z0-9_]{0,127}$/.test(field)) throw new Error("Field must contain only letters, numbers, and underscores and start with a letter.");
    return field;
  }

  function composeSearch(search, field) {
    const query = String(search || "").trim();
    if (!query) throw new Error("SPL is required.");
    const rawField = String(field || "").trim();
    const selected = rawField ? validateField(rawField) : "";
    return query + "\n| aimarkdown" + (selected ? " field=" + selected : "");
  }

  function splitPipeline(search) {
    const text = String(search || "");
    const segments = [];
    let current = "", quote = null, escaped = false, comment = false;
    for (let i = 0; i < text.length; i += 1) {
      const ch = text[i];
      if (!quote && text.slice(i, i + 3) === "```") { current += "```"; comment = !comment; i += 2; continue; }
      if (comment) { current += ch; continue; }
      if (escaped) { current += ch; escaped = false; continue; }
      if (quote && ch === "\\") { current += ch; escaped = true; continue; }
      if (quote) { current += ch; if (ch === quote) quote = null; continue; }
      if (ch === '"' || ch === "'") { quote = ch; current += ch; continue; }
      if (ch === "|") { if (current.trim()) segments.push(current.trim()); current = "|"; continue; }
      current += ch;
    }
    if (current.trim()) segments.push(current.trim());
    return segments;
  }

  function stripComments(segment) {
    return String(segment || "").replace(/```[\s\S]*?```/g, " ");
  }

  function detectRiskyCommands(search) {
    const commands = new Set(splitPipeline(search).map((segment) => {
      const match = stripComments(segment).replace(/^\|\s*/, "").trim().match(/^([A-Za-z][A-Za-z0-9_]*)\b/);
      return match ? match[1].toLowerCase() : "";
    }));
    return RISKY_COMMANDS.filter((name) => commands.has(name));
  }

  function createSearchOptions(search, field, earliest, latest, count, owner) {
    return {
      id: "ai_markdown_python_" + owner,
      app: APP_ID,
      search: composeSearch(search, field),
      earliest_time: earliest,
      latest_time: latest,
      count: normalizeRowCap(count),
      preview: false,
      cache: false,
      autostart: false
    };
  }

  function isCurrentGeneration(runtime, generation) {
    return Boolean(runtime && runtime.generation === generation);
  }

  function insertSanitizedHtml(target, html, purifier) {
    if (!purifier || typeof purifier.sanitize !== "function") throw new Error("DOMPurify is unavailable.");
    target.innerHTML = purifier.sanitize(String(html || ""), {
      USE_PROFILES: { html: true },
      ALLOWED_TAGS: ["a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "li", "ol", "p", "pre", "strong", "table", "tbody", "td", "th", "thead", "tr", "ul"],
      ALLOWED_ATTR: ["href", "title", "class"],
      FORBID_TAGS: ["img", "script", "style", "iframe", "form", "input", "button", "video", "audio", "svg", "math"],
      ALLOW_DATA_ATTR: false
    });
    target.querySelectorAll && target.querySelectorAll("a").forEach((link) => { link.rel = "noopener noreferrer"; link.target = "_blank"; });
  }

  const api = { APP_ID, ALLOWED_CAPS, TIME_PRESETS, RISKY_COMMANDS, normalizeRowCap, resolveTimeRange, validateField, composeSearch, detectRiskyCommands, createSearchOptions, isCurrentGeneration, insertSanitizedHtml };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }
  const documentRef = root.document;
  if (!documentRef) return;

  let SearchManager = null;
  let runtime = { generation: 0, manager: null };
  const byId = (id) => documentRef.getElementById(id);
  function status(message, state) { const el = byId("amp-status"); el.textContent = message; el.dataset.state = state || "idle"; }
  function clearResults() { const target = byId("amp-results"); while (target.firstChild) target.removeChild(target.firstChild); }
  function dispose(cancel) { if (!runtime.manager) return; try { if (cancel && runtime.manager.cancel) runtime.manager.cancel(); } catch (_) {} try { if (runtime.manager.dispose) runtime.manager.dispose(); } catch (_) {} runtime.manager = null; }

  function renderRows(data, generation) {
    if (!isCurrentGeneration(runtime, generation)) return;
    clearResults();
    const target = byId("amp-results");
    const fields = (data.fields || []).map((field) => typeof field === "string" ? field : field.name);
    const htmlIndex = fields.indexOf("ai_markdown_html");
    const sourceIndex = fields.indexOf("ai_markdown_field");
    if (htmlIndex < 0 || !Array.isArray(data.rows) || !data.rows.length) { const empty = documentRef.createElement("div"); empty.className = "amp-empty"; empty.textContent = "No renderable Markdown results returned."; target.appendChild(empty); return; }
    data.rows.forEach((row, index) => {
      const card = documentRef.createElement("article"); card.className = "amp-result-card";
      const header = documentRef.createElement("header"); header.textContent = "Result " + (index + 1) + (sourceIndex >= 0 && row[sourceIndex] ? " · " + row[sourceIndex] : ""); card.appendChild(header);
      const body = documentRef.createElement("div"); body.className = "amp-markdown";
      insertSanitizedHtml(body, row[htmlIndex], root.DOMPurify); card.appendChild(body); target.appendChild(card);
    });
  }

  function runSearch() {
    try {
      const query = byId("amp-query").value;
      const risky = detectRiskyCommands(query);
      if (risky.length && !root.confirm("This SPL contains action-capable commands: " + risky.join(", ") + ". Run it?")) return;
      const range = resolveTimeRange(byId("amp-time-preset").value, byId("amp-earliest").value, byId("amp-latest").value);
      const cap = normalizeRowCap(byId("amp-row-cap").value);
      const generation = runtime.generation + 1; dispose(true); runtime = { generation, manager: null };
      const options = createSearchOptions(query, byId("amp-field").value, range.earliest, range.latest, cap, String(generation));
      const resultCount = options.count; delete options.count;
      const manager = new SearchManager(options); runtime.manager = manager;
      const model = manager.data("results", { count: resultCount, offset: 0 });
      model.on("data", function () { if (!isCurrentGeneration(runtime, generation)) return; const data = this.data(); if (!data || !Array.isArray(data.rows)) return; renderRows(data, generation); status("Completed · " + data.rows.length + " rows displayed.", "done"); dispose(false); });
      model.on("error", (event) => { if (isCurrentGeneration(runtime, generation)) status(String(event && event.message || "Search result error."), "error"); });
      manager.on("search:start", () => { if (isCurrentGeneration(runtime, generation)) status("Running…", "running"); });
      manager.on("search:done", () => { if (isCurrentGeneration(runtime, generation) && model.fetch) model.fetch(); });
      manager.on("search:failed", (event) => { if (isCurrentGeneration(runtime, generation)) status(String(event && event.message || "Search failed."), "error"); });
      manager.on("search:error", (event) => { if (isCurrentGeneration(runtime, generation)) status(String(event && event.message || "Search error."), "error"); });
      manager.startSearch();
    } catch (error) { status(error.message || String(error), "error"); }
  }

  function init(Constructor) {
    SearchManager = Constructor;
    byId("amp-query").value = '| makeresults | eval ai_result_1="# Python Markdown\\n\\n**Ready.** Enter bounded SPL that returns `ai_result_1` or `ai_results_1`." | table ai_result_1';
    byId("amp-run").addEventListener("click", runSearch);
    byId("amp-cancel").addEventListener("click", () => { runtime.generation += 1; dispose(true); status("Cancelled.", "idle"); });
    byId("amp-time-preset").addEventListener("change", (event) => { const range = TIME_PRESETS[event.target.value]; if (range) { byId("amp-earliest").value = range.earliest; byId("amp-latest").value = range.latest; } });
    byId("amp-query").addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key === "Enter") { event.preventDefault(); runSearch(); } });
    status("Ready.", "idle");
  }

  require(["splunkjs/mvc/searchmanager", "splunkjs/mvc/simplexml/ready!"], init);
})(typeof window !== "undefined" ? window : globalThis);
