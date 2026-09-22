"""Knowledge Graph — relational now, graph-ready later."""
from __future__ import annotations

import time
import uuid

_NODES: dict[str, dict] = {}
_EDGES: list[dict] = []


def add_node(kind: str, ref_id: str, label: str) -> dict:
    node = {"id": str(uuid.uuid4())[:8], "kind": kind, "ref_id": ref_id,
            "label": label, "created_at": time.time()}
    _NODES[node["id"]] = node
    return node


def add_edge(from_node: str, to_node: str, relation: str) -> dict:
    edge = {"from": from_node, "to": to_node, "relation": relation,
            "created_at": time.time()}
    _EDGES.append(edge)
    return edge


def graph() -> dict:
    return {"nodes": list(_NODES.values()), "edges": list(_EDGES)}


def neighbors(ref_id: str) -> list[dict]:
    node_ids = [n["id"] for n in _NODES.values() if n["ref_id"] == ref_id]
    out = []
    for e in _EDGES:
        if e["from"] in node_ids and e["to"] in _NODES:
            out.append({"relation": e["relation"], "node": _NODES[e["to"]]})
        elif e["to"] in node_ids and e["from"] in _NODES:
            out.append({"relation": f"inverse:{e['relation']}", "node": _NODES[e["from"]]})
    return out
