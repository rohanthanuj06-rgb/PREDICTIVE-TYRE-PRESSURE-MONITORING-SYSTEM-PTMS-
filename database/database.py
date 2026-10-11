"""
Predictive Tyre Monitoring System (PTMS) - Database Layer
Author: PTMS Core Engineering Team
Database: SQLite
"""

import sqlite3
import os
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional


class PTMSDatabase:
    """
    Thread-safe SQLite database manager for PTMS telemetry, alerts, and system events.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Default to local data directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "ptms_telemetry.db")
        else:
            self.db_path = db_path
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Telemetry Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    tyre_id TEXT NOT NULL,
                    pressure REAL NOT NULL,
                    temperature REAL NOT NULL,
                    pressure_rate REAL NOT NULL,
                    temp_rate REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    status TEXT NOT NULL,
                    fault_type TEXT NOT NULL
                )
            """)

            # Alerts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    tyre_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0
                )
            """)

            # System Events Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT NOT NULL
                )
            """)

            # Indices for rapid querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_tyre ON telemetry(tyre_id, timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp DESC)")
            conn.commit()

    def log_telemetry(self, tyre_id: str, pressure: float, temperature: float,
                      pressure_rate: float, temp_rate: float, risk_score: float,
                      status: str, fault_type: str = "NORMAL") -> int:
        """Logs a single telemetry reading from a tyre sensor package."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO telemetry 
                (timestamp, tyre_id, pressure, temperature, pressure_rate, temp_rate, risk_score, status, fault_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, tyre_id, round(pressure, 2), round(temperature, 2),
                  round(pressure_rate, 4), round(temp_rate, 4), round(risk_score, 1),
                  status, fault_type))
            conn.commit()
            return cursor.lastrowid

    def log_telemetry_batch(self, batch_data: List[Dict[str, Any]]):
        """Logs multiple tyre readings in a single atomic transaction."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        records = [
            (
                timestamp,
                d["tyre_id"],
                round(d["pressure"], 2),
                round(d["temperature"], 2),
                round(d.get("pressure_rate", 0.0), 4),
                round(d.get("temp_rate", 0.0), 4),
                round(d.get("risk_score", 0.0), 1),
                d.get("status", "SAFE"),
                d.get("fault_type", "NORMAL")
            )
            for d in batch_data
        ]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany("""
                INSERT INTO telemetry 
                (timestamp, tyre_id, pressure, temperature, pressure_rate, temp_rate, risk_score, status, fault_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()

    def log_alert(self, tyre_id: str, severity: str, message: str) -> int:
        """Logs an alert message with severity (SAFE, CAUTION, WARNING, CRITICAL)."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (timestamp, tyre_id, severity, message)
                VALUES (?, ?, ?, ?)
            """, (timestamp, tyre_id, severity, message))
            conn.commit()
            return cursor.lastrowid

    def get_history(self, limit: int = 200, tyre_id: Optional[str] = None,
                    status_filter: Optional[str] = None,
                    fault_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves historical telemetry records with optional filters."""
        query = "SELECT * FROM telemetry WHERE 1=1"
        params: List[Any] = []

        if tyre_id and tyre_id != "ALL":
            query += " AND tyre_id = ?"
            params.append(tyre_id)

        if status_filter and status_filter != "ALL":
            query += " AND status = ?"
            params.append(status_filter)

        if fault_filter and fault_filter != "ALL":
            query += " AND fault_type = ?"
            params.append(fault_filter)

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent alerts."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def export_to_csv(self, file_path: str, tyre_id: Optional[str] = None) -> int:
        """Exports telemetry history to CSV file."""
        records = self.get_history(limit=50000, tyre_id=tyre_id)
        if not records:
            return 0

        keys = records[0].keys()
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(records)

        return len(records)

    def clear_history(self):
        """Clears all stored records."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM telemetry")
            cursor.execute("DELETE FROM alerts")
            cursor.execute("DELETE FROM system_events")
            cursor.execute("VACUUM")
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Returns database statistics for diagnostics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry")
            telemetry_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM alerts")
            alert_count = cursor.fetchone()[0]
            return {
                "telemetry_count": telemetry_count,
                "alert_count": alert_count,
                "db_path": self.db_path,
                "db_size_kb": round(os.path.getsize(self.db_path) / 1024, 2) if os.path.exists(self.db_path) else 0
            }


# Singleton instance
_db_instance: Optional[PTMSDatabase] = None

def get_database() -> PTMSDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = PTMSDatabase()
    return _db_instance
