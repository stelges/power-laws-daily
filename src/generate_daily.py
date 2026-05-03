from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from lesson_models import (
    BASE_DIR,
    CurriculumItem,
    add_history,
    choose_balanced_new_kind,
    clean_for_filename,
    count_introduced,
    due_items,
    ensure_item_state,
    history_for_date,
    introduced_items,
    iso,
    item_map,
    load_curriculum,
    mark_seen,
    read_json,
    today_in_timezone,
    unintroduced_items,
    write_json,
)


TODAY_LABELS = {
    "new_law": "Neues Gesetz",
    "new_strategy": "Neue Strategie",
    "review": "Wiederholung",
    "application": "Anwendung / Mini-Fallanalyse",
    "comparison": "Vergleich",
    "weekly_review": "Wochenreview",
}


THEME_LABELS = {
    "status": "Status",
    "loyalität": "Loyalität",
    "informationskontrolle": "Informationskontrolle",
    "kommunikation": "Kommunikation",
    "ruf": "Ruf",
    "aufmerksamkeit": "Aufmerksamkeit",
    "selbstführung": "Selbstführung",
    "muster": "Muster",
    "ruhe": "Ruhe",
    "dringlichkeit": "Dringlichkeit",
    "gruppe": "Gruppendruck",
    "segmentierung": "Organisation",
}


def _theme(item: CurriculumItem) -> str:
    for tag in item.tags:
        if tag != "notion-cache":
            return THEME_LABELS.get(tag, tag.replace("_", " ").title())
    return "Einfluss"


def _bullet_list(items: List[str]) -> str:
    return "\n".join(f"* {item}" for item in items)


def _today_intro(item: CurriculumItem, today_key: str) -> str:
    previous = "Du hast bisher an Sichtbarkeit, Ruf, Status und Selbstführung gearbeitet."
    lead = "Heute kommt ein Gesetz dazu, das dein Verhalten im Hintergrund steuert:"
    if item.kind == "strategy":
        previous = "Du hast bisher an Machtmechaniken, Selbstführung und strategischer Wahrnehmung gearbeitet."
        lead = "Heute kommt eine Strategie dazu, die dein Verhalten im Hintergrund steuert:"
    return (
        f"{previous}\n"
        f"{lead}\n\n"
        f"{item.summary}"
    )


def _recall_questions(item: CurriculumItem) -> List[str]:
    theme = _theme(item)
    if item.id == "law_04":
        return [
            "Warum kann es strategisch klüger sein, nicht alles zu sagen, was du weißt?",
            "Wann wirkt jemand kompetenter: wenn er viel redet oder wenn er gezielt spricht?",
            "Hast du schon erlebt, dass jemand sich durch zu viel Reden selbst geschwächt hat?",
        ]
    if item.kind == "law":
        return [
            f"Wo hast du {theme} zuletzt in einer Gruppe oder Konferenz beobachtet?",
            f"Was passiert, wenn jemand {theme} unterschätzt?",
            f"Wie könntest du {item.title} integer nutzen, ohne Spielchen daraus zu machen?",
        ]
    return [
        f"Welche innere Reaktion könnte {item.title} bei dir auslösen?",
        "Welche Situation der letzten Woche würdest du mit dieser Strategie neu lesen?",
        "Was wäre heute ein kleiner, ruhiger Schritt statt einer automatischen Reaktion?",
    ]


