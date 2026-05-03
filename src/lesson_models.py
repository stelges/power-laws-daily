from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9 fallback.
    ZoneInfo = None


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TIMEZONE = "Europe/Berlin"
KIND_LABELS = {
    "law": "Gesetz",
    "strategy": "Strategie",
}


@dataclass(frozen=True)
class CurriculumItem:
    id: str
    kind: str
    number: int
    title: str
    summary: str
    mechanic: str
    why: str
    example: str
    dark_application: str
    countermeasure: str
    recall_questions: List[str]
    daily_task: str
    tags: List[str]
    links: List[str]
    source: Dict[str, Any]

    @property
    def label(self) -> str:
        return f"{KIND_LABELS.get(self.kind, self.kind)} {self.number}: {self.title}"


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def today_in_timezone(timezone: str = DEFAULT_TIMEZONE) -> date:
    if ZoneInfo is None:
        return date.today()
    return datetime.now(ZoneInfo(timezone)).date()


def parse_iso_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


def iso(value: date) -> str:
    return value.isoformat()


def load_curriculum(base_dir: Path = BASE_DIR) -> List[CurriculumItem]:
    files = [
        base_dir / "curriculum" / "laws_48.json",
        base_dir / "curriculum" / "strategies_33.json",
    ]
    items: List[CurriculumItem] = []
    for file_path in files:
        data = read_json(file_path)
        for raw in data.get("items", []):
            items.append(
                CurriculumItem(
                    id=raw["id"],
                    kind=raw["kind"],
                    number=int(raw["number"]),
                    title=raw["title"],
                    summary=raw.get("summary", ""),
                    mechanic=raw.get("mechanic", ""),
                    why=raw.get("why", ""),
                    example=raw.get("example", ""),
                    dark_application=raw.get("dark_application", ""),
                    countermeasure=raw.get("countermeasure", ""),
                    recall_questions=list(raw.get("recall_questions", [])),
                    daily_task=raw.get("daily_task", ""),
                    tags=list(raw.get("tags", [])),
                    links=list(raw.get("links", [])),
                    source=dict(raw.get("source", {})),
                )
            )
    return sorted(items, key=lambda item: (item.kind, item.number))


def item_map(items: Iterable[CurriculumItem]) -> Dict[str, CurriculumItem]:
    return {item.id: item for item in items}


def ensure_item_state(state: Dict[str, Any], items: Iterable[CurriculumItem]) -> None:
    state.setdefault("items", {})
    for item in items:
        state["items"].setdefault(
            item.id,
            {
                "introduced": False,
                "introduced_on": None,
                "last_seen": None,
                "next_due": None,
                "review_count": 0,
                "times_seen": 0,
            },
        )


def introduced_items(state: Dict[str, Any], items: Iterable[CurriculumItem]) -> List[CurriculumItem]:
    return [item for item in items if state["items"].get(item.id, {}).get("introduced")]


def unintroduced_items(state: Dict[str, Any], items: Iterable[CurriculumItem], kind: str) -> List[CurriculumItem]:
    return [
        item
        for item in sorted(items, key=lambda candidate: candidate.number)
        if item.kind == kind and not state["items"].get(item.id, {}).get("introduced")
    ]


def due_items(state: Dict[str, Any], items: Iterable[CurriculumItem], today: date) -> List[CurriculumItem]:
    due: List[CurriculumItem] = []
    for item in items:
        item_state = state["items"].get(item.id, {})
        if not item_state.get("introduced"):
            continue
        next_due = parse_iso_date(item_state.get("next_due"))
        if next_due and next_due <= today:
            due.append(item)
    return sorted(
        due,
        key=lambda item: (
            parse_iso_date(state["items"][item.id].get("next_due")) or today,
            state["items"][item.id].get("review_count", 0),
            item.kind,
            item.number,
        ),
    )


def count_introduced(state: Dict[str, Any], kind: Optional[str] = None) -> int:
    total = 0
    for item_id, item_state in state.get("items", {}).items():
        if not item_state.get("introduced"):
            continue
        if kind is None or item_id.startswith(f"{kind}_"):
            total += 1
    return total


def choose_balanced_new_kind(state: Dict[str, Any], items: Iterable[CurriculumItem]) -> Optional[str]:
    law_remaining = unintroduced_items(state, items, "law")
    strategy_remaining = unintroduced_items(state, items, "strategy")
    if not law_remaining and not strategy_remaining:
        return None
    if not law_remaining:
        return "strategy"
    if not strategy_remaining:
        return "law"

    laws_done = count_introduced(state, "law")
    strategies_done = count_introduced(state, "strategy")
    law_progress = laws_done / max(1, laws_done + len(law_remaining))
    strategy_progress = strategies_done / max(1, strategies_done + len(strategy_remaining))
    return "law" if law_progress <= strategy_progress else "strategy"


def schedule_next_review(item_state: Dict[str, Any], today: date, intervals: List[int]) -> None:
    review_count = int(item_state.get("review_count", 0))
    index = min(review_count, len(intervals) - 1)
    item_state["next_due"] = iso(today + timedelta(days=int(intervals[index])))


def mark_seen(state: Dict[str, Any], item: CurriculumItem, today: date) -> None:
    intervals = state.get("settings", {}).get("review_intervals_days", [1, 3, 7, 14, 30, 60])
    item_state = state["items"][item.id]
    if not item_state.get("introduced"):
        item_state["introduced"] = True
        item_state["introduced_on"] = iso(today)
        item_state["review_count"] = 0
    else:
        item_state["review_count"] = int(item_state.get("review_count", 0)) + 1
    item_state["last_seen"] = iso(today)
    item_state["times_seen"] = int(item_state.get("times_seen", 0)) + 1
    schedule_next_review(item_state, today, intervals)


def add_history(state: Dict[str, Any], lesson: Dict[str, Any]) -> None:
    state.setdefault("history", [])
    state["history"].append(
        {
            "date": lesson["date"],
            "type": lesson["today_key"],
            "title": lesson["focus_title"],
            "items": lesson.get("source_item_ids", []),
            "output_json": lesson.get("output_json"),
            "output_pdf": lesson.get("output_pdf"),
        }
    )


def mark_history_sent(state: Dict[str, Any], lesson_date: date, sent_at: str, output_epub: Optional[str]) -> None:
    entry = history_for_date(state, lesson_date)
    if not entry:
        return
    entry["sent_at"] = sent_at
    if output_epub:
        entry["output_epub"] = output_epub


def history_for_date(state: Dict[str, Any], lesson_date: date) -> Optional[Dict[str, Any]]:
    target = iso(lesson_date)
    for entry in state.get("history", []):
        if entry.get("date") == target:
            return entry
    return None


def clean_for_filename(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "lektion"
