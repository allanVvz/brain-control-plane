"""Node Markdown PATCH + FAQ append (Gerar updates the same FAQ, no new node).

Monkeypatched; no live Supabase.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
API_DIR = ROOT / "api"
for path in (API_DIR, ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def _req():
    return SimpleNamespace(state=SimpleNamespace(user={"id": "u1", "role": "admin"}))


# ── PATCH /knowledge/graph-nodes/{id} ────────────────────────────────────────

def test_update_graph_node_persists_markdown_to_metadata(monkeypatch):
    from routes import graph

    monkeypatch.setattr(graph.auth_service, "assert_persona_access", lambda *a, **k: None)
    monkeypatch.setattr(graph.supabase_client, "get_knowledge_node", lambda nid: {
        "id": "p1", "node_type": "product", "persona_id": "per1", "metadata": {"x": 1},
    })
    captured = {}
    monkeypatch.setattr(graph.supabase_client, "update_knowledge_node", lambda nid, data, **k: captured.update({"node": (nid, data)}) or {"id": nid, **data})
    monkeypatch.setattr(graph, "_knowledge_item_for_graph_node", lambda node: None)
    monkeypatch.setattr(graph, "emit", lambda *a, **k: None)
    monkeypatch.setattr(graph, "current_actor", lambda req: "u1")

    body = graph.GraphNodeUpdateBody(markdown="# Produto\nLente Prizm UV400", title="Plantaris")
    out = graph.update_graph_node("gn:p1", body, _req())

    assert out["ok"] is True
    assert out["reverted_to_draft"] is False
    _, data = captured["node"]
    assert data["metadata"]["markdown"] == "# Produto\nLente Prizm UV400"
    assert data["title"] == "Plantaris"


def test_update_graph_node_faq_reverts_and_rebuilds_embedded(monkeypatch):
    from routes import graph

    monkeypatch.setattr(graph.auth_service, "assert_persona_access", lambda *a, **k: None)
    monkeypatch.setattr(graph.supabase_client, "get_knowledge_node", lambda nid: {
        "id": "f1", "node_type": "faq", "persona_id": "per1", "source_table": "knowledge_items",
        "source_id": "ki1", "metadata": {},
    })
    monkeypatch.setattr(graph.supabase_client, "update_knowledge_node", lambda nid, data, **k: {"id": nid, **data})
    monkeypatch.setattr(graph, "_knowledge_item_for_graph_node", lambda node: {"id": "ki1", "status": "embedded"})
    item_updates = {}
    monkeypatch.setattr(graph.supabase_client, "update_knowledge_item", lambda iid, data: item_updates.update(data))
    withdrawn = {}
    monkeypatch.setattr(graph.supabase_client, "withdraw_faq_from_embedded", lambda iid: withdrawn.update({"id": iid}))
    rebuilt = {}
    monkeypatch.setattr(graph.embedded_markdown, "rebuild_embedded_markdown", lambda pid: rebuilt.update({"pid": pid}))
    monkeypatch.setattr(graph, "emit", lambda *a, **k: None)
    monkeypatch.setattr(graph, "current_actor", lambda req: "u1")

    out = graph.update_graph_node("gn:f1", graph.GraphNodeUpdateBody(markdown="novo corpo"), _req())

    assert out["reverted_to_draft"] is True
    assert item_updates["status"] == "pending"
    assert withdrawn["id"] == "ki1"
    assert rebuilt["pid"] == "per1"


def test_update_graph_node_blocks_protected(monkeypatch):
    from routes import graph
    from fastapi import HTTPException

    monkeypatch.setattr(graph.auth_service, "assert_persona_access", lambda *a, **k: None)
    monkeypatch.setattr(graph.supabase_client, "get_knowledge_node", lambda nid: {"id": "e1", "node_type": "embedded", "persona_id": "per1"})
    try:
        graph.update_graph_node("gn:e1", graph.GraphNodeUpdateBody(markdown="x"), _req())
        assert False, "expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400


# ── /sofia/faq/append ────────────────────────────────────────────────────────

