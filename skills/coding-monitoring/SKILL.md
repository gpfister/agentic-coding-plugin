---
name: coding-monitoring
description: >-
  Standalone worker subagent for background telemetry, application log surveillance,
  and serial console monitoring with automatic error detection and pause gates.
---

# Coding Monitoring (`@monitoring`)

The `coding-monitoring` subagent streams and watches continuous output sources to intercept crashes, errors, or anomalies early.

## Capabilities

- **Log & Stream Surveillance**: Tails application logs, Docker stdout, or serial port streams (`/dev/tty*`).
- **Error Detection**: Detects exceptions, stack traces, and custom alert conditions.
- **Intervention Gate**: Pauses monitoring immediately when an anomaly is discovered, formulating a structured `MonitoringAlert` and asking the user via `ask_question` how to proceed.
- **Multiple Concurrent Instances**: Run separate monitors simultaneously, differentiated by target identifiers (e.g., `coding-monitoring-serial`, `coding-monitoring-backend`).

## Triggering Monitoring

- Type `@monitoring watch serial port /dev/ttyUSB0 at 115200 baud`
- Or prompt: "Start monitoring server logs at /var/log/app.log and alert me on any 5xx errors."
