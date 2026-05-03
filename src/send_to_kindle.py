from __future__ import annotations

import argparse
import mimetypes
import os
import re
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Dict


REQUIRED_ENV = [
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASS",
    "FROM_EMAIL",
    "KINDLE_EMAIL",
]

mimetypes.add_type("application/epub+zip", ".epub")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_snapshot() -> Dict[str, str]:
    values = {key: os.environ.get(key, "") for key in REQUIRED_ENV}
    if values.get("SMTP_PASS"):
        values["SMTP_PASS"] = re.sub(r"\s+", "", values["SMTP_PASS"])
    return values


def validate_env(values: Dict[str, str]) -> None:
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))


def build_message(pdf_path: Path, values: Dict[str, str]) -> EmailMessage:
    message = EmailMessage()
    message["From"] = values["FROM_EMAIL"]
    message["To"] = values["KINDLE_EMAIL"]
    message["Subject"] = "Tagesdosis Strategie & Macht"
    message.set_content("Deine heutige Tagesdosis Strategie & Macht ist im Anhang.")

    content_type, _ = mimetypes.guess_type(str(pdf_path))
    if not content_type:
        content_type = "application/pdf"
    maintype, subtype = content_type.split("/", 1)
    message.add_attachment(
        pdf_path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=pdf_path.name,
    )
    return message


def _send_once(message: EmailMessage, values: Dict[str, str]) -> None:
    port = int(values["SMTP_PORT"])
    if port == 465:
        with smtplib.SMTP_SSL(values["SMTP_HOST"], port, timeout=30) as smtp:
            smtp.login(values["SMTP_USER"], values["SMTP_PASS"])
            smtp.send_message(message)
    else:
        with smtplib.SMTP(values["SMTP_HOST"], port, timeout=30) as smtp:
            smtp.starttls()
            smtp.login(values["SMTP_USER"], values["SMTP_PASS"])
            smtp.send_message(message)


def send_pdf(pdf_path: Path, dry_run: bool = True, env_file: Path = Path(".env"), retries: int = 3) -> None:
    load_env_file(env_file)
    values = env_snapshot()

    if dry_run:
        kindle = values.get("KINDLE_EMAIL") or "<KINDLE_EMAIL>"
        sender = values.get("FROM_EMAIL") or "<FROM_EMAIL>"
        missing = [key for key, value in values.items() if not value]
        suffix = f" Missing for real send: {', '.join(missing)}." if missing else ""
        print(f"Dry run: would send {pdf_path} to {kindle} from {sender}.{suffix}")
        return

    validate_env(values)
    message = build_message(pdf_path, values)
    attempts = max(1, retries)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            _send_once(message, values)
            print(f"Sent {pdf_path} to {values['KINDLE_EMAIL']} from {values['FROM_EMAIL']}.")
            return
        except (OSError, smtplib.SMTPException) as error:
            last_error = error
            if attempt == attempts:
                break
            delay_seconds = min(60, 5 * attempt)
            print(
                f"Send attempt {attempt}/{attempts} failed: {type(error).__name__}: {error}. "
                f"Retrying in {delay_seconds}s."
            )
            time.sleep(delay_seconds)
    raise RuntimeError(f"Could not send {pdf_path} after {attempts} attempt(s): {last_error}") from last_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a PDF to your Kindle address via SMTP.")
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--send", action="store_true", help="Actually send. Default is dry-run.")
    parser.add_argument("--retries", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    send_pdf(args.pdf_path, dry_run=not args.send, env_file=args.env_file, retries=args.retries)


if __name__ == "__main__":
    main()
