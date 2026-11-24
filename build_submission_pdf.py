import json
import os
import sys
import matplotlib
from fpdf import FPDF

TEAM_ID = sys.argv[1] if len(sys.argv) > 1 else "TEAM-ID-PENDING"

with open("parameter_lock.json", "r", encoding="utf-8") as f:
    LOCK = json.load(f)

C = LOCK["computed"]
INP = LOCK["inputs"]

FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data", "fonts", "ttf")


class SubmissionPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="Letter")
        self.add_font("DejaVu", "", os.path.join(FONT_DIR, "DejaVuSans.ttf"))
        self.add_font("DejaVu", "B", os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf"))
        self.set_margins(20, 18, 20)
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if self.page_no() == 1 or self.cur_orientation == "L":
            return
        self.set_font("DejaVu", "", 8.2)
        self.set_text_color(100, 116, 139)
        self.cell(self.epw * 0.65, 5, f"Track 1: Power Generation & Storage | HELIOS-R3 ({TEAM_ID})")
        self.cell(self.epw * 0.35, 5, f"Concept Paper Page {self.page_no() - 1}", align="R")
        self.ln(6)
        self.set_draw_color(203, 213, 225)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3.5)

    def footer(self):
        if self.page_no() == 1 or self.cur_orientation == "L":
            return
        self.set_y(-13)
        self.set_font("DejaVu", "", 7.8)
        self.set_text_color(148, 163, 184)
        self.cell(self.epw, 5, "HELIOS-R3 Lunar South Pole Architecture — Anonymized Phase 1 Submission", align="C")

    def section_heading(self, title: str):
        if self.get_y() > self.h - 38:
            self.add_page()
        self.ln(2.5)
        self.set_font("DejaVu", "B", 11.8)
        self.set_text_color(15, 23, 42)
        self.multi_cell(self.epw, 6.2, title)
        self.set_draw_color(2, 132, 199)
        self.set_line_width(0.55)
        self.line(self.l_margin, self.get_y() + 0.5, self.l_margin + 38, self.get_y() + 0.5)
        self.set_line_width(0.2)
        self.ln(3.0)

    def body_para(self, text: str):
        self.set_font("DejaVu", "", 10.0)
        self.set_text_color(30, 41, 59)
        self.multi_cell(self.epw, 5.2, text)
        self.ln(2.2)

    def bullet_item(self, lead: str, text: str):
        clean_lead = lead.rstrip(":")
        self.set_font("DejaVu", "B", 9.8)
        self.set_text_color(15, 23, 42)
        self.set_x(self.l_margin + 3.0)
        self.write(5.0, f"• {clean_lead}: ")
        self.set_font("DejaVu", "", 9.8)
        self.set_text_color(30, 41, 59)
        self.multi_cell(self.epw - 3.0, 5.0, text)
        self.ln(1.4)


def draw_table(pdf: SubmissionPDF, headers, rows, widths, font_size=8.0):
    def render_header():
        pdf.set_font("DejaVu", "B", font_size)
        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        h_head = 6.8
        for col, w in zip(headers, widths):
            pdf.cell(w, h_head, col, border=1, align="L", fill=True)
        pdf.ln(h_head)

    if pdf.get_y() + 20 > pdf.h - pdf.b_margin:
        pdf.add_page()
    render_header()

    for idx, row in enumerate(rows):
        if pdf.get_y() + 12 > pdf.h - pdf.b_margin:
            pdf.add_page()
            render_header()

        is_total = (idx == len(rows) - 1) and ("TOTAL" in row[0] or "HELIOS-R3" in row[0])
        pdf.set_fill_color(224, 242, 254) if is_total else (
            pdf.set_fill_color(248, 250, 252) if idx % 2 == 1 else pdf.set_fill_color(255, 255, 255)
        )
        pdf.set_text_color(15, 23, 42) if is_total else pdf.set_text_color(30, 41, 59)
        pdf.set_font("DejaVu", "B" if is_total else "", font_size)

        pdf.set_auto_page_break(auto=False)
        y_start = pdf.get_y()
        x_curr = pdf.l_margin
        max_y = y_start

        for val, w in zip(row, widths):
            pdf.set_xy(x_curr + 1.2, y_start + 1.0)
            pdf.multi_cell(w - 2.4, 4.4, val, border=0, align="L")
            max_y = max(max_y, pdf.get_y())
            x_curr += w

        row_h = max(max_y - y_start + 1.1, 6.2)
        x_curr = pdf.l_margin
        pdf.set_draw_color(203, 213, 225)
        for val, w in zip(row, widths):
            pdf.rect(x_curr, y_start, w, row_h, style="DF")
            pdf.set_xy(x_curr + 1.2, y_start + 1.0)
            pdf.multi_cell(w - 2.4, 4.4, val, border=0, align="L")
            x_curr += w

        pdf.set_auto_page_break(auto=True, margin=18)
        pdf.set_xy(pdf.l_margin, y_start + row_h)

    pdf.ln(2.2)


