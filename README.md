# Tagesdosis Strategie & Macht

Lokale Phase-1-Pipeline für eine tägliche Lern-Automation aus deinen Notion-Studienkursen.

## Status

Phase 1 ist ein lokaler Durchstich:

- Notion-Quellen sind in `config/notion_sources.json` hinterlegt.
- `curriculum/laws_48.json` und `curriculum/strategies_33.json` enthalten einen kleinen Start-Cache aus den gefundenen Kursseiten.
- `state/learning_state.json` speichert Lernstand, Wiederholungen und Historie.
- `src/run_daily.py` erzeugt eine Tageslektion, rendert eine lokale PDF-Archivfassung, erzeugt eine Kindle-EPUB und macht standardmäßig nur einen SMTP-Dry-Run.

Noch nicht aktiv:

- kein echter Kindle-Versand ohne `.env`
- keine laufende Codex-Automation
- keine KI-Bilder
- kein vollständiger Notion-Sync ohne `NOTION_API_KEY`

## Schnellstart

Mit dem gebündelten Codex-Python:

```bash
/Users/kevinstelges/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/run_daily.py --date 2026-04-24 --no-state-update
```

Nur generieren:

```bash
/Users/kevinstelges/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/generate_daily.py --date 2026-04-24 --no-state-update
```

PDF aus einer Lektion rendern:

```bash
/Users/kevinstelges/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/render_pdf.py output/lessons/2026-04-24-new-law.json
```

## Versand

Kopiere `.env.example` nach `.env` und fülle die Werte aus. Die `FROM_EMAIL` muss bei Amazon als erlaubter Send-to-Kindle-Absender eingetragen sein.

Aktuelle Versandadresse:

```text
coworker.stelges@gmail.com
```

Ein echter Versand passiert nur mit:

```bash
/Users/kevinstelges/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/run_daily.py --send
```

Der Versand nutzt EPUB, weil Send-to-Kindle damit auf dem Kindle Paperwhite zuverlässiger funktioniert als mit den gestalteten PDFs. Die PDF bleibt zusätzlich lokal unter `output/pdf/`.

Der echte Versand versucht SMTP bis zu dreimal und schreibt bei Erfolg eine eindeutige `Sent ...`-Zeile. Für den täglichen lokalen Lauf gibt es zusätzlich:

```bash
scripts/run_daily_logged.sh
```

Dieser Starter schreibt Logs nach `logs/daily-YYYY-MM-DD.log` und verhindert parallele Doppelläufe.

## Täglicher Mac-Start

Die LaunchAgent-Vorlage liegt unter:

```text
config/com.kevinstelges.tagesdosis.plist
```

Sie startet alle 30 Minuten. Der Starter sendet aber erst ab 06:30 Uhr und nur einmal pro Tag. Dadurch holt der Mac den Lauf eher nach, wenn er morgens geschlafen hat.

Wichtig: Der aktive Hintergrundlauf nutzt eine lokale Runtime-Kopie unter:

```text
/Users/kevinstelges/Library/Application Support/Tagesdosis/LebenLernen
```

Der iCloud-Drive-Ordner bleibt die Arbeitskopie. launchd arbeitet stabiler aus dem lokalen Ordner, weil Hintergrundjobs in `Mobile Documents` sonst Schreibrechte verlieren koennen.

Installation:

```bash
scripts/install_launch_agent.sh
```

Die Installation aktualisiert die lokale Runtime-Kopie aus dem iCloud-Ordner und lädt den LaunchAgent neu.

## Notion-Sync

Der tägliche Lauf nutzt den lokalen Vollcache und braucht keinen Notion-Zugriff. Nur wenn du die Notion-Kurse später deutlich änderst, kann der Cache manuell aktualisiert werden.

Für einen optionalen späteren Sync außerhalb des Codex-Connectors:

```bash
export NOTION_API_KEY=secret_...
/Users/kevinstelges/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 src/sync_notion.py
```

Die Notion-Integration muss Zugriff auf die beiden Kursseiten haben.

Setup:

1. In Notion unter `Settings -> Connections -> Develop or manage integrations` eine interne Integration erstellen.
2. Den Secret-Token in `.env` als `NOTION_API_KEY=` eintragen.
3. Beide Kursseiten in Notion mit dieser Integration teilen.
4. Danach `src/sync_notion.py` ausführen.

## Design

Das PDF ist bewusst kleinformatig, einspaltig, mit großer Schrift, viel Weißraum, Black-Gold-Cover und klaren Abschnittsüberschriften. Es ist für Kindle Paperwhite Lesbarkeit priorisiert, nicht für A4-Ausdruck.
