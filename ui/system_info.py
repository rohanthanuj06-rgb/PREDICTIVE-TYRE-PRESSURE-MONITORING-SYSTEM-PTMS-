"""
Predictive Tyre Monitoring System (PTMS) - System Information & Hardware Digital Twin Page
Simulates the physical hardware peripherals:
- Virtual 128x64 SSD1306 I2C OLED display (pixel/phosphor rendering)
- GPIO Status LEDs (Green=GPIO18, Yellow=GPIO19, Red=GPIO21)
- Active Piezo Buzzer (GPIO22, 2.7 kHz resonant alert)
- ESP32 Dual-Core Microcontroller runtime diagnostics
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class VirtualOLEDWidget(QFrame):
    """
    Renders a realistic physical 0.96-inch 128x64 monochrome SSD1306 OLED display
    with cyber-cyan phosphor aesthetics.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 180)
        self.setStyleSheet("""
            QFrame {
                background-color: #050a0f;
                border: 6px solid #1c2128;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # OLED Display Screen Container
        screen_frame = QFrame()
        screen_frame.setStyleSheet("""
            QFrame {
                background-color: #02060a;
                border: 1px solid #1f364d;
                border-radius: 4px;
                padding: 6px;
            }
        """)
        s_layout = QVBoxLayout(screen_frame)
        s_layout.setContentsMargins(4, 4, 4, 4)
        s_layout.setSpacing(2)

        self.screen_labels = []
        for i in range(6):
            lbl = QLabel(f"LINE {i}")
            lbl.setStyleSheet("""
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                font-weight: bold;
                color: #38bdf8;
                letter-spacing: 1px;
            """)
            s_layout.addWidget(lbl)
            self.screen_labels.append(lbl)

        layout.addWidget(screen_frame)

        # OLED Module Bezel Branding
        lbl_brand = QLabel("0.96\" I2C 128x64 OLED (SSD1306)")
        lbl_brand.setStyleSheet("font-size: 9px; color: #475569; text-align: center;")
        lbl_brand.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_brand)

    def set_lines(self, lines: list):
        for i, text in enumerate(lines[:6]):
            self.screen_labels[i].setText(text)


class HardwareLEDWidget(QWidget):
    """
    Simulates a 5mm dome LED indicator with active glow diffusion.
    """

    def __init__(self, color_name: str, label_text: str, gpio_pin: str, parent=None):
        super().__init__(parent)
        self.color_name = color_name.lower()
        self.label_text = label_text
        self.gpio_pin = gpio_pin
        self.is_on = False

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        # LED circular bulb
        self.bulb = QFrame()
        self.bulb.setFixedSize(32, 32)
        self._update_bulb_style()

        layout.addWidget(self.bulb, 0, Qt.AlignCenter)

        lbl_name = QLabel(self.label_text)
        lbl_name.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffffff;")
        lbl_name.setAlignment(Qt.AlignCenter)

        lbl_gpio = QLabel(self.gpio_pin)
        lbl_gpio.setStyleSheet("font-size: 10px; color: #64748b;")
        lbl_gpio.setAlignment(Qt.AlignCenter)

        layout.addWidget(lbl_name)
        layout.addWidget(lbl_gpio)

    def set_active(self, active: bool):
        if self.is_on != active:
            self.is_on = active
            self._update_bulb_style()

    def _update_bulb_style(self):
        color_map = {
            "green": ("#22c55e", "rgba(34, 197, 94, 0.7)", "#14532d"),
            "yellow": ("#eab308", "rgba(234, 179, 8, 0.7)", "#713f12"),
            "red": ("#ef4444", "rgba(239, 68, 68, 0.7)", "#7f1d1d")
        }
        bright, glow, dim = color_map.get(self.color_name, ("#22c55e", "rgba(34, 197, 94, 0.7)", "#14532d"))

        if self.is_on:
            self.bulb.setStyleSheet(f"""
                QFrame {{
                    background-color: {bright};
                    border: 2px solid #ffffff;
                    border-radius: 16px;
                    box-shadow: 0 0 16px {glow};
                }}
            """)
        else:
            self.bulb.setStyleSheet(f"""
                QFrame {{
                    background-color: {dim};
                    border: 2px solid #334155;
                    border-radius: 16px;
                }}
            """)


class BuzzerWidget(QWidget):
    """
    Simulates physical active piezo buzzer transducer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_active = False

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)

        self.icon_lbl = QLabel("🔇")
        self.icon_lbl.setStyleSheet("font-size: 32px;")
        self.icon_lbl.setAlignment(Qt.AlignCenter)

        self.status_lbl = QLabel("BUZZER: SILENT")
        self.status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b;")
        self.status_lbl.setAlignment(Qt.AlignCenter)

        lbl_gpio = QLabel("GPIO 22 (PWM 2.7 kHz)")
        lbl_gpio.setStyleSheet("font-size: 10px; color: #64748b;")
        lbl_gpio.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.status_lbl)
        layout.addWidget(lbl_gpio)

    def set_active(self, active: bool, freq: int = 2700):
        self.is_active = active
        if active:
            self.icon_lbl.setText("🔊")
            self.status_lbl.setText(f"BUZZER: ACTIVE ({freq} Hz)")
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #ef4444;")
        else:
            self.icon_lbl.setText("🔇")
            self.status_lbl.setText("BUZZER: SILENT")
            self.status_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748b;")


