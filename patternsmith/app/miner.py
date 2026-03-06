from datetime import datetime, timezone
from .publisher import build_yaml


MANUAL_ACTION_STATES = {
    "light": {"on", "off"},
    "switch": {"on", "off"},
    "fan": {"on", "off"},
}


def _entity_domain(entity_id):
    return entity_id.split(".", 1)[0] if "." in entity_id else ""


def is_candidate_manual_action(event, cfg):
    entity_id = event["entity_id"]
    domain = _entity_domain(entity_id)

    if not cfg.is_action_domain_safe(entity_id):
        return False

    if event.get("new_state") is None:
        return False

    if domain not in MANUAL_ACTION_STATES:
        return False

    if event["new_state"] not in MANUAL_ACTION_STATES[domain]:
        return False

    return bool(event.get("is_manual"))


def find_trigger_candidates(recent_events, action_event):
    candidates = []

    for row in recent_events:
        if row["entity_id"] == action_event["entity_id"]:
            continue

        domain = row["domain"]

        if domain == "binary_sensor" and row["new_state"] in ("on", "off"):
            candidates.append({
                "trigger_entity_id": row["entity_id"],
                "trigger_to_state": row["new_state"],
                "condition_type": None,
                "condition_value": None,
            })

        if row["entity_id"] == "sun.sun" and row["new_state"] in ("above_horizon", "below_horizon"):
            candidates.append({
                "trigger_entity_id": row["entity_id"],
                "trigger_to_state": row["new_state"],
                "condition_type": "sun",
                "condition_value": row["new_state"],
            })

    return candidates


def score_pattern(repetitions, has_condition=False):
    base = min(0.5 + (repetitions * 0.1), 0.95)
    if has_condition:
        base += 0.03
    return min(base, 0.99)


def build_suggestion(candidate, action_event, repetitions):
    has_condition = candidate.get("condition_type") is not None
    confidence = score_pattern(repetitions, has_condition=has_condition)
    action_service = "turn_on" if action_event["new_state"] == "on" else "turn_off"

    yaml_preview = build_yaml(
        trigger_entity_id=candidate["trigger_entity_id"],
        trigger_to_state=candidate.get("trigger_to_state"),
        action_entity_id=action_event["entity_id"],
        action_service=action_service,
        condition_type=candidate.get("condition_type"),
        condition_value=candidate.get("condition_value"),
    )

    why = (
        "Observed repeated manual action: {action_entity} -> {new_state} "
        "after {trigger_entity} changed to {trigger_state}. Repetitions: {reps}."
    ).format(
        action_entity=action_event["entity_id"],
        new_state=action_event["new_state"],
        trigger_entity=candidate["trigger_entity_id"],
        trigger_state=candidate.get("trigger_to_state"),
        reps=repetitions,
    )

    return {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "trigger_entity_id": candidate["trigger_entity_id"],
        "trigger_to_state": candidate.get("trigger_to_state"),
        "condition_type": candidate.get("condition_type"),
        "condition_value": candidate.get("condition_value"),
        "action_entity_id": action_event["entity_id"],
        "action_service": action_service,
        "confidence": confidence,
        "repetitions": repetitions,
        "yaml_preview": yaml_preview,
        "why_text": why,
        "status": "new",
    }
