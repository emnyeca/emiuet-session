# -*- coding: utf-8 -*-
"""One-shot generator for the Phase A perfboard reference schematic.
Run once with KiCad 10 installed; produces .kicad_sch and .kicad_pro.
Kept in-tree for reproducibility / future regeneration."""
import os, uuid, json

SYMDIR = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
OUTDIR = os.path.dirname(os.path.abspath(__file__))
NAME = "phase_a_perfboard_reference"

def U():
    return str(uuid.uuid4())
ROOT = U()

def read(n):
    return open(os.path.join(SYMDIR, n), encoding="utf-8").read()

def extract(text, name):
    needle = '(symbol "%s"' % name
    i = text.find(needle); d = 0; j = i
    while j < len(text):
        if text[j] == '(':
            d += 1
        elif text[j] == ')':
            d -= 1
            if d == 0:
                return text[i:j + 1]
        j += 1
    raise SystemExit("missing " + name)

libmap = {
    "Device:D": ("Device.kicad_sym", "D"),
    "Switch:SW_Push": ("Switch.kicad_sym", "SW_Push"),
    "Connector_Generic:Conn_01x04": ("Connector_Generic.kicad_sym", "Conn_01x04"),
    "Connector_Generic:Conn_01x05": ("Connector_Generic.kicad_sym", "Conn_01x05"),
    "Connector_Generic:Conn_01x08": ("Connector_Generic.kicad_sym", "Conn_01x08"),
}
lib_blocks = []
for libid, (fn, nm) in libmap.items():
    blk = extract(read(fn), nm)
    blk = blk.replace('(symbol "%s"' % nm, '(symbol "%s"' % libid, 1)
    lib_blocks.append(blk)

# custom Teensy symbol pins
left = [("3V3", "3V3", 17.78, "passive"),
        ("24", "ROW0", 15.24, "bidirectional"), ("25", "ROW1", 12.7, "bidirectional"),
        ("26", "ROW2", 10.16, "bidirectional"), ("27", "ROW3", 7.62, "bidirectional"),
        ("28", "COL0", 5.08, "bidirectional"), ("29", "COL1", 2.54, "bidirectional"),
        ("30", "COL2", 0.0, "bidirectional"), ("31", "COL3", -2.54, "bidirectional"),
        ("36", "ENC_A", -5.08, "bidirectional"), ("37", "ENC_B", -7.62, "bidirectional"),
        ("38", "ENC_SW", -10.16, "bidirectional"), ("GND", "GND", -12.7, "passive")]
right = [("18", "SDA", 15.24, "bidirectional"), ("19", "SCL", 12.7, "bidirectional"),
         ("13", "SCK", 10.16, "bidirectional"), ("11", "MOSI", 7.62, "bidirectional"),
         ("10", "CS", 5.08, "bidirectional"), ("32", "LCD_RES", 2.54, "bidirectional"),
         ("33", "LCD_DC", 0.0, "bidirectional"), ("34", "LCD_BLK", -2.54, "bidirectional"),
         ("0", "RX1_RSVD", -5.08, "bidirectional"), ("1", "TX1_RSVD", -7.62, "bidirectional")]

def pin(et, px, py, rot, name, num):
    return ('\t\t\t(pin %s line\n\t\t\t\t(at %s %s %d)\n\t\t\t\t(length 5.08)\n'
            '\t\t\t\t(name "%s" (effects (font (size 1.016 1.016))))\n'
            '\t\t\t\t(number "%s" (effects (font (size 1.016 1.016))))\n\t\t\t)\n'
            % (et, px, py, rot, name, num))

teensy_pins = ""
for num, name, py, et in left:
    teensy_pins += pin(et, -20.32, py, 0, name, num)
for num, name, py, et in right:
    teensy_pins += pin(et, 20.32, py, 180, name, num)

teensy_sym = (
    '\t\t(symbol "EmiuetBench:Teensy4_1_Bench"\n'
    '\t\t\t(pin_names (offset 1.016))\n'
    '\t\t\t(exclude_from_sim no)\n\t\t\t(in_bom yes)\n\t\t\t(on_board yes)\n'
    '\t\t\t(property "Reference" "U" (at -15.24 22.86 0) (effects (font (size 1.27 1.27))))\n'
    '\t\t\t(property "Value" "Teensy 4.1 (bench header)" (at 0 -17.78 0) (effects (font (size 1.27 1.27))))\n'
    '\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
    '\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
    '\t\t\t(property "Description" "Generic Teensy 4.1 header for Phase A hand-wiring reference (no footprint)" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
    '\t\t\t(symbol "Teensy4_1_Bench_0_1"\n'
    '\t\t\t\t(rectangle (start -15.24 20.32) (end 15.24 -15.24)\n'
    '\t\t\t\t\t(stroke (width 0.254) (type default))\n\t\t\t\t\t(fill (type background))\n\t\t\t\t)\n'
    '\t\t\t)\n'
    '\t\t\t(symbol "Teensy4_1_Bench_1_1"\n'
    + teensy_pins +
    '\t\t\t)\n'
    '\t\t\t(embedded_fonts no)\n'
    '\t\t)\n')