class SystemInfoView(QWidget):
    """
    System Information & Embedded Hardware Digital Twin View.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Title
        title_box = QVBoxLayout()
        lbl_title = QLabel("SYSTEM INFORMATION & HARDWARE DIGITAL TWIN")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_CYAN};")
        lbl_sub = QLabel("Virtual replica of ESP32 edge microcontroller, physical SSD1306 OLED, status LEDs, and buzzer")
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        main_layout.addLayout(title_box)

        # Top Hardware Peripherals Frame (OLED + LEDs + Buzzer)
        hw_frame = QFrame()
        hw_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        hw_layout = QHBoxLayout(hw_frame)
        hw_layout.setSpacing(24)

        # 1. Virtual OLED Box
        oled_box = QVBoxLayout()
        lbl_oled_title = QLabel("VIRTUAL OLED DISPLAY")
        lbl_oled_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
        oled_box.addWidget(lbl_oled_title)
        self.virtual_oled = VirtualOLEDWidget()
        oled_box.addWidget(self.virtual_oled)
        hw_layout.addLayout(oled_box)

        # Divider
        div1 = QFrame()
        div1.setFrameShape(QFrame.VLine)
        div1.setStyleSheet(f"background-color: {BORDER_COLOR}; max-width: 1px;")
        hw_layout.addWidget(div1)

        # 2. Status LEDs Strip
        led_box = QVBoxLayout()
        lbl_led_title = QLabel("HARDWARE STATUS LEDS")
        lbl_led_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
        led_box.addWidget(lbl_led_title)

        leds_row = QHBoxLayout()
        self.led_green = HardwareLEDWidget("green", "SAFE", "GPIO 18")
        self.led_yellow = HardwareLEDWidget("yellow", "WARNING", "GPIO 19")
        self.led_red = HardwareLEDWidget("red", "CRITICAL", "GPIO 21")

        self.led_green.set_active(True)

        leds_row.addWidget(self.led_green)
        leds_row.addWidget(self.led_yellow)
        leds_row.addWidget(self.led_red)
        led_box.addLayout(leds_row)
        hw_layout.addLayout(led_box)

        # Divider
        div2 = QFrame()
        div2.setFrameShape(QFrame.VLine)
        div2.setStyleSheet(f"background-color: {BORDER_COLOR}; max-width: 1px;")
        hw_layout.addWidget(div2)

        # 3. Piezo Buzzer
        buzzer_box = QVBoxLayout()
        lbl_bz_title = QLabel("ACTIVE PIEZO BUZZER")
        lbl_bz_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #ffffff;")
        buzzer_box.addWidget(lbl_bz_title)

        self.virtual_buzzer = BuzzerWidget()
        buzzer_box.addWidget(self.virtual_buzzer)
        hw_layout.addLayout(buzzer_box)

        main_layout.addWidget(hw_frame)

        # Bottom Hardware Specifications Grid (ESP32, Sensors, Power)
        spec_grid = QGridLayout()
        spec_grid.setSpacing(14)

        # Card 1: ESP32 Firmware & System Details
        self.card_esp = self._create_spec_card("ESP32 CONTROLLER ARCHITECTURE", [
            ("Microcontroller", "ESP32-WROOM-32D (Dual-Core Tensilica LX6)"),
            ("Clock Speed", "240 MHz (Dynamic Frequency Scaling)"),
            ("Operating System", "FreeRTOS Dual-Core Multi-Tasking"),
            ("Core 0 Task", "RF 433 MHz Telemetry Ingestion (100 Hz)"),
            ("Core 1 Task", "Edge Regression & OLED Framebuffer (10 Hz)"),
            ("Internal Flash", "4 MB SPI Flash Memory"),
            ("Free Heap RAM", "214,580 Bytes"),
            ("I2C Bus Address", "0x3C (SSD1306 Display)")
        ])

        # Card 2: Sensor Package Specifications
        self.card_sensor_spec = self._create_spec_card("WHEEL SENSOR NODE SPECIFICATIONS", [
            ("TPMS Transducer", "Piezo-resistive MEMS (0 to 65 PSI range)"),
            ("Pressure Accuracy", "±0.1 PSI (12-bit ADC quantization)"),
            ("RF Transmission", "433.92 MHz FSK Manchester Encoded"),
            ("Temperature Probe", "DS18B20 1-Wire Digital Sensor"),
            ("Temp Accuracy", "±0.0625 °C (-40°C to +125°C)"),
            ("Power Source", "CR2032 3.0V Lithium Coin Cell (Estimated 5 yr)"),
            ("RF Protocol", "Custom Lightweight Automotive Packet Protocol"),
            ("Sampling Frequency", "10 Hz continuous active mode")
        ])

        spec_grid.addWidget(self.card_esp, 0, 0)
        spec_grid.addWidget(self.card_sensor_spec, 0, 1)

        main_layout.addLayout(spec_grid)
        main_layout.addStretch()

    def _create_spec_card(self, title: str, items: list) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(8)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLOR_CYAN};")
        layout.addWidget(t_lbl)

        grid = QGridLayout()
        grid.setSpacing(6)
        for r, (k, v) in enumerate(items):
            k_lbl = QLabel(f"<b>{k}:</b>")
            k_lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
            v_lbl = QLabel(v)
            v_lbl.setStyleSheet("font-size: 12px; color: #ffffff;")
            grid.addWidget(k_lbl, r, 0)
            grid.addWidget(v_lbl, r, 1)

        layout.addLayout(grid)
        return frame

    def update_state(self, snapshot: dict):
        # Update Virtual OLED
        oled_lines = snapshot.get("oled_lines", [])
        if oled_lines:
            self.virtual_oled.set_lines(oled_lines)

        # Update GPIO LEDs & Buzzer
        gpio = snapshot.get("gpio", {})
        self.led_green.set_active(gpio.get("led_green", True))
        self.led_yellow.set_active(gpio.get("led_yellow", False))
        self.led_red.set_active(gpio.get("led_red", False))

        self.virtual_buzzer.set_active(
            gpio.get("buzzer_active", False),
            gpio.get("buzzer_freq_hz", 2700)
        )
