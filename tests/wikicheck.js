// Checks every reference inside the wiki's data: sources, links, citations.
// Usage: node tests/wikicheck.js ai/index.html  (exits 1 on any problem)
const fs = require("fs");
const html = fs.readFileSync(process.argv[2], "utf8");
const js = html.split("<script>")[1].split("</script>")[0];
const data = js.replace(/document\.documentElement\.lang = "en";/, "").split("// ---------- helpers ----------")[0];
const { S, E, CATS, GLOSSARY, TIMELINE } = new Function(data + "; return { S, E, CATS, GLOSSARY, TIMELINE };")();
const byId = Object.fromEntries(E.map((e) => [e.id, e]));
const catById = Object.fromEntries(CATS.map((c) => [c.id, c]));
const bad = [];
for (const e of E) {
  e.src.forEach((k) => { if (!S[k]) bad.push(`missing source ${k} in ${e.id}`); });
  e.related.forEach((r) => { if (!byId[r]) bad.push(`missing related ${r} in ${e.id}`); });
  if (!catById[e.cat]) bad.push(`bad cat ${e.cat}`);
  const cited = new Set();
  e.body.forEach(([, p]) => {
    (p.match(/\{\{([a-z0-9-]+)\|/g) || []).forEach((m) => { const id = m.slice(2, -1); if (id !== "t-timeline" && !byId[id]) bad.push(`bad link ${id} in ${e.id}`); });
    (p.match(/\[(\d+)\]/g) || []).forEach((m) => { const n = +m.slice(1, -1); cited.add(n); if (n < 1 || n > e.src.length) bad.push(`cite ${n} out of range in ${e.id}`); });
  });
  e.src.forEach((k, i) => { if (!cited.has(i + 1)) bad.push(`source ${i + 1} (${k}) never cited in ${e.id}`); });
}
GLOSSARY.forEach((g) => { if (!byId[g[2]]) bad.push(`glossary link ${g[2]}`); });
TIMELINE.forEach((t) => { if (!S[t[3]]) bad.push(`timeline src ${t[3]}`); if (t[4] && !byId[t[4]]) bad.push(`timeline link ${t[4]}`); });
(byId["where-to-begin"].path || []).forEach((id) => { if (!byId[id]) bad.push(`path ${id}`); });
const used = new Set([...E.flatMap((e) => e.src), ...TIMELINE.map((t) => t[3])]);
const ids = E.map((e) => e.id); const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
if (dup.length) bad.push("duplicate ids " + dup);
console.log("entries", E.length, "| starter", E.filter((e) => e.stub).length, "| sources", Object.keys(S).length, "| unused", Object.keys(S).filter((k) => !used.has(k)));
console.log(bad.length ? bad.join("\n") : "all references resolve");
if (bad.length) process.exit(1);