parts = []
labels = []
texts = []

def place(libid, ref, val, sx, sy, pin_nums, show_val=False, ref_dy=-6.35):
    pins = "".join('\t\t(pin "%s" (uuid "%s"))\n' % (p, U()) for p in pin_nums)
    valhide = "" if show_val else " (hide yes)"
    s = ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s 0)\n\t\t(unit 1)\n'
         '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
         '\t\t(uuid "%s")\n'
         '\t\t(property "Reference" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))))\n'
         '\t\t(property "Value" "%s" (at %s %s 0) (effects (font (size 1.27 1.27))%s))\n'
         '\t\t(property "Footprint" "" (at %s %s 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
         % (libid, sx, sy, U(), ref, sx, round(sy + ref_dy, 2), val, sx, round(sy - ref_dy, 2), valhide, sx, sy))
    s += pins
    s += ('\t\t(instances (project "" (path "/%s" (reference "%s") (unit 1))))\n\t)\n' % (ROOT, ref))
    parts.append(s)

def label(net, x, y, just):
    labels.append('\t(label "%s" (at %s %s 0) (effects (font (size 1.27 1.27)) (justify %s)) (uuid "%s"))\n'
                  % (net, round(x, 2), round(y, 2), just, U()))

def text(t, x, y, size=2.0):
    texts.append('\t(text "%s" (at %s %s 0) (effects (font (size %s %s)) (justify left)) (uuid "%s"))\n'
                 % (t, x, y, size, size, U()))

TX, TY = 50.8, 101.6
place("EmiuetBench:Teensy4_1_Bench", "U1", "Teensy 4.1 (bench header)", TX, TY,
      [p[0] for p in left] + [p[0] for p in right], show_val=True, ref_dy=-23.0)
net_for_left = {"3V3": "+3V3", "24": "KEY_ROW0", "25": "KEY_ROW1", "26": "KEY_ROW2", "27": "KEY_ROW3",
                "28": "KEY_COL0", "29": "KEY_COL1", "30": "KEY_COL2", "31": "KEY_COL3",
                "36": "ENC_A", "37": "ENC_B", "38": "ENC_SW", "GND": "GND"}
net_for_right = {"18": "OLED_SDA", "19": "OLED_SCL", "13": "LCD_SCK", "11": "LCD_MOSI", "10": "LCD_CS",
                 "32": "LCD_RES", "33": "LCD_DC", "34": "LCD_BLK", "0": "MIDI_RX1_RSVD", "1": "MIDI_TX1_RSVD"}
for num, name, py, et in left:
    label(net_for_left[num], TX - 20.32, TY - py, "right")
for num, name, py, et in right:
    label(net_for_right[num], TX + 20.32, TY - py, "left")

COL_X0, COL_DX = 116.84, 45.72
ROW_Y0, ROW_DY = 71.12, 20.32
for r in range(4):
    for c in range(4):
        swx = COL_X0 + c * COL_DX; swy = ROW_Y0 + r * ROW_DY
        dx = swx + 8.89; dy = swy
        place("Switch:SW_Push", "SW_R%dC%d" % (r, c), "SW_Push", swx, swy, ["1", "2"])
        place("Device:D", "D_R%dC%d" % (r, c), "1N4148", dx, dy, ["1", "2"])
        label("KEY_ROW%d" % r, swx - 5.08, swy, "right")
        label("KEY_COL%d" % c, dx + 3.81, dy, "left")

EX, EY = 50.8, 165.1
place("Connector_Generic:Conn_01x05", "J_ENC", "EC11 encoder", EX, EY, ["1", "2", "3", "4", "5"])
for num, net, py in [("1", "ENC_A", 5.08), ("2", "GND", 2.54), ("3", "ENC_B", 0.0),
                     ("4", "ENC_SW", -2.54), ("5", "GND", -5.08)]:
    label(net, EX - 5.08, EY - py, "right")

