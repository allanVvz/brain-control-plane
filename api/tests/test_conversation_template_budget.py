import json
from pathlib import Path


TEMPLATE = Path(__file__).parents[1] / "n8n-workflows" / "persona-conversation-template.json"


def test_conversation_template_bounds_ranked_rag_context_without_persona_rules():
    workflow = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    code = next(node for node in workflow["nodes"] if node["id"] == "model_request")["parameters"]["jsCode"]

    assert "const promptTargetTokens = 19000" in code
    assert "prompt.approved_chunks.length > 1" in code
    assert "prompt.approved_chunks.pop()" in code
    assert "retained_chunk_count" in code
    assert "prompt_budget_exceeded" in code
    assert "aurora" not in code.lower()
    assert "tock-fatal" not in code.lower()
