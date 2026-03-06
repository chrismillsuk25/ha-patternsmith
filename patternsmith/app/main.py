import logging
import threading
import time
from flask import Flask, render_template, jsonify, redirect, url_for
from waitress import serve

from .config_runtime import RuntimeConfig
from .db import Database
from .ha_client import HomeAssistantClient
from .collector import EventCollector
from .miner import is_candidate_manual_action, find_trigger_candidates, build_suggestion


cfg = RuntimeConfig()

logging.basicConfig(
    level=getattr(logging, cfg.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("patternsmith")

db = Database(cfg.db_path)
db.init()

ha = HomeAssistantClient(cfg.ha_base_url, cfg.supervisor_token)
collector = EventCollector(cfg, db, ha, logger)

app = Flask(__name__, template_folder="templates")


def miner_loop():
    logger.info("Miner loop started")
    while True:
        try:
            recent_rows = db.get_recent_events(seconds=cfg.lookback_seconds)
            action_events = [dict(r) for r in recent_rows if is_candidate_manual_action(dict(r), cfg)]

            for action_event in action_events:
                candidates = find_trigger_candidates(recent_rows, action_event)
                for candidate in candidates:
                    repetitions = db.find_matching_pattern_count(
                        candidate["trigger_entity_id"],
                        candidate.get("trigger_to_state"),
                        action_event["entity_id"],
                        "turn_on" if action_event["new_state"] == "on" else "turn_off",
                    ) + 1

                    if repetitions < cfg.min_repetitions:
                        continue

                    if db.suggestion_exists(
                        candidate["trigger_entity_id"],
                        candidate.get("trigger_to_state"),
                        action_event["entity_id"],
                        "turn_on" if action_event["new_state"] == "on" else "turn_off",
                    ):
                        continue

                    suggestion = build_suggestion(candidate, action_event, repetitions)
                    db.insert_suggestion(suggestion)
                    logger.info(
                        "Created suggestion: %s -> %s",
                        suggestion["trigger_entity_id"],
                        suggestion["action_entity_id"],
                    )

        except Exception as exc:
            logger.exception("Miner error: %s", exc)

        time.sleep(15)


@app.route("/")
def index():
    suggestions = db.get_suggestions()
    return render_template("index.html", suggestions=suggestions)


@app.route("/api/suggestions")
def api_suggestions():
    rows = db.get_suggestions()
    return jsonify([dict(r) for r in rows])


@app.route("/suggestion/<int:suggestion_id>/<status>", methods=["POST"])
def update_suggestion_status(suggestion_id, status):
    allowed = {"accepted", "dismissed", "snoozed"}
    if status not in allowed:
        return jsonify({"ok": False, "error": "invalid status"}), 400
    db.set_suggestion_status(suggestion_id, status)
    return redirect(url_for("index"))


def start_background_threads():
    collector_thread = threading.Thread(target=collector.run_forever, daemon=True)
    collector_thread.start()

    pattern_thread = threading.Thread(target=miner_loop, daemon=True)
    pattern_thread.start()


if __name__ == "__main__":
    logger.info("Starting PatternSmith")
    start_background_threads()
    serve(app, host="0.0.0.0", port=8099)
