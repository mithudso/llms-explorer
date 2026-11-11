"""Render a private, self-contained data snapshot for inspecting local expertise."""

# Bundled HTML/CSS/JS uses browser formatting rather than the Python line limit.
# ruff: noqa: E501

from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import tempfile


def render_explorer(data: dict, out: Path) -> Path:
    """Write an interactive HTML snapshot from actual supplied Neo4j/MCP results.

    This renderer performs no database queries, network requests or inference.
    The snapshot includes the supplied records rather than invented examples.
    """
    if not isinstance(data, dict):
        raise TypeError("Explorer data must be an object")
    out = Path(out).expanduser()
    if out.is_symlink():
        raise ValueError("Explorer output must not be a symbolic link")
    out = out.resolve()
    if out.suffix.lower() != ".html":
        raise ValueError("Explorer output must use the .html extension")
    payload = dict(data)
    payload.setdefault("generated_at", datetime.now(UTC).isoformat())
    encoded = (
        json.dumps(payload, ensure_ascii=False, allow_nan=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    html = _HTML.replace("__EXPERTISE_DATA__", encoded)
    out.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".expertise-view-", suffix=".html", dir=out.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(html)
        Path(temporary).replace(out)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return out


_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>Research expertise — local data</title>
<style>
:root{font-family:"Avenir Next","Segoe UI",sans-serif;color:#172f45;background:#f2f5f8;
font-synthesis:none;--blue:#175f9d;--line:#d8e2eb;--muted:#536b7e;--paper:#fff}
*{box-sizing:border-box}body{margin:0}button,input{font:inherit}button{cursor:pointer}
a{color:#175f9d;text-underline-offset:3px;overflow-wrap:anywhere}button:focus-visible,
input:focus-visible,a:focus-visible,[tabindex]:focus-visible{outline:3px solid #3987c4;
outline-offset:3px}button{color:inherit}header{background:#172f45;color:#fff;
padding:20px max(24px,calc((100vw - 1400px)/2));display:flex;gap:24px;align-items:center;
justify-content:space-between}header strong{font-size:21px;font-weight:650;letter-spacing:-.4px}
header span{font-size:13px;color:#d3e5f3}.brand{display:flex;align-items:center;gap:12px}
.mark{width:24px;height:24px;display:grid;grid-template-columns:repeat(2,8px);gap:5px;
transform:rotate(-8deg)}.mark i{border:2px solid #c4def0;border-radius:50%}
main{max-width:1448px;margin:auto;padding:28px 24px 60px}h1{font-size:35px;line-height:1.15;
letter-spacing:-1.1px;margin:0 0 10px;font-weight:650}h2{font-size:21px;margin:0 0 8px;
letter-spacing:-.35px}h3{font-size:16px;margin:0 0 8px}p{line-height:1.55;margin:0 0 12px;
max-width:82ch}.muted{color:var(--muted);font-size:14px}.intro{display:flex;gap:30px;
justify-content:space-between;align-items:start;margin-bottom:22px}.intro p{max-width:75ch}
.status{padding:7px 12px;background:#e0ede1;border:1px solid #aac7ae;border-radius:20px;
white-space:nowrap;font-size:13px}.metrics{display:grid;grid-template-columns:repeat(4,1fr);
border:1px solid var(--line);background:#fff;border-radius:9px;overflow:hidden;margin-bottom:24px}
.metric{padding:16px 20px;border-right:1px solid var(--line)}.metric:last-child{border:0}
.metric b{font-size:27px;font-weight:650;display:block;font-variant-numeric:tabular-nums;
letter-spacing:-.7px}.metric span{font-size:13px;color:var(--muted)}.panel{background:var(--paper);
border:1px solid var(--line);border-radius:9px;padding:22px;min-width:0}.panelhead{display:flex;
justify-content:space-between;gap:20px;margin-bottom:12px}.panelhead p{margin:0}.panelhead small{
font-size:12px;color:var(--muted)}.grid{display:grid;grid-template-columns:minmax(0,1.3fr)
minmax(320px,1fr);gap:20px;align-items:start}.wide{grid-column:1/-1}.docs{display:grid;
grid-template-columns:260px minmax(0,1fr);min-height:350px;border-top:1px solid var(--line)}
.docnav{border-right:1px solid var(--line);padding:15px 15px 0 0}.docnav input{width:100%;
padding:9px 11px;border:1px solid #bacbd8;border-radius:5px;background:#f8fafc;color:#172f45}
.doclist{max-height:360px;overflow:auto;margin-top:10px}.docbutton{display:block;text-align:left;
width:100%;border:0;background:none;padding:12px;border-radius:5px;margin:3px 0;
font-size:14px;line-height:1.35}.docbutton:hover{background:#edf4fa}.docbutton[aria-pressed=true]{
background:#e7f0f8;box-shadow:inset 3px 0 var(--blue)}.docbutton small{display:block;
margin-top:5px;color:#63788a;font-size:11px;overflow-wrap:anywhere}.docdetail{padding:18px 0 0 20px;
min-width:0}.tag{display:inline-block;background:#fff4d6;color:#6b500e;padding:3px 8px;
border-radius:4px;font-size:12px;margin-bottom:10px}.provenance{display:grid;gap:8px;
font-size:12px;color:var(--muted);margin:16px 0}.provenance strong{font-weight:600;color:#344d61}
code,pre{font-family:"SFMono-Regular",Consolas,monospace}code{font-size:11px;
overflow-wrap:anywhere}pre{font-size:12px;line-height:1.6;white-space:pre-wrap;
overflow-wrap:anywhere;margin:0;background:#f4f7fa;border:1px solid #e2eaf0;border-radius:5px;
padding:14px;max-height:310px;overflow:auto}.graphbox{border:1px solid #e2eaf0;border-radius:6px;
background:#f8fafc;overflow:hidden}.graphbox svg{width:100%;height:310px;display:block}
.graph-detail{padding:12px;background:#f2f6fa;border-top:1px solid var(--line);font-size:13px;
min-height:54px;overflow-wrap:anywhere}.graph-detail b{display:block}.legend{display:flex;gap:14px;
flex-wrap:wrap;font-size:12px;color:var(--muted);margin:12px 0}.legend span{display:flex;
align-items:center;gap:5px}.legend i{width:8px;height:8px;background:#175f9d;border-radius:50%}
.steps{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:0;border-top:1px solid var(--line);
margin-top:16px}.step{padding:16px 14px 0;border-right:1px solid var(--line);min-width:0}
.step:first-child{padding-left:0}.step:last-child{border:0}.step .number{color:#59758b;font-size:12px;
margin-bottom:7px;display:block}.step h3{font-size:15px}.step p{font-size:13px;overflow-wrap:anywhere}
.step code{display:block;margin-top:8px}.sources{display:grid;gap:12px}.source{border-left:3px solid #9dbdd5;
padding:0 0 0 13px}.source strong{display:block;font-size:14px;margin-bottom:5px}.source blockquote{
margin:8px 0;font-size:13px;line-height:1.55;color:#405c71}.source a{font-size:12px}.hits{display:grid;
gap:12px;margin-top:16px}.hit{border-top:1px solid var(--line);padding-top:13px}.hit h3{
font-size:14px;color:#175f9d}.hit p{font-size:14px;white-space:pre-wrap}.hit small{font-size:11px;
color:var(--muted);overflow-wrap:anywhere}.search-question{font-size:16px;background:#edf4fa;
border-radius:5px;padding:12px;margin:10px 0}.empty{padding:20px 4px;color:#647a8c;font-size:14px}
details{margin-top:15px;border-top:1px solid var(--line);padding-top:14px}summary{cursor:pointer;
font-size:14px;color:#175f9d;margin-bottom:10px}.note{font-size:12px;color:#536b7e;line-height:1.6;
margin-top:20px}.count{font-size:12px;margin:10px 0}.timelinecode{max-height:280px}
footer{font-size:12px;color:#536b7e;margin-top:22px;border-top:1px solid var(--line);padding-top:16px}
@media(max-width:1000px){.grid{grid-template-columns:1fr}.wide{grid-column:auto}.docs{
grid-template-columns:235px minmax(0,1fr)}}@media(max-width:650px){header{padding:16px 20px;
align-items:start;flex-direction:column;gap:7px}main{padding:22px 16px 40px}h1{font-size:29px}
.intro{display:block}.status{display:inline-block;margin-top:5px}.metrics{grid-template-columns:1fr 1fr}
.metric:nth-child(2){border-right:0}.metric:nth-child(-n+2){border-bottom:1px solid var(--line)}
.docs{grid-template-columns:1fr}.docnav{padding-right:0;border:0}.doclist{max-height:170px}
.docdetail{border-top:1px solid var(--line);padding:16px 0 0}.steps{grid-template-columns:1fr 1fr;
row-gap:18px}.step:nth-child(2){border-right:0}.step:nth-child(3){padding-left:0}
.panel{padding:18px}.panelhead{display:block}.graphbox svg{height:280px}}
</style>
</head>
<body>
<header><div class="brand"><span class="mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
<strong>Research expertise</strong></div><span id="snapshot-time">Snapshot from local Neo4j</span></header>
<main>
<section class="intro"><div><h1>See the research. Follow the evidence.</h1>
<p class="muted">Explore the actual documents, relationships and source passages returned by your
local expertise system. This page is an inspectable snapshot; it does not query the database.</p></div>
<span class="status" id="state">Snapshot</span></section>
<section class="metrics" aria-label="Database coverage" id="metrics"></section>
<div class="grid">
<section class="panel wide" aria-labelledby="workflow-heading">
<h2 id="workflow-heading">One research question, saved and retrieved</h2>
<p class="muted" id="research-question"></p><div class="steps" id="steps"></div>
<details id="execution"><summary>Inspect the recorded MCP execution</summary>
<pre class="timelinecode" id="execution-json"></pre></details></section>
<section class="panel wide" aria-labelledby="documents-heading">
<div class="panelhead"><div><h2 id="documents-heading">Documents in the graph</h2>
<p class="muted">Select a document to inspect its text and canonical identity.</p></div>
<small id="document-coverage"></small></div>
<div class="docs"><div class="docnav"><label class="muted" for="document-search">Find a document</label>
<input type="search" id="document-search" placeholder="Topic, phrase or path" autocomplete="off">
<p class="count muted" id="document-count" aria-live="polite"></p><div class="doclist" id="document-list"></div>
</div><article class="docdetail" id="document-detail" aria-live="polite"></article></div></section>
<section class="panel" aria-labelledby="graph-heading"><div class="panelhead"><div>
<h2 id="graph-heading">Follow the relationships</h2><p class="muted">Select a node to inspect it.
Arrows preserve the recorded direction.</p></div></div><div class="graphbox"><svg id="graph"
viewBox="0 0 780 340" role="group" aria-label="Directed relationships from local Neo4j"></svg>
<div class="graph-detail" id="graph-detail">Select a node to see its identity and connections.</div></div>
<div class="legend" id="graph-legend"></div><p class="note" id="graph-coverage"></p></section>
<section class="panel" aria-labelledby="sources-heading"><h2 id="sources-heading">Sources read for this question</h2>
<p class="muted">Original URLs and recorded supporting quotations.</p><div class="sources" id="sources"></div></section>
<section class="panel wide" aria-labelledby="retrieval-heading"><h2 id="retrieval-heading">Using the saved research</h2>
<p class="muted">A later query retrieves the saved context with its source identity.</p>
<div class="search-question" id="retrieval-query"></div><div class="hits" id="hits"></div>
<p class="note">Retrieval scores rank candidates; they do not certify a statement. Qualification
labels remain attached to the source. Source snapshots and quotations are evidence to inspect.</p></section>
</div>
<footer>Private local snapshot · Canonical research files remain authoritative · No external scripts,
fonts or network requests are needed to view this page.</footer>
</main>
<script id="expertise-data" type="application/json">__EXPERTISE_DATA__</script>
<script>
"use strict";
const data = JSON.parse(document.getElementById("expertise-data").textContent);
const byId = id => document.getElementById(id);
const object = value => value && typeof value === "object" && !Array.isArray(value) ? value : {};
const array = value => Array.isArray(value) ? value : [];
const text = value => value === undefined || value === null ? "" : String(value);
const fmt = value => typeof value === "number" ? value.toLocaleString() : (text(value) || "Not recorded");
const el = (tag, value, cls) => {
  const node = document.createElement(tag);
  if (value !== undefined) node.textContent = text(value);
  if (cls) node.className = cls;
  return node;
};
const pretty = value => JSON.stringify(value, null, 2);
const safeUrl = value => {
  try { const u = new URL(text(value)); return ["http:", "https:"].includes(u.protocol) ? u.href : null; }
  catch (_) { return null; }
};
const status = object(data.status);
const counts = object(status.counts);
const corpus = object(status.corpus);
const demo = object(data.demo);
const sources = array(demo.sources).map(object);
const documents = array(data.documents).map(object);
const result = object(demo.result);
const hits = array(result.hits || demo.hits).map(object);
const save = object(demo.save_result);
const timestamp = text(data.generated_at);
byId("snapshot-time").textContent = "Snapshot from local Neo4j · " + timestamp;
byId("state").textContent = "Projection: " + (text(corpus.state || status.state) || "not recorded");
[
  [counts.documents, "Canonical documents"],
  [counts.passages, "Indexed passages"],
  [counts.vectors, "Semantic vectors"],
  [status.dimensions || corpus.dimensions, "Vector dimensions"]
].forEach(([value, label]) => {
  const box = el("div", undefined, "metric");box.append(el("b", fmt(value)), el("span", label));
  byId("metrics").append(box);
});
byId("research-question").textContent = text(demo.question) || "No research question recorded in this snapshot.";
const stepData = [
  ["Inspect", "Existing expertise", Object.keys(status).length || documents.length ?
    "Recorded coverage and document records appear below." : "No inspection result recorded.",
    demo.before ? pretty(demo.before) : "Coverage shown above"],
  ["Research", "Read the sources", sources.length ? sources.length + " source records supplied." : "No source records supplied.", ""],
  ["Save", "Capture canonically", Object.keys(save).length ?
    (save.indexed === true ? "Canonical save and indexing completed." :
      save.indexed === false ? "Canonical save recorded; indexing has not completed." : "Inspect the recorded save result.") :
    "No save result recorded.", text(save.canonical_path || save.path || save.canonical_file)],
  ["Retrieve", "Use the saved context", hits.length ? hits.length + " returned passage(s) shown below." :
    "No retrieval hits recorded.", text(demo.query || result.query)]
];
stepData.forEach(([number, title, description, detail], index) => {
 const step = el("div", undefined, "step");step.append(el("span", (index+1) + " · " + number, "number"),
 el("h3", title), el("p", description));if(detail) step.append(el("code", detail));byId("steps").append(step);
});
const calls = array(demo.tool_calls || data.tool_calls);
const execution = calls.length ? {tool_calls: calls} : {
  save_result: Object.keys(save).length ? save : null,
  retrieval_result: Object.keys(result).length ? result : null,
  note: "Only supplied recorded results are displayed. No live calls run in this page."
};
byId("execution-json").textContent = pretty(execution);
byId("document-coverage").textContent = documents.length + " document records in this snapshot" +
 (typeof counts.documents === "number" ? " / " + fmt(counts.documents) + " in the database" : "");
let selectedDocument = null;
function showDocument(doc) {
 selectedDocument = doc;
 const target = byId("document-detail");target.replaceChildren();
 target.append(el("h3", doc.title || doc.concept || "Untitled document"),
 el("span", doc.qualification || "Qualification not recorded", "tag"));
 const properties = el("div", undefined, "provenance");
 [["Concept", doc.concept], ["Canonical path", doc.path || doc.relative_path],
 ["SHA256", doc.sha256 || doc.doc_sha256]].forEach(([label,value]) => {
  if(value){const row=el("div");row.append(el("strong", label + ": "),el("code",value));properties.append(row);}
 });
 target.append(properties,el("pre",doc.text_excerpt || doc.text || "No text excerpt supplied."));
 document.querySelectorAll(".docbutton").forEach(button =>
 button.setAttribute("aria-pressed", String(button.dataset.documentIndex === String(doc._index))));
}
const indexedDocs = documents.map((d,i)=>({...d,_index:i}));
function renderDocuments() {
 const needle = byId("document-search").value.toLocaleLowerCase();
 const visible = indexedDocs.filter(doc => [doc.title,doc.concept,doc.path,doc.text_excerpt,doc.text]
 .map(text).join(" ").toLocaleLowerCase().includes(needle));
 const target=byId("document-list");target.replaceChildren();
 byId("document-count").textContent=visible.length + " matching document"+(visible.length===1?"":"s");
 visible.forEach(doc=>{
  const button=el("button",undefined,"docbutton");button.type="button";
  button.dataset.documentIndex=doc._index;button.setAttribute("aria-pressed",String(selectedDocument?._index===doc._index));
  button.append(el("span",doc.title||doc.concept||"Untitled document"),el("small",doc.concept||doc.path));
  button.addEventListener("click",()=>showDocument(doc));target.append(button);
 });
 if(!visible.length)target.append(el("p","No matching records. Try another topic or phrase.","empty"));
 if(!selectedDocument&&visible.length)showDocument(visible[0]);
}
byId("document-search").addEventListener("input",renderDocuments);renderDocuments();
if(!documents.length)byId("document-detail").append(el("p","No document records were supplied.","empty"));
sources.forEach(source=>{
 const box=el("div",undefined,"source");box.append(el("strong",source.title||source.id||"Source"));
 if(source.quote)box.append(el("blockquote",source.quote));
 const url=safeUrl(source.url);if(url){const link=el("a",source.url);link.href=url;link.target="_blank";
 link.rel="noopener noreferrer";box.append(link);}else if(source.url)box.append(el("code",source.url));
 byId("sources").append(box);
});
if(!sources.length)byId("sources").append(el("p","No source records were supplied.","empty"));
byId("retrieval-query").textContent=text(demo.query||result.query)||"No retrieval query recorded.";
hits.forEach(hit=>{
 const box=el("article",undefined,"hit");box.append(el("h3",hit.concept||hit.title||hit.id||"Passage"));
 box.append(el("span",hit.qualification||"Qualification not recorded","tag"));
 box.append(el("p",hit.text||hit.excerpt||"No passage text supplied."));
 box.append(el("small",hit.citation||((hit.path||"")+(hit.start_line?":"+hit.start_line:""))));
 if(hit.doc_sha256||hit.sha256)box.append(el("code"," · SHA256 "+(hit.doc_sha256||hit.sha256)));
 byId("hits").append(box);
});
if(!hits.length)byId("hits").append(el("p","No retrieval hits were supplied.","empty"));
const graph=object(data.graph),nodes=array(graph.nodes).map(object),edges=array(graph.edges).map(object);
const nodeMap=new Map(nodes.map(n=>[text(n.id),n]));
const kinds=[...new Set(nodes.map(n=>text(n.kind)||"record"))];
const colors=["#175f9d","#426d69","#66539b","#9a6932","#436d86","#526a50"];
const colorFor=kind=>colors[Math.max(0,kinds.indexOf(text(kind)||"record"))%colors.length];
const svg=byId("graph"),ns="http://www.w3.org/2000/svg";
const shape=(tag,attrs)=>{const n=document.createElementNS(ns,tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,text(v)));return n;};
const defs=shape("defs",{}),marker=shape("marker",{id:"arrow",viewBox:"0 0 10 10",refX:19,refY:5,
markerWidth:5,markerHeight:5,orient:"auto-start-reverse"});
marker.append(shape("path",{d:"M 0 0 L 10 5 L 0 10 z",fill:"#91a8bb"}));defs.append(marker);svg.append(defs);
const groups=new Map(kinds.map(k=>[k,nodes.filter(n=>(text(n.kind)||"record")===k)]));
const positions=new Map();
kinds.forEach((kind,column)=>{const group=groups.get(kind);group.forEach((node,row)=>{
 positions.set(text(node.id),{x:kinds.length===1?390:75+column*(630/(kinds.length-1)),
 y:group.length===1?170:42+row*(246/(group.length-1))});});});
const validEdges=edges.filter(edge=>positions.has(text(edge.source))&&positions.has(text(edge.target)));
validEdges.forEach(edge=>{
 const a=positions.get(text(edge.source)),b=positions.get(text(edge.target));
 const line=shape("line",{x1:a.x,y1:a.y,x2:b.x,y2:b.y,stroke:"#a6bacb","stroke-width":1.5,
 "marker-end":"url(#arrow)"});const title=shape("title",{});title.textContent=text(edge.relation);
 line.append(title);svg.append(line);
});
function inspectNode(node) {
 const detail=byId("graph-detail");detail.replaceChildren(el("b",node.label||node.id));
 const connected=edges.filter(e=>text(e.source)===text(node.id)||text(e.target)===text(node.id));
 detail.append(el("code",node.id),el("div",connected.length+" recorded connection(s)"));
 connected.slice(0,8).forEach(edge=>{
  const source=nodeMap.get(text(edge.source)),target=nodeMap.get(text(edge.target));
  detail.append(el("div",(source?.label||edge.source)+" → "+(target?.label||edge.target)+
   (edge.relation?" · "+edge.relation:"")));
 });
 const doc=indexedDocs.find(d=>d.concept===node.id||d.path===node.id||d.id===node.id);
 if(doc)showDocument(doc);
}
nodes.forEach(node=>{
 const p=positions.get(text(node.id));const g=shape("g",{tabindex:0,role:"button",
 "aria-label":"Inspect "+text(node.label||node.id),style:"cursor:pointer"});
 g.append(shape("circle",{cx:p.x,cy:p.y,r:12,fill:colorFor(node.kind),stroke:"#fff","stroke-width":3}));
 const label=shape("text",{x:p.x,y:p.y+25,"text-anchor":"middle",fill:"#344f65",
 "font-size":11,"font-family":"Avenir Next,Segoe UI,sans-serif"});
 const name=text(node.label||node.id);label.textContent=name.length>30?name.slice(0,27)+"…":name;
 const title=shape("title",{});title.textContent=name;g.append(label,title);
 g.addEventListener("click",()=>inspectNode(node));g.addEventListener("keydown",event=>{
  if(event.key==="Enter"||event.key===" "){event.preventDefault();inspectNode(node);}});svg.append(g);
});
kinds.forEach(kind=>{const item=el("span"),dot=el("i");dot.style.background=colorFor(kind);
item.append(dot,document.createTextNode(kind));byId("graph-legend").append(item);});
byId("graph-coverage").textContent=nodes.length+" nodes and "+validEdges.length+
" directed relationships shown from the supplied graph snapshot.";
if(!nodes.length)byId("graph-detail").textContent="No graph nodes were supplied in this snapshot.";
</script>
</body>
</html>
"""