def _mechanic_body(item: CurriculumItem) -> str:
    theme = _theme(item)
    if item.id == "law_04":
        return (
            "Viele Menschen reden zu viel, weil sie:\n\n"
            + _bullet_list(
                [
                    "kompetent wirken wollen",
                    "Unsicherheit überspielen",
                    "Kontrolle behalten wollen",
                    "gemocht werden möchten",
                ]
            )
            + "\n\nAber:\n\nWer zu viel spricht, gibt Kontrolle ab.\n\nWarum?\n\n"
            + _bullet_list(
                [
                    "Du verrätst unbeabsichtigt Informationen",
                    "Du machst dich angreifbar",
                    "Du wirkst weniger präzise",
                    "Deine Aussagen verlieren Gewicht",
                ]
            )
            + "\n\nMenschen, die klar und knapp sprechen:\n\n"
            + _bullet_list(
                [
                    "wirken souveräner",
                    "werden ernster genommen",
                    "behalten Deutungshoheit",
                ]
            )
            + "\n\nStrategischer Kern:\n\nKnappheit erhöht Wirkung."
        )
    return (
        f"{item.mechanic or item.summary}\n\n"
        f"Diese Mechanik wirkt, weil soziale Systeme nicht nur auf Fakten reagieren, sondern auf Signale: "
        f"Wer spricht, wer schweigt, wer den Rahmen setzt, wer unsicher wirkt und wer ruhig bleibt.\n\n"
        f"Typische Auslöser:\n\n"
        + _bullet_list(
            [
                f"Menschen wollen {theme} sichern oder zurückgewinnen",
                "Unsicherheit wird durch schnelle Reaktion überspielt",
                "Gruppen bewerten nicht nur Inhalt, sondern Auftreten",
                "kleine Signale werden später als Muster erinnert",
            ]
        )
        + "\n\nStrategischer Kern:\n\n"
        f"{item.summary}"
    )


def _example_body(item: CurriculumItem) -> str:
    if item.id == "law_04":
        return (
            "Diskussion über ein Problem im Unterricht.\n\n"
            "Variante A:\n\n"
            "Du erklärst ausführlich alle Details, Probleme, Gedanken.\n\n"
            "Wirkung:\n\n"
            + _bullet_list(["lang", "unklar", "angreifbar", "weniger Autorität"])
            + "\n\nVariante B:\n\n"
            "Du sagst:\n\n"
            "„Ich sehe das Problem. Mein Vorschlag: Wir testen Lösung X für zwei Wochen und evaluieren dann.“\n\n"
            "Wirkung:\n\n"
            + _bullet_list(["klar", "strukturiert", "führend"])
            + "\n\nDu wirkst automatisch kompetenter - bei weniger Worten."
        )
    return (
        "Situation: Schule / Konferenz.\n\n"
        f"Du bemerkst eine Dynamik rund um {item.title}. Jetzt hast du zwei Möglichkeiten.\n\n"
        "Variante A:\n\n"
        "Du reagierst sofort, erklärst dich zu stark oder versuchst, die Lage frontal zu kontrollieren.\n\n"
        "Wirkung:\n\n"
        + _bullet_list(["reaktiv", "emotional lesbar", "leichter angreifbar", "weniger führend"])
        + "\n\nVariante B:\n\n"
        f"Du hältst kurz inne, liest Interessen und Statussignale, und formulierst einen ruhigen nächsten Schritt.\n\n"
        "Wirkung:\n\n"
        + _bullet_list(["klar", "strukturiert", "souverän", "anschlussfähig"])
        + f"\n\n{item.example}"
    )


def _dark_body(item: CurriculumItem) -> str:
    theme = _theme(item)
    return (
        "Manipulativ genutzt:\n\n"
        + _bullet_list(
            [
                f"{theme} bewusst ausnutzen, statt transparent zu handeln",
                "andere im Unklaren lassen, um Kontrolle zu behalten",
                "Schwächen sammeln, statt Probleme fair zu klären",
                "Druck erzeugen, während man selbst ruhig und überlegen wirkt",
            ]
        )
        + "\n\nDas kann kurzfristig Einfluss verschaffen, erzeugt aber Misstrauen, Abwehr und verdeckte Gegenspieler.\n\n"
        f"{item.dark_application}"
    )


def _countermeasure_body(item: CurriculumItem) -> str:
    return (
        "Wenn jemand diese Mechanik gegen dich nutzt:\n\nAchte auf:\n\n"
        + _bullet_list(
            [
                "unklare Aussagen",
                "plötzliche Informationslücken",
                "emotionalen Druck",
                "strategisches Ausweichen",
            ]
        )
        + "\n\nDein Umgang:\n\n"
        + _bullet_list(
            [
                "stelle präzise Nachfragen",
                "zwinge zur Konkretisierung",
                "dokumentiere Absprachen",
                "bleibe ruhig, nicht defensiv",
            ]
        )
        + "\n\nEigener integrer Weg:\n\n"
        + _bullet_list(
            [
                "klar statt laut handeln",
                "wichtige Dinge bewusst platzieren",
                "Interessen prüfen, bevor du reagierst",
                "keine Spielchen, aber Struktur",
            ]
        )
        + f"\n\nMerksatz:\n\n{_lesson_formula(item)}"
    )


