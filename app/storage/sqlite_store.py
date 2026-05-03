from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

from app.models import (
    ControlDecision,
    ControlSettings,
    Measurement,
    datetime_to_iso,
    parse_bool,
    utc_now,
)


class SQLiteStore:
    def __init__(self, database_path: str) -> None:
        self.database_path = database_path
        self._lock = threading.RLock()
        if database_path != ":memory:":
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(database_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def init_db(self) -> None:
        with self._lock, self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    pv_power_w INTEGER NOT NULL,
                    output_power_w INTEGER NOT NULL,
                    grid_power_w INTEGER NOT NULL,
                    battery_soc INTEGER NOT NULL,
                    charge_discharge_power_w INTEGER NOT NULL,
                    device_status TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
                ON measurements(timestamp);

                CREATE TABLE IF NOT EXISTS control_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    current_output_power_w INTEGER NOT NULL,
                    target_output_power_w INTEGER NOT NULL,
                    grid_power_w INTEGER,
                    battery_soc INTEGER,
                    zero_export_enabled TEXT NOT NULL,
                    control_mode TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    error_status TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_control_decisions_timestamp
                ON control_decisions(timestamp);

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    source TEXT NOT NULL,
                    message TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_logs_timestamp
                ON logs(timestamp);
                """
            )

    def save_measurement(self, measurement: Measurement) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO measurements (
                    timestamp,
                    pv_power_w,
                    output_power_w,
                    grid_power_w,
                    battery_soc,
                    charge_discharge_power_w,
                    device_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime_to_iso(measurement.timestamp),
                    measurement.pv_power_w,
                    measurement.output_power_w,
                    measurement.grid_power_w,
                    measurement.battery_soc,
                    measurement.charge_discharge_power_w,
                    measurement.device_status,
                ),
            )

    def get_latest_measurement(self) -> Measurement | None:
        row = self._fetch_one("SELECT * FROM measurements ORDER BY id DESC LIMIT 1")
        return None if row is None else Measurement.from_row(row)

    def get_measurement_history(self, limit: int = 200) -> list[Measurement]:
        rows = self._fetch_all(
            "SELECT * FROM measurements ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 2000)),),
        )
        return [Measurement.from_row(row) for row in reversed(rows)]

    def save_control_decision(self, decision: ControlDecision) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                INSERT INTO control_decisions (
                    timestamp,
                    current_output_power_w,
                    target_output_power_w,
                    grid_power_w,
                    battery_soc,
                    zero_export_enabled,
                    control_mode,
                    reason,
                    error_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime_to_iso(decision.timestamp),
                    decision.current_output_power_w,
                    decision.target_output_power_w,
                    decision.grid_power_w,
                    decision.battery_soc,
                    "true" if decision.zero_export_enabled else "false",
                    decision.control_mode,
                    decision.reason,
                    decision.error_status,
                ),
            )

    def get_latest_control_decision(self) -> ControlDecision | None:
        row = self._fetch_one("SELECT * FROM control_decisions ORDER BY id DESC LIMIT 1")
        return None if row is None else ControlDecision.from_row(row)

    def save_settings(self, settings: ControlSettings) -> None:
        updated_at = datetime_to_iso(utc_now())
        with self._lock, self._connection:
            for key, value in settings.to_dict().items():
                stored = "true" if isinstance(value, bool) and value else "false" if isinstance(value, bool) else str(value)
                self._connection.execute(
                    """
                    INSERT INTO settings (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at
                    """,
                    (key, stored, updated_at),
                )

    def load_settings(self, defaults: ControlSettings | None = None) -> ControlSettings:
        rows = self._fetch_all("SELECT key, value FROM settings")
        if not rows:
            return defaults or ControlSettings()
        raw = {str(row["key"]): row["value"] for row in rows}
        return ControlSettings.from_mapping(raw, base=defaults or ControlSettings())

    def add_log(self, level: str, source: str, message: str) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                "INSERT INTO logs (timestamp, level, source, message) VALUES (?, ?, ?, ?)",
                (datetime_to_iso(utc_now()), level.upper(), source, message),
            )

    def get_logs(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            "SELECT timestamp, level, source, message FROM logs ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 1000)),),
        )
        return [dict(row) for row in rows]

    def _fetch_one(self, sql: str, parameters: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self._lock:
            return self._connection.execute(sql, parameters).fetchone()

    def _fetch_all(self, sql: str, parameters: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._connection.execute(sql, parameters).fetchall())

