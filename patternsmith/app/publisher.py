def build_yaml(trigger_entity_id, trigger_to_state, action_entity_id, action_service, condition_type=None, condition_value=None):
    lines = []
    lines.append("alias: PatternSmith suggestion - {0}".format(action_entity_id))
    lines.append("triggers:")
    lines.append("  - trigger: state")
    lines.append("    entity_id: {0}".format(trigger_entity_id))
    if trigger_to_state:
        lines.append('    to: "{0}"'.format(trigger_to_state))

    lines.append("conditions:")
    if condition_type == "sun":
        lines.append("  - condition: state")
        lines.append("    entity_id: sun.sun")
        lines.append("    state: {0}".format(condition_value))
    else:
        lines.append("  - condition: template")
        lines.append("    value_template: '{{ true }}'")

    lines.append("actions:")
    domain = action_entity_id.split(".", 1)[0]
    lines.append("  - action: {0}.{1}".format(domain, action_service))
    lines.append("    target:")
    lines.append("      entity_id: {0}".format(action_entity_id))
    lines.append("mode: single")
    return "\n".join(lines)
