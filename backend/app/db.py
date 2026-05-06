import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import ensure_data_dir, settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
  project_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  goal TEXT NOT NULL,
  agent_type TEXT NOT NULL,
  budget_dollars REAL,
  latency_slo_seconds INTEGER,
  priority TEXT,
  status TEXT NOT NULL DEFAULT 'running',
  summary TEXT,
  started_at TEXT,
  ended_at TEXT,
  benchmark_name TEXT,
  benchmark_task_id TEXT,
  repo_name TEXT,
  issue_id TEXT,
  agent_name TEXT,
  baseline_or_optimized TEXT,
  task_success INTEGER,
  tests_passed INTEGER,
  tests_failed INTEGER,
  patch_generated INTEGER,
  files_changed_count INTEGER,
  retry_count INTEGER,
  before_after_pair_id TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  event_type TEXT NOT NULL,
  span_id TEXT NOT NULL,
  parent_span_id TEXT,
  name TEXT NOT NULL,
  attributes_json TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE INDEX IF NOT EXISTS idx_events_task_time ON events(task_id, timestamp);

CREATE TABLE IF NOT EXISTS context_snapshots (
  context_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  event_id TEXT NOT NULL,
  size_tokens INTEGER NOT NULL DEFAULT 0,
  repeated_tokens_estimate INTEGER NOT NULL DEFAULT 0,
  context_kind TEXT,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id),
  FOREIGN KEY(event_id) REFERENCES events(event_id)
);

CREATE TABLE IF NOT EXISTS analysis_reports (
  task_id TEXT PRIMARY KEY,
  report_json TEXT NOT NULL,
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
  recommendation_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  rationale TEXT NOT NULL,
  confidence REAL NOT NULL,
  metrics_json TEXT NOT NULL,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE TABLE IF NOT EXISTS context_optimization_reports (
  task_id TEXT PRIMARY KEY,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE TABLE IF NOT EXISTS scheduler_reports (
  task_id TEXT PRIMARY KEY,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE TABLE IF NOT EXISTS backend_hint_reports (
  task_id TEXT PRIMARY KEY,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE TABLE IF NOT EXISTS hardware_telemetry_samples (
  sample_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  backend_id TEXT NOT NULL,
  gpu_utilization_percent REAL,
  cpu_utilization_percent REAL,
  gpu_memory_used_percent REAL,
  queue_depth INTEGER,
  prefill_ms INTEGER,
  decode_ms INTEGER,
  kv_cache_hit_rate REAL,
  attributes_json TEXT NOT NULL,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE INDEX IF NOT EXISTS idx_hardware_telemetry_task_time ON hardware_telemetry_samples(task_id, timestamp);

CREATE TABLE IF NOT EXISTS hardware_analysis_reports (
  task_id TEXT PRIMARY KEY,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(task_id) REFERENCES tasks(task_id)
);

CREATE TABLE IF NOT EXISTS silicon_blueprint_reports (
  blueprint_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trace_replay_reports (
  replay_id TEXT PRIMARY KEY,
  blueprint_id TEXT NOT NULL,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(blueprint_id) REFERENCES silicon_blueprint_reports(blueprint_id)
);

CREATE TABLE IF NOT EXISTS measured_validation_experiments (
  experiment_id TEXT PRIMARY KEY,
  scenario_id TEXT NOT NULL,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS benchmark_suite_runs (
  benchmark_run_id TEXT PRIMARY KEY,
  suite_name TEXT NOT NULL,
  agent_name TEXT NOT NULL,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phase1_exit_packages (
  package_id TEXT PRIMARY KEY,
  report_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        ensure_task_validation_columns(conn)


def ensure_task_validation_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
    columns = {
        "benchmark_name": "TEXT",
        "priority": "TEXT",
        "benchmark_task_id": "TEXT",
        "repo_name": "TEXT",
        "issue_id": "TEXT",
        "agent_name": "TEXT",
        "baseline_or_optimized": "TEXT",
        "task_success": "INTEGER",
        "tests_passed": "INTEGER",
        "tests_failed": "INTEGER",
        "patch_generated": "INTEGER",
        "files_changed_count": "INTEGER",
        "retry_count": "INTEGER",
        "before_after_pair_id": "TEXT",
    }
    for name, column_type in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE tasks ADD COLUMN {name} {column_type}")


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
