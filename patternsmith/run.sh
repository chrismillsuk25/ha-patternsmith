#!/usr/bin/with-contenv bashio
set -e

export PATTERNSMITH_LOG_LEVEL="$(bashio::config 'log_level')"
export PATTERNSMITH_RETENTION_DAYS="$(bashio::config 'retention_days')"
export PATTERNSMITH_LOOKBACK_SECONDS="$(bashio::config 'lookback_seconds')"
export PATTERNSMITH_MIN_REPETITIONS="$(bashio::config 'min_repetitions')"

export PATTERNSMITH_INCLUDE_DOMAINS="$(bashio::config 'include_domains')"
export PATTERNSMITH_SAFE_ACTION_DOMAINS="$(bashio::config 'safe_action_domains')"
export PATTERNSMITH_EXCLUDE_ENTITIES="$(bashio::config 'exclude_entities')"

export PATTERNSMITH_DATA_DIR="/data"
export PATTERNSMITH_OPTIONS_JSON="/data/options.json"

mkdir -p /data

echo "[PatternSmith] Starting..."
exec python -m app.main
