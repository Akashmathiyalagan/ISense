"""Searchable lookup for the BIS published-standards catalogue exported from the portal.

The CSV is generated in the same run as docs/bis-standards/BIS_Published_Indian_Standards_Index.pdf.
It is used here rather than parsing the 853-page PDF at every query: it contains the same catalogue
records in a machine-readable format. These records provide candidate identifiers/titles only;
they do not establish scope, current validity, QCO status, or certification applicability.
"""
from __future__ import annotations

import csv
import logging
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger("isense_bis_catalogue")

DEFAULT_PORTAL_URL = "https://standards.bis.gov.in/website/know-your-standards"

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does",
    "for", "from", "give", "how", "i", "in", "into", "is", "it", "its",
    "me", "of", "on", "or", "please", "product", "tell", "that", "the",
    "their", "this", "to", "under", "what", "which", "who", "with", "would",
    "bis", "indian", "standard", "standards", "requirement", "requirements",
    "certification", "mandatory", "compulsory", "testing", "test", "process",
    "procedure", "apply", "applicable", "applicability", "manufacturer",
    "manufactured", "factory", "registration", "documents", "document",
    "whether", "need", "needed", "want", "guidance", "help", "number",
    "qco", "isi", "mark", "marking", "current", "official", "source",
    "evidence", "retrieved", "user", "details", "provided", "seeking",
    "based", "exact", "following", "activity", "use", "used",
}


def _tokens(value: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9]+", (value or "").casefold())
        if len(token) >= 2 and token not in _STOP_WORDS
    ]


