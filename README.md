# Predictive Tyre Monitoring System (PTMS) Using TPMS for Cars
### Automotive Digital Twin & Edge Predictive Intelligence Platform

![PTMS Platform](PTMS/assets/icons/app_icon.png)

---

## 📌 Executive Summary

The **Predictive Tyre Monitoring System (PTMS)** is a high-fidelity automotive desktop application that serves as a **Digital Twin** for direct Tyre Pressure Monitoring Systems (TPMS).

In standard automotive implementations, conventional TPMS is purely **reactive**—it only alerts the driver after a tyre has lost 25% or more of its nominal pressure (typically dropping below 24 PSI), which often occurs when a puncture or blowout is already hazardous.

**PTMS introduces predictive intelligence:**
1. Continuous evaluation of **first derivatives**:
   - $\frac{dP}{dt}$ (Pressure loss rate in $\text{PSI/min}$)
   - $\frac{dT}{dt}$ (Temperature rise rate in $^\circ\text{C/min}$)
2. Detection of **sidewall deflection hysteretic friction heating**:
   - When an under-inflated tyre flexes against the asphalt, it generates internal casing heat.
3. Cross-axle symmetry monitoring ($\Delta P_{\text{axle}}$ between FL/FR and RL/RR).
4. Early hazard detection: PTMS alerts the driver of slow leaks and degradation **15 to 45 minutes earlier** while the tyre is still operating near 30 PSI!

---

## 🚀 Key Features

- **Embedded Interactive 3D CAD-Style Vehicle Prototype**:
  - Rendered **directly inside the PySide6 desktop window** using PyVistaQt / VTK.
  - No external windows, browsers, or CAD applications required.
  - Interactive camera control: Pan, Zoom, Orbit, and 5 Camera Presets (*RESET, TOP, FRONT, SIDE, ISOMETRIC*).
  - **Exploded Assembly Mode**: Separates chassis, wheel nodes, electronics enclosure, ESP32, OLED, LEDs, and buzzer with 3D engineering annotations.
  - **Dynamic Sensor Status Lighting**: Wheels highlight in *Safe Charcoal*, *Caution Amber*, *Warning Orange*, or *Critical Neon Red*.
  - **Animated 3D Data Flow**: Moving packet streams between Wheel Transducers $\rightarrow$ ESP32 $\rightarrow$ Prediction Engine.
- **Unified Digital Twin Architecture**:
  - Single simulation engine updates **Dashboard, Live Monitoring, 3D Vehicle, Prediction, Graphs, OLED, and Database** synchronously.
- **12-Step Automated Demonstration Mode**:
  - Fully scripted end-to-end scenario demonstrating real-time fault escalation, derivative detection, 3D visual alert, OLED update, GPIO LEDs, and buzzer alarm.
- **Virtual Hardware Integration**:
  - Virtual 128x64 SSD1306 I2C OLED display with real-time text rendering.
  - Status LEDs: GPIO 18 (Green), GPIO 19 (Yellow), GPIO 21 (Red).
  - Active Piezo Buzzer: GPIO 22 (2.7 kHz resonant alert).
  - Dual-Core ESP32 controller simulation (FreeRTOS Core 0 RF ingestion, Core 1 regression loop).
- **Persistent SQLite Telemetry & Forensic CSV Export**:
  - Stores timestamped records for all 4 tyres with query filtering and CSV export.

---

## 📂 Project Directory Structure

```
PTMS/
│
├── main.py                          # Primary application entry point
├── test_ptms.py                     # Automated integration test suite
├── requirements.txt                 # Python dependencies
│
├── ui/                              # PySide6 User Interface Pages
│   ├── main_window.py               # Sidebar navigation & universal header
│   ├── dashboard.py                 # Automotive KPI overview & 4 tyre cards
│   ├── monitoring.py                # 2D top-view vehicle blueprint & beacons
│   ├── vehicle_3d.py                # Embedded 3D CAD viewer & exploded view
│   ├── prediction.py                # Trend analysis & multi-factor risk engine
│   ├── sensor_data.py               # Live PyQtGraph waveforms (P, T, Risk vs Time)
│   ├── simulation.py                # Fault injection & 12-step demo sequencer
│   ├── history.py                   # SQLite query table & CSV exporter
│   ├── system_info.py               # Hardware Twin (OLED, LEDs, Buzzer, ESP32)
│   └── styles.py                    # Automotive dark theme & color palette
│
├── simulation/                      # Physics & Telemetry Engine
│   ├── tyre_model.py                # Thermodynamic gas laws & sidewall flex
│   ├── sensor_simulator.py          # Coordinates 4 wheel sensor nodes
│   └── simulation_engine.py         # Central 10 Hz coordinator & demo sequencer
│
├── sensors/                         # Virtual Transducer Modules
│   ├── tpms.py                      # Direct TPMS MEMS & 433 MHz RF packet
│   └── temperature.py               # DS18B20 1-Wire temperature sensor
│
├── controller/                      # Embedded Firmware Simulation
│   └── virtual_esp32.py             # Dual-core FreeRTOS logic & OLED buffer
│
├── prediction/                      # Edge Intelligence Algorithms
│   ├── trend_analysis.py            # Linear regression dP/dt & axle delta
│   └── risk_engine.py               # Multi-factor 0-100% Risk Score engine
│
├── database/                        # Persistence Layer
│   ├── database.py                  # SQLite database manager
│   └── data/
│       └── ptms_telemetry.db        # SQLite database file
│
├── cad/                             # CAD Geometry & FreeCAD Scripts
│   ├── generate_cad.py              # Procedural STL & FreeCAD generator
│   ├── build_freecad_model.py       # Standalone FreeCAD Python script
│   ├── PTMS_Assembly.FCStd          # Editable FreeCAD project file
│   ├── chassis.stl                  # Ladder-frame vehicle chassis
│   ├── wheel.stl                    # 5-spoke alloy rim
│   ├── tyre.stl                     # Pneumatic radial tyre
│   ├── tpms_sensor.stl              # TPMS micro-sensor assembly
│   ├── temperature_sensor.stl       # DS18B20 probe housing
│   ├── esp32.stl                    # ESP32-WROOM-32 DevKit board
│   ├── oled.stl                     # SSD1306 0.96" display module
│   ├── leds.stl                     # 5mm status LEDs
│   ├── buzzer.stl                   # Piezo buzzer transducer
│   ├── enclosure.stl                # Electronics enclosure casing
│   └── brackets.stl                 # Chassis mounting brackets
│
└── assets/                          # Graphic Assets & Icons
    ├── icons/
    │   └── app_icon.png
    └── images/
        └── logo.png
```

