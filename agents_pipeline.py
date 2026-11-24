import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import numpy as np
import requests
from bs4 import BeautifulSoup

STATE_FILE = "agent1_memory.json"
LOCK_FILE = "parameter_lock.json"
LOG_FILE = "pipeline_events.log"

RULES_URL = "https://moonbasechallenge.org/rules/"
NASA_FEEDS = [
    "https://www.nasa.gov/news-release/feed/",
    "https://www.nasa.gov/technology/feed/",
]
NTRS_QUERIES = [
    "lunar surface power",
    "vertical solar array technology",
    "regolith thermal energy storage",
    "thermophotovoltaic space power",
]


def log(agent: str, msg: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{ts}] [{agent}] {msg}"
    print(entry, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


class Agent1PhysicsAndIntel:
    def __init__(self):
        self.memory = self._load_memory()
        self.spec = {
            "version": 3,
            "mission_codename": "HELIOS-R3",
            "category": "Track 1: Power Generation & Storage",
            "constraints": {
                "max_file_mb": 6.0,
                "anonymized": True,
                "no_nasa_logos": True,
                "ai_disclosure_required": True,
                "no_pressurized_vessels": True,
                "no_hazardous_chemicals": True,
                "night_duration_hr": 354.0,
                "synodic_period_hr": 708.0,
                "temp_min_c": -170.0,
                "temp_max_c": 120.0,
                "psr_temp_c": -203.0,
                "fairing_max_dia_m": 4.20,
                "ispsis_bus_vdc": 120.0,
            },
            "inputs": {
                "net_power_kwe": 10.0,
                "core_temp_max_k": 1660.0,
                "core_temp_melt_k": 1435.0,
                "core_temp_min_k": 1250.0,
                "tpv_cell_efficiency": 0.34,       # W/HfO2 selective emitter + Au BSR
                "sic_pmad_efficiency": 0.975,      # Rad-hard SiC boost to 120 VDC ISPSIS
                "regolith_cp_j_kgk": 1400.0,
                "regolith_latent_j_kg": 161200.0,
                "regolith_density_kg_m3": 2600.0,
                "regolith_k_eff_w_mk": 0.15,
                "berm_k_eff_w_mk": 0.045,
                "berm_thickness_m": 1.50,
                "solar_flux_w_m2": 1365.0,
                "optical_efficiency": 0.84,        # Windowless solar tower + heliostat
                "radiator_temp_k": 300.0,
                "sink_temp_k": 180.0,
                "radiator_emissivity": 0.90,
                "fin_efficiency": 0.86,
                "mast_height_m": 12.0,
                "guy_wire_count": 3,
                "beam_abort_response_s": 0.20,
                "radial_fin_count": 32,
                "concentric_ring_count": 3,
                "isru_rover_mass_kg": 110.0,
                "keep_alive_battery_kwh": 4.0,
            },
            "mass_budget_kg": {
                "sic_32fin_3ring_matrix": 310.0,
                "selective_tpv_1dof_sleeve": 145.0,
                "vchp_z93_radiators_4x": 195.0,
                "vsat_12m_mast_zylon_guys": 195.0,
                "heliostat_gimbal_quad_sensor": 125.0,
                "rosa_12kwe_daytime_pv": 95.0,
                "ispsis_120vdc_pmad_4kwh_batt": 145.0,
                "tethered_isru_minidozer_rover": 110.0,
                "lander_deck_anchors_margin": 160.0,
            },
            "intel_feed": [],
            "rules_snapshot_hash": "",
        }

    def _load_memory(self):
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"seen_urls": [], "rules_hash": ""}

    def _save_memory(self):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, indent=2)

    def poll_official_rules(self):
        try:
            r = requests.get(RULES_URL, timeout=15, headers={"User-Agent": "HELIOS-R3-Agent1"})
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
                h = hashlib.sha256(text.encode("utf-8")).hexdigest()
                if h != self.memory.get("rules_hash"):
                    self.memory["rules_hash"] = h
                    self.spec["rules_snapshot_hash"] = h[:16]
                    log("AGENT-1", f"Official rules CHANGED (SHA256: {h[:12]}). Saved rules_snapshot.txt")
                    with open("rules_snapshot.txt", "w", encoding="utf-8") as rf:
                        rf.write(text)
                    subprocess.run(["msg", os.environ.get("USERNAME", "*"), "HELIOS-R3 Alert: Official Moon Base Challenge rules page changed! Check rules_snapshot.txt."], check=False)
                    return True
        except Exception as e:
            log("AGENT-1", f"Rules check warning: {e}")
        return False

    def poll_nasa_and_ntrs(self):
        new_hits = []
        seen = set(self.memory.get("seen_urls", []))
        for feed in NASA_FEEDS:
            try:
                r = requests.get(feed, timeout=15)
                root = ET.fromstring(r.content)
                for item in root.findall(".//item"):
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    if link and link not in seen and any(
                        k in title.lower() for k in ("moon", "lunar", "artemis", "south pole", "power")
                    ):
                        seen.add(link)
                        new_hits.append({"source": "NASA_NEWS", "title": title, "url": link})
            except Exception as e:
                log("AGENT-1", f"RSS warning ({feed}): {e}")

        for q in NTRS_QUERIES:
            try:
                r = requests.get(
                    "https://ntrs.nasa.gov/api/citations/search",
                    params={"q": q, "page[size]": 5},
                    timeout=15,
                )
                for rec in r.json().get("results", []):
                    nid = str(rec.get("id", ""))
                    url = f"https://ntrs.nasa.gov/citations/{nid}"
                    if nid and url not in seen:
                        seen.add(url)
                        new_hits.append({
                            "source": "NASA_NTRS",
                            "title": f"[NTRS {nid}] {rec.get('title', 'Report')}",
                            "url": url,
                        })
            except Exception as e:
                log("AGENT-1", f"NTRS warning ({q}): {e}")

        self.memory["seen_urls"] = sorted(list(seen))
        return new_hits

    def solve_physics_and_transient_cycle(self):
        inp = self.spec["inputs"]
        c = self.spec["constraints"]
        sigma = 5.670374419e-8

        eta_net = inp["tpv_cell_efficiency"] * inp["sic_pmad_efficiency"]
        e_elec_j = inp["net_power_kwe"] * 1000.0 * c["night_duration_hr"] * 3600.0
        e_th_gross_j = e_elec_j / (eta_net * 0.94)

        delta_t = inp["core_temp_max_k"] - inp["core_temp_min_k"]
        spec_energy = inp["regolith_cp_j_kgk"] * delta_t + inp["regolith_latent_j_kg"]
        m_reg_kg = e_th_gross_j / spec_energy
        v_core_m3 = m_reg_kg / inp["regolith_density_kg_m3"]
        d_core_m = round(((4.0 * v_core_m3) / math.pi) ** (1.0 / 3.0) * 1.02, 3)
        h_core_m = d_core_m

        a_core = math.pi * d_core_m * h_core_m + 0.5 * math.pi * (d_core_m ** 2)
        t_mean = 0.5 * (inp["core_temp_max_k"] + inp["core_temp_min_k"])
        q_cond_w = (inp["berm_k_eff_w_mk"] * a_core * (t_mean - 150.0)) / inp["berm_thickness_m"]
        e_cond_j = q_cond_w * c["night_duration_hr"] * 3600.0
        retention = 1.0 - (e_cond_j / e_th_gross_j)

        alpha_reg = inp["regolith_k_eff_w_mk"] / (inp["regolith_density_kg_m3"] * inp["regolith_cp_j_kgk"])
        pitch_radial = (math.pi * (d_core_m / 2.0)) / inp["radial_fin_count"]
        l_char = pitch_radial / 2.0
        tau_diff_hr = (l_char ** 2) / alpha_reg / 3600.0

        p_charge_w = (e_th_gross_j / (c["night_duration_hr"] * 3600.0)) * 1.18
        a_dish_m2 = p_charge_w / (inp["solar_flux_w_m2"] * inp["optical_efficiency"])
        d_dish_m = round(math.sqrt((4.0 * a_dish_m2) / math.pi), 3)

        q_rej_w = (inp["net_power_kwe"] * 1000.0) * ((1.0 / eta_net) - 1.0)
        q_flux = (
            inp["fin_efficiency"]
            * inp["radiator_emissivity"]
            * sigma
            * (inp["radiator_temp_k"] ** 4 - inp["sink_temp_k"] ** 4)
        )
        a_rad_total_m2 = round(q_rej_w / q_flux, 2)
        wing_len_m = round((a_rad_total_m2 / 8.0) / 2.0, 2)

        hours = np.arange(0, 709, 1, dtype=float)
        t_core_arr = np.zeros_like(hours)
        sleeve_arr = np.zeros_like(hours)
        p_pv_arr = np.zeros_like(hours)
        p_tpv_arr = np.zeros_like(hours)

        t_curr = inp["core_temp_min_k"]
        latent_fraction = 0.0
        dt_sec = 3600.0

        for idx, hr in enumerate(hours):
            is_day = hr < 354.0
            if is_day:
                p_pv_arr[idx] = 12.0
                p_tpv_arr[idx] = 0.0
                sleeve_arr[idx] = 0.0
                q_net_w = p_charge_w - q_cond_w
            else:
                p_pv_arr[idx] = 0.0
                p_tpv_arr[idx] = inp["net_power_kwe"]
                q_tpv_draw_w = (inp["net_power_kwe"] * 1000.0) / eta_net
                q_net_w = -(q_tpv_draw_w + q_cond_w)
                sleeve_arr[idx] = min(0.95, round(((inp["core_temp_min_k"] / max(t_curr, 1200.0)) ** 4) * 0.86, 3))

            dq_j = q_net_w * dt_sec
            if dq_j > 0:
                if abs(t_curr - inp["core_temp_melt_k"]) < 1.0 and latent_fraction < 1.0:
                    latent_fraction += dq_j / (m_reg_kg * inp["regolith_latent_j_kg"])
                    if latent_fraction > 1.0:
                        excess = (latent_fraction - 1.0) * m_reg_kg * inp["regolith_latent_j_kg"]
                        latent_fraction = 1.0
                        t_curr += excess / (m_reg_kg * inp["regolith_cp_j_kgk"])
                else:
                    t_next = t_curr + dq_j / (m_reg_kg * inp["regolith_cp_j_kgk"])
                    if t_curr < inp["core_temp_melt_k"] <= t_next and latent_fraction < 1.0:
                        to_melt = (inp["core_temp_melt_k"] - t_curr) * m_reg_kg * inp["regolith_cp_j_kgk"]
                        rem = dq_j - to_melt
                        t_curr = inp["core_temp_melt_k"]
                        latent_fraction = min(1.0, rem / (m_reg_kg * inp["regolith_latent_j_kg"]))
                    else:
                        t_curr = min(inp["core_temp_max_k"], t_next)
            else:
                if abs(t_curr - inp["core_temp_melt_k"]) < 1.0 and latent_fraction > 0.0:
                    latent_fraction += dq_j / (m_reg_kg * inp["regolith_latent_j_kg"])
                    if latent_fraction < 0.0:
                        deficit = latent_fraction * m_reg_kg * inp["regolith_latent_j_kg"]
                        latent_fraction = 0.0
                        t_curr += deficit / (m_reg_kg * inp["regolith_cp_j_kgk"])
                else:
                    t_next = t_curr + dq_j / (m_reg_kg * inp["regolith_cp_j_kgk"])
                    if t_curr > inp["core_temp_melt_k"] >= t_next and latent_fraction > 0.0:
                        to_melt = (inp["core_temp_melt_k"] - t_curr) * m_reg_kg * inp["regolith_cp_j_kgk"]
                        rem = dq_j - to_melt
                        t_curr = inp["core_temp_melt_k"]
                        latent_fraction = max(0.0, 1.0 + rem / (m_reg_kg * inp["regolith_latent_j_kg"]))
                    else:
                        t_curr = max(inp["core_temp_min_k"], t_next)

            t_core_arr[idx] = round(t_curr, 1)

        t_rad_fmea = ((q_rej_w / (0.75 * a_rad_total_m2 * inp["fin_efficiency"] * inp["radiator_emissivity"] * sigma)) + inp["sink_temp_k"] ** 4) ** 0.25
        total_launched_kg = sum(self.spec["mass_budget_kg"].values())

        self.spec["computed"] = {
            "net_tpv_pmad_efficiency_pct": round(eta_net * 100.0, 2),
            "e_th_gross_gj": round(e_th_gross_j / 1e9, 2),
            "regolith_mass_kg": round(m_reg_kg, 1),
            "core_diameter_m": d_core_m,
            "core_height_m": h_core_m,
            "thermal_retention_pct": round(retention * 100.0, 2),
            "diffusion_time_hr": round(tau_diff_hr, 1),
            "dish_diameter_m": d_dish_m,
            "radiator_total_area_m2": a_rad_total_m2,
            "radiator_wing_length_m": wing_len_m,
            "fmea_3wing_radiator_temp_k": round(t_rad_fmea, 1),
            "earth_launched_mass_kg": total_launched_kg,
            "specific_mass_kg_kwe": round(total_launched_kg / inp["net_power_kwe"], 1),
            "transient_sample_every_12h": {
                "hours": hours[::12].tolist(),
                "t_core_k": t_core_arr[::12].tolist(),
                "sleeve_open": sleeve_arr[::12].tolist(),
                "p_pv_kwe": p_pv_arr[::12].tolist(),
                "p_tpv_kwe": p_tpv_arr[::12].tolist(),
            },
        }

    def run_cycle(self, force=False):
        rules_changed = self.poll_official_rules()
        intel_hits = self.poll_nasa_and_ntrs()
        if force or rules_changed or intel_hits or not os.path.exists(LOCK_FILE):
            if intel_hits:
                self.spec["version"] += 1
                self.spec["intel_feed"] = (intel_hits + self.spec["intel_feed"])[:20]
                log("AGENT-1", f"Ingested {len(intel_hits)} new NASA/NTRS records.")
            self.solve_physics_and_transient_cycle()
            self._save_memory()
            with open(LOCK_FILE, "w", encoding="utf-8") as f:
                json.dump(self.spec, f, indent=2)
            log("AGENT-1", f"Locked HELIOS-R3 physics & ISPSIS telemetry -> {LOCK_FILE} (v{self.spec['version']})")
            return True
        log("AGENT-1", "No new external deltas.")
        return False


def trigger_downstream_agents():
    if os.path.exists("cadquery_pro.py"):
        log("AGENT-2", "Building HELIOS-R3 multi-body aerospace CAD (.step + .stl)...")
        subprocess.run(["python", "cadquery_pro.py"], check=False)
    if os.path.exists("generate_figures.py"):
        log("AGENT-3", "Rendering HELIOS-R3 Visual Aid Plate (.png + .pdf)...")
        subprocess.run(["python", "generate_figures.py"], check=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--interval", type=int, default=1800)
    args = parser.parse_args()

    agent1 = Agent1PhysicsAndIntel()
    if args.once or not args.daemon:
        agent1.run_cycle(force=True)
        trigger_downstream_agents()
    else:
        log("SYSTEM", f"Continuous HELIOS-R3 Pipeline online (poll interval: {args.interval}s)")
        while True:
            if agent1.run_cycle():
                trigger_downstream_agents()
            time.sleep(args.interval)