def _mini_task(item: CurriculumItem) -> str:
    if item.id == "law_04":
        return (
            "Achte heute bewusst auf dein Kommunikationsverhalten:\n\n"
            "1. In welcher Situation redest du normalerweise zu viel?\n"
            "2. Wo könntest du heute bewusst kürzer und klarer sein?\n"
            "3. Formuliere eine Aussage im Voraus in einem präzisen Satz.\n\n"
            "Setze es mindestens einmal um."
        )
    return (
        "Achte heute bewusst auf eine reale Situation:\n\n"
        f"1. Wo taucht {item.title} in kleiner Form auf?\n"
        "2. Welche Person, welches Interesse und welche Emotion spielen mit?\n"
        "3. Was ist ein ruhiger, präziser nächster Schritt?\n\n"
        "Setze eine kleine Handlung um oder schreibe sie in drei Sätzen auf."
    )


def _lesson_formula(item: CurriculumItem) -> str:
    formulas = {
        "law_04": "Weniger Worte. Mehr Wirkung.",
        "law_01": "Lass andere größer wirken, wenn du selbst wachsen willst.",
        "law_02": "Nähe beweist nichts. Verhalten beweist mehr.",
        "law_03": "Nicht jede Wahrheit gehört sofort auf den Tisch.",
        "strategy_01": "Der erste Gegner ist oft die eigene Reaktion.",
        "strategy_02": "Lies die Lage, nicht deine alte Wunde.",
    }
    if item.id in formulas:
        return formulas[item.id]
    return item.summary


def _fallback_questions(item: CurriculumItem) -> List[str]:
    if item.recall_questions:
        return item.recall_questions[:3]
    return [
        f"Worum könnte es bei {item.label} im Kern gehen?",
        "Wo könnte diese Mechanik in Schule, Karriere oder Politik auftauchen?",
        "Wie könnte man sie integer nutzen?",
    ]


def _sections_for_item(item: CurriculumItem) -> List[Dict[str, str]]:
    return [
        {
            "heading": "Gesetz(e)" if item.kind == "law" else "Strategie(n)",
            "body": item.label,
        },
        {"heading": "Kernmechanik", "body": _mechanic_body(item)},
        {"heading": "Beispiel: Schule / Konferenz", "body": _example_body(item)},
        {"heading": "Dunkle Anwendung", "body": _dark_body(item)},
        {"heading": "Gegenmittel", "body": _countermeasure_body(item)},
    ]


def _new_item_lesson(today: date, item: CurriculumItem, today_key: str) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "date": iso(today),
        "title": "Tagesdosis Strategie & Macht",
        "today_key": today_key,
        "today": TODAY_LABELS[today_key],
        "focus_title": item.label,
        "subtitle": "Ein klarer Fokus für 10-15 Minuten.",
        "intro": _today_intro(item, today_key),
        "source_item_ids": [item.id],
        "recall_questions": _recall_questions(item),
        "sections": _sections_for_item(item),
        "quote": _lesson_formula(item),
        "mini_task": _mini_task(item),
    }


def _review_lesson(today: date, items: List[CurriculumItem]) -> Dict[str, Any]:
    focus = items[0]
    questions: List[str] = []
    for item in items[:2]:
        questions.extend(_fallback_questions(item)[:2])
    sections = [
        {
            "heading": "Inhalt",
            "body": "Heute geht es nicht um neuen Stoff, sondern um Abruf: Was ist noch aktiv verfügbar?",
        },
        {
            "heading": "Kernmechanik",
            "body": f"Wiederhole zuerst {focus.label}. Formuliere die Mechanik aus dem Kopf, bevor du weiterliest.",
        },
        {"heading": "Warum das funktioniert", "body": focus.why},
        {"heading": "Beispiel", "body": focus.example},
        {"heading": "Dunkle Anwendung", "body": focus.dark_application},
        {"heading": "Gegenmittel", "body": focus.countermeasure},
    ]
    if len(items) > 1:
        sections.append(
            {
                "heading": "Zweiter Abrufanker",
                "body": f"Verbinde anschließend {items[1].label} mit {focus.label}. Wo verstärken sie sich, wo widersprechen sie sich?",
            }
        )
    return {
        "schema_version": 1,
        "date": iso(today),
        "title": "Tagesdosis Strategie & Macht",
        "today_key": "review",
        "today": TODAY_LABELS["review"],
        "focus_title": f"Wiederholung: {focus.label}",
        "subtitle": "Abrufen, verdichten, erneut verfügbar machen.",
        "intro": (
            "Heute geht es nicht um neuen Stoff, sondern um aktiven Abruf.\n\n"
            f"Im Fokus steht {focus.label}. Erst erinnern, dann vergleichen, dann sauber verdichten."
        ),
        "source_item_ids": [item.id for item in items[:2]],
        "recall_questions": questions[:3],
        "sections": sections,
        "quote": "Wissen zählt erst, wenn es unter Druck abrufbar bleibt.",
        "mini_task": "Erkläre die heutige Mechanik in drei Sätzen aus dem Kopf und prüfe dich erst danach mit der PDF.",
    }


