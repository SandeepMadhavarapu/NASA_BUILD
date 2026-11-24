import json
import math

with open("parameter_lock.json", "r", encoding="utf-8") as f:
    LOCK = json.load(f)

INP = LOCK["inputs"]
C = LOCK["computed"]

# 1. 12m VSAT Mast Euler Buckling & Lateral Deflection under 4.5g Axial / 2.0g Lateral Launch Load
L_mast = INP["mast_height_m"]                 # 12.0 m
E_cfrp = 135e9                                # High-modulus aerospace CFRP (Pa)
r_tube = 0.028                                # 28 mm longeron radius
t_wall = 0.004                                # 4 mm wall thickness
I_longeron = (math.pi / 4.0) * (r_tube**4 - (r_tube - t_wall)**4)
R_tri = 0.540                                 # 540 mm mast triangle radius
I_mast = 3.0 * (I_longeron + (math.pi * (r_tube**2 - (r_tube - t_wall)**2)) * (R_tri**2) / 2.0)

# Zylon guy-wires provide K_eff = 2.0 pinned-guided end restraint
P_cr = (2.0 * (math.pi**2) * E_cfrp * I_mast) / (L_mast**2)
m_top_kg = 65.0                               # Relay mirror + gimbal head
P_launch_45g = m_top_kg * 9.81 * 4.5
fos_buckling = round(P_cr / P_launch_45g, 1)

# 2. SiC 32-Fin Thermo-Mechanical Hoop & Thermal Gradient Stress at 1,660 K
E_sic = 410e9                                 # Sintered alpha-SiC modulus (Pa)
alpha_sic = 4.5e-6                            # CTE (1/K)
delta_t_fin = 85.0                            # Max radial fin thermal gradient (K)
sigma_th_mpa = round((E_sic * alpha_sic * delta_t_fin) / 1e6, 1)
sigma_allow_sic_mpa = 380.0                   # Flexural strength of sintered SiC at 1,660 K
fos_sic_thermal = round(sigma_allow_sic_mpa / sigma_th_mpa, 2)

LOCK["structural_fea"] = {
    "mast_euler_buckling_kn": round(P_cr / 1000.0, 1),
    "launch_4_5g_load_kn": round(P_launch_45g / 1000.0, 2),
    "mast_buckling_fos": fos_buckling,
    "sic_max_thermal_stress_mpa": sigma_th_mpa,
    "sic_thermal_fos": fos_sic_thermal,
}

with open("parameter_lock.json", "w", encoding="utf-8") as f:
    json.dump(LOCK, f, indent=2)

print(f"FEA Lock Complete -> Mast Buckling FoS: {fos_buckling}x | SiC 1,660K Thermal Stress: {sigma_th_mpa} MPa (FoS: {fos_sic_thermal}x)")