---

## 🛠️ Installation & Setup (Windows)

### Prerequisites
- Python 3.10 to 3.13 installed on Windows (64-bit).
- Pip package installer.

### 1. Install Required Dependencies
Open PowerShell or Command Prompt in the repository folder:
```powershell
pip install -r requirements.txt
```

*(All required packages: `PySide6`, `pyqtgraph`, `pyvista`, `pyvistaqt`, `vtk`, `numpy`, `pandas`, `scipy`, `matplotlib`, `pillow` will be installed).*

### 2. Verify System
Run the built-in test suite to ensure all 3D CAD meshes, database, and Qt bindings are operational:
```powershell
python PTMS\test_ptms.py
```

---

## 🖥️ Running the Application

### Method 1: Using the Windows Batch File
Double-click `run.bat` or run:
```powershell
.\run.bat
```

### Method 2: Using Python Directly
```powershell
python PTMS\main.py
```
*(Or from root: `python main.py`)*

---

## 🧭 Navigation Guide

| Page | Description |
|---|---|
| **📊 Dashboard** | Overall vehicle status, ESP32 metrics, health score, and 4 tyre status cards (*FL, FR, RL, RR*). |
| **🚗 Live Monitoring** | Top-view 2D vehicle blueprint with animated RF signal pulses and dynamic telemetry cards. |
| **🧊 3D Vehicle CAD** | **Embedded interactive 3D model**. Orbit, pan, zoom, view presets, exploded view, component inspector, and live fault highlighting. |
| **📈 Predictive Analysis** | Deep trend analysis, $dP/dt$ and $dT/dt$ linear regression slopes, cross-axle imbalance, and multi-factor risk decomposition. |
| **⚡ Sensor Data** | Real-time scrolling waveforms for Pressure vs Time, Temperature vs Time, and Risk Score vs Time. |
| **🧪 Simulation & Demo** | Manual fault injection (*Slow leak, Rapid leak, Overheating, High/Low pressure*) + **12-Step Automated Demonstration**. |
| **🗄️ History Logs** | Searchable SQLite database table with filtering by tyre, status, or fault mode, and CSV file export. |
| **⚙️ System Info** | Hardware Digital Twin featuring the Virtual SSD1306 OLED display, GPIO status LEDs, active buzzer, and ESP32 specs. |

---

## 🧪 12-Step Demonstration Scenario

To view the complete end-to-end fault escalation:
1. Click **"🚀 Run 12-Step Demo"** from the top header or the **Simulation** page.
2. Watch the sequence execute automatically:
   - **Step 1**: All tyres in nominal SAFE state.
   - **Step 2**: Rear Left (RL) tyre initiates slow pressure leakage.
   - **Step 3**: Pressure gradually drops ($32 \rightarrow 30.5$ PSI).
   - **Step 4**: Tyre temperature rises as sidewall flexes against the road.
   - **Step 5**: Trend analysis detects $dP/dt < -1.5\text{ PSI/min}$ and $dT/dt > +1.2^\circ\text{C/min}$.
   - **Step 6**: Predictive Risk Score climbs to $42\%$ (Entering *CAUTION*).
   - **Step 7**: RL status transitions: `SAFE` $\rightarrow$ `CAUTION` $\rightarrow$ `WARNING`.
   - **Step 8**: 3D RL tyre in the CAD model changes to Warning Amber/Yellow glow.
   - **Step 9**: Virtual OLED display updates with live fault line and degraded pressure.
   - **Step 10**: GPIO 18 (Green) turns OFF; GPIO 19 (Yellow) illuminates.
   - **Step 11**: Critical threshold reached; GPIO 21 (Red) illuminates; Piezo Buzzer pulses.
   - **Step 12**: System issues alert: **"PREDICTED TYRE FAILURE RISK" - "INSPECTION RECOMMENDED"**.

---

## 📐 FreeCAD & CAD Mesh Customization

- To re-generate or modify the CAD meshes:
  ```powershell
  python PTMS\cad\generate_cad.py
  ```
- To open the assembly in FreeCAD:
  Open `PTMS/cad/PTMS_Assembly.FCStd` directly in FreeCAD.
- To execute FreeCAD Python automation:
  Run `freecadcmd PTMS/cad/build_freecad_model.py`.
#   P R E D I C T I V E - T Y R E - P R E S S U R E - M O N I T O R I N G - S Y S T E M - P T M S -  
 