# Home Assistant Add-on: PatternSmith

PatternSmith observes repeated manual actions in Home Assistant and suggests possible automations.

## Features

- Watches entity state changes
- Stores event history in SQLite
- Detects repeated trigger -> action patterns
- Shows suggestions in a web UI
- Exports YAML snippets for automations

## Configuration

log_level: info
retention_days: 30
lookback_seconds: 120
min_repetitions: 3
include_domains:
  - light
  - switch
  - fan
  - binary_sensor
  - sensor
safe_action_domains:
  - light
  - switch
  - fan
exclude_entities: []

## Notes

This starter version focuses on:
- motion + darkness -> light on
- binary sensor / state change -> manual action patterns

It does not automatically create Home Assistant automations yet.
