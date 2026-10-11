"""
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
