import json
import math
from build123d import (
    Align,
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    RegularPolygon,
    Rot,
    Vector,
    export_step,
    export_stl,
    extrude,
    revolve,
)

with open("parameter_lock.json", "r", encoding="utf-8") as f:
    LOCK = json.load(f)

C = LOCK["computed"]
INP = LOCK["inputs"]

CORE_DIA = C["core_diameter_m"] * 1000.0
CORE_H = C["core_height_m"] * 1000.0
BERM_T = INP["berm_thickness_m"] * 1000.0
RAD_FINS = INP["radial_fin_count"]
CONC_RINGS = INP["concentric_ring_count"]

DECK_DIA = 4200.0
DECK_H = 220.0
TPV_OD = 1860.0
TPV_ID = 1120.0
TPV_H = 1150.0
APERTURE_D = 480.0

RAD_WINGS = 4
RAD_L = C["radiator_wing_length_m"] * 1000.0
RAD_H = 2000.0
MAST_H = INP["mast_height_m"] * 1000.0
DISH_D = C["dish_diameter_m"] * 1000.0
DISH_F = DISH_D * 0.45


def make_strut(p1, p2, radius):
    v1, v2 = Vector(*p1), Vector(*p2)
    diff = v2 - v1
    length = diff.length
    if length < 1e-3:
        return None
    plane = Plane(origin=v1, z_dir=diff.normalized())
    return plane * Cylinder(radius=radius, height=length, align=(Align.CENTER, Align.CENTER, Align.MIN))


