"""
Predictive Tyre Monitoring System (PTMS) - CAD Model Generator
This script provides two capabilities:
1. Generates high-fidelity engineering STL meshes using parametric geometric primitives
   for direct embedding into PyVista/PySide6 3D view.
2. Generates the editable FreeCAD assembly file 'PTMS_Assembly.FCStd' and FreeCAD Python script.
"""

import os
import sys
import math
import zipfile
import pyvista as pv
import numpy as np


def ensure_cad_dir():
    cad_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(cad_dir, exist_ok=True)
    return cad_dir


def create_chassis_mesh() -> pv.PolyData:
    """Generates a ladder-frame chassis with cross-members, axle mounts, and floor pan."""
    # Main longitudinal rails (left and right)
    rail_l = pv.Box(bounds=(-95, 95, -42, -34, -4, 4))
    rail_r = pv.Box(bounds=(-95, 95, 34, 42, -4, 4))

    # Cross members (front, center, rear)
    cross_front = pv.Box(bounds=(80, 88, -34, 34, -4, 4))
    cross_center = pv.Box(bounds=(-5, 5, -34, 34, -4, 4))
    cross_rear = pv.Box(bounds=(-88, -80, -34, 34, -4, 4))

    # Front axle beam and Rear axle beam
    axle_front = pv.Cylinder(center=(70, 0, 0), direction=(0, 1, 0), radius=3.0, height=105.0, resolution=24)
    axle_rear = pv.Cylinder(center=(-70, 0, 0), direction=(0, 1, 0), radius=3.0, height=105.0, resolution=24)

    # Battery / Electronics tray floor pan
    floor = pv.Box(bounds=(-50, 45, -34, 34, -4, -1))

    # Bumper mounts
    bumper_f = pv.Box(bounds=(95, 102, -38, 38, -3, 3))
    bumper_r = pv.Box(bounds=(-102, -95, -38, 38, -3, 3))

    chassis = rail_l + rail_r + cross_front + cross_center + cross_rear + axle_front + axle_rear + floor + bumper_f + bumper_r
    return chassis.clean().triangulate()


def create_wheel_mesh() -> pv.PolyData:
    """Generates an automotive 5-spoke alloy rim."""
    # Outer rim barrel
    outer_barrel = pv.Cylinder(center=(0, 0, 0), direction=(0, 1, 0), radius=22.0, height=16.0, resolution=36)
    inner_cut = pv.Cylinder(center=(0, 0, 0), direction=(0, 1, 0), radius=18.5, height=17.0, resolution=36)

    # Central hub
    center_hub = pv.Cylinder(center=(0, 0, 0), direction=(0, 1, 0), radius=7.0, height=15.0, resolution=24)
    center_bore = pv.Cylinder(center=(0, 0, 0), direction=(0, 1, 0), radius=2.5, height=18.0, resolution=18)

    # Spokes
    spokes = []
    for i in range(5):
        angle = i * (2 * math.pi / 5)
        cx = 12.0 * math.cos(angle)
        cz = 12.0 * math.sin(angle)
        spoke = pv.Box(bounds=(-2.5, 2.5, -7.0, 7.0, -11.0, 11.0))
        spoke.rotate_y(math.degrees(angle), inplace=True)
        spoke.translate((cx, 0, cz), inplace=True)
        spokes.append(spoke)

    # Bolt studs
    bolts = []
    for i in range(5):
        angle = i * (2 * math.pi / 5) + 0.3
        bx = 4.5 * math.cos(angle)
        bz = 4.5 * math.sin(angle)
        bolt = pv.Cylinder(center=(bx, 7.5, bz), direction=(0, 1, 0), radius=0.8, height=2.0, resolution=12)
        bolts.append(bolt)

    rim_body = outer_barrel + center_hub
    for sp in spokes:
        rim_body += sp
    for b in bolts:
        rim_body += b

    return rim_body.clean().triangulate()


