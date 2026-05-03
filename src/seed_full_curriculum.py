from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from lesson_models import BASE_DIR, read_json, write_json


LAW_LESSONS = [
    (1, 5, "34cd75434a3581468d7ac56e89524201", "Lektion 1 - Gesetze 1-5"),
    (6, 10, "34cd75434a35812a9032f45638dc6477", "Lektion 2 - Gesetze 6-10"),
    (11, 15, "34cd75434a3581bf89e7d5a4c132e6bc", "Lektion 3 - Gesetze 11-15"),
    (16, 20, "34cd75434a358109975bdcd1cfe8dafc", "Lektion 4 - Gesetze 16-20"),
    (21, 25, "34cd75434a3581d9b76cf80fc8093fd6", "Lektion 5 - Gesetze 21-25"),
    (26, 30, "34cd75434a3581c5add0d64023e81b57", "Lektion 6 - Gesetze 26-30"),
    (31, 35, "34cd75434a358192b0f9f951ce7468c9", "Lektion 7 - Gesetze 31-35"),
    (36, 40, "34cd75434a3581b6ba65d8f73166c1fe", "Lektion 8 - Gesetze 36-40"),
    (41, 48, "34cd75434a35812c9d6bc82b125d7823", "Lektion 9 - Gesetze 41-48"),
]

STRATEGY_LESSONS = [
    (1, 4, "34cd75434a35815e8450dd91216bc9af", "Lektion 1 - Strategien 1-4"),
    (5, 8, "34cd75434a3581c18a5bf85fc7a172cd", "Lektion 2 - Strategien 5-8"),
    (9, 11, "34cd75434a35817fb7d3c915e6d6b90f", "Lektion 3 - Strategien 9-11"),
    (12, 18, "34cd75434a35818b9b45f3d615fbc767", "Lektion 4 - Strategien 12-18"),
    (19, 22, "34cd75434a3581bf870bc315bf99d4e3", "Lektion 5 - Strategien 19-22"),
    (23, 27, "34cd75434a358150a664f6f363a0ee03", "Lektion 6 - Strategien 23-27"),
    (28, 33, "34cd75434a35810ab1d1c115ff63f637", "Lektion 7 - Strategien 28-33"),
]


