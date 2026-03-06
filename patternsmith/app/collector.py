from datetime import datetime, timezone
import time


class EventCollector(object):
    def __init__(self, cfg, db, ha_client, logger):
        self.cfg = cfg
        self.db = db
        self.ha = ha_client
        self.logger = logger
        self._last_states = {}

    def poll_once(self):
        states = self.ha.get_states()
        current = {}

        for item in states:
            entity_id = item.get("entity_id")
            if not entity_id:
                continue

            if self.cfg.is_excluded(entity_id):
                continue

            if not self.cfg.is_domain_included(entity_id):
                if entity_id != "sun.sun":
                    continue

            state = item.get("state")
            attrs = item.get("attributes", {})
            context = item.get("context", {}) or {}
            domain = entity_id.split(".", 1)[0]

            current[entity_id] = {
                "state": state,
                "attributes": attrs,
                "context": context,
                "domain": domain,
            }

            previous = self._last_states.get(entity_id)
            if previous is None:
                continue

            if previous["state"] != state:
                event = {
                    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "entity_id": entity_id,
                    "domain": domain,
                    "old_state": previous["state"],
                    "new_state": state,
                    "attributes": attrs,
                    "context_user_id": context.get("user_id"),
                    "context_id": context.get("id"),
                    "source": "manual" if context.get("user_id") else "unknown",
                    "is_manual": bool(context.get("user_id")),
                }
                self.db.insert_event(event)
                self.logger.info(
                    "State change: %s %s -> %s manual=%s",
                    entity_id,
                    previous["state"],
                    state,
                    event["is_manual"],
                )

        self._last_states = current

    def run_forever(self, interval_seconds=5):
        self.logger.info("Collector started, polling every %s seconds", interval_seconds)
        while True:
            try:
                self.poll_once()
            except Exception as exc:
                self.logger.exception("Collector error: %s", exc)
            time.sleep(interval_seconds)