def _application_lesson(today: date, item: CurriculumItem) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "date": iso(today),
        "title": "Tagesdosis Strategie & Macht",
        "today_key": "application",
        "today": TODAY_LABELS["application"],
        "focus_title": f"Mini-Fallanalyse: {item.label}",
        "subtitle": "Eine reale Lage lesen, statt nur eine Regel zu merken.",
        "intro": (
            "Heute steht keine neue Regel im Vordergrund, sondern ihre Anwendung auf eine Lage.\n\n"
            f"Nutze {item.label} als Linse, um die Situation strategisch zu lesen."
        ),
        "source_item_ids": [item.id],
        "recall_questions": [
            "Was ist in der Situation der sichtbare Konflikt?",
            "Welche Emotion soll vermutlich ausgelöst werden?",
            f"Wie würde {item.label} die Lage deuten?",
        ],
        "sections": [
            {
                "heading": "Inhalt",
                "body": "Fall: Du bist neu an einer Schule. Du hast eine starke Idee für ein MINT-/Technikprojekt, kennst aber die informellen Kräfte im Kollegium noch nicht.",
            },
            {
                "heading": "Kernmechanik",
                "body": item.mechanic,
            },
            {
                "heading": "Warum das funktioniert",
                "body": "Eine Mini-Fallanalyse zwingt dich, vom Begriff zur Lage zu wechseln: Wer will was, wer braucht wen, wer könnte sich bedroht fühlen, welche Handlung ist der nächste kleine Schritt?",
            },
            {
                "heading": "Beispiel",
                "body": item.example,
            },
            {
                "heading": "Dunkle Anwendung",
                "body": item.dark_application,
            },
            {
                "heading": "Gegenmittel",
                "body": item.countermeasure,
            },
        ],
        "quote": "Strategie beginnt, wenn du nicht mehr automatisch reagierst.",
        "mini_task": "Beschreibe heute eine Situation mit zehn Stichworten: Ziel, Personen, Interessen, Emotion, Risiko, bester nächster Schritt.",
    }


def _comparison_lesson(today: date, law: CurriculumItem, strategy: CurriculumItem) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "date": iso(today),
        "title": "Tagesdosis Strategie & Macht",
        "today_key": "comparison",
        "today": TODAY_LABELS["comparison"],
        "focus_title": f"{law.label} vs. {strategy.label}",
        "subtitle": "Zwei Denkwerkzeuge, eine Lage.",
        "intro": (
            f"Heute vergleichst du {law.label} mit {strategy.label}.\n\n"
            "Ziel ist nicht nur Wiedererkennen, sondern bessere Werkzeugwahl in echten Situationen."
        ),
        "source_item_ids": [law.id, strategy.id],
        "recall_questions": [
            f"Was ist die Kernmechanik von {law.label}?",
            f"Was ist die Kernmechanik von {strategy.label}?",
            "Wann würde das eine Werkzeug schaden und das andere helfen?",
        ],
        "sections": [
            {"heading": "Inhalt", "body": f"Vergleich zwischen {law.label} und {strategy.label}."},
            {
                "heading": "Kernmechanik",
                "body": f"{law.label}: {law.mechanic}\n\n{strategy.label}: {strategy.mechanic}",
            },
            {
                "heading": "Warum das funktioniert",
                "body": "Vergleiche erzeugen flexible Abrufbarkeit. Du lernst nicht nur eine Regel, sondern wann welches Werkzeug passt.",
            },
            {
                "heading": "Beispiel",
                "body": "In einer neuen Schule kann dieselbe Situation Statussensibilität verlangen, aber auch Geistesgegenwart. Erst ruhig bleiben, dann die eigene Idee so rahmen, dass sie anschlussfähig wirkt.",
            },
            {
                "heading": "Dunkle Anwendung",
                "body": f"{law.dark_application}\n\n{strategy.dark_application}",
            },
            {
                "heading": "Gegenmittel",
                "body": f"{law.countermeasure}\n\n{strategy.countermeasure}",
            },
        ],
        "quote": "Macht liegt oft nicht im Werkzeug, sondern in der Wahl des richtigen Werkzeugs.",
        "mini_task": "Wende beide Werkzeuge auf dieselbe Alltagssituation an und entscheide, welches heute führend sein sollte.",
    }


