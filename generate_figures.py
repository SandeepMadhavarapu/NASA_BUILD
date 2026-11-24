import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

with open("parameter_lock.json", "r", encoding="utf-8") as f:
    LOCK = json.load(f)

C = LOCK["computed"]
INP = LOCK["inputs"]
TS = C["transient_sample_every_12h"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9.5,
    "axes.titlesize": 10.5,
    "axes.titleweight": "bold",
    "axes.edgecolor": "#334155",
    "axes.linewidth": 0.9,
})

fig = plt.figure(figsize=(11, 8.5), dpi=300)
gs = gridspec.GridSpec(2, 2, hspace=0.34, wspace=0.26, left=0.08, right=0.95, top=0.90, bottom=0.08)

fig.suptitle(
    "HELIOS-R3: Lunar South Pole 10 kWe (24/7) Optical-Thermal & Selective TPV Architecture",
    fontsize=13, fontweight="bold", color="#0f172a", y=0.96
)

# ------------------------------------------------------------------------------
# PANEL A: 708-Hour Synodic Thermal Core & 1-DOF Cold-Side Sleeve Profile
# ------------------------------------------------------------------------------
ax1 = fig.add_subplot(gs[0, 0])
hrs = np.array(TS["hours"])
t_core = np.array(TS["t_core_k"])
sleeve = np.array(TS["sleeve_open"]) * 100.0

ax1.axvspan(0, 354, color="#fef3c7", alpha=0.55, label="Lunar Day (354 h)")
ax1.axvspan(354, 708, color="#e2e8f0", alpha=0.65, label="Lunar Night (354 h)")
l1 = ax1.plot(hrs, t_core, color="#ea580c", lw=2.2, label="Core Temp $T_{core}$ (K)")
ax1.axhline(1435, color="#9a3412", ls="--", lw=1.0, label="Regolith Melt Plateau (1,435 K)")
ax1.set_ylabel("Core Temperature (K)", color="#c2410c", fontweight="bold")
ax1.set_xlabel("Synodic Mission Time (Hours)")
ax1.set_xlim(0, 708)
ax1.set_ylim(1200, 1710)
ax1.grid(True, linestyle=":", alpha=0.5)

ax1b = ax1.twinx()
l2 = ax1b.plot(hrs, sleeve, color="#0284c7", lw=2.0, ls="-.", label="1-DOF Mo Sleeve Open (%)")
ax1b.set_ylabel("Cold-Side Sleeve Opening (%)", color="#0369a1", fontweight="bold")
ax1b.set_ylim(-5, 105)

lines = l1 + l2
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc="upper left", fontsize=7.5, framealpha=0.9)
ax1.set_title("A. 708-Hour Transient Core Cycle & 1-DOF Sleeve Control")

# ------------------------------------------------------------------------------
# PANEL B: Earth-Launched System Mass Comparison (10 kWe / 354-hr Night)
# ------------------------------------------------------------------------------
ax2 = fig.add_subplot(gs[0, 1])
techs = [
    "Li-Ion Batteries\n(150 Wh/kg)",
    "H2/O2 Reg. Fuel Cell\n(High-P Tanks)",
    "HELIOS-R3\n(ISRU Core + TPV)"
]
masses_t = [23.60, 4.45, C["earth_launched_mass_kg"] / 1000.0]
colors = ["#94a3b8", "#64748b", "#0284c7"]

bars = ax2.bar(techs, masses_t, color=colors, width=0.52, edgecolor="#1e293b")
ax2.set_ylabel("Earth-Launched Mass (Metric Tons)", fontweight="bold")
ax2.set_ylim(0, 27.5)
ax2.grid(axis="y", linestyle=":", alpha=0.5)
for bar, val in zip(bars, masses_t):
    ax2.text(
        bar.get_x() + bar.get_width() / 2.0, val + 0.6,
        f"{val:.2f} t\n({int(val*1000):,} kg)",
        ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0f172a"
    )