LAWS = {
    1: ("Stelle deinen Meister nie in den Schatten", "Kompetenz kann Widerstand auslösen, wenn sie Personen über dir öffentlich bedroht. Stärke wirkt strategischer, wenn sie andere ebenfalls stärker erscheinen lässt.", "status"),
    2: ("Vertraue Freunden nicht zu sehr; lerne, Feinde zu nutzen", "Nähe ist nicht dasselbe wie Loyalität. Verlässlichkeit, Interessen und Verhalten zählen mehr als Sympathie.", "loyalität"),
    3: ("Verberge deine Absichten", "Nicht jeder braucht deine ganze Strategie. Dosierte Information schützt vor Blockade, Ausnutzung und falscher Deutung.", "informationskontrolle"),
    4: ("Sage immer weniger als nötig", "Zu viele Worte schaffen Angriffsfläche und verwässern Grenzen. Knappheit macht Aussagen stärker.", "kommunikation"),
    5: ("Schütze deinen Ruf um jeden Preis", "Ruf ist ein sozialer Filter. Er entscheidet, ob Fehler als Ausnahme oder als Beweis gedeutet werden.", "ruf"),
    6: ("Ziehe um jeden Preis Aufmerksamkeit auf dich", "Sichtbarkeit erzeugt Bedeutung. Gute Arbeit baut erst Einfluss auf, wenn sie wahrgenommen, erinnert und mit dir verbunden wird.", "aufmerksamkeit"),
    7: ("Lass andere für dich arbeiten, aber nimm selbst den Ruhm", "Macht entsteht durch Hebelwirkung, Koordination und Zuschreibung. Wer Arbeit bündelt und sichtbar präsentiert, prägt die Wahrnehmung des Ergebnisses.", "zuschreibung"),
    8: ("Bring andere dazu, zu dir zu kommen", "Anziehung gibt mehr Kontrolle als Hinterherlaufen. Wer sichtbaren Wert aufbaut, erzeugt Nachfrage statt Bedürftigkeit.", "anziehung"),
    9: ("Gewinne durch Taten, nicht durch Argumente", "Ergebnisse überzeugen stärker als Debatten. Sichtbare Beweise umgehen Reaktanz und machen Wirkung konkret.", "beweis"),
    10: ("Meide Unglückliche und Pechvögel", "Chronische Negativität, Opferhaltung und Chaos sind sozial ansteckend. Energie und Ruf brauchen Schutz.", "energie"),
    11: ("Mache Menschen von dir abhängig", "Wer etwas besitzt oder kann, das andere wirklich brauchen, wird relevant. Gesunde Abhängigkeit entsteht durch echten Wert, nicht durch Wissenshortung.", "abhängigkeit"),
    12: ("Setze gezielte Ehrlichkeit und Großzügigkeit ein", "Ein ehrlicher oder großzügiger Moment kann Abwehr senken und Vertrauen öffnen. Einzelne Signale wirken stark auf Charakterurteile.", "vertrauen"),
    13: ("Appelliere an Eigeninteresse, nicht an Dankbarkeit", "Dankbarkeit verblasst, Eigeninteresse bleibt. Wer Nutzen klar zeigt, muss weniger betteln.", "eigeninteresse"),
    14: ("Gib dich als Freund aus, arbeite aber wie ein Spion", "Information ist Macht. Aufmerksames Zuhören und Beobachten zeigen Motive, Loyalitäten, Ängste und Hebel.", "information"),
    15: ("Vernichte deinen Feind vollständig", "Ungeklärte Konflikte verschwinden selten. Reif gelesen heißt das: Konflikte sauber beenden oder klar begrenzen.", "konflikt"),
    16: ("Nutze Abwesenheit, um Respekt und Wert zu steigern", "Dauerverfügbarkeit senkt Wert. Grenzen und bewusste Knappheit machen ein Ja bedeutungsvoller.", "knappheit"),
    17: ("Halte andere in Unsicherheit und Unberechenbarkeit", "Wer völlig berechenbar ist, wird leichter gesteuert. Bewusste Reaktion schützt vor automatischer Aktivierbarkeit.", "unberechenbarkeit"),
    18: ("Baue keine Festungen, um dich zu schützen", "Isolation fühlt sich sicher an, macht aber blind und verletzlich. Netzwerke liefern Information, Schutz und Korrektur.", "netzwerk"),
    19: ("Wisse, mit wem du es zu tun hast", "Strategie ohne Menschenkenntnis ist blind. Ton, Timing und Direktheit müssen zur Person passen.", "menschenkenntnis"),
    20: ("Binde dich an niemanden", "Zu frühe Bindung macht dich Teil fremder Konflikte. Kooperation ist stark, Vereinnahmung schwächt Beweglichkeit.", "unabhängigkeit"),
    21: ("Stelle dich dümmer, als du bist", "Understatement senkt Abwehr. Wer nicht sofort überlegen wirkt, sieht mehr und wird weniger schnell als Bedrohung gelesen.", "understatement"),
    22: ("Nutze die Strategie der Kapitulation", "Nachgeben kann Zeit kaufen, Druck entziehen und spätere Handlungsmacht sichern. Nicht jeder Rückzug ist Niederlage.", "rückzug"),
    23: ("Konzentriere deine Kräfte", "Fokus macht aus Energie Einfluss. Wer überall ein bisschen wirkt, baut selten echte Macht auf.", "fokus"),
    24: ("Spiele den perfekten Höfling", "In Hierarchien zählt nicht nur Wahrheit, sondern Form, Timing, Ton und soziale Eleganz.", "hierarchie"),
    25: ("Erschaffe dich neu", "Rollen werden gemacht, nicht nur bekommen. Wer sich nicht positioniert, wird von anderen eingeordnet.", "positionierung"),
    26: ("Halte deine Hände sauber", "Rufschutz beginnt bei sauberer Zuschreibung. Wer mit Drama und Schuld verbunden wird, wird angreifbar.", "ruf"),
    27: ("Nutze das Bedürfnis der Menschen zu glauben", "Menschen brauchen Sinn, Zugehörigkeit und Hoffnung. Vision bewegt stärker als reine Fakten.", "vision"),
    28: ("Handle kühn", "Entschlossenheit erzeugt Respekt und Dynamik. Kühnheit öffnet Türen, wenn sie auf Substanz ruht.", "kühnheit"),
    29: ("Plane bis zum Ende", "Strategie denkt Folgen, Risiken und Abschluss mit. Wer vom Ende her plant, wird weniger vom Verlauf regiert.", "planung"),
    30: ("Lass deine Leistungen mühelos erscheinen", "Souveränität verstärkt Wirkung. Gute Vorbereitung darf schwer sein, der Auftritt sollte klar bleiben.", "souveränität"),
    31: ("Kontrolliere die Optionen anderer", "Wer den Rahmen der Wahl setzt, steuert oft die Entscheidung. Scheinwahl kann Freiheit simulieren.", "optionen"),
    32: ("Spiele mit den Fantasien der Menschen", "Menschen kaufen selten nur Fakten, sondern Bilder einer besseren Zukunft. Fantasie emotionalisiert Entscheidungen.", "storytelling"),
    33: ("Finde die Schwäche jedes Menschen", "Jeder Mensch hat Hebel: Anerkennung, Angst, Status, Schuld, Harmonie oder Sicherheit. Wer eigene Trigger kennt, wird schwerer steuerbar.", "trigger"),
    34: ("Handle königlich, um königlich behandelt zu werden", "Das eigene Auftreten setzt oft den wahrgenommenen Wert. Würde erzeugt Respekt, ohne Überheblichkeit zu brauchen.", "würde"),
    35: ("Beherrsche das Timing", "Die richtige Idee zur falschen Zeit scheitert. Systeme haben Aufnahmefenster.", "timing"),
    36: ("Verachte, was du nicht haben kannst", "Begehren macht abhängig. Gleichgültigkeit und Alternativen schützen Status und Energie.", "abhängigkeit"),
    37: ("Erschaffe eindrucksvolle Inszenierungen", "Bilder, Symbole und Bühnenwirkung machen Bedeutung fühlbar. Gute Inhalte brauchen eine starke Form.", "inszenierung"),
    38: ("Denke, wie du willst, aber verhalte dich wie die anderen", "Innere Freiheit braucht äußere Anschlussfähigkeit. Wer Gruppennormen plump verletzt, aktiviert Abwehr.", "anpassung"),
    39: ("Rühre die Gewässer auf, um Fische zu fangen", "Provokation bringt Menschen aus der Selbstkontrolle. Wer emotional reagiert, verrät mehr und verliert Autorität.", "provokation"),
    40: ("Verachte kostenlose Geschenke", "Kostenlose Dinge können Verpflichtung, Loyalität oder Kontrolle erzeugen. Reziprozität ist ein starker Hebel.", "geschenke"),
    41: ("Tritt nicht in die Fußstapfen großer Vorgänger", "Kopien bleiben im Schatten des Originals. Ein eigenes Profil schafft neue Bewertungsmaßstäbe.", "profil"),
    42: ("Schlage den Hirten, und die Schafe zerstreuen sich", "Gruppen haben Schlüsselpersonen. Wer Einflussknoten versteht, versteht Dynamik schneller.", "schlüsselpersonen"),
    43: ("Arbeite an Herz und Geist anderer", "Zwang erzeugt Widerstand; Verbindung, Sinn und Verständnis erzeugen freiwillige Kooperation.", "empathie"),
    44: ("Entwaffne und verärgere mit dem Spiegel-Effekt", "Spiegelung kann beruhigen, irritieren oder Verhalten sichtbar machen. Sie verbindet oder täuscht.", "spiegelung"),
    45: ("Predige Veränderung, aber verändere nie zu viel auf einmal", "Menschen mögen Fortschritt, fürchten aber Kontrollverlust. Veränderung braucht Dosierung.", "veränderung"),
    46: ("Wirke nie zu perfekt", "Perfektion erzeugt Bewunderung, aber auch Neid und Distanz. Nahbarkeit macht Kompetenz anschlussfähig.", "nahbarkeit"),
    47: ("Überschreite nicht das Ziel, das du erreicht hast", "Nach Erfolg drohen Übermut und Selbstüberschätzung. Konsolidierung schützt Gewinne.", "maß"),
    48: ("Nimm keine feste Form an", "Starre macht berechenbar. Flexibilität schützt, solange der innere Kern stabil bleibt.", "flexibilität"),
}


