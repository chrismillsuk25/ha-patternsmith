import json
import os


def _parse_json_env(name, default):
    raw = os.getenv(name, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default


class RuntimeConfig(object):
    def __init__(self):
        self.log_level = os.getenv("PATTERNSMITH_LOG_LEVEL", "info")
        self.retention_days = int(os.getenv("PATTERNSMITH_RETENTION_DAYS", "30"))
        self.lookback_seconds = int(os.getenv("PATTERNSMITH_LOOKBACK_SECONDS", "120"))
        self.min_repetitions = int(os.getenv("PATTERNSMITH_MIN_REPETITIONS", "3"))

        self.include_domains = _parse_json_env(
            "PATTERNSMITH_INCLUDE_DOMAINS",
            ["light", "switch", "fan", "binary_sensor", "sensor"],
        )
        self.safe_action_domains = _parse_json_env(
            "PATTERNSMITH_SAFE_ACTION_DOMAINS",
            ["light", "switch", "fan"],
        )
        self.exclude_entities = _parse_json_env(
            "PATTERNSMITH_EXCLUDE_ENTITIES",
            [],
        )

        self.data_dir = os.getenv("PATTERNSMITH_DATA_DIR", "/data")
        self.db_path = os.path.join(self.data_dir, "patternsmith.db")
        self.ha_base_url = "http://supervisor/core/api"
        self.supervisor_url = "http://supervisor"
        self.supervisor_token = os.getenv("SUPERVISOR_TOKEN", "")

    def is_domain_included(self, entity_id):
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        return domain in self.include_domains

    def is_action_domain_safe(self, entity_id):
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        return domain in self.safe_action_domains

    def is_excluded(self, entity_id):
        return entity_id in self.exclude_entities
