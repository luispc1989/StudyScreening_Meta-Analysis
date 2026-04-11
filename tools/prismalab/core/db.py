from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from tools.pdf_fetcher.core.config import ACTIVE_PROJECT_ROOT


PRISMALAB_DIRNAME = "PrismaLab"
DATA_DIRNAME = "Data"
EXPORTS_DIRNAME = "Exports"
DEFAULT_DATABASE_FILENAME = "prismalab.sqlite3"


def build_prismalab_root(project_root: Optional[Path] = None) -> Path:
    return (project_root or ACTIVE_PROJECT_ROOT) / PRISMALAB_DIRNAME


def build_prismalab_data_dir(project_root: Optional[Path] = None) -> Path:
    return build_prismalab_root(project_root) / DATA_DIRNAME


def build_project_database_path(project_root: Optional[Path] = None) -> Path:
    return build_prismalab_data_dir(project_root) / DEFAULT_DATABASE_FILENAME


def ensure_prismalab_directories(project_root: Optional[Path] = None) -> dict[str, Path]:
    root = build_prismalab_root(project_root)
    data_dir = root / DATA_DIRNAME
    exports_dir = root / EXPORTS_DIRNAME

    for path in (root, data_dir, exports_dir):
        path.mkdir(parents=True, exist_ok=True)

    return {
        "root": root,
        "data": data_dir,
        "exports": exports_dir,
        "database": data_dir / DEFAULT_DATABASE_FILENAME,
    }


def open_database(database_path: Optional[Path] = None) -> sqlite3.Connection:
    if database_path is None:
        path = ensure_prismalab_directories()["database"]
    else:
        path = Path(database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def initialize_project_database(
    project_name: Optional[str] = None,
    project_root: Optional[Path] = None,
    database_path: Optional[Path] = None,
) -> Path:
    project_root = project_root or ACTIVE_PROJECT_ROOT
    directories = ensure_prismalab_directories(project_root)
    db_path = database_path or directories["database"]

    with open_database(db_path) as connection:
        _create_schema(connection)
        connection.execute(
            """
            INSERT INTO projects (project_key, project_name, project_root)
            VALUES (?, ?, ?)
            ON CONFLICT(project_key) DO UPDATE SET
                project_name = excluded.project_name,
                project_root = excluded.project_root,
                updated_at = CURRENT_TIMESTAMP
            """,
            (project_root.name.lower(), project_name or project_root.name, str(project_root)),
        )
        connection.commit()

    return db_path


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_key TEXT NOT NULL UNIQUE,
            project_name TEXT NOT NULL,
            project_root TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS import_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            source_slug TEXT NOT NULL,
            source_label TEXT,
            file_name TEXT NOT NULL,
            file_hash TEXT,
            imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            row_count INTEGER,
            notes TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS source_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_batch_id INTEGER NOT NULL,
            source_record_id TEXT,
            row_index INTEGER,
            raw_payload_json TEXT NOT NULL,
            mapped_payload_json TEXT,
            ingest_status TEXT NOT NULL DEFAULT 'pending',
            duplicate_status TEXT NOT NULL DEFAULT 'unchecked',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(import_batch_id) REFERENCES import_batches(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT,
            normalized_title TEXT,
            doi TEXT,
            normalized_doi TEXT,
            doi_url TEXT,
            authors_text TEXT,
            first_author TEXT,
            corresponding_author TEXT,
            corresponding_email TEXT,
            publication_year INTEGER,
            journal TEXT,
            abstract TEXT,
            keywords_text TEXT,
            volume TEXT,
            issue TEXT,
            pages TEXT,
            language TEXT,
            document_type TEXT,
            source_url TEXT,
            pdf_url TEXT,
            merge_status TEXT NOT NULL DEFAULT 'canonical_pending',
            quality_status TEXT NOT NULL DEFAULT 'needs_review',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS article_identifiers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            identifier_type TEXT NOT NULL,
            identifier_value TEXT NOT NULL,
            is_primary INTEGER NOT NULL DEFAULT 0,
            source_slug TEXT,
            UNIQUE(article_id, identifier_type, identifier_value),
            FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS article_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            source_record_id INTEGER NOT NULL,
            source_slug TEXT NOT NULL,
            source_record_key TEXT,
            is_canonical_source INTEGER NOT NULL DEFAULT 0,
            match_strategy TEXT,
            FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE,
            FOREIGN KEY(source_record_id) REFERENCES source_records(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS article_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            person_name TEXT,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'corresponding_author',
            source_slug TEXT,
            is_primary INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS article_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL UNIQUE,
            screening_status TEXT,
            pdf_status TEXT,
            appraisal_status TEXT,
            extraction_status TEXT,
            synthesis_status TEXT,
            last_phase TEXT,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS article_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            note_type TEXT NOT NULL DEFAULT 'general',
            note_text TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(article_id) REFERENCES articles(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_import_batches_project_id ON import_batches(project_id);
        CREATE INDEX IF NOT EXISTS idx_source_records_batch_id ON source_records(import_batch_id);
        CREATE INDEX IF NOT EXISTS idx_articles_project_id ON articles(project_id);
        CREATE INDEX IF NOT EXISTS idx_articles_normalized_doi ON articles(normalized_doi);
        CREATE INDEX IF NOT EXISTS idx_articles_normalized_title_year ON articles(normalized_title, publication_year);
        CREATE INDEX IF NOT EXISTS idx_article_identifiers_lookup ON article_identifiers(identifier_type, identifier_value);
        CREATE INDEX IF NOT EXISTS idx_article_contacts_email ON article_contacts(email);
        """
    )
