#!/usr/bin/env python3
"""Download BIS published Indian Standard metadata and build a searchable PDF index.

This collects catalogue metadata (standard number, title and portal classification),
not the copyrighted text of any Indian Standard. The catalogue API endpoint is used by
the public BIS Standards Portal's Know Your Standards / Published Standards interface.

Run:
    python scripts/scrape_bis_standards_catalogue.py --output-dir docs/bis-standards

Optional local test:
    python scripts/scrape_bis_standards_catalogue.py --input-json sample.json --output-dir out
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit


API_URL = "https://standardsadmin.bis.gov.in/proposal-service/getWebsiteIndianStandardsList"
PORTAL_URL = "https://standards.bis.gov.in/website/know-your-standards"
PUBLISHED_URL = (
    "https://standards.bis.gov.in/website/published-standards/"
    "published-standards-list?selectedType=7&totalRow=1"
)
PAGE_SIZE = 100
REQUEST_DELAY_SECONDS = 0.25
MAX_PAGES = 2000

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://standards.bis.gov.in",
    "Referer": "https://standards.bis.gov.in/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    ),
}

CSV_FIELDS = [
    "is_number",
    "title",
    "technical_department",
    "sectional_committee",
    "standard_type",
    "published_on",
    "bis_record_id",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("bis_catalogue_export")


def clean(value: Any) -> str:
    """Make catalogue values safe for CSV/PDF while preserving their meaning."""
    if value is None:
        return ""
    text = html.unescape(str(value))
    text = text.replace("\x00", " ")
    return " ".join(text.split())


def is_is_standard_number(value: str) -> bool:
    """Keep Indian Standard identifiers (including IS/ISO, IS/IEC and IS/QC forms)."""
    return bool(re.match(r"^\s*IS(?:\s|/|:|-|\d)", value or "", flags=re.IGNORECASE))


def standard_key(value: str) -> str:
    """Normalize whitespace/case for de-duplication while preserving the display value."""
    return re.sub(r"\s+", "", (value or "").strip()).upper()


def request_page(client: httpx.Client, page: int) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = client.post(
                API_URL,
                json={"page": page, "pageSize": PAGE_SIZE},
            )
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError(f"Unexpected API response on page {page}: expected a JSON object")
            return payload
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt == 4:
                break
            delay = min(2 ** attempt, 12)
            logger.warning(
                "Page %s failed (attempt %s/5): %s; retrying in %ss",
                page, attempt + 1, type(exc).__name__, delay
            )
            time.sleep(delay)
    raise RuntimeError(f"Failed to fetch BIS catalogue page {page}: {last_error}") from last_error


def fetch_catalogue() -> tuple[list[dict[str, Any]], int | None, int]:
    rows: list[dict[str, Any]] = []
    reported_total: int | None = None
    page = 1

    with httpx.Client(
        headers=HEADERS,
        timeout=httpx.Timeout(90.0, connect=20.0),
        follow_redirects=True,
    ) as client:
        while True:
            if page > MAX_PAGES:
                raise RuntimeError(f"Safety stop: catalogue exceeded {MAX_PAGES} pages.")
            payload = request_page(client, page)
            batch = payload.get("data") or []
            if not isinstance(batch, list):
                raise RuntimeError(
                    f"Unexpected BIS response shape on page {page}: 'data' is not a list."
                )
            if page == 1:
                reported = payload.get("totalRecord")
                if isinstance(reported, int):
                    reported_total = reported
                logger.info("BIS API catalogue total reported: %s", reported_total)
            if not batch:
                logger.info("BIS API returned no records on page %s; stopping.", page)
                break

            rows.extend(row for row in batch if isinstance(row, dict))
            if page % 20 == 0:
                logger.info("Fetched page %s; raw rows collected: %s", page, len(rows))

            has_more = payload.get("hasMore")
            if has_more is False:
                break
            if has_more is None and reported_total is not None and len(rows) >= reported_total:
                break

            page += 1
            time.sleep(REQUEST_DELAY_SECONDS)

    return rows, reported_total, page


def transform_and_deduplicate(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    best: dict[str, dict[str, str]] = {}
    for row in rows:
        number = clean(row.get("standardNumber"))
        title = clean(row.get("standardName"))
        # The portal can also show "Standards India" magazine entries (SI ...).
        # This document is specifically an index of Indian Standard (IS) numbers.
        if not number or not title or not is_is_standard_number(number):
            continue

        item = {
            "is_number": number,
            "title": title,
            "technical_department": clean(row.get("departmentName")),
            "sectional_committee": clean(row.get("sectionalCommitteeName")),
            "standard_type": clean(row.get("typeOfStandardName")),
            "published_on": clean(row.get("publishedOn")),
            "bis_record_id": clean(row.get("standardId")),
        }
        key = standard_key(number)
        previous = best.get(key)
        # A duplicate identifier can occur in multiple portal rows. Keep the
        # row with the most populated metadata; do not merge different editions
        # because the year is part of the displayed identifier.
        completeness = sum(bool(item[field]) for field in CSV_FIELDS)
        previous_completeness = (
            sum(bool(previous[field]) for field in CSV_FIELDS) if previous else -1
        )
        if previous is None or completeness > previous_completeness:
            best[key] = item

    records = list(best.values())
    records.sort(
        key=lambda r: (
            r["technical_department"].casefold(),
            r["is_number"].casefold(),
            r["title"].casefold(),
        )
    )
    if not records:
        raise RuntimeError(
            "No IS-number records were collected. Refusing to generate an empty catalogue PDF."
        )
    return records


def register_fonts() -> tuple[str, str]:
    """Use DejaVu for readable punctuation when available, else standard PDF fonts."""
    regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]
    regular_path = next((p for p in regular_paths if Path(p).exists()), None)
    bold_path = next((p for p in bold_paths if Path(p).exists()), None)
    if regular_path and bold_path:
        pdfmetrics.registerFont(TTFont("BISIndex", regular_path))
        pdfmetrics.registerFont(TTFont("BISIndex-Bold", bold_path))
        return "BISIndex", "BISIndex-Bold"
    return "Helvetica", "Helvetica-Bold"


def wrap_lines(text: str, font: str, size: float, width: float, limit: int = 3) -> list[str]:
    lines = simpleSplit(text or "-", font, size, width)
    if len(lines) > limit:
        lines = lines[:limit]
        if lines:
            while lines[-1] and pdfmetrics.stringWidth(lines[-1] + "...", font, size) > width:
                lines[-1] = lines[-1][:-1]
            lines[-1] = lines[-1].rstrip() + "..."
    return lines or ["-"]


def draw_record(
    pdf: canvas.Canvas,
    record: dict[str, str],
    index: int,
    x: float,
    y: float,
    column_width: float,
    regular_font: str,
    bold_font: str,
) -> float:
    """Draw one compact, searchable catalogue entry and return the next y position."""
    pad = 4
    content_width = column_width - 2 * pad
    identifier = f"{index:,}. {record['is_number']}"
    id_size = 7.1
    while pdfmetrics.stringWidth(identifier, bold_font, id_size) > content_width and id_size > 5.6:
        id_size -= 0.2
    pdf.setFillColor(colors.HexColor("#15364F"))
    pdf.setFont(bold_font, id_size)
    pdf.drawString(x + pad, y - 7.3, identifier)
    y -= 10.0

    title_lines = wrap_lines(record["title"], regular_font, 6.2, content_width, limit=3)
    pdf.setFillColor(colors.HexColor("#252B31"))
    pdf.setFont(regular_font, 6.2)
    for line in title_lines:
        pdf.drawString(x + pad, y - 6.5, line)
        y -= 7.2

    department = record["technical_department"] or "Department not listed"
    standard_type = record["standard_type"] or "Type not listed"
    published = record["published_on"] or "Date not listed"
    committee = record["sectional_committee"]
    meta = f"{department} | {standard_type} | {published}"
    if committee:
        meta += f" | {committee}"
    meta_lines = wrap_lines(meta, regular_font, 4.9, content_width, limit=2)
    pdf.setFillColor(colors.HexColor("#606A73"))
    pdf.setFont(regular_font, 4.9)
    for line in meta_lines:
        pdf.drawString(x + pad, y - 5.2, line)
        y -= 5.8

    y -= 3.4
    pdf.setStrokeColor(colors.HexColor("#DCE2E7"))
    pdf.setLineWidth(0.25)
    pdf.line(x + pad, y, x + column_width - pad, y)
    return y - 4.2


def write_pdf(
    path: Path,
    records: list[dict[str, str]],
    raw_row_count: int,
    api_total: int | None,
    fetched_at: str,
) -> None:
    regular_font, bold_font = register_fonts()
    page_width, page_height = landscape(A4)
    margin = 25.0
    gap = 14.0
    column_width = (page_width - 2 * margin - gap) / 2
    top_y = page_height - 79
    footer_y = 21.0
    page_no = 0
    next_index = 0
    total_records = len(records)

    pdf = canvas.Canvas(str(path), pagesize=landscape(A4), pageCompression=1)
    pdf.setTitle("BIS Published Indian Standards Index")
    pdf.setAuthor("ISense SIH Project - catalogue metadata exported from BIS")
    pdf.setSubject(
        "Searchable index of IS-number records and titles from the public BIS standards catalogue"
    )
    pdf.setKeywords("BIS, Indian Standards, IS number, Know Your Standards, catalogue")

    while next_index < total_records:
        page_no += 1
        pdf.setFillColor(colors.HexColor("#15364F"))
        pdf.setFont(bold_font, 13)
        pdf.drawString(margin, page_height - 30, "BIS Published Indian Standards Index")
        pdf.setFillColor(colors.HexColor("#404A53"))
        pdf.setFont(regular_font, 7)
        pdf.drawString(
            margin,
            page_height - 43,
            f"IS-number records: {total_records:,} unique | Raw API rows: {raw_row_count:,} | "
            f"BIS-reported total: {api_total if api_total is not None else 'not supplied'}",
        )
        pdf.setFont(regular_font, 6.1)
        pdf.drawString(
            margin,
            page_height - 54,
            f"Retrieved: {fetched_at} UTC | Portal metadata only - not a validity, QCO or certification determination",
        )
        pdf.setFillColor(colors.HexColor("#1976A8"))
        pdf.drawString(margin, page_height - 65, PORTAL_URL)
        pdf.setStrokeColor(colors.HexColor("#15364F"))
        pdf.setLineWidth(0.7)
        pdf.line(margin, page_height - 70, page_width - margin, page_height - 70)

        y_positions = [top_y, top_y]
        column_x = [margin, margin + column_width + gap]
        column_records = [0, 0]

        while next_index < total_records and any(y > footer_y + 35 for y in y_positions):
            for column in range(2):
                if next_index >= total_records:
                    break
                if y_positions[column] <= footer_y + 35:
                    continue
                new_y = draw_record(
                    pdf,
                    records[next_index],
                    next_index + 1,
                    column_x[column],
                    y_positions[column],
                    column_width,
                    regular_font,
                    bold_font,
                )
                # Each column is filled independently and entry metadata is capped
                # so every item fits. If one entry barely crosses the lower limit,
                # start the next page instead of clipping it.
                if new_y < footer_y + 4 and column_records[column] > 0:
                    # This record is already drawn; keep it visible and finish the
                    # page. This branch is rare because record text is line-limited.
                    y_positions[column] = new_y
                    column_records[column] += 1
                    next_index += 1
                    continue
                y_positions[column] = new_y
                column_records[column] += 1
                next_index += 1

        pdf.setStrokeColor(colors.HexColor("#DCE2E7"))
        pdf.line(margin, footer_y + 9, page_width - margin, footer_y + 9)
        pdf.setFillColor(colors.HexColor("#58636D"))
        pdf.setFont(regular_font, 5.5)
        pdf.drawString(
            margin,
            footer_y,
            "Source: BIS Standards Portal. Verify each record, current edition and applicability on the official portal before relying on it.",
        )
        pdf.drawRightString(page_width - margin, footer_y, f"Page {page_no}")
        pdf.showPage()

    pdf.save()
    logger.info("PDF written: %s (%s pages)", path, page_no)


def write_csv(path: Path, records: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def load_json_input(path: Path) -> tuple[list[dict[str, Any]], int | None, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("data"), list):
        return data["data"], data.get("totalRecord"), len(data["data"])
    if isinstance(data, list):
        return data, len(data), len(data)
    raise ValueError("Input JSON must be a list of records or a BIS API payload with a 'data' list.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export BIS IS-number catalogue metadata to PDF and CSV.")
    parser.add_argument("--output-dir", default="docs/bis-standards", help="Output directory.")
    parser.add_argument("--input-json", default="", help="Optional saved BIS API payload/list for offline testing.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if args.input_json:
        raw_rows, api_total, pages = load_json_input(Path(args.input_json))
        logger.info("Loaded %s sample/input rows from %s", len(raw_rows), args.input_json)
    else:
        raw_rows, api_total, pages = fetch_catalogue()

    records = transform_and_deduplicate(raw_rows)
    pdf_path = output_dir / "BIS_Published_Indian_Standards_Index.pdf"
    csv_path = output_dir / "BIS_Published_Indian_Standards_Index.csv"
    metadata_path = output_dir / "catalogue-metadata.json"

    write_csv(csv_path, records)
    write_pdf(pdf_path, records, len(raw_rows), api_total, fetched_at)

    metadata = {
        "source": PORTAL_URL,
        "published_standards_page": PUBLISHED_URL,
        "api_endpoint": API_URL,
        "retrieved_at_utc": fetched_at,
        "api_reported_total_rows": api_total,
        "raw_rows_fetched": len(raw_rows),
        "pages_requested": pages,
        "unique_is_number_records": len(records),
        "note": (
            "Catalogue metadata only. This index does not include the full text of Indian Standards "
            "and does not determine whether any edition is current, compulsory, withdrawn, or applicable "
            "to a particular product. Check the individual official BIS record and current orders."
        ),
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info("BIS API rows reported: %s", api_total)
    logger.info("Raw rows fetched: %s", len(raw_rows))
    logger.info("Unique IS-number records exported: %s", len(records))
    logger.info("Wrote %s", pdf_path)
    logger.info("Wrote %s", csv_path)
    logger.info("Wrote %s", metadata_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        logger.error("Interrupted by user.")
        raise SystemExit(130)
    except Exception as exc:
        logger.exception("Catalogue export failed: %s", exc)
        raise SystemExit(1)