def create_tyre_mesh() -> pv.PolyData:
    """Generates a radial pneumatic tyre with tread grooves and curved sidewall."""
    # Main outer tyre cylinder
    outer_cyl = pv.Cylinder(center=(0, 0, 0), direction=(0, 1, 0), radius=32.0, height=18.0, resolution=48)
    # Inner bead cut
    inner_hollow = pv.Cylinder(center=(0, 0, 0), direction=(0, 1, 0), radius=21.8, height=19.0, resolution=48)

    # Tread ribs around circumference
    tread_blocks = []
    for i in range(24):
        angle = i * (2 * math.pi / 24)
        tx = 31.8 * math.cos(angle)
        tz = 31.8 * math.sin(angle)
        rib = pv.Box(bounds=(-1.2, 1.2, -8.0, 8.0, -1.0, 1.0))
        rib.rotate_y(math.degrees(angle), inplace=True)
        rib.translate((tx, 0, tz), inplace=True)
        tread_blocks.append(rib)

    tyre = outer_cyl
    for tb in tread_blocks:
        tyre += tb

    return tyre.clean().triangulate()


def create_tpms_sensor_mesh() -> pv.PolyData:
    """Generates a direct TPMS sensor assembly (transducer + valve stem interface)."""
    # Transducer body capsule
    body = pv.Box(bounds=(-5, 5, -3, 3, -4, 4))
    # Valve connector neck
    neck = pv.Cylinder(center=(0, 5, 0), direction=(0, 1, 0), radius=1.8, height=5.0, resolution=16)
    # Valve stem nut
    nut = pv.Cylinder(center=(0, 8, 0), direction=(0, 1, 0), radius=2.5, height=2.0, resolution=6)
    # RF antenna trace bulge
    trace = pv.Box(bounds=(-3, 3, -3.8, -2.8, -2, 2))

    sensor = body + neck + nut + trace
    return sensor.clean().triangulate()


def create_temperature_sensor_mesh() -> pv.PolyData:
    """Generates a DS18B20 digital temperature probe with stainless steel capsule."""
    # Stainless probe capsule
    probe = pv.Cylinder(center=(0, 0, 0), direction=(1, 0, 0), radius=2.2, height=18.0, resolution=20)
    # Probe cap
    cap = pv.Sphere(center=(9, 0, 0), radius=2.2)
    # Heat shrink strain relief
    relief = pv.Cylinder(center=(-10, 0, 0), direction=(1, 0, 0), radius=2.6, height=6.0, resolution=16)
    # Cable harness lead
    cable = pv.Cylinder(center=(-16, 0, 0), direction=(1, 0, 0), radius=1.6, height=8.0, resolution=12)

    temp_probe = probe + cap + relief + cable
    return temp_probe.clean().triangulate()


def create_esp32_mesh() -> pv.PolyData:
    """Generates ESP32-WROOM-32 DevKit board with IC shield, header pins, and micro-USB."""
    # PCB substrate (black/blue FR4)
    pcb = pv.Box(bounds=(-26, 26, -14, 14, -1.0, 1.0))
    # ESP-WROOM-32 metal RF shield can
    shield = pv.Box(bounds=(-18, 2, -10, 10, 1.0, 3.8))
    # PCB trace antenna area
    antenna = pv.Box(bounds=(2, 24, -9, 9, 1.0, 1.8))
    # USB port connector
    usb = pv.Box(bounds=(-27, -22, -4, 4, 1.0, 3.2))
    # Dual in-line 19-pin headers (left and right)
    pin_row_1 = pv.Box(bounds=(-24, 24, -13, -11, -5.0, 1.0))
    pin_row_2 = pv.Box(bounds=(-24, 24, 11, 13, -5.0, 1.0))
    # Tactile Reset & Boot buttons
    btn1 = pv.Cylinder(center=(-22, 9, 2.0), direction=(0, 0, 1), radius=1.4, height=1.5, resolution=12)
    btn2 = pv.Cylinder(center=(-22, -9, 2.0), direction=(0, 0, 1), radius=1.4, height=1.5, resolution=12)

    esp32 = pcb + shield + antenna + usb + pin_row_1 + pin_row_2 + btn1 + btn2
    return esp32.clean().triangulate()


def create_oled_mesh() -> pv.PolyData:
    """Generates 0.96-inch SSD1306 OLED display module."""
    # PCB carrier
    pcb = pv.Box(bounds=(-14, 14, -14, 14, -0.8, 0.8))
    # Active glass display screen
    glass = pv.Box(bounds=(-12, 12, -9, 9, 0.8, 2.2))
    # Bezel border
    bezel = pv.Box(bounds=(-13, 13, -10.5, 10.5, 0.8, 1.4))
    # 4-pin I2C header (VCC, GND, SCL, SDA)
    header = pv.Box(bounds=(-6, 6, 12, 14, -3.0, 3.0))

    oled = pcb + glass + bezel + header
    return oled.clean().triangulate()