def _weekly_review(today: date, state: Dict[str, Any], items_by_id: Dict[str, CurriculumItem]) -> Dict[str, Any]:
    recent = state.get("history", [])[-6:]
    recent_items: List[CurriculumItem] = []
    for entry in recent:
        for item_id in entry.get("items", []):
            item = items_by_id.get(item_id)
            if item and item not in recent_items:
                recent_items.append(item)

    focus = "Wochenreview"
    if recent_items:
        focus = "Wochenreview: " + ", ".join(item.label for item in recent_items[:3])
    return {
        "schema_version": 1,
        "date": iso(today),
        "title": "Tagesdosis Strategie & Macht",
        "today_key": "weekly_review",
        "today": TODAY_LABELS["weekly_review"],
        "focus_title": focus,
        "subtitle": "Verdichten, verbinden, anwenden.",
        "intro": (
            "Heute ist Wochenreview: kein neuer Input, sondern Konsolidierung.\n\n"
            "Abrufen, verknüpfen, anwenden."
        ),
        "source_item_ids": [item.id for item in recent_items[:4]],
        "recall_questions": [
            "Welche Mechanik der Woche erkenne ich ohne Nachlesen am klarsten?",
            "Welche habe ich im Alltag tatsächlich beobachtet?",
            "Welche würde unter Stress vermutlich verschwinden?",
        ],
        "sections": [
            {
                "heading": "Inhalt",
                "body": "Heute kein neuer Input. Das Ziel ist Konsolidierung: abrufen, verknüpfen, eine reale Situation lesen.",
            },
            {
                "heading": "Kernmechanik",
                "body": "Spaced repetition wirkt, wenn du aktiv prüfst, was noch im Kopf ist, bevor du erneut liest.",
            },
            {
                "heading": "Warum das funktioniert",
                "body": "Wochenreviews verhindern, dass einzelne Lektionen isoliert bleiben. Sie verwandeln Stoff in ein nutzbares mentales Modell.",
            },
            {
                "heading": "Beispiel",
                "body": "Nimm eine Situation aus Schule, Politik oder App-Business und prüfe: Wer setzt den Rahmen, welche Emotion entsteht, wer profitiert, was ist der souveräne nächste Schritt?",
            },
            {
                "heading": "Dunkle Anwendung",
                "body": "Ohne Review entsteht Scheinsicherheit: Man hat gelesen, aber kann unter Druck nichts abrufen.",
            },
            {
                "heading": "Gegenmittel",
                "body": "Schreibe drei kurze Sätze aus dem Kopf. Erst danach nachlesen. Lücken sind kein Scheitern, sondern Trainingsdaten.",
            },
        ],
        "quote": "Nicht mehr Stoff. Mehr Zugriff.",
        "mini_task": "Wähle eine reale Lage der Woche und analysiere sie mit: Ziel, Gegenspieler, Terrain, Emotion, nächster Schritt.",
    }


