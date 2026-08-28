"""Domain service for journey events and state transitions."""

from fastapi import HTTPException

from schemas.journey import JourneyEventBody, JourneyStateBody
from services import agents_service, event_emitter, supabase_client


def lead_or_404(lead_ref: int) -> dict:
    lead = supabase_client.get_lead_by_ref(lead_ref) or {}
    if not lead or not lead.get("persona_id"):
        raise HTTPException(404, "Lead not found")
    return lead


def record_journey_event(
    lead_ref: int, body: JourneyEventBody, responsible_user_id: str | None,
) -> dict:
    lead = lead_or_404(lead_ref)
    try:
        return supabase_client.record_conversation_journey_event(
            p_persona_id=lead["persona_id"], p_lead_ref=lead_ref,
            p_event_type=body.event_type,
            p_idempotency_key=body.idempotency_key, p_source=body.source,
            p_occurred_at=body.occurred_at.isoformat(), p_external_ref=body.external_ref,
            p_amount_minor=body.amount_minor, p_currency=body.currency,
            p_items=body.items, p_metadata=body.metadata,
            p_responsible_user_id=responsible_user_id,
        )
    except Exception as exc:
        raise HTTPException(409, "Journey event could not be recorded") from exc


def set_journey_state(
    lead_ref: int, body: JourneyStateBody, responsible_user_id: str | None,
    *, offering: str = "sales",
) -> dict:
    lead = lead_or_404(lead_ref)
    try:
        result = supabase_client.set_conversation_journey_state(
            p_persona_id=lead["persona_id"], p_lead_ref=lead_ref,
            p_target=body.target, p_source=body.source,
            p_occurred_at=body.occurred_at.isoformat(), p_offering=offering,
            p_responsible_user_id=responsible_user_id, p_metadata=body.metadata,
        )
    except Exception as exc:
        raise HTTPException(409, state_conflict_detail(exc)) from exc

    if result.get("changed") and result.get("journey_closed"):
        resumed = agents_service.resume_lead(lead_ref)
        result["ai_resumed"] = bool(resumed)
        if resumed:
            event_emitter.emit(
                "lead.ai_resumed", entity_type="lead", entity_id=str(lead_ref),
                payload={"ai_paused": False, "by": "journey_closed", "target": body.target},
            )
            result["notice"] = agents_service.reactivation_notice(
                lead_ref, reason="journey_closed"
            )
    elif result.get("changed") and body.target == "qualificado":
        paused = agents_service.pause_lead(lead_ref)
        result["ai_paused"] = bool(paused)
        if paused:
            event_emitter.emit(
                "lead.ai_paused", entity_type="lead", entity_id=str(lead_ref),
                payload={"ai_paused": True, "by": "journey_qualified", "target": body.target},
            )
    return result


def state_conflict_detail(exc: Exception) -> str:
    text = str(exc)
    if "a newer order already exists" in text:
        return "Ja existe um pedido mais novo para esta lead; nao da para reabrir o anterior."
    if "lead already converted" in text:
        return "Esta lead ja converteu: qualificado nao esta mais disponivel."
    if "no journey for this lead" in text:
        return "Esta lead ainda nao tem pedido."
    return "Journey state could not be changed"