STRATEGIES = {
    1: ("Erkläre deinen inneren Feinden den Krieg", "Der wichtigste Gegner ist oft innen: Trägheit, Angst, Ablenkung, Selbstmitleid oder Reaktivität.", "selbstführung"),
    2: ("Führe keinen vergangenen Krieg", "Alte Muster können neue Situationen sabotieren. Strategie liest die aktuelle Lage statt die letzte Niederlage.", "muster"),
    3: ("Bewahre auch im Chaos Geistesgegenwart", "Ruhe unter Stress schafft Optionen. Wer zwischen Reiz und Reaktion Raum gewinnt, wird weniger steuerbar.", "ruhe"),
    4: ("Schaffe ein Gefühl von Dringlichkeit und Verzweiflung", "Dringlichkeit bündelt Energie, wenn sie realistisch und selbst gewählt ist. Künstlicher Druck macht manipulierbar.", "dringlichkeit"),
    5: ("Vermeide Gruppendenken", "Gruppen können klug oder blind machen. Gruppendruck unterdrückt Zweifel und stabilisiert Fehler.", "gruppe"),
    6: ("Segmentiere deine Kräfte", "Kleine bewegliche Einheiten handeln schneller als träge Gesamtstrukturen. Große Ziele brauchen handlungsfähige Module.", "segmentierung"),
    7: ("Verwandle deinen Krieg in einen Kreuzzug", "Mission erzeugt Energie. Menschen folgen stärker, wenn sie Sinn und Bedeutung sehen.", "mission"),
    8: ("Wähle deine Schlachten sorgfältig", "Nicht jeder Konflikt lohnt sich. Energie ist begrenzt und muss auf strategisch relevante Kämpfe gelenkt werden.", "schlachten"),
    9: ("Drehe den Spieß um", "Ruhige Defensive kann Angriffe ins Leere laufen lassen. Der Angreifer schwächt sich, wenn er überzieht.", "defensive"),
    10: ("Schaffe eine bedrohliche Präsenz", "Konsequenz, Kompetenz und klare Grenzen erzeugen Abschreckung. Wer nicht leicht angreifbar wirkt, wird seltener getestet.", "abschreckung"),
    11: ("Tausche Raum gegen Zeit", "Rückzug kann Zeit, Informationen und bessere Position bringen. Nicht jeder Verlust ist Niederlage.", "zeitgewinn"),
    12: ("Verliere Schlachten, aber gewinne den Krieg", "Strategie misst Richtung, nicht jeden Moment. Kurzfristiger Verlust kann langfristige Position stärken.", "langfristigkeit"),
    13: ("Kenne deinen Gegner", "Gute Strategie beginnt mit Motiven, Ängsten, Mustern und Grenzen des Gegenspielers.", "gegner"),
    14: ("Überwältige Widerstand durch Geschwindigkeit", "Tempo reduziert Reaktionszeit und setzt Fakten. Es wirkt nur mit klarer Richtung.", "tempo"),
    15: ("Kontrolliere die Dynamik", "Wer Rhythmus, Stimmung und Richtung kontrolliert, kontrolliert oft den Konflikt.", "dynamik"),
    16: ("Triff dort, wo es weh tut", "Präzision schlägt Streuung. Der entscheidende Engpass bewirkt mehr als diffuse Anstrengung.", "engpass"),
    17: ("Teile und herrsche", "Gruppen wirken stark, solange sie geschlossen sind. Unterschiedliche Interessen können große Blöcke differenzieren.", "gruppen"),
    18: ("Wende dich der Flanke zu", "Frontalangriff erzeugt Widerstand. Indirekte Zugänge über Pilotprojekte, Verbündete oder Nebenwege sind oft wirksamer.", "flanke"),
    19: ("Umschließe den Gegner", "Wer Optionen schrittweise enger macht, muss oft gar nicht frontal kämpfen.", "optionen"),
    20: ("Manövriere sie in Schwäche", "Stärke hängt vom Terrain ab. Verändere Bedingungen so, dass Substanz oder Mangel sichtbar wird.", "terrain"),
    21: ("Verhandle, während du vorankommst", "Wer parallel Alternativen und Fakten aufbaut, verhandelt stärker als jemand, der nur wartet.", "verhandlung"),
    22: ("Wisse, wie du Dinge beendest", "Ein schlechter Abschluss ruiniert gute Verläufe. Ende, Kommunikation und Sicherung gehören zur Strategie.", "abschluss"),
    23: ("Verschmelze Fakt und Fiktion", "Menschen reagieren auf Realität plus Geschichte. Deutung gibt Fakten emotionale Bedeutung.", "deutung"),
    24: ("Nimm die Linie des geringsten Widerstands", "Arbeite mit vorhandenen Strömungen, Bedürfnissen und Interessen, statt unnötig Kraft zu verbrennen.", "strömung"),
    25: ("Besetze die moralische Höhe", "Moralische Legitimität schafft Unterstützung und Schutz. Heuchelei zerstört Vertrauen.", "legitimität"),
    26: ("Verweigere ihnen Ziele", "Beweglichkeit nimmt Angriffsflächen. Wer nicht klar festgelegt ist, wird schwerer getroffen.", "beweglichkeit"),
    27: ("Erwecke den Eindruck, im Interesse anderer zu handeln", "Kooperation wächst, wenn andere ihren echten Nutzen im Ziel erkennen.", "win-win"),
    28: ("Gib deinen Gegnern genug Seil, damit sie sich selbst hängen", "Manche Muster werden erst sichtbar, wenn man nicht zu früh eingreift.", "beobachtung"),
    29: ("Nimm kleine Bissen", "Kleine Schritte bauen große Realitäten. Fortschritt wird leichter akzeptiert als das Gesamtpaket.", "inkrement"),
    30: ("Dringe in ihren Geist ein", "Wer die innere Welt anderer versteht, versteht ihr äußeres Verhalten besser.", "perspektive"),
    31: ("Zerstöre von innen heraus", "Gruppen brechen oft durch Misstrauen, Gerüchte und unklare Rollen. Defensiv heißt das: innere Stabilität schützen.", "vertrauen"),
    32: ("Dominiere, während du dich unterwirfst", "Scheinbare Schwäche kann Kontrolle erzeugen, etwa durch Schuld, Mitleid oder Passiv-Aggression.", "passiv-aggression"),
    33: ("Säe Unsicherheit und Panik durch Terrorakte", "Defensiv gelesen: Schock und Panik umgehen Denken. Tempo herausnehmen und Fakten sammeln.", "panik"),
}


