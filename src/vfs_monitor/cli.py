from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from vfs_monitor.config import load_settings
from vfs_monitor.monitor import run_monitor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vfs-monitor")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--notify", action="store_true")
    check.add_argument("--persist-state", action="store_true")
    check.add_argument("--heartbeat", action="store_true")
    check.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command != "check":
        parser.error("unsupported command")

    settings = load_settings()
    result = run_monitor(
        settings,
        notify=args.notify,
        persist_state=args.persist_state,
        update_daily_heartbeat=args.heartbeat,
    )
    detection = result.detection
    if args.json:
        detection_payload = asdict(detection)
        detection_payload["status"] = detection.status.value
        print(
            json.dumps(
                {
                    "detection": detection_payload,
                    "notification_sent": result.notification_sent,
                    "heartbeat_updated": result.heartbeat_updated,
                    "event_type": result.event_type,
                    "decision_reason": result.decision_reason,
                },
                indent=2,
                default=str,
            )
        )
        return 0

    print(f"Centre: {detection.location}")
    print(f"Category: {detection.category or 'unknown'}")
    print(f"Status: {detection.status.value.upper()}")
    print(f"Available dates: {', '.join(detection.available_dates) if detection.available_dates else 'none'}")
    print(f"Available times: {', '.join(detection.available_times) if detection.available_times else 'none'}")
    print(f"Method: {detection.method}")
    print(f"Signals: {'; '.join(detection.signals) if detection.signals else 'none'}")
    print(f"Event: {result.event_type}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