OX, OY = 119.38, 165.1
place("Connector_Generic:Conn_01x04", "J_OLED", "I2C OLED", OX, OY, ["1", "2", "3", "4"])
for num, net, py in [("1", "GND", 2.54), ("2", "+3V3", 0.0), ("3", "OLED_SCL", -2.54), ("4", "OLED_SDA", -5.08)]:
    label(net, OX - 5.08, OY - py, "right")

LX, LY = 190.5, 167.64
place("Connector_Generic:Conn_01x08", "J_LCD", "SPI LCD", LX, LY, ["1", "2", "3", "4", "5", "6", "7", "8"])
for num, net, py in [("1", "GND", 7.62), ("2", "+3V3", 5.08), ("3", "LCD_SCK", 2.54), ("4", "LCD_MOSI", 0.0),
                     ("5", "LCD_RES", -2.54), ("6", "LCD_DC", -5.08), ("7", "LCD_CS", -7.62), ("8", "LCD_BLK", -10.16)]:
    label(net, LX - 5.08, LY - py, "right")

text("Emiuet Session Bench - Phase A hand-wiring reference (NOT a production PCB)", 110.0, 18.0, 2.2)
text("Scan: columns INPUT_PULLUP, rows driven LOW one at a time; pressed key reads LOW on its column.", 110.0, 28.0, 1.6)
text("Diode orientation: ANODE -> COLUMN, CATHODE -> ROW.  *** CONFIRM diode orientation before soldering the 16-key board ***", 110.0, 34.0, 1.6)
text("All logic 3.3V. Teensy 4.1 GPIO is NOT 5V tolerant. Do NOT connect 5V to Teensy GPIO. Verify OLED/LCD module VCC = 3.3V.", 110.0, 40.0, 1.6)
text("Pins 0/1 (Serial1 RX1/TX1) reserved for Phase B TRS MIDI. No MIDI jack/optocoupler/transistor/circuit in this schematic.", 110.0, 46.0, 1.6)
text("Display options: I2C OLED and SPI LCD are alternatives - populate only one. Connector pin order varies by module: verify.", 110.0, 52.0, 1.6)
text("Key matrix: rows = Teensy 24-27, columns = Teensy 28-31. Nets KEY_ROW0..3 / KEY_COL0..3.", 110.0, 142.0, 1.6)
text("Encoder: A=36 B=37 PUSH=38.  I2C OLED: SDA=18 SCL=19.  SPI LCD: SCK=13 MOSI=11 CS=10 RES=32 DC=33 BLK=34.", 110.0, 148.0, 1.6)

out = ['(kicad_sch\n\t(version 20250114)\n\t(generator "emiuet-bench-gen")\n\t(generator_version "1.0")\n']
out.append('\t(uuid "%s")\n\t(paper "A4")\n' % ROOT)
out.append('\t(lib_symbols\n')
out.append(teensy_sym)
for b in lib_blocks:
    for line in b.splitlines():
        out.append('\t\t' + line + '\n')
out.append('\t)\n')
out.extend(labels)
out.extend(texts)
out.extend(parts)
out.append('\t(sheet_instances\n\t\t(path "/" (page "1"))\n\t)\n')
out.append('\t(embedded_fonts no)\n)\n')
sch = "".join(out)
open(os.path.join(OUTDIR, NAME + ".kicad_sch"), "w", encoding="utf-8").write(sch)

pro = {
    "board": {"design_settings": {"defaults": {}}, "layer_presets": [], "viewports": []},
    "boards": [],
    "cvpcb": {"equivalence_files": []},
    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    "meta": {"filename": NAME + ".kicad_pro", "version": 3},
    "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.2,
        "via_diameter": 0.6, "via_drill": 0.3, "wire_width": 6, "bus_width": 12, "line_style": 0,
        "diff_pair_gap": 0.25, "diff_pair_width": 0.2, "diff_pair_via_gap": 0.25,
        "microvia_diameter": 0.3, "microvia_drill": 0.1, "priority": -1,
        "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}],
        "meta": {"version": 4}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": []},
    "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
    "schematic": {"drawing": {}, "meta": {"version": 1}, "legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [[ROOT, "Root"]],
    "text_variables": {},
}
open(os.path.join(OUTDIR, NAME + ".kicad_pro"), "w", encoding="utf-8").write(json.dumps(pro, indent=2))
print("ROOT_UUID:", ROOT)
print("sch bytes:", len(sch))
print("counts: parts=%d labels=%d texts=%d" % (len(parts), len(labels), len(texts)))