def lesson_for(number: int, lessons: List[tuple[int, int, str, str]]) -> tuple[str, str]:
    for start, end, page_id, title in lessons:
        if start <= number <= end:
            return page_id, title
    raise ValueError(number)


def make_item(kind: str, number: int, title: str, summary: str, tag: str, page_id: str, lesson_title: str) -> Dict[str, Any]:
    label = "Gesetz" if kind == "law" else "Strategie"
    context_examples = "Schule, Karriere, Politik, App-Business oder Selbstführung"
    return {
        "id": f"{kind}_{number:02d}",
        "kind": kind,
        "number": number,
        "title": title,
        "source": {"lesson_title": lesson_title, "notion_page_id": page_id},
        "summary": summary,
        "mechanic": summary,
        "why": f"Das funktioniert, weil soziale Systeme auf Wahrnehmung, Interessen, Emotionen und wiederholte Signale reagieren. {label} {number} macht einen bestimmten Hebel sichtbar: {tag}.",
        "example": f"Prüfe eine aktuelle Situation aus {context_examples}: Wo zeigt sich '{title}' konkret, und welcher nächste Schritt wäre ruhig, strategisch und integer?",
        "dark_application": f"Destruktiv wird diese Mechanik, wenn '{title}' genutzt wird, um Menschen zu täuschen, zu beschämen, abhängig zu machen oder Handlungsspielräume unfair zu verengen.",
        "countermeasure": "Langsam werden, Interessen klären, Verhalten statt Worte beobachten, eigene Grenzen schützen und nicht unter emotionalem Druck entscheiden.",
        "recall_questions": [
            f"Was ist die Kernmechanik von {label} {number}?",
            f"Wo könnte '{title}' in meinem Alltag auftauchen?",
            "Wie nutze ich diese Einsicht integer statt manipulativ?",
        ],
        "daily_task": f"Beobachte heute eine Situation, in der {tag} eine Rolle spielt. Notiere Beteiligte, Emotion, Interesse und deinen souveränsten nächsten Schritt.",
        "tags": [tag, "notion-cache"],
        "links": [],
    }