def choose_lesson(
    today: date,
    state: Dict[str, Any],
    items: List[CurriculumItem],
    force_type: Optional[str] = None,
) -> Dict[str, Any]:
    items_by_id = item_map(items)
    if force_type:
        lesson_type = force_type
    elif today.weekday() == 6:
        lesson_type = "weekly_review"
    else:
        due = due_items(state, items, today)
        total_history = len(state.get("history", []))
        enough_for_application = len(introduced_items(state, items)) >= 1
        enough_for_comparison = count_introduced(state, "law") >= 1 and count_introduced(state, "strategy") >= 1
        if due:
            lesson_type = "review"
        elif enough_for_comparison and total_history > 0 and total_history % state["settings"].get("comparison_after_lessons", 6) == 0:
            lesson_type = "comparison"
        elif enough_for_application and total_history > 0 and total_history % state["settings"].get("application_after_lessons", 4) == 0:
            lesson_type = "application"
        else:
            new_kind = choose_balanced_new_kind(state, items)
            lesson_type = f"new_{new_kind}" if new_kind else "review"

    if lesson_type == "weekly_review":
        return _weekly_review(today, state, items_by_id)

    if lesson_type == "new_law":
        candidates = unintroduced_items(state, items, "law")
        if candidates:
            return _new_item_lesson(today, candidates[0], "new_law")
        return choose_lesson(today, state, items, "review")

    if lesson_type == "new_strategy":
        candidates = unintroduced_items(state, items, "strategy")
        if candidates:
            return _new_item_lesson(today, candidates[0], "new_strategy")
        return choose_lesson(today, state, items, "review")

    if lesson_type == "review":
        candidates = due_items(state, items, today) or introduced_items(state, items) or items[:1]
        return _review_lesson(today, candidates[:2])

    if lesson_type == "application":
        candidates = introduced_items(state, items) or items[:1]
        return _application_lesson(today, candidates[-1])

    if lesson_type == "comparison":
        introduced = introduced_items(state, items)
        laws = [item for item in introduced if item.kind == "law"]
        strategies = [item for item in introduced if item.kind == "strategy"]
        if not laws or not strategies:
            return choose_lesson(today, state, items, "application")
        law = laws[-1]
        linked = [items_by_id[item_id] for item_id in law.links if item_id in items_by_id and items_by_id[item_id].kind == "strategy"]
        strategy = linked[0] if linked else strategies[-1]
        return _comparison_lesson(today, law, strategy)

    raise ValueError(f"Unknown lesson type: {lesson_type}")


def generate_daily(
    lesson_date: date,
    base_dir: Path = BASE_DIR,
    force_type: Optional[str] = None,
    update_state: bool = True,
    allow_duplicate: bool = False,
) -> Path:
    state_path = base_dir / "state" / "learning_state.json"
    state = read_json(state_path)
    items = load_curriculum(base_dir)
    ensure_item_state(state, items)

    existing = history_for_date(state, lesson_date)
    if existing and update_state and not allow_duplicate:
        existing_path = existing.get("output_json")
        if existing_path:
            return base_dir / existing_path
        raise RuntimeError(f"For {iso(lesson_date)} a lesson already exists. Use --allow-duplicate.")

    lesson = choose_lesson(lesson_date, state, items, force_type)
    filename = f"{iso(lesson_date)}-{clean_for_filename(lesson['today_key'])}.json"
    output_path = base_dir / "output" / "lessons" / filename
    lesson["output_json"] = str(output_path.relative_to(base_dir))
    write_json(output_path, lesson)

    if update_state:
        items_by_id = item_map(items)
        for item_id in lesson.get("source_item_ids", []):
            item = items_by_id.get(item_id)
            if item:
                mark_seen(state, item, lesson_date)
        add_history(state, lesson)
        write_json(state_path, state)

    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the daily Strategy & Power lesson JSON.")
    parser.add_argument("--date", help="Lesson date as YYYY-MM-DD. Defaults to today in Europe/Berlin.")
    parser.add_argument(
        "--force-type",
        choices=["new_law", "new_strategy", "review", "application", "comparison", "weekly_review"],
        help="Override the learning scheduler for testing.",
    )
    parser.add_argument("--no-state-update", action="store_true", help="Generate without mutating learning_state.json.")
    parser.add_argument("--allow-duplicate", action="store_true", help="Allow multiple stateful generations for one date.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lesson_date = date.fromisoformat(args.date) if args.date else today_in_timezone()
    output_path = generate_daily(
        lesson_date,
        force_type=args.force_type,
        update_state=not args.no_state_update,
        allow_duplicate=args.allow_duplicate,
    )
    print(output_path)


if __name__ == "__main__":
    main()