def build_regolith_and_berm():
    r_out = CORE_DIA / 2.0 + BERM_T
    berm = Cylinder(radius=r_out, height=CORE_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cav = Pos(0, 0, -50) * Cylinder(radius=CORE_DIA / 2.0, height=CORE_H + 100, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cut_q = Pos(0, 0, -50) * Box(r_out + 300, r_out + 300, CORE_H + 100, align=(Align.MIN, Align.MIN, Align.MIN))
    berm_cut = berm - cav - cut_q

    core = Cylinder(radius=CORE_DIA / 2.0 - 18.0, height=CORE_H, align=(Align.CENTER, Align.CENTER, Align.MIN)) - cut_q
    berm_cut.label = "01_AboveGrade_Regolith_Berm"
    berm_cut.color = Color(0.45, 0.45, 0.48, 0.65)
    core.label = "02_Sintered_Regolith_Core_1660K"
    core.color = Color(0.90, 0.30, 0.08, 1.0)
    return berm_cut, core


def build_32fin_concentric_matrix():
    parts = [
        Cylinder(radius=APERTURE_D / 2.0 + 95.0, height=CORE_H + TPV_H + DECK_H + 180.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Pos(0, 0, -10) * Cylinder(radius=APERTURE_D / 2.0, height=CORE_H + TPV_H + DECK_H + 200.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ]
    fin_len = CORE_DIA / 2.0 - 160.0
    for i in range(RAD_FINS):
        ang = i * (360.0 / RAD_FINS)
        fin = (
            Rot(0, 0, ang)
            * Pos(fin_len / 2.0 + APERTURE_D / 2.0, 0, 100.0)
            * Box(fin_len, 20.0, CORE_H - 200.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        )
        parts.append(fin)

    for idx in range(1, CONC_RINGS + 1):
        r_ring = (CORE_DIA / 2.0) * (idx / (CONC_RINGS + 0.6))
        ring = (
            Pos(0, 0, 140.0) * Cylinder(radius=r_ring + 18.0, height=CORE_H - 280.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
            - Pos(0, 0, 130.0) * Cylinder(radius=r_ring, height=CORE_H - 260.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        )
        parts.append(ring)

    comp = Compound(label="03_SiC_32Fin_3Ring_Matrix", children=parts)
    comp.color = Color(0.20, 0.20, 0.22, 1.0)
    return comp


def build_tpv_and_1dof_sleeve():
    z0 = CORE_H + DECK_H
    # 1-DOF Cold-Side Translating Molybdenum Radiation Shield Sleeve (zero hot bearings)
    sleeve = (
        Pos(0, 0, z0 + 260.0) * Cylinder(radius=(TPV_ID / 2.0) - 25.0, height=TPV_H * 0.62, align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Pos(0, 0, z0 + 250.0) * Cylinder(radius=(TPV_ID / 2.0) - 48.0, height=TPV_H * 0.62 + 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    # 3 cold-side linear flexure actuator rods at 300 K
    actuator_parts = [sleeve]
    for a in (0.0, 120.0, 240.0):
        rx = ((TPV_ID / 2.0) - 36.0) * math.cos(math.radians(a))
        ry = ((TPV_ID / 2.0) - 36.0) * math.sin(math.radians(a))
        actuator_parts.append(make_strut((rx, ry, z0 - 120.0), (rx, ry, z0 + 300.0), 16.0))

    sleeve_comp = Compound(label="06_Molybdenum_1DOF_ColdSide_Sleeve", children=actuator_parts)
    sleeve_comp.color = Color(0.82, 0.84, 0.88, 1.0)

    tpv_ring = (
        Pos(0, 0, z0) * Cylinder(radius=TPV_OD / 2.0, height=TPV_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Pos(0, 0, z0 - 10) * Cylinder(radius=TPV_ID / 2.0, height=TPV_H + 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    tpv_ring.label = "07_InGaAs_GaSb_Selective_TPV_Ring"
    tpv_ring.color = Color(0.14, 0.36, 0.68, 1.0)
    return tpv_ring, sleeve_comp


def build_lander_pmad_and_tethered_rover():
    z_deck = CORE_H
    deck_parts = [Pos(0, 0, z_deck) * extrude(RegularPolygon(radius=DECK_DIA / 2.0, side_count=8), amount=DECK_H)]
    for i in range(4):
        ang = 45.0 + i * 90.0
        r_pad = DECK_DIA / 2.0 + 480.0
        px, py = r_pad * math.cos(math.radians(ang)), r_pad * math.sin(math.radians(ang))
        deck_parts.append(make_strut((px * 0.72, py * 0.72, z_deck + 80.0), (px, py, z_deck - 260.0), 65.0))
        deck_parts.append(Pos(px, py, z_deck - 310.0) * Cylinder(radius=380.0, height=75.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))

    # ISPSIS 120 VDC SiC Boost Converter + 4.0 kWh Solid-State Keep-Alive Battery Enclosure
    deck_parts.append(Pos(-1450.0, 950.0, z_deck + DECK_H) * Box(780.0, 540.0, 420.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))

    deck_comp = Compound(label="04_Octagonal_Deck_ISPSIS_120VDC_PMAD", children=deck_parts)
    deck_comp.color = Color(0.78, 0.65, 0.25, 1.0)

    # 110 kg Tethered ISRU Mini-Dozer Rover + Power/Data Tether
    rx, ry, rz = 4600.0, 2600.0, 0.0
    rover_parts = [
        Pos(rx, ry, rz + 180.0) * Box(1150.0, 820.0, 340.0, align=(Align.CENTER, Align.CENTER, Align.MIN)),
        Pos(rx + 680.0, ry, rz + 40.0) * Box(240.0, 980.0, 380.0, align=(Align.CENTER, Align.CENTER, Align.MIN)),
        Pos(rx, ry + 480.0, rz + 180.0) * Rot(90, 0, 0) * Cylinder(radius=180.0, height=160.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        Pos(rx, ry - 480.0, rz + 180.0) * Rot(90, 0, 0) * Cylinder(radius=180.0, height=160.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        make_strut((DECK_DIA / 2.0, 600.0, z_deck + 100.0), (rx - 400.0, ry, rz + 320.0), 14.0),
    ]
    rover_comp = Compound(label="05_Tethered_ISRU_MiniDozer_Rover_110kg", children=rover_parts)
    rover_comp.color = Color(0.92, 0.58, 0.12, 1.0)
    return deck_comp, rover_comp


def build_vchp_radiators():
    z_base = CORE_H + DECK_H + 220.0
    wings = []
    for i in range(RAD_WINGS):
        ang = i * 90.0
        r_start = TPV_OD / 2.0 + 550.0
        panel = Pos(r_start + RAD_L / 2.0, 0, z_base) * Box(RAD_L, 42.0, RAD_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
        wings.append(Rot(0, 0, ang) * panel)
        for zb in (z_base + 140.0, z_base + RAD_H - 140.0):
            hdr = Pos(TPV_OD / 2.0 + (550.0 + RAD_L) / 2.0, 0, zb) * Box(550.0 + RAD_L, 95.0, 95.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
            wings.append(Rot(0, 0, ang) * hdr)
        for j in range(1, 7):
            rx = r_start + j * (RAD_L / 7.0)
            rib = Pos(rx, 0, z_base) * Box(55.0, 88.0, RAD_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
            wings.append(Rot(0, 0, ang) * rib)

    rad_comp = Compound(label="08_VCHP_Z93_Radiator_Wings", children=wings)
    rad_comp.color = Color(0.95, 0.96, 0.98, 1.0)
    return rad_comp


def build_mast_tower_and_heliostat():
    z0 = CORE_H + DECK_H + TPV_H
    z_top = z0 + MAST_H
    bays = 12
    bh = MAST_H / bays
    verts = [(540.0 * math.cos(math.radians(a)), 540.0 * math.sin(math.radians(a))) for a in (0.0, 120.0, 240.0)]

    mast_parts = [make_strut((vx, vy, z0), (vx, vy, z_top), 28.0) for vx, vy in verts]
    for b in range(bays + 1):
        zb = z0 + b * bh
        for i in range(3):
            p1, p2 = (verts[i][0], verts[i][1], zb), (verts[(i + 1) % 3][0], verts[(i + 1) % 3][1], zb)
            mast_parts.append(make_strut(p1, p2, 16.0))
            if b < bays:
                p3 = (verts[(i + 1) % 3][0], verts[(i + 1) % 3][1], zb + bh)
                mast_parts.append(make_strut(p1, p3, 13.0))

    # 3 Tensioned Zylon Guy-Wires stabilizing the 12m mast against thermal bending
    for a in (45.0, 165.0, 285.0):
        ax = (DECK_DIA / 2.0 + 380.0) * math.cos(math.radians(a))
        ay = (DECK_DIA / 2.0 + 380.0) * math.sin(math.radians(a))
        tx = 540.0 * math.cos(math.radians(a))
        ty = 540.0 * math.sin(math.radians(a))
        mast_parts.append(make_strut((ax, ay, CORE_H + DECK_H), (tx, ty, z_top - 400.0), 9.0))

    mast_parts.append(Pos(0, 0, z_top) * Cylinder(radius=760.0, height=140.0, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    mast_comp = Compound(label="09_VSAT_12m_Mast_Zylon_GuyWires", children=mast_parts)
    mast_comp.color = Color(0.26, 0.26, 0.30, 1.0)

    pv_parts = [
        Pos(-1150.0, 0.0, z_top - 2300.0) * Box(28.0, 8800.0, 3900.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)),
        make_strut((-540.0, 0.0, z_top - 2300.0), (-1150.0, 0.0, z_top - 2300.0), 65.0),
    ]
    pv_comp = Compound(label="10_ROSA_12kWe_Daytime_PV_Wing", children=pv_parts)
    pv_comp.color = Color(0.08, 0.18, 0.46, 1.0)

    r_max = DISH_D / 2.0
    front = [(r_max * (i / 28.0), 0.0, ((r_max * (i / 28.0)) ** 2) / (4.0 * DISH_F)) for i in range(29)]
    back = [(r, 0.0, z - 55.0) for r, _, z in reversed(front)]
    profile = Plane.XZ * Polygon(front + back, align=None)
    dish_solid = revolve(profile, axis=Axis.Z, revolution_arc=360.0)
    dish_placed = Pos(5800.0, 0.0, CORE_H + 2100.0) * Rot(0, -44.0, 0) * dish_solid
    yoke = make_strut((5800.0, 0.0, CORE_H), (5800.0, 0.0, CORE_H + 1950.0), 140.0)

    dish_comp = Compound(label="11_Heliostat_Gimbal_QuadSensor", children=[dish_placed, yoke])
    dish_comp.color = Color(0.88, 0.90, 0.94, 1.0)
    return mast_comp, pv_comp, dish_comp


def build_assembly():
    berm, core = build_regolith_and_berm()
    matrix = build_32fin_concentric_matrix()
    tpv, sleeve = build_tpv_and_1dof_sleeve()
    deck, rover = build_lander_pmad_and_tethered_rover()
    rads = build_vchp_radiators()
    mast, pv, dish = build_mast_tower_and_heliostat()

    assy = Compound(
        label="HELIOS_R3_Aerospace_Assembly",
        children=[berm, core, matrix, deck, rover, sleeve, tpv, rads, mast, pv, dish],
    )
    export_step(assy, "HELIOS_R3_Aerospace_Assembly.step")
    export_stl(assy, "HELIOS_R3_Aerospace_Assembly.stl", tolerance=0.45)
    print(f"HELIOS-R3 CAD Build Complete: HELIOS_R3_Aerospace_Assembly.step & .stl (Lock v{LOCK['version']})")


if __name__ == "__main__":
    build_assembly()
