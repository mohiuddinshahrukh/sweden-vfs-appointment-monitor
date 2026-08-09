from __future__ import annotations

import argparse
import json
import time
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
    watch = subparsers.add_parser("watch")
    watch.add_argument("--notify", action="store_true")
    watch.add_argument("--persist-state", action="store_true")
    watch.add_argument("--heartbeat", action="store_true")
    watch.add_argument("--json", action="store_true")
    watch.add_argument("--interval-minutes", type=int, default=15)
    open_browser = subparsers.add_parser("open-browser")
    open_browser.add_argument(
        "--headed",
        action="store_true",
        help="force a visible browser window even if VFS_BROWSER_HEADLESS=true",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    settings = load_settings()
    if args.command == "open-browser":
        from vfs_monitor.browser import open_persistent_browser_for_manual_login

        open_persistent_browser_for_manual_login(
            booking_url=settings.booking_url,
            browser_user_data_dir=settings.browser_user_data_dir,
            browser_profile_directory=settings.browser_profile_directory,
            browser_channel=settings.browser_channel,
            browser_executable_path=settings.browser_executable_path,
            timeout_ms=settings.browser_timeout_ms,
            headless=False if args.headed else settings.browser_headless,
        )
        return 0
    if args.command == "watch":
        while True:
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
            else:
                print(
                    f"{detection.checked_at} {detection.status.value.upper()} "
                    f"{result.event_type} {detection.method}"
                )
            time.sleep(max(args.interval_minutes, 1) * 60)
    if args.command != "check":
        parser.error("unsupported command")

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
    print(f"Sub-category: {detection.subcategory or 'unknown'}")
    print(f"Status: {detection.status.value.upper()}")
    print(f"Available dates: {', '.join(detection.available_dates) if detection.available_dates else 'none'}")
    print(f"Available times: {', '.join(detection.available_times) if detection.available_times else 'none'}")
    print(f"Method: {detection.method}")
    print(f"Signals: {'; '.join(detection.signals) if detection.signals else 'none'}")
    print(f"Event: {result.event_type}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
