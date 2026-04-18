"""SQLite Database Layer for MedExtract"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

from app.core.config import settings


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(settings.DB_PATH)), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            session_id   TEXT PRIMARY KEY,
            document_count INTEGER,
            status       TEXT DEFAULT 'complete',
            created_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS documents (
            document_id              TEXT PRIMARY KEY,
            session_id               TEXT,
            original_filename        TEXT,
            document_type            TEXT,
            classification_confidence REAL,
            file_path                TEXT,
            created_at               TEXT,
            FOREIGN KEY (session_id) REFERENCES analysis_sessions(session_id)
        );

        CREATE TABLE IF NOT EXISTS extractions (
            extraction_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id     TEXT,
            extraction_class TEXT,
            extraction_text  TEXT,
            char_start       INTEGER,
            char_end         INTEGER,
            alignment_status TEXT,
            group_key        TEXT,
            attributes       TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        );

        CREATE TABLE IF NOT EXISTS medication_records (
            record_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id         TEXT,
            medication_name     TEXT,
            dosage              TEXT,
            route               TEXT,
            frequency           TEXT,
            duration            TEXT,
            indication          TEXT,
            special_instruction TEXT,
            char_positions      TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        );

        CREATE TABLE IF NOT EXISTS radiology_findings (
            finding_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id    TEXT,
            finding        TEXT,
            body_part      TEXT,
            laterality     TEXT,
            character      TEXT,
            measurement    TEXT,
            impression     TEXT,
            recommendation TEXT,
            severity       TEXT,
            char_positions TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        );

        CREATE TABLE IF NOT EXISTS lab_results (
            result_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id     TEXT,
            test_name       TEXT,
            result_value    TEXT,
            unit            TEXT,
            reference_range TEXT,
            flag            TEXT,
            panel_name      TEXT,
            char_positions  TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        );
    """)

    conn.commit()
    conn.close()


def save_session(session_id: str, document_count: int):
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO analysis_sessions (session_id, document_count, status, created_at) VALUES (?, ?, ?, ?)",
        (session_id, document_count, "complete", datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def save_document(document_id: str, session_id: str, filename: str,
                  doc_type: str, confidence: float, file_path: str):
    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO documents
           (document_id, session_id, original_filename, document_type,
            classification_confidence, file_path, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (document_id, session_id, filename, doc_type, confidence, file_path,
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def save_extractions(document_id: str, extractions: list):
    conn = get_db()
    for e in extractions:
        span = e.source_span
        conn.execute(
            """INSERT INTO extractions
               (document_id, extraction_class, extraction_text,
                char_start, char_end, alignment_status, group_key, attributes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                document_id,
                e.extraction_class,
                e.extraction_text,
                span.char_start if span else None,
                span.char_end if span else None,
                span.alignment_status if span else None,
                e.group_key,
                json.dumps(e.attributes or {})
            )
        )
    conn.commit()
    conn.close()


def save_medication_records(document_id: str, records: list):
    conn = get_db()
    for r in records:
        char_positions = {k: (v.dict() if v else None) for k, v in r.source_spans.items()}
        conn.execute(
            """INSERT INTO medication_records
               (document_id, medication_name, dosage, route, frequency,
                duration, indication, special_instruction, char_positions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (document_id, r.medication_name, r.dosage, r.route, r.frequency,
             r.duration, r.indication, r.special_instruction,
             json.dumps(char_positions))
        )
    conn.commit()
    conn.close()


def save_radiology_findings(document_id: str, findings: list):
    conn = get_db()
    for f in findings:
        char_positions = {k: (v.dict() if v else None) for k, v in f.source_spans.items()}
        conn.execute(
            """INSERT INTO radiology_findings
               (document_id, finding, body_part, laterality, character,
                measurement, impression, recommendation, severity, char_positions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (document_id, f.finding, f.body_part, f.laterality, f.character,
             f.measurement, f.impression, f.recommendation, f.severity,
             json.dumps(char_positions))
        )
    conn.commit()
    conn.close()


def save_lab_results(document_id: str, results: list):
    conn = get_db()
    for r in results:
        char_positions = {k: (v.dict() if v else None) for k, v in r.source_spans.items()}
        conn.execute(
            """INSERT INTO lab_results
               (document_id, test_name, result_value, unit, reference_range,
                flag, panel_name, char_positions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (document_id, r.test_name, r.result_value, r.unit, r.reference_range,
             r.flag, r.panel_name, json.dumps(char_positions))
        )
    conn.commit()
    conn.close()


def get_session_history(limit: int = 20) -> list:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM analysis_sessions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
