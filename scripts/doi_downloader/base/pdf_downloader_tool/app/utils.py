# app/utils.py
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def sanitize_filename(text: str, max_len: int = 140) -> str:
    text = str(text or "").strip()

    text = re.sub(r'[\\/:*?"<>|]', " ", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ", "_")
    text = re.sub(r"_+", "_", text).strip("_")

    if not text:
        text = "untitled"

    return text[:max_len].rstrip("_")


def build_pdf_filename(record_id: str, title: str) -> str:
    safe_title = sanitize_filename(title)
    return f"{record_id}__{safe_title}.pdf"


def normalize_doi(doi: str) -> Optional[str]:
    if is_blank(doi):
        return None

    doi = str(doi).strip()
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    doi = doi.strip()

    if re.match(r"^10\.\d{4,9}/\S+$", doi):
        return doi.rstrip(" .;,:)")

    match = re.search(r"(10\.\d{4,9}/\S+)", doi, flags=re.IGNORECASE)
    if match:
        return match.group(1).rstrip(" .;,:)")

    return None


def make_doi_url(doi: str) -> str:
    return f"https://doi.org/{doi}"


def extract_host(url: str) -> str:
    parsed = urlparse(str(url or "").strip())
    return (parsed.netloc or "").lower()


def url_matches_domain_pattern(url: str, pattern: str) -> bool:
    host = extract_host(url)
    if not host:
        return False
    return re.search(pattern, host) is not None


def format_seconds(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def deduplicate_urls(urls: list[str]) -> list[str]:
    seen = set()
    unique_urls: list[str] = []

    for url in urls:
        cleaned = str(url or "").strip()
        if not cleaned:
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            unique_urls.append(cleaned)

    return unique_urls


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def save_pdf_bytes(pdf_path: Path, content: bytes) -> bool:
    if not content:
        return False

    ensure_parent_dir(pdf_path)
    pdf_path.write_bytes(content)
    return pdf_path.exists() and pdf_path.stat().st_size > 0