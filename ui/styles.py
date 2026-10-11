"""
Predictive Tyre Monitoring System (PTMS) - Modern Automotive Dark Theme
Custom stylesheet and color palette definitions.
"""

# Color Palette Definitions
BG_DARK = "#0d1117"
BG_PANEL = "#161b22"
BG_CARD = "#1c2128"
BG_CARD_HOVER = "#242c38"
BORDER_COLOR = "#30363d"
BORDER_HIGHLIGHT = "#388bfd"

TEXT_PRIMARY = "#f0f6fc"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED = "#6e7681"

# Status colors
COLOR_SAFE = "#2ea043"       # Emerald Green (0-20%)
COLOR_NORMAL = "#3fb950"     # Light Green (21-40%)
COLOR_CAUTION = "#d29922"    # Amber Yellow (41-60%)
COLOR_WARNING = "#db6d28"    # Orange (61-80%)
COLOR_CRITICAL = "#f85149"   # Crimson Red (81-100%)
COLOR_CYAN = "#58a6ff"       # Neon Blue / Cyan Accent

GLOBAL_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
}}

QWidget {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}}

/* Sidebar Styling */
#sidebar {{
    background-color: {BG_PANEL};
    border-right: 1px solid {BORDER_COLOR};
    min-width: 240px;
    max-width: 240px;
}}

#sidebar QPushButton {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    text-align: left;
    padding: 12px 18px;
    border: none;
    border-left: 3px solid transparent;
    font-size: 14px;
    font-weight: 500;
    border-radius: 0px;
}}

#sidebar QPushButton:hover {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border-left: 3px solid {COLOR_CYAN};
}}

#sidebar QPushButton:checked {{
    background-color: rgba(56, 139, 253, 0.15);
    color: #ffffff;
    font-weight: bold;
    border-left: 3px solid {BORDER_HIGHLIGHT};
}}

/* Header Bar */
#headerBar {{
    background-color: {BG_PANEL};
    border-bottom: 1px solid {BORDER_COLOR};
    padding: 8px 16px;
}}

/* Cards and Panels */
.Card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_COLOR};
    border-radius: 10px;
    padding: 16px;
}}

.Card:hover {{
    border-color: #444c56;
}}

/* Tyre Card Styling */
.TyreCard {{
    background-color: {BG_CARD};
    border: 2px solid {BORDER_COLOR};
    border-radius: 12px;
    padding: 14px;
}}

/* Buttons */
QPushButton.PrimaryBtn {{
    background-color: #1f6feb;
    color: #ffffff;
    border: 1px solid #388bfd;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton.PrimaryBtn:hover {{
    background-color: #388bfd;
}}

QPushButton.SecondaryBtn {{
    background-color: #21262d;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}}

QPushButton.SecondaryBtn:hover {{
    background-color: #30363d;
    border-color: #8b949e;
}}

QPushButton.DangerBtn {{
    background-color: rgba(248, 81, 73, 0.2);
    color: #ff7b72;
    border: 1px solid rgba(248, 81, 73, 0.4);
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}}

QPushButton.DangerBtn:hover {{
    background-color: rgba(248, 81, 73, 0.4);
}}

/* ComboBox */
QComboBox {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 24px;
}}

QComboBox:hover {{
    border-color: {BORDER_HIGHLIGHT};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: #1f6feb;
}}

/* Slider */
QSlider::groove:horizontal {{
    height: 6px;
    background: #21262d;
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: #1f6feb;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: #58a6ff;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}}

/* Scrollbar */
QScrollBar:vertical {{
    background: {BG_PANEL};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #30363d;
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: #484f58;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Table */
QTableWidget {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_COLOR};
    gridline-color: #21262d;
    border-radius: 8px;
    color: {TEXT_PRIMARY};
}}

QTableWidget::item {{
    padding: 6px;
}}

QTableWidget::item:selected {{
    background-color: rgba(56, 139, 253, 0.25);
    color: #ffffff;
}}

QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {BORDER_COLOR};
    font-weight: 600;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    background-color: {BG_CARD};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 4px;
}}

QTabBar::tab:selected {{
    background-color: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-bottom: none;
    font-weight: bold;
}}
"""


def get_status_color(status: str) -> str:
    """Returns hexadecimal color code for a tyre status."""
    status_map = {
        "SAFE": COLOR_SAFE,
        "NORMAL": COLOR_NORMAL,
        "CAUTION": COLOR_CAUTION,
        "WARNING": COLOR_WARNING,
        "CRITICAL": COLOR_CRITICAL
    }
    return status_map.get(status.upper(), COLOR_SAFE)


def get_status_rgb(status: str):
    """Returns normalized RGB tuple (0.0 to 1.0) for 3D shaders."""
    s = status.upper()
    if s == "SAFE":
        return (0.18, 0.63, 0.26)
    elif s == "NORMAL":
        return (0.25, 0.73, 0.31)
    elif s == "CAUTION":
        return (0.82, 0.60, 0.13)
    elif s == "WARNING":
        return (0.86, 0.43, 0.16)
    elif s == "CRITICAL":
        return (0.97, 0.32, 0.29)
    return (0.18, 0.63, 0.26)