ax2.annotate(
    "15.9x Lighter than Li-Ion\nZero Pressure Vessels",
    xy=(2, 1.55), xytext=(1.05, 13.5),
    arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.5),
    fontsize=8.5, fontweight="bold", color="#0369a1",
    bbox=dict(boxstyle="round,pad=0.35", facecolor="#f0f9ff", edgecolor="#0284c7")
)
ax2.set_title("B. Launched Mass Benchmark (3,540 kWh Night Load)")

# ------------------------------------------------------------------------------
# PANEL C: 32-Fin + 3-Ring Conductive Diffusion Proof vs. Fin Count
# ------------------------------------------------------------------------------
ax3 = fig.add_subplot(gs[1, 0])
fin_counts = np.array([4, 8, 16, 24, 32, 48])
r_core = C["core_diameter_m"] / 2.0
alpha_reg = INP["regolith_k_eff_w_mk"] / (INP["regolith_density_kg_m3"] * INP["regolith_cp_j_kgk"])
l_chars = ((np.pi * r_core) / fin_counts) / 2.0
tau_hrs = (l_chars ** 2) / alpha_reg / 3600.0

ax3.plot(fin_counts, tau_hrs, marker="o", color="#0f172a", lw=2.0, label="Thermal Diffusion Time $\\tau_{diff}$")
ax3.axhline(354.0, color="#dc2626", ls="--", lw=1.3, label="Lunar Night Limit (354 hr)")
ax3.scatter([32], [C["diffusion_time_hr"]], color="#16a34a", s=90, zorder=5, label=f"HELIOS-R3 Locked (32 fins = {C['diffusion_time_hr']} hr)")
ax3.set_yscale("log")
ax3.set_xlabel("Radial SiC Fin Count ($N_{fins}$)")
ax3.set_ylabel("Characteristic Diffusion Time (Hours, Log)", fontweight="bold")
ax3.set_xticks(fin_counts)
ax3.grid(True, which="both", linestyle=":", alpha=0.5)
ax3.legend(loc="upper right", fontsize=7.8)
ax3.set_title("C. Core Conduction Bottleneck Elimination (32-Fin Matrix)")

# ------------------------------------------------------------------------------
# PANEL D: 3-Stage Autonomous Commissioning & Bus Output Ramp
# ------------------------------------------------------------------------------
ax4 = fig.add_subplot(gs[1, 1])
stages = ["Stage 1 (Days 1-14)\nRover Grading +\n4 kWh Battery", "Stage 2 (Days 15-42)\n20 t Partial Core\nSintered", "Stage 3 (Day 43+)\n59 t Full Core +\n1.5 m Berm"]
night_kw = [0.4, 3.5, 10.0]
day_kw = [12.0, 12.0, 12.0]
x = np.arange(len(stages))
w = 0.34

b1 = ax4.bar(x - w/2, day_kw, width=w, color="#f59e0b", edgecolor="#1e293b", label="Lunar Day Bus (ROSA PV)")
b2 = ax4.bar(x + w/2, night_kw, width=w, color="#1d4ed8", edgecolor="#1e293b", label="Lunar Night Bus (TPV / Batt)")
ax4.set_ylabel("ISPSIS 120 VDC Bus Output (kWe)", fontweight="bold")
ax4.set_xticks(x)
ax4.set_xticklabels(stages, fontsize=8.2)
ax4.set_ylim(0, 14.5)
ax4.grid(axis="y", linestyle=":", alpha=0.5)
for bar in list(b1) + list(b2):
    h = bar.get_height()
    ax4.text(bar.get_x() + bar.get_width()/2.0, h + 0.3, f"{h:.1f}", ha="center", va="bottom", fontsize=8, fontweight="bold")
ax4.legend(loc="upper left", fontsize=7.8)
ax4.set_title("D. Autonomous 3-Stage ISRU Commissioning Schedule")

fig.savefig("HELIOS_R3_Visual_Aid_Plate.png", dpi=300)
fig.savefig("HELIOS_R3_Visual_Aid_Plate.pdf")
print("Generated HELIOS_R3_Visual_Aid_Plate.png & .pdf successfully.")