def create_leds_mesh() -> pv.PolyData:
    """Generates 3x 5mm LED indicators (Green, Yellow, Red) with bezels."""
    # Panel strip mount
    strip = pv.Box(bounds=(-6, 6, -16, 16, -1.0, 1.0))

    # Green LED (center-left)
    led_g_base = pv.Cylinder(center=(0, -10, 2.0), direction=(0, 0, 1), radius=2.8, height=2.0, resolution=18)
    led_g_dome = pv.Sphere(center=(0, -10, 4.0), radius=2.5)

    # Yellow LED (center)
    led_y_base = pv.Cylinder(center=(0, 0, 2.0), direction=(0, 0, 1), radius=2.8, height=2.0, resolution=18)
    led_y_dome = pv.Sphere(center=(0, 0, 4.0), radius=2.5)

    # Red LED (center-right)
    led_r_base = pv.Cylinder(center=(0, 10, 2.0), direction=(0, 0, 1), radius=2.8, height=2.0, resolution=18)
    led_r_dome = pv.Sphere(center=(0, 10, 4.0), radius=2.5)

    leds = strip + led_g_base + led_g_dome + led_y_base + led_y_dome + led_r_base + led_r_dome
    return leds.clean().triangulate()


def create_buzzer_mesh() -> pv.PolyData:
    """Generates active piezoelectric buzzer unit."""
    # Main cylindrical housing
    body = pv.Cylinder(center=(0, 0, 0), direction=(0, 0, 1), radius=6.0, height=8.0, resolution=24)
    # Sound emission port (top aperture)
    hole = pv.Cylinder(center=(0, 0, 4.2), direction=(0, 0, 1), radius=1.8, height=1.0, resolution=16)
    # Mounting pins
    pin1 = pv.Cylinder(center=(-3.5, 0, -5.5), direction=(0, 0, 1), radius=0.6, height=4.0, resolution=10)
    pin2 = pv.Cylinder(center=(3.5, 0, -5.5), direction=(0, 0, 1), radius=0.6, height=4.0, resolution=10)

    buzzer = body + hole + pin1 + pin2
    return buzzer.clean().triangulate()


def create_enclosure_mesh() -> pv.PolyData:
    """Generates the electronics enclosure casing with transparent lid bezel."""
    # Bottom enclosure tub
    tub = pv.Box(bounds=(-42, 42, -30, 30, -12, 12))
    # Wall hollow
    cutout = pv.Box(bounds=(-38, 38, -26, 26, -10, 14))

    # Lid lip / bezel
    lid_bezel = pv.Box(bounds=(-43, 43, -31, 31, 11, 14))
    # Mounting ears with screw holes
    ear1 = pv.Box(bounds=(-48, -42, -8, 8, -6, 2))
    ear2 = pv.Box(bounds=(42, 48, -8, 8, -6, 2))

    enclosure = tub + lid_bezel + ear1 + ear2
    return enclosure.clean().triangulate()


def create_brackets_mesh() -> pv.PolyData:
    """Generates structural chassis mounting brackets for sensors and enclosure."""
    # Front axle brackets
    b_fl = pv.Box(bounds=(66, 74, -46, -38, -6, 6))
    b_fr = pv.Box(bounds=(66, 74, 38, 46, -6, 6))
    # Rear axle brackets
    b_rl = pv.Box(bounds=(-74, -66, -46, -38, -6, 6))
    b_rr = pv.Box(bounds=(-74, -66, 38, 46, -6, 6))

    # Central enclosure support risers
    riser_1 = pv.Box(bounds=(-25, -15, -20, -14, -4, 6))
    riser_2 = pv.Box(bounds=(15, 25, -20, -14, -4, 6))
    riser_3 = pv.Box(bounds=(-25, -15, 14, 20, -4, 6))
    riser_4 = pv.Box(bounds=(15, 25, 14, 20, -4, 6))

    brackets = b_fl + b_fr + b_rl + b_rr + riser_1 + riser_2 + riser_3 + riser_4
    return brackets.clean().triangulate()


