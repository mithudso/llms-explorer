"""Read a bounded slice of actual graph data for a private HTML snapshot."""

from __future__ import annotations

from datetime import datetime, UTC

from .store import CORPUS, current


def snapshot(store, concept="", demo=None):
    rows = store.read(
        "MATCH (d:RXDocument {corpus:$corpus,active:true}) "
        "MATCH (d)-[:RX_HAS_PASSAGE]->(p:RXPassage {start:0}) "
        "RETURN properties(d) AS doc,p.text AS text "
        "ORDER BY CASE WHEN d.concept=$concept THEN 0 ELSE 1 END,d.updated_at DESC LIMIT 12",
        corpus=CORPUS,
        concept=concept,
    )
    docs = []
    for row in rows:
        d = row["doc"]
        if current(dict(d, doc_sha256=d["sha256"])):
            docs.append(
                {k: d.get(k) for k in ["id", "concept", "title", "path", "sha256", "qualification"]}
            )
            docs[-1]["text_excerpt"] = row["text"]
    nodes, edges = {}, []
    if docs:
        d = next((d for d in docs if d["concept"] == concept), docs[0])
        nodes[d["id"]] = dict(d, label=d["title"], kind="Document")
        relations = store.read(
            "MATCH (d:RXDocument {id:$id})-[r]->(n) "
            "WHERE type(r) IN ['RX_ABOUT','RX_CITES','RX_HAS_PASSAGE'] "
            "RETURN type(r) AS relation,n.id AS id,labels(n) AS labels, "
            "n{.*,embedding:null} AS props "
            "ORDER BY CASE type(r) WHEN 'RX_ABOUT' THEN 0 WHEN 'RX_CITES' THEN 1 "
            "ELSE 2 END,n.start LIMIT 16",
            id=d["id"],
        )
        for row in relations:
            props = row["props"]
            props.pop("embedding", None)
            label = props.get("title") or props.get("concept") or props.get("url") or row["id"]
            if row["relation"] == "RX_HAS_PASSAGE":
                label = f"Passage · line {props.get('start_line')}"
            nodes[row["id"]] = dict(
                props, id=row["id"], label=label, kind=row["labels"][0].removeprefix("RX")
            )
            edges.append({"source": d["id"], "target": row["id"], "relation": row["relation"]})
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": store.status(),
        "documents": docs,
        "graph": {"nodes": list(nodes.values()), "edges": edges},
        "demo": demo or {},
    }
