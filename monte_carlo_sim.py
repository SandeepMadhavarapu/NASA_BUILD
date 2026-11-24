import json
import numpy as np
import matplotlib.pyplot as plt

with open("parameter_lock.json", "r", encoding="utf-8") as f:
    LOCK = json.load(f)

C = LOCK["computed"]
INP = LOCK["inputs"]

rng = np.random.default_rng(42)
N_TRIALS = 5000
YEARS = 10

# Stochastic lunar environment & aging distributions across 5,000 missions
k_berm_samples = np.clip(rng.normal(0.045, 0.007, N_TRIALS), 0.030, 0.070)
tpv_deg_per_yr = np.clip(rng.normal(0.0035, 0.0010, N_TRIALS), 0.0010, 0.0075)
opt_deg_per_yr = np.clip(rng.normal(0.0040, 0.0012, N_TRIALS), 0.0010, 0.0085)
core_mass_actual = 59020.0  # Full 3.069m x 3.069m cylinder capacity (kg)

# Year-by-year End-of-Night (Hour 708) bus power and required sleeve opening
yr_axis = np.arange(0, YEARS + 1)
p_night_eol = np.zeros((N_TRIALS, YEARS + 1))
sleeve_req = np.zeros((N_TRIALS, YEARS + 1))

e_spec = INP["regolith_cp_j_kgk"] * (INP["core_temp_max_k"] - INP["core_temp_min_k"]) + INP["regolith_latent_j_kg"]
e_stored_base = core_mass_actual * e_spec

for y in yr_axis:
    eta_tpv_y = INP["tpv_cell_efficiency"] * ((1.0 - tpv_deg_per_yr) ** y)
    eta_net_y = eta_tpv_y * INP["sic_pmad_efficiency"]
    eta_opt_y = INP["optical_efficiency"] * ((1.0 - opt_deg_per_yr) ** y)

    # Conductive loss over 354 hr night
    q_cond_y = (k_berm_samples * 44.38 * (1455.0 - 150.0)) / INP["berm_thickness_m"]
    e_loss_y = q_cond_y * 354.0 * 3600.0

    # Available thermal energy after daytime charge & nighttime loss
    e_charge_cap = 33.03 * INP["solar_flux_w_m2"] * eta_opt_y * 354.0 * 3600.0
    e_avail_th = np.minimum(e_stored_base, e_charge_cap) - e_loss_y

    # Sleeve compensates up to 95% open; above 95% output gracefully derates
    req_open = 0.86 * (0.3315 / eta_net_y)
    sleeve_req[:, y] = np.clip(req_open, 0.24, 0.95)
    sleeve_factor = np.minimum(1.0, 0.95 / req_open)

    p_max_elec_kw = (e_avail_th * eta_net_y) / (354.0 * 3600.0 * 1000.0)
    p_night_eol[:, y] = np.minimum(10.0, p_max_elec_kw) * sleeve_factor

p10 = np.percentile(p_night_eol, 10, axis=0)
p50 = np.percentile(p_night_eol, 50, axis=0)
p90 = np.percentile(p_night_eol, 90, axis=0)
reliability_pct = round(float(np.mean(p_night_eol[:, -1] >= 9.8) * 100.0), 2)

LOCK["monte_carlo_10yr"] = {
    "trials": N_TRIALS,
    "eol_p50_power_kwe": round(float(p50[-1]), 2),
    "eol_p10_power_kwe": round(float(p10[-1]), 2),
    "eol_p90_power_kwe": round(float(p90[-1]), 2),
    "prob_ge_9_8kwe_pct": reliability_pct,
    "eol_median_sleeve_open_pct": round(float(np.median(sleeve_req[:, -1]) * 100.0), 1),
}

with open("parameter_lock.json", "w", encoding="utf-8") as f:
    json.dump(LOCK, f, indent=2)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2), dpi=300)
fig.suptitle("HELIOS-R3: 10-Year Stochastic Reliability & EOL Margin (5,000 Monte Carlo Trials)", fontweight="bold")

ax1.fill_between(yr_axis, p10, p90, color="#38bdf8", alpha=0.35, label="P10–P90 Confidence Band")
ax1.plot(yr_axis, p50, color="#0284c7", lw=2.3, marker="o", label="Median Output (P50)")
ax1.axhline(10.0, color="#16a34a", ls="--", lw=1.2, label="Nominal Baseload (10.0 kWe)")
ax1.set_xlabel("Mission Duration (Years)")
ax1.set_ylabel("End-of-Night Bus Power (kWe)")
ax1.set_ylim(8.8, 10.4)
ax1.grid(True, ls=":", alpha=0.6)
ax1.legend(loc="lower left", fontsize=8)
ax1.set_title("A. 10-Year End-of-Night Power Stability")

ax2.hist(p_night_eol[:, -1], bins=28, color="#0f172a", edgecolor="#38bdf8", alpha=0.9)
ax2.axvline(9.8, color="#dc2626", ls="--", lw=1.4, label=f"9.8 kWe Threshold ({reliability_pct}% Pass)")
ax2.set_xlabel("Year-10 End-of-Night Power (kWe)")
ax2.set_ylabel("Simulation Trials (out of 5,000)")
ax2.grid(True, ls=":", alpha=0.5)
ax2.legend(loc="upper left", fontsize=8)
ax2.set_title("B. Year-10 Baseload Distribution")

plt.tight_layout()
fig.savefig("HELIOS_R3_MonteCarlo_10Yr.png", dpi=300)
print(f"Monte Carlo Complete -> Year-10 P50: {p50[-1]:.2f} kWe | >=9.8 kWe Reliability: {reliability_pct}%")