def build_pdf():
    pdf = SubmissionPDF()

    # ==========================================================================
    # PAGE 1: COVER PAGE (EXCLUDED FROM 5-7 PAGE COUNT)
    # ==========================================================================
    pdf.add_page()
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, pdf.w, 68, style="F")

    pdf.set_xy(20, 18)
    pdf.set_font("DejaVu", "B", 9.8)
    pdf.set_text_color(56, 189, 248)
    pdf.cell(pdf.epw, 6, "PHASE 1 CONCEPT OVERVIEW SUBMISSION  |  TRACK 1: POWER GENERATION & STORAGE")

    pdf.set_xy(20, 28)
    pdf.set_font("DejaVu", "B", 23)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pdf.epw, 10, "HELIOS-R3")

    pdf.set_xy(20, 41)
    pdf.set_font("DejaVu", "", 11.2)
    pdf.set_text_color(226, 232, 240)
    pdf.multi_cell(pdf.epw, 6.0, "Hybrid Elevated Lunar In-Situ Optical-Thermal Storage & Selective Thermophotovoltaic Power Station (10 kWe Continuous Baseload)")

    pdf.set_fill_color(248, 250, 252)
    pdf.set_draw_color(203, 213, 225)
    pdf.rect(20, 80, pdf.epw, 44, style="DF")

    meta_rows = [
        ("Team ID Number:", TEAM_ID),
        ("Technical Track:", "Track 1 — Power Generation & Storage"),
        ("Target Environment:", "Lunar South Pole (85°S–90°S, 354-Hour Lunar Night, -170°C to +120°C)"),
        ("Architecture Class:", "100% Solid-State TPV + In-Situ Sintered Regolith Thermal Energy Storage"),
    ]
    y_m = 84
    for k, v in meta_rows:
        pdf.set_xy(25, y_m)
        pdf.set_font("DejaVu", "B", 9.8)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(46, 7, k)
        pdf.set_font("DejaVu", "", 9.8)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(pdf.epw - 54, 7, v)
        y_m += 9.2

    pdf.set_xy(20, 136)
    pdf.set_font("DejaVu", "B", 11.5)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(pdf.epw, 7, "Key Performance & Compliance Highlights")
    pdf.ln(10)

    kpis = [
        ("Continuous Output", f"{INP['net_power_kwe']:.1f} kWe (24/7) on 120 VDC ISPSIS microgrid bus; 12.0 kWe daytime peak"),
        ("Earth-Launched Mass", f"{int(C['earth_launched_mass_kg']):,} kg ({C['specific_mass_kg_kwe']} kg/kWe) — 15.9x lighter than Li-ion batteries"),
        ("In-Situ Thermal Core", f"{C['regolith_mass_kg']:,.0f} kg sintered lunar regolith ({C['core_diameter_m']} m D x {C['core_height_m']} m H) @ 1,660 K"),
        ("Thermal Diffusion & Retention", f"{C['diffusion_time_hr']} hr conductive diffusion via 32-fin SiC matrix; {C['thermal_retention_pct']}% retention"),
        ("Safety & Autonomy", "Zero pressurized vessels, zero hazardous chemicals, 1-DOF cold-side sleeve, 0.20 s optical abort"),
    ]
    for k, v in kpis:
        pdf.bullet_item(k, v)

    # ==========================================================================
    # CONCEPT OVERVIEW PAPER (5-7 PAGES STRICTLY ENFORCED)
    # ==========================================================================
    pdf.add_page()

    pdf.section_heading("1. Executive Summary & Category Selection")
    pdf.body_para(
        "Uninterrupted electrical power across the 354-hour (~14.8 Earth-day) lunar night is the primary engineering bottleneck "
        "preventing permanent human habitation near the Moon's South Pole. Submitted under Track 1: Power Generation & Storage, "
        f"HELIOS-R3 is a fully autonomous, {int(C['earth_launched_mass_kg']):,} kg Earth-launched power station engineered to deliver "
        f"{INP['net_power_kwe']:.1f} kWe continuous (24/7) baseload power (12.0 kWe daytime peak) on a standard 120 VDC International Space "
        "Power System Interoperability Standard (ISPSIS) microgrid without pressurized vessels, hazardous chemicals, or human intervention."
    )
    pdf.body_para(
        "Conventional electrochemical and fuel-cell architectures fail mass or safety thresholds over a 354-hour eclipse. "
        "Delivering 10.0 kWe for 354 hours requires 3,540 kWh (12.744 GJ). At 150 Wh/kg system-level specific energy, secondary "
        "lithium-ion batteries require 23,600 kg (23.6 metric tons) of launched mass. Regenerative Fuel Cells (RFCs) require "
        "high-pressure H2/O2 storage tanks (20–35 MPa) and multi-stage electrolyzer pumps that violate competition constraints "
        "prohibiting pressurized vessels and introduce cryogenic/mechanical failure points."
    )
    pdf.body_para(
        f"HELIOS-R3 eliminates both penalties by storing thermal energy in {C['regolith_mass_kg']:,.0f} kg of sintered in-situ lunar regolith "
        "heated to 1,660 K by concentrated polar sunlight during the lunar day, and converting stored infrared energy into electricity "
        f"at night via solid-state InGaAs/GaSb Thermophotovoltaic (TPV) cells paired with a W/HfO2 photonic selective emitter "
        f"({INP['tpv_cell_efficiency']*100:.1f}% cell efficiency; {C['net_tpv_pmad_efficiency_pct']}% net bus efficiency after "
        f"{INP['sic_pmad_efficiency']*100:.1f}% SiC DC-DC conversion). By utilizing local lunar soil for 97.4% of total system mass, "
        f"HELIOS-R3 cuts Earth-launched mass by 15.9x compared to batteries ({C['specific_mass_kg_kwe']} kg/kWe specific mass)."
    )

    pdf.section_heading("2. Background of the Problem & Lunar South Pole Constraints")
    pdf.bullet_item(
        "Horizon-Grazing Solar Geometry",
        "Because the Moon's rotational axis is tilted only 1.54° to the ecliptic, sunlight skims the South Pole horizon at "
        "0°–5° elevation, causing severe terrain shadowing on ground-level solar collectors and requiring elevated optical apertures."
    )
    pdf.bullet_item(
        "Hard Vacuum & Radiative-Only Heat Rejection",
        "At 10^-12 torr ambient pressure, convective cooling is zero. Every watt of unrecovered conversion heat must be rejected "
        "to deep space solely via Stefan-Boltzmann thermal radiation without excessive radiator mass."
    )
    pdf.bullet_item(
        "Extreme Thermal Swings & Regolith Phase Change",
        "Surface temperatures swing from +120°C (393 K) in direct sun to -170°C (103 K) during lunar night and -203°C (70 K) "
        "inside Permanently Shadowed Regions (PSRs), inducing severe thermal-cycling fatigue in exposed structural joints."
    )
    pdf.bullet_item(
        "Electrostatically Levitated Abrasive Dust",
        "Solar UV and plasma charging levitate jagged 4–250 µm regolith grains that degrade mirror reflectance, coat radiators, "
        "and induce high-voltage electrostatic arcing on ungrounded hardware."
    )
    pdf.bullet_item(
        "Vacuum Cold-Welding of High-Temperature Bearings",
        "Unlubricated rotary bearings exposed to >1,000 K in hard vacuum experience atomic diffusion bonding (cold-welding) and dust seizure, "
        "making multi-blade high-temperature louvers unsuitable for 10-year autonomous missions."
    )

    pdf.section_heading("3. Proposed Solution: HELIOS-R3 System Architecture")
    pdf.body_para(
        "HELIOS-R3 integrates six tightly coupled subsystems packaged within a single 4.20 m launch fairing:"
    )
    pdf.bullet_item(
        "1. Windowless Solar-Tower Optical Concentrator (12.0 m VSAT Mast + 6.485 m Heliostat)",
        f"A ground-level {C['dish_diameter_m']} m parabolic primary heliostat on a 2-axis gimbal tracks the low-angle polar Sun and "
        "reflects sunlight upward to a 1.52 m hyperbolic relay mirror mounted atop a 12.0 m triangulated composite VSAT truss mast "
        "(clearing crater rims and dust saltation). The relay directs a focused beam downward into an open-aperture 480 mm blackbody "
        "cavity, eliminating dust-prone quartz windows. Three tensioned Zylon guy-wires prevent thermal mast bending, while an "
        f"aperture-collar quadrant photodiode sensor commands an off-sun abort slew within {INP['beam_abort_response_s']:.2f} s if drift exceeds 25 mm."
    )
    pdf.bullet_item(
        "2. Above-Grade Sintered Regolith Core & 110 kg Tethered ISRU Mini-Dozer Rover",
        f"Instead of excavating dense subsurface rock in 1/6g, HELIOS-R3 deploys an above-grade woven-basalt containment cylinder "
        f"({C['core_diameter_m']} m D x {C['core_height_m']} m H) around its pre-deployed heat-exchanger matrix. A 110 kg tethered "
        "autonomous mini-dozer rover grades loose surface regolith into the cylinder and banks an external 1.50 m thick loose "
        "regolith insulation berm (~180 metric tons in-situ), while the concentrator sinters the core in 5 cm layers (2,600 kg/m³)."
    )
    pdf.bullet_item(
        "3. 32-Fin + 3-Concentric-Ring SiC Thermal Extraction Matrix",
        "Sintered regolith exhibits low thermal conductivity (k_eff = 0.15 W/m·K). Embedding 32 radial Silicon Carbide (SiC) fins "
        "joined by 3 concentric thermal-equalization rings limits maximum conductive path length to 7.53 cm, eliminating thermal "
        "bottlenecks during both daytime sintering and nighttime extraction."
    )
    pdf.bullet_item(
        "4. Photonic Selective Emitter & 1-DOF Cold-Side Translating Molybdenum Sleeve",
        "The central SiC emitter cylinder (1,660 K peak) is coated with a 1D tungsten/hafnia (W/HfO2) photonic crystal that "
        "suppresses sub-bandgap infrared emission and reflects unused photons back into the core, achieving 34.0% TPV cell efficiency. "
        "To hold electrical output constant at 10.0 kWe as the core cools from 1,660 K to 1,250 K without hot rotary hinges, a single "
        "cold-side (300 K) linear flexure actuator vertically translates a reflective molybdenum sleeve (24% open at 1,660 K to 86% at 1,250 K)."
    )
    pdf.bullet_item(
        "5. Four Double-Sided VCHP Z-93 Radiator Wings (65.17 m² Total Area)",
        f"Waste heat (20.17 kW_th) from the 300 K TPV cold plate is rejected by four {C['radiator_wing_length_m']} m x 2.00 m "
        "double-sided carbon-carbon radiator wings coated with Z-93 white thermal paint (emissivity 0.90), oriented edge-on to "
        "the polar horizon and isolated by Variable-Conductance Heat Pipes (VCHPs)."
    )
    pdf.bullet_item(
        "6. ISPSIS 120 VDC PMAD, Daytime ROSA PV Wing & Electrodynamic Dust Shield (EDS)",
        "During the 354-hour lunar day, a mast-mounted 12.0 kWe Roll-Out Solar Array (ROSA, 34.3 m²) supplies base loads directly "
        "while 100% of heliostat flux recharges the thermal core. A radiation-hardened SiC interleaved boost converter (97.5% eff.) "
        "regulates power onto NASA's 120 VDC ISPSIS bus alongside a 4.0 kWh solid-state keep-alive battery. Transparent ITO EDS grids "
        "pulsed at 1.2 kV, 10 Hz continuously clear dust from optical and PV surfaces."
    )

    pdf.section_heading("4. Solution Viability: First-Principles Physics & Trade Verification")
    pdf.body_para(
        "1. Nighttime Energy & Regolith Core Mass Sizing: Delivering 10.0 kWe for 354 hours requires E_elec = 12.744 GJ (3,540 kWh). "
        f"With net conversion efficiency eta_net = 0.340 x 0.975 = {C['net_tpv_pmad_efficiency_pct']}% and 94.0% thermal retention, "
        f"required gross thermal storage is E_th,gross = 12.744 GJ / (0.3315 x 0.94) = {C['e_th_gross_gj']} GJ. Operating between "
        "T_max = 1,660 K and T_min = 1,250 K (Delta_T = 410 K) across the regolith melting plateau (1,435 K, latent heat "
        "L_f = 161.2 kJ/kg, c_p = 1,400 J/kg·K) yields specific storage capacity e_reg = (1,400 x 410) + 161,200 = 735.2 kJ/kg. "
        f"Required regolith mass is m_reg = 40.90 GJ / 735.2 kJ/kg = {C['regolith_mass_kg']:,.0f} kg (21.40 m³ at 2,600 kg/m³). "
        f"A {C['core_diameter_m']} m D x {C['core_height_m']} m H cylinder holds 22.70 m³ (59,020 kg, +6.1% thermal margin)."
    )
    pdf.body_para(
        "2. Conductive Berm Insulation & 32-Fin Diffusion Proof: Across core surface area A_core = 44.38 m² and a 1.50 m loose "
        "regolith berm (k_berm = 0.045 W/m·K, T_mean = 1,455 K, T_amb = 150 K), conductive heat loss is Q_cond = "
        "(0.045 x 44.38 x 1,305) / 1.50 = 1.74 kW_th (2.21 GJ over 354 hr, or 5.41% of stored energy), achieving "
        f"{C['thermal_retention_pct']}% thermal retention. Inside the core (thermal diffusivity alpha = 4.12 x 10^-8 m²/s), "
        "32 radial fins enforce a half-pitch L_c = 7.53 cm, giving characteristic diffusion time tau_diff = L_c² / alpha = "
        f"{C['diffusion_time_hr']} hours (an 82x speedup over an 8-fin core at 3,130 hr), guaranteeing full heat extraction."
    )
    pdf.body_para(
        "3. Heliostat Concentrator & Vacuum Radiator Sizing: Recharging 40.90 GJ in 354 hr with an 18% margin requires "
        "Q_in = 37.87 kW_th. At I_sun = 1,365 W/m² and optical efficiency 84%, required aperture area is 33.03 m² "
        f"(D_dish = {C['dish_diameter_m']} m). At night, rejecting Q_rej = 10.0 kWe x (1/0.3315 - 1) = 20.17 kW_th at "
        "T_rad = 300 K against T_sink = 180 K (emissivity 0.90, fin efficiency 0.86) requires A_rad = 20,166 / 309.43 = "
        f"{C['radiator_total_area_m2']} m² across four double-sided radiator wings."
    )

    trade_headers = ["Architecture Candidate", "Launched Mass", "Pressurized Tanks?", "Moving Parts", "10-Yr Reliability"]
    trade_rows = [
        ["Secondary Li-Ion Battery Bank", "23,600 kg", "No (Sealed cells)", "Thermal louvers", "Low (150 Wh/kg penalty)"],
        ["H2/O2 Regenerative Fuel Cell", "4,450 kg", "YES (20–35 MPa)", "Pumps, valves, compressors", "Moderate (Disqualified)"],
        ["Stirling + Regolith Thermal Core", "1,890 kg", "YES (He gas)", "High-freq linear pistons", "Moderate (Wear/vibration)"],
        ["HELIOS-R3 (ISRU Core + TPV)", "1,480 kg", "NO (Zero)", "1-DOF cold-side sleeve", "High (100% solid-state)"],
    ]
    draw_table(pdf, trade_headers, trade_rows, [52, 27, 32, 34, 30.9], font_size=7.6)

    mass_headers = ["Subsystem Component", "Key Engineering Specifications", "Earth Mass", "Verification"]
    mass_rows = [
        ["ISRU Sintered Core + Berm", f"{C['core_diameter_m']} m D x {C['core_height_m']} m H (59.0 t) + 1.5 m berm", "0 kg (ISRU)", f"PASS ({C['thermal_retention_pct']}% ret.)"],
        ["SiC 32-Fin + 3-Ring Matrix", "32 radial fins (7.53 cm pitch) + 3 rings + liner", "310 kg", f"PASS (tau = {C['diffusion_time_hr']} hr)"],
        ["Selective TPV + 1-DOF Sleeve", "W/HfO2 emitter + InGaAs/GaSb + 300 K Mo sleeve", "145 kg", "PASS (34.0% cell eff.)"],
        ["4x VCHP Z-93 Radiator Wings", f"4 x ({C['radiator_wing_length_m']} m x 2.00 m) = {C['radiator_total_area_m2']} m²", "195 kg", "PASS (20.17 kW_th)"],
        ["12 m VSAT Mast + Zylon Guys", "12-bay composite truss + relay mirror + 3 guys", "195 kg", "PASS (>10 m spec)"],
        ["Heliostat + Quad Sensor", f"{C['dish_diameter_m']} m parabolic mirror + 0.20 s beam abort", "125 kg", "PASS (37.87 kW_th)"],
        ["Auxiliary 12 kWe ROSA PV", "34.3 m² roll-out triple-junction wing + EDS", "95 kg", "PASS (Day baseload)"],
        ["ISPSIS 120 VDC PMAD + Batt.", "97.5% SiC boost converter + 4.0 kWh battery", "145 kg", "PASS (ISPSIS 120 VDC)"],
        ["Tethered ISRU Mini-Dozer", "4-wheel autonomous regolith grader + tether", "110 kg", "PASS (Auto fill/berm)"],
        ["Lander Deck & Margin", "4.20 m octagonal deck + 4 footpads + margin", "160 kg", "PASS (<4.20 m fairing)"],
        ["TOTAL SYSTEM (10 kWe 24/7)", f"Specific Mass: {C['specific_mass_kg_kwe']} kg/kWe", f"{int(C['earth_launched_mass_kg']):,} kg", "15.9x lighter vs Li-ion"],
    ]
    draw_table(pdf, mass_headers, mass_rows, [47, 72, 24, 32.9], font_size=7.6)

    pdf.section_heading("5. System Operations, Electrical PMAD & FMEA")
    pdf.body_para(
        "ISPSIS Electrical Architecture & Keep-Alive Startup: Each TPV module contains 140 series-connected InGaAs/GaSb tandem "
        "cells operating at V_mpp = 84 VDC, stepped up via a dual-redundant, radiation-hardened Silicon Carbide (SiC) interleaved "
        "boost converter (97.5% efficiency) onto NASA's 120 VDC ISPSIS microgrid bus (with a 3 kVAC / 1 kHz step-up transformer "
        "port for long-distance habitat feeders). Prior to full thermal core commissioning, an integrated 4.0 kWh solid-state "
        "battery provides 400 W continuous keep-alive power for flight avionics, linear sleeve actuators, and rover telemetry."
    )
    pdf.bullet_item(
        "Stage 1 — Autonomous Deployment & Civil Works (Days 1–14)",
        "Outrigger legs level the deck, the 12 m VSAT mast deploys with Zylon guy-wires, and the ROSA wing unfurls (12.0 kWe). "
        "The 110 kg tethered mini-dozer fills the containment cylinder and grades the 1.50 m berm while the 4.0 kWh solid-state "
        "battery sustains avionics (0.4 kWe) across Commissioning Night 1."
    )
    pdf.bullet_item(
        "Stage 2 — Partial-Core Sintering & Ramp-Up (Days 15–42)",
        "During Lunar Day 2, the heliostat sinters the lower 20 metric tons of regolith (1,435–1,660 K), delivering 3.5 kWe "
        "continuous baseload power throughout Lunar Night 2."
    )
    pdf.bullet_item(
        "Stage 3 — Full Operational Baseload (Day 43+)",
        "All 59.0 metric tons reach full operating temperature, sustaining 10.0 kWe continuous nighttime power (12.0 kWe daytime) "
        "across a 10-year design life without crew intervention."
    )

    fmea_headers = ["Failure Scenario", "Autonomous Detection", "Built-In Hardware Recovery", "Residual Output"]
    fmea_rows = [
        ["Micrometeoroid Puncture of 1 Radiator Wing (-25%)", "VCHP pressure drop in damaged header", f"VCHP gas diode isolates wing; 3 wings equilibrate at {C['fmea_3wing_radiator_temp_k']} K", "10.0 kWe (100% power)"],
        ["Mast Thermal Bending / Tracking Drift (>25 mm)", "Aperture collar quadrant photodiodes", f"Gimbal slews off-sun in {INP['beam_abort_response_s']:.2f} s; Zylon guys limit deflection <4 mm", "Zero damage; auto-lock"],
        ["Electrostatic Lunar Dust Storm Surge", "Mirror reflectance & PV current drop", "1.2 kV, 10 Hz traveling-wave EDS clears surfaces in 90 s", ">98% optical eff."],
        ["Cold-Side Sleeve Actuator Stall", "Linear encoder position discrepancy", "Dual-wound stepper + spring fail-safe bias sleeve to 55%", "8.2–10.0 kWe continuous"],
    ]
    draw_table(pdf, fmea_headers, fmea_rows, [45, 41, 58, 31.9], font_size=7.6)

    pdf.section_heading("6. Development Roadmap, References & AI Disclosure")
    pdf.body_para(
        "TRL Advancement & Ground Validation Path: Subsystems leverage flight-heritage technologies—ROSA arrays (TRL 9), "
        "VCHP radiators (TRL 9), SiC power electronics (TRL 7), and selective TPV cells (TRL 5–6). Phase 2 ground validation "
        "utilizes a 1/5-scale (2.0 kWe) engineering test unit inside a dirty thermal-vacuum chamber using JSC-1A lunar regolith "
        "simulant and a xenon solar simulator to verify 32-fin heat extraction, 1-DOF sleeve regulation, and EDS dust clearance."
    )
    pdf.body_para(
        "References: (1) NASA/TM-20240003496, Polar Solar Environment and Vertical Solar Array Technology (VSAT); "
        "(2) NASA NTRS 20240013588, Electric Power on the Lunar Surface (ISPSIS 120 VDC Standard); "
        "(3) NASA-CR-189073, In-Situ Regolith Thermal Energy Storage (LUTHER); (4) Heiken, Vaniman, & French, Lunar Sourcebook; "
        "(5) Omair et al., Ultra-Efficient Thermophotovoltaic Power Conversion (>30%), PNAS."
    )
    pdf.body_para(
        "AI Tool Usage Disclosure: In accordance with official Moon Base Challenge rules, generative AI and automated Python "
        "scripting tools were used to assist with literature organization, cross-checking symbolic thermodynamic and radiative "
        "heat-transfer derivations, and generating parametric CAD (build123d) and simulation (NumPy/Matplotlib) visualization code. "
        "All physical constants, boundary conditions, engineering trade-offs, and final design parameters were independently "
        "verified and authored by the student team."
    )

    # ==========================================================================
    # DEDICATED VISUAL-AID PAGE (LANDSCAPE PLATE)
    # ==========================================================================
    pdf.add_page(orientation="L")
    if os.path.exists("HELIOS_R3_Visual_Aid_Plate.png"):
        pdf.image("HELIOS_R3_Visual_Aid_Plate.png", x=10, y=8, w=259)
    else:
        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(0, 20, "HELIOS_R3_Visual_Aid_Plate.png not found — run generate_figures.py first.")

    out_name = "HELIOS_R3_Phase1_Submission.pdf"
    pdf.output(out_name)
    concept_pages = pdf.page_no() - 2
    print(f"Built {out_name}: {pdf.page_no()} total pages (1 Cover + {concept_pages} Concept Paper Pages + 1 Visual-Aid Page).")


if __name__ == "__main__":
    build_pdf()