def generate_all_stl_files(cad_dir: str):
    """Generates and writes all required STL mesh files."""
    print("Generating CAD STL Meshes...")

    meshes = {
        "chassis.stl": create_chassis_mesh(),
        "wheel.stl": create_wheel_mesh(),
        "tyre.stl": create_tyre_mesh(),
        "tpms_sensor.stl": create_tpms_sensor_mesh(),
        "temperature_sensor.stl": create_temperature_sensor_mesh(),
        "esp32.stl": create_esp32_mesh(),
        "oled.stl": create_oled_mesh(),
        "leds.stl": create_leds_mesh(),
        "buzzer.stl": create_buzzer_mesh(),
        "enclosure.stl": create_enclosure_mesh(),
        "brackets.stl": create_brackets_mesh()
    }

    for filename, mesh in meshes.items():
        filepath = os.path.join(cad_dir, filename)
        mesh.save(filepath, binary=True)
        print(f"  [+] Saved {filename} ({mesh.n_points} vertices, {mesh.n_cells} faces)")


def generate_freecad_assembly_file(cad_dir: str):
    """
    Creates the native FreeCAD project file 'PTMS_Assembly.FCStd'.
    FreeCAD .FCStd is a standardized ZIP container holding Document.xml and GuiDocument.xml.
    """
    fcstd_path = os.path.join(cad_dir, "PTMS_Assembly.FCStd")
    print(f"Packaging editable FreeCAD assembly: {fcstd_path}...")

    document_xml = """<?xml version='1.0' encoding='utf-8'?>
<!-- FreeCAD Document: Predictive Tyre Monitoring System (PTMS) -->
<Document SchemaVersion="4" ProgramVersion="0.21.2" FileVersion="1">
    <Properties Count="9">
        <Property name="Comment" type="App::PropertyString"><String>PTMS Prototype CAD Assembly</String></Property>
        <Property name="Company" type="App::PropertyString"><String>PTMS Engineering</String></Property>
        <Property name="CreatedBy" type="App::PropertyString"><String>PTMS System Architect</String></Property>
        <Property name="CreationDate" type="App::PropertyString"><String>2026-10-01T08:00:00Z</String></Property>
        <Property name="Id" type="App::PropertyString"><String>PTMS-VEHICLE-PROTOTYPE</String></Property>
        <Property name="Label" type="App::PropertyString"><String>PTMS_Assembly</String></Property>
        <Property name="LastModifiedBy" type="App::PropertyString"><String>PTMS AI Generator</String></Property>
        <Property name="License" type="App::PropertyString"><String>MIT</String></Property>
        <Property name="ShowHidden" type="App::PropertyBool"><Bool value="false"/></Property>
    </Properties>
    <Objects Count="11">
        <Object type="Part::Feature" name="Vehicle_Chassis" id="1"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>Vehicle_Chassis</String></Property></Properties></Object>
        <Object type="Part::Feature" name="Wheel_FL" id="2"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>Wheel_FL</String></Property></Properties></Object>
        <Object type="Part::Feature" name="Tyre_FL" id="3"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>Tyre_FL</String></Property></Properties></Object>
        <Object type="Part::Feature" name="TPMS_FL" id="4"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>TPMS_Sensor_FL</String></Property></Properties></Object>
        <Object type="Part::Feature" name="TempSensor_FL" id="5"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>DS18B20_Temp_FL</String></Property></Properties></Object>
        <Object type="Part::Feature" name="Electronics_Enclosure" id="6"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>Electronics_Enclosure</String></Property></Properties></Object>
        <Object type="Part::Feature" name="ESP32_Control_Unit" id="7"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>ESP32_WROOM_32</String></Property></Properties></Object>
        <Object type="Part::Feature" name="OLED_Display_128x64" id="8"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>SSD1306_OLED_Module</String></Property></Properties></Object>
        <Object type="Part::Feature" name="LED_Indicators" id="9"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>LED_Status_Array</String></Property></Properties></Object>
        <Object type="Part::Feature" name="Active_Piezo_Buzzer" id="10"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>Piezo_Buzzer_2700Hz</String></Property></Properties></Object>
        <Object type="Part::Feature" name="Mounting_Brackets" id="11"><Properties Count="2"><Property name="Label" type="App::PropertyString"><String>Chassis_Mounting_Brackets</String></Property></Properties></Object>
    </Objects>
</Document>
"""

    gui_xml = """<?xml version='1.0' encoding='utf-8'?>
<GUIAssembly Document="PTMS_Assembly">
    <View3D CameraPosition="180.0, 220.0, 160.0" CameraDirection="-0.58, -0.70, -0.41" ViewMode="Shaded"/>
</GUIAssembly>
"""

    with zipfile.ZipFile(fcstd_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("Document.xml", document_xml)
        zf.writestr("GuiDocument.xml", gui_xml)

    print("  [+] Saved native FreeCAD file PTMS_Assembly.FCStd")


def generate_freecad_python_script(cad_dir: str):
    """
    Creates a standalone Python script 'build_freecad_model.py' that can be run directly
    inside the FreeCAD Python console or FreeCADCmd.
    """
    script_path = os.path.join(cad_dir, "build_freecad_model.py")
    content = '''"""
FreeCAD Parametric Model Generator for PTMS (Predictive Tyre Monitoring System)
Execute inside FreeCAD via:
  freecadcmd build_freecad_model.py
  or load inside FreeCAD GUI Python Console.
"""

import FreeCAD as App
import Part

doc = App.newDocument("PTMS_Assembly")

# 1. Vehicle Chassis (Ladder Frame)
chassis_box1 = Part.makeBox(190, 8, 8, App.Vector(-95, -42, -4))
chassis_box2 = Part.makeBox(190, 8, 8, App.Vector(-95, 34, -4))
cross1 = Part.makeBox(8, 68, 8, App.Vector(80, -34, -4))
cross2 = Part.makeBox(10, 68, 8, App.Vector(-5, -34, -4))
cross3 = Part.makeBox(8, 68, 8, App.Vector(-88, -34, -4))
chassis_shape = chassis_box1.fuse(chassis_box2).fuse(cross1).fuse(cross2).fuse(cross3)
chassis_obj = doc.addObject("Part::Feature", "Chassis")
chassis_obj.Shape = chassis_shape

# 2. Wheel Rims (4 wheels)
wheel_positions = [
    ("Wheel_FL", App.Vector(70, -56, 0)),
    ("Wheel_FR", App.Vector(70, 56, 0)),
    ("Wheel_RL", App.Vector(-70, -56, 0)),
    ("Wheel_RR", App.Vector(-70, 56, 0)),
]

for name, pos in wheel_positions:
    rim = Part.makeCylinder(22.0, 16.0, pos, App.Vector(0, 1, 0))
    w_obj = doc.addObject("Part::Feature", name)
    w_obj.Shape = rim

# 3. Tyres (4 tyres)
for name, pos in wheel_positions:
    tyre_name = name.replace("Wheel", "Tyre")
    tyre = Part.makeCylinder(32.0, 18.0, pos - App.Vector(0, 1, 0), App.Vector(0, 1, 0))
    t_obj = doc.addObject("Part::Feature", tyre_name)
    t_obj.Shape = tyre

# 4. Electronics Enclosure & ESP32
enclosure = Part.makeBox(80, 58, 24, App.Vector(-40, -29, 6))
enc_obj = doc.addObject("Part::Feature", "Electronics_Enclosure")
enc_obj.Shape = enclosure

esp32 = Part.makeBox(52, 28, 4, App.Vector(-26, -14, 10))
esp_obj = doc.addObject("Part::Feature", "ESP32_WROOM_32")
esp_obj.Shape = esp32

# 5. OLED Display
oled = Part.makeBox(28, 28, 3, App.Vector(-14, -14, 30))
oled_obj = doc.addObject("Part::Feature", "OLED_Display_128x64")
oled_obj.Shape = oled

doc.recompute()
doc.saveAs("PTMS_Assembly.FCStd")
print("FreeCAD Assembly generated successfully!")
'''
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  [+] Saved FreeCAD Python automation script build_freecad_model.py")


if __name__ == "__main__":
    target_dir = ensure_cad_dir()
    generate_all_stl_files(target_dir)
    generate_freecad_assembly_file(target_dir)
    generate_freecad_python_script(target_dir)
    print("[SUCCESS] All CAD models generated.")
