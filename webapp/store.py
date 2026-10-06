"""Fila SQLite de uma única execução ativa e retenção de envios públicos."""

from __future__ import annotations

import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path


DATA_DIR = Path(os.environ.get("RANKING_DATA_DIR", Path(__file__).resolve().parents[1] / "runtime-data"))
DB_PATH = DATA_DIR / "jobs.sqlite3"


class LimitError(ValueError):
    pass


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(value: datetime | None = None) -> str:
    return (value or now()).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=15000")
    return con


@contextmanager
def db():
    con = connect()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def initialize() -> None:
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            reference_date TEXT NOT NULL,
            input_sha256 TEXT NOT NULL,
            client_ip TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed')),
            stage TEXT NOT NULL,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS jobs_status_idx ON jobs(status, created_at);
        CREATE INDEX IF NOT EXISTS jobs_rate_idx ON jobs(client_ip, created_at);
        """)


def check_limits(client_ip: str) -> None:
    initialize()
    since = stamp(now() - timedelta(hours=1))
    with db() as con:
        if con.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0] >= 3:
            raise LimitError("Há três análises em andamento ou aguardando. Tente novamente mais tarde.")
        if con.execute("SELECT count(*) FROM jobs WHERE client_ip=? AND created_at>=?", (client_ip, since)).fetchone()[0] >= 3:
            raise LimitError("Limite de três análises por hora atingido para esta origem.")
        if con.execute("SELECT count(*) FROM jobs WHERE created_at>=?", (since,)).fetchone()[0] >= 30:
            raise LimitError("O limite temporário de análises foi atingido. Tente mais tarde.")


def create_job(job_id: str, reference_date: str, input_sha256: str, client_ip: str) -> None:
    initialize()
    with db() as con:
        con.execute("BEGIN IMMEDIATE")
        since = stamp(now() - timedelta(hours=1))
        if con.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0] >= 3:
            raise LimitError("Há três análises em andamento ou aguardando. Tente novamente mais tarde.")
        if con.execute("SELECT count(*) FROM jobs WHERE client_ip=? AND created_at>=?", (client_ip, since)).fetchone()[0] >= 3:
            raise LimitError("Limite de três análises por hora atingido para esta origem.")
        if con.execute("SELECT count(*) FROM jobs WHERE created_at>=?", (since,)).fetchone()[0] >= 30:
            raise LimitError("O limite temporário de análises foi atingido. Tente mais tarde.")
        con.execute("INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
                    (job_id, reference_date, input_sha256, client_ip, "queued", "Aguardando processamento", None, stamp(), stamp()))


def get_job(job_id: str) -> dict | None:
    initialize()
    with db() as con:
        row = con.execute("SELECT id,reference_date,input_sha256,status,stage,error,created_at,updated_at FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None


def next_job() -> dict | None:
    initialize()
    with db() as con:
        con.execute("BEGIN IMMEDIATE")
        if con.execute("SELECT 1 FROM jobs WHERE status='running' LIMIT 1").fetchone():
            return None
        row = con.execute("SELECT id,reference_date FROM jobs WHERE status='queued' ORDER BY created_at,id LIMIT 1").fetchone()
        if not row:
            return None
        con.execute("UPDATE jobs SET status='running',stage='Validando extração',updated_at=? WHERE id=?", (stamp(), row["id"]))
        return dict(row)


def update_job(job_id: str, *, status: str | None = None, stage: str | None = None,
               error: str | None = None) -> None:
    columns = ["updated_at=?"]
    values: list[str] = [stamp()]
    for key, value in (("status", status), ("stage", stage), ("error", error)):
        if value is not None:
            columns.append(f"{key}=?")
            values.append(value)
    values.append(job_id)
    with db() as con:
        con.execute(f"UPDATE jobs SET {','.join(columns)} WHERE id=?", values)


def recover_interrupted() -> None:
    initialize()
    with db() as con:
        con.execute("UPDATE jobs SET status='failed',stage='Interrompida',error='O servidor reiniciou durante o processamento. Envie o arquivo novamente.',updated_at=? WHERE status='running'", (stamp(),))


def cleanup() -> None:
    """Apaga arquivos expirados sem tocar no resultado fixo do case."""
    initialize()
    raw_before = stamp(now() - timedelta(hours=24))
    result_before = stamp(now() - timedelta(days=7))
    metadata_before = stamp(now() - timedelta(days=30))
    with db() as con:
        rows = con.execute("SELECT id,status,created_at FROM jobs WHERE status IN ('completed','failed')").fetchall()
        for row in rows:
            job_id = row["id"]
            if len(job_id) != 32 or not all(c in "0123456789abcdef" for c in job_id):
                continue
            if row["created_at"] < raw_before:
                (DATA_DIR / "uploads" / f"{job_id}.csv").unlink(missing_ok=True)
            if row["created_at"] < result_before:
                shutil.rmtree(DATA_DIR / "runs" / job_id, ignore_errors=True)
                (DATA_DIR / "logs" / f"{job_id}.log").unlink(missing_ok=True)
            if row["created_at"] < metadata_before:
                con.execute("DELETE FROM jobs WHERE id=?", (job_id,))
