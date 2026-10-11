"""
Predictive Tyre Monitoring System (PTMS) - History & Database Logs Page
View historical telemetry logged in SQLite, filter by tyre/status/fault,
and export datasets to CSV format.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    get_status_color, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)
from database.database import get_database


class HistoryView(QWidget):
    """
    Historical telemetry log table and CSV export manager.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_database()
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header Title
        title_box = QVBoxLayout()
        lbl_title = QLabel("TELEMETRY ARCHIVE & PERSISTENT DATABASE")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_CYAN};")
        lbl_sub = QLabel("Query historical wheel sensor logs, track fault events, and export forensic CSV datasets")
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        main_layout.addLayout(title_box)

        # Database Stats & Filter Toolbar
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        tb_layout = QHBoxLayout(toolbar_frame)
        tb_layout.setSpacing(12)

        # Filters
        tb_layout.addWidget(QLabel("Tyre:"))
        self.combo_tyre_filter = QComboBox()
        self.combo_tyre_filter.addItems(["ALL", "FL", "FR", "RL", "RR"])
        self.combo_tyre_filter.currentTextChanged.connect(self.refresh_data)
        tb_layout.addWidget(self.combo_tyre_filter)

        tb_layout.addWidget(QLabel("Status:"))
        self.combo_status_filter = QComboBox()
        self.combo_status_filter.addItems(["ALL", "SAFE", "NORMAL", "CAUTION", "WARNING", "CRITICAL"])
        self.combo_status_filter.currentTextChanged.connect(self.refresh_data)
        tb_layout.addWidget(self.combo_status_filter)

        tb_layout.addWidget(QLabel("Limit:"))
        self.combo_limit = QComboBox()
        self.combo_limit.addItems(["100", "250", "500", "1000"])
        self.combo_limit.currentTextChanged.connect(self.refresh_data)
        tb_layout.addWidget(self.combo_limit)

        tb_layout.addStretch()

        # Database Stats Label
        self.lbl_stats = QLabel("Records: 0 | Size: 0 KB")
        self.lbl_stats.setStyleSheet(f"color: {COLOR_CYAN}; font-weight: bold;")
        tb_layout.addWidget(self.lbl_stats)

        # Action Buttons
        btn_refresh = QPushButton("↺ Refresh")
        btn_refresh.setProperty("class", "SecondaryBtn")
        btn_refresh.clicked.connect(self.refresh_data)
        tb_layout.addWidget(btn_refresh)

        btn_export = QPushButton("📥 Export CSV")
        btn_export.setProperty("class", "PrimaryBtn")
        btn_export.clicked.connect(self._export_csv)
        tb_layout.addWidget(btn_export)

        btn_clear = QPushButton("🗑 Clear History")
        btn_clear.setProperty("class", "DangerBtn")
        btn_clear.clicked.connect(self._clear_history)
        tb_layout.addWidget(btn_clear)

        main_layout.addWidget(toolbar_frame)

        # Telemetry Data Table
        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Tyre", "Pressure (PSI)", "Temp (°C)",
            "dP/dt (PSI/min)", "dT/dt (°C/min)", "Risk (%)", "Status", "Fault Mode"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
        """)
        main_layout.addWidget(self.table, 1)

    def refresh_data(self):
        """Queries SQLite database with active filters and populates table."""
        tyre_filter = self.combo_tyre_filter.currentText()
        status_filter = self.combo_status_filter.currentText()
        limit = int(self.combo_limit.currentText())

        records = self.db.get_history(
            limit=limit,
            tyre_id=tyre_filter,
            status_filter=status_filter
        )

        self.table.setRowCount(len(records))
        for row, rec in enumerate(records):
            status = rec.get("status", "SAFE")
            color = get_status_color(status)

            self.table.setItem(row, 0, QTableWidgetItem(str(rec.get("timestamp", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(rec.get("tyre_id", ""))))

            item_p = QTableWidgetItem(f"{rec.get('pressure', 0.0):.2f}")
            self.table.setItem(row, 2, item_p)

            item_t = QTableWidgetItem(f"{rec.get('temperature', 0.0):.2f}")
            self.table.setItem(row, 3, item_t)

            item_dp = QTableWidgetItem(f"{rec.get('pressure_rate', 0.0):+.3f}")
            self.table.setItem(row, 4, item_dp)

            item_dt = QTableWidgetItem(f"{rec.get('temp_rate', 0.0):+.3f}")
            self.table.setItem(row, 5, item_dt)

            item_risk = QTableWidgetItem(f"{rec.get('risk_score', 0.0):.1f}%")
            self.table.setItem(row, 6, item_risk)

            item_status = QTableWidgetItem(status)
            item_status.setForeground(QColor(color))
            self.table.setItem(row, 7, item_status)

            self.table.setItem(row, 8, QTableWidgetItem(str(rec.get("fault_type", "NORMAL"))))

        stats = self.db.get_stats()
        self.lbl_stats.setText(f"Records: {stats['telemetry_count']} | Alerts: {stats['alert_count']} | Size: {stats['db_size_kb']} KB")

    def _export_csv(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Telemetry Dataset", "ptms_telemetry_export.csv", "CSV Files (*.csv)"
        )
        if file_path:
            count = self.db.export_to_csv(file_path)
            QMessageBox.information(self, "Export Complete", f"Successfully exported {count} telemetry records to:\n{file_path}")

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Clear Database", "Are you sure you want to permanently delete all telemetry and alert records?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.clear_history()
            self.refresh_data()