def _normalise_identifier(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


@dataclass(frozen=True)
class BISStandardRecord:
    is_number: str
    title: str
    technical_department: str = ""
    sectional_committee: str = ""
    standard_type: str = ""
    published_on: str = ""
    bis_record_id: str = ""

    @property
    def search_text(self) -> str:
        return " ".join((
            self.is_number, self.title, self.technical_department,
            self.sectional_committee, self.standard_type,
        ))

    def to_catalogue_chunk(self, score: float = 0.0) -> dict[str, Any]:
        return {
            "is_number": self.is_number,
            "title": self.title,
            "technical_department": self.technical_department,
            "sectional_committee": self.sectional_committee,
            "standard_type": self.standard_type,
            "published_on": self.published_on,
            "bis_record_id": self.bis_record_id,
            "score": round(float(score), 4),
            "source_url": DEFAULT_PORTAL_URL,
            "evidence_level": "catalogue_metadata_only",
        }


class BISStandardCatalogue:
    """Small in-memory inverted index over IS-number/title metadata from the BIS CSV."""

    def __init__(self, csv_path: str | os.PathLike[str] | None = None):
        self.csv_path = Path(csv_path) if csv_path else self._default_csv_path()
        self.records: list[BISStandardRecord] = []
        self._postings: dict[str, list[int]] = defaultdict(list)
        self._doc_frequency: Counter[str] = Counter()
        self._identifier_map: dict[str, list[int]] = defaultdict(list)
        self._load()

    @staticmethod
    def _default_csv_path() -> Path:
        # File layout in this repo: docs/... and Bis_model3/backend/rag/catalogue.py
        configured = os.getenv("BIS_STANDARDS_CATALOGUE_CSV")
        if configured:
            return Path(configured).expanduser()
        repo_root = Path(__file__).resolve().parents[3]
        candidates = [
            repo_root / "docs" / "bis-standards" / "BIS_Published_Indian_Standards_Index.csv",
            repo_root / "Bis_model3" / "docs" / "bis-standards" / "BIS_Published_Indian_Standards_Index.csv",
            Path.cwd() / "docs" / "bis-standards" / "BIS_Published_Indian_Standards_Index.csv",
        ]
        for path in candidates:
            if path.is_file():
                return path
        return candidates[0]

    def _load(self) -> None:
        if not self.csv_path.is_file():
            logger.warning(
                "BIS published-standards catalogue CSV not found at %s. "
                "Catalogue lookup is disabled; add the generated CSV or set BIS_STANDARDS_CATALOGUE_CSV.",
                self.csv_path,
            )
            return

        try:
            # Exporter writes UTF-8 with BOM so Excel opens the file cleanly.
            with self.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    is_number = " ".join((row.get("is_number") or "").split())
                    title = " ".join((row.get("title") or "").split())
                    if not is_number or not title:
                        continue
                    record = BISStandardRecord(
                        is_number=is_number,
                        title=title,
                        technical_department=" ".join((row.get("technical_department") or "").split()),
                        sectional_committee=" ".join((row.get("sectional_committee") or "").split()),
                        standard_type=" ".join((row.get("standard_type") or "").split()),
                        published_on=" ".join((row.get("published_on") or "").split()),
                        bis_record_id=" ".join((row.get("bis_record_id") or "").split()),
                    )
                    idx = len(self.records)
                    self.records.append(record)
                    self._identifier_map[_normalise_identifier(is_number)].append(idx)
                    terms = set(_tokens(record.search_text))
                    for term in terms:
                        self._postings[term].append(idx)
                        self._doc_frequency[term] += 1
            logger.info("Loaded %s BIS catalogue records from %s", len(self.records), self.csv_path)
        except (OSError, UnicodeError, csv.Error) as exc:
            self.records.clear()
            self._postings.clear()
            self._doc_frequency.clear()
            self._identifier_map.clear()
            logger.exception("Failed loading BIS catalogue at %s: %s", self.csv_path, type(exc).__name__)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return ranked catalogue candidates. They are not regulatory scope evidence."""
        if not self.records or not (query or "").strip() or top_k < 1:
            return []

        query_text = query.strip()
        identifier_query = _normalise_identifier(query_text)
        exact_candidates: list[tuple[int, float]] = []

        # Exact standard identifier takes precedence over lexical product search.
        match = re.search(
            r"\bIS(?:O|/IEC|/ISO|/IEC)?\s*[-:]?\s*\d{3,6}(?:\s*\([^)]*\))?(?:\s*:\s*(?:19|20)\d{2})?",
            query_text,
            flags=re.IGNORECASE,
        )
        if match:
            wanted = _normalise_identifier(match.group(0))
            for identifier, indices in self._identifier_map.items():
                if identifier == wanted or identifier.startswith(wanted):
                    exact_candidates.extend((idx, 10.0) for idx in indices)
        elif identifier_query and len(identifier_query) >= 5:
            for identifier, indices in self._identifier_map.items():
                if identifier == identifier_query or identifier.startswith(identifier_query):
                    exact_candidates.extend((idx, 10.0) for idx in indices)

        ranked: dict[int, float] = {idx: score for idx, score in exact_candidates}
        query_terms = list(dict.fromkeys(_tokens(query_text)))
        if query_terms:
            query_weight = 0.0
            for term in query_terms:
                doc_freq = self._doc_frequency.get(term, 0)
                if not doc_freq:
                    continue
                idf = 1.0 + __import__("math").log((len(self.records) + 1) / (doc_freq + 1))
                query_weight += idf
                for idx in self._postings.get(term, []):
                    record = self.records[idx]
                    title_terms = set(_tokens(record.title))
                    number_terms = set(_tokens(record.is_number))
                    department_terms = set(_tokens(record.technical_department))
                    weight = idf
                    if term in title_terms:
                        weight *= 2.6
                    elif term in number_terms:
                        weight *= 2.0
                    elif term in department_terms:
                        weight *= 0.65
                    else:
                        weight *= 0.45
                    ranked[idx] = ranked.get(idx, 0.0) + weight

            if query_weight:
                for idx in list(ranked):
                    if ranked[idx] < 10.0:
                        ranked[idx] = ranked[idx] / query_weight

        ordered = sorted(
            ranked.items(),
            key=lambda pair: (
                pair[1],
                bool(set(_tokens(self.records[pair[0]].title)) & set(query_terms)),
            ),
            reverse=True,
        )

        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for idx, score in ordered:
            record = self.records[idx]
            key = _normalise_identifier(record.is_number)
            if key in seen:
                continue
            # Avoid returning weak accidental hits caused by generic words.
            if score < 0.22:
                continue
            seen.add(key)
            results.append(record.to_catalogue_chunk(score))
            if len(results) >= top_k:
                break
        return results

    def get_by_identifier(self, identifier: str) -> list[dict[str, Any]]:
        wanted = _normalise_identifier(identifier)
        if not wanted:
            return []
        return [
            self.records[idx].to_catalogue_chunk(10.0)
            for key, indices in self._identifier_map.items()
            if key == wanted or key.startswith(wanted)
            for idx in indices
        ]

    def status(self) -> dict[str, Any]:
        return {
            "loaded": bool(self.records),
            "records": len(self.records),
            "source_file": str(self.csv_path),
            "metadata_only": True,
        }
