from __future__ import annotations

import argparse
import os
from datetime import date
from datetime import datetime
from pathlib import Path

from generate_daily import generate_daily
from lesson_models import BASE_DIR
from lesson_models import history_for_date
from lesson_models import mark_history_sent
from lesson_models import read_json
from lesson_models import today_in_timezone
from lesson_models import write_json
from render_epub import render_lesson_epub
from render_pdf import render_lesson_pdf
from send_to_kindle import load_env_file
from send_to_kindle import send_pdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate, render, and optionally send today's lesson.")
    parser.add_argument("--date", help="YYYY-MM-DD. Defaults to today in Europe/Berlin.")
    parser.add_argument(
        "--force-type",
        choices=["new_law", "new_strategy", "review", "application", "comparison", "weekly_review"],
        help="Override the learning scheduler for testing.",
    )
    parser.add_argument("--no-state-update", action="store_true")
    parser.add_argument("--allow-duplicate", action="store_true")
    parser.add_argument("--send", action="store_true", help="Send via SMTP. Default is dry-run only.")
    parser.add_argument("--skip-if-sent", action="store_true", help="Exit without sending if today's history is already marked sent.")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--send-retries", type=int, default=3)
    parser.add_argument("--sync-notion", action="store_true", help="Refresh curriculum JSON from Notion before choosing the lesson.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)
    if args.sync_notion:
        from sync_notion import sync_all

        token = os.environ.get("NOTION_API_KEY", "")
        if not token:
            raise RuntimeError("Set NOTION_API_KEY in .env before using --sync-notion.")
        sync_all(BASE_DIR / "config" / "notion_sources.json", token)

    lesson_date = date.fromisoformat(args.date) if args.date else today_in_timezone()
    state_path = BASE_DIR / "state" / "learning_state.json"
    if args.skip_if_sent and not args.no_state_update and state_path.exists():
        existing_state = read_json(state_path)
        existing_history = history_for_date(existing_state, lesson_date)
        if existing_history and existing_history.get("sent_at"):
            print(f"Already sent for {lesson_date}: {existing_history.get('title', 'Tagesdosis Strategie & Macht')}")
            return

    lesson_json = generate_daily(
        lesson_date,
        force_type=args.force_type,
        update_state=not args.no_state_update,
        allow_duplicate=args.allow_duplicate,
    )
    pdf_path = render_lesson_pdf(lesson_json)
    epub_path = render_lesson_epub(lesson_json)
    print(f"Lesson JSON: {lesson_json}")
    print(f"PDF archive: {pdf_path}")
    print(f"Kindle EPUB: {epub_path}")
    send_pdf(epub_path, dry_run=not args.send, env_file=args.env_file, retries=args.send_retries)
    if args.send and not args.no_state_update:
        state = read_json(state_path)
        rel_epub = str(epub_path.relative_to(BASE_DIR))
        mark_history_sent(state, lesson_date, datetime.now().isoformat(timespec="seconds"), rel_epub)
        write_json(state_path, state)


if __name__ == "__main__":
    main()