def merge_existing(path: Path, full_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    if path.exists():
        current = read_json(path)
    else:
        course_id = "laws_48" if "laws" in path.name else "strategies_33"
        title = "Die 48 Gesetze der Macht - Studienkurs" if course_id == "laws_48" else "Die 33 Gesetze der Strategie - Studienkurs"
        current = {
            "schema_version": 1,
            "course": {
                "id": course_id,
                "title": title,
                "source": "seed",
            },
            "items": [],
        }
    existing = {item["id"]: item for item in current.get("items", [])}
    merged = []
    for item in full_items:
        merged.append(existing.get(item["id"], item))
    current["items"] = merged
    return current


def main() -> None:
    law_items = []
    for number in range(1, 49):
        if number in LAWS:
            title, summary, tag = LAWS[number]
            page_id, lesson_title = lesson_for(number, LAW_LESSONS)
            law_items.append(make_item("law", number, title, summary, tag, page_id, lesson_title))

    strategy_items = []
    for number in range(1, 34):
        if number in STRATEGIES:
            title, summary, tag = STRATEGIES[number]
            page_id, lesson_title = lesson_for(number, STRATEGY_LESSONS)
            strategy_items.append(make_item("strategy", number, title, summary, tag, page_id, lesson_title))

    law_path = BASE_DIR / "curriculum" / "laws_48.json"
    strategy_path = BASE_DIR / "curriculum" / "strategies_33.json"
    write_json(law_path, merge_existing(law_path, law_items))
    write_json(strategy_path, merge_existing(strategy_path, strategy_items))
    print(f"Wrote {law_path} with {len(read_json(law_path)['items'])} laws.")
    print(f"Wrote {strategy_path} with {len(read_json(strategy_path)['items'])} strategies.")


if __name__ == "__main__":
    main()
