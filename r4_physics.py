"""R4 independent screening model. SI units; estimates, not flight validation."""
import math
import json
import random
from pathlib import Path

SIGMA = 5.670374419e-8

def simulate(cfg, *, efficiency=0.34, aperture_open=True, illumination=1.0,
             conductivity=None, optical_factor=1.0, cycles=2, dt=900,
             initial_fraction=1.0, mass=59020.0, dish_area=33.03,
             load_kw=10.0, emitter_area=3.0, effective_emissivity=0.8):
    """Energy-conserving lumped enthalpy model; no temperature/output clipping
    without accounting for curtailed charge or unmet demand."""
    i=cfg["inputs"]; low=i["core_temp_min_k"]; high=i["core_temp_max_k"]
    melt=i["core_temp_melt_k"]; cp=i["regolith_cp_j_kgk"]
    latent=mass*i["regolith_latent_j_kg"]; em=mass*cp*(melt-low)
    cap=mass*cp*(high-low)+latent
    k=i["berm_k_eff_w_mk"] if conductivity is None else conductivity
    area=1.5*math.pi*cfg["computed"]["core_diameter_m"]**2
    aperture=math.pi*0.24**2
    eta_pmad=i["sic_pmad_efficiency"]
    night=cfg["constraints"]["night_duration_hr"]*3600
    if dt<=0 or night%dt or not 0<=illumination<=1 or not 0<efficiency<=1:
        raise ValueError("invalid timestep, illumination or efficiency")
    energy=cap*initial_fraction; start=energy
    total_in=total_out=total_loss=curtail=0.0
    records=[]; night_powers=[]
    for step in range(int(2*night*cycles/dt)):
        day=(step*dt)%(2*night)<night
        if energy<em: temp=low+energy/(mass*cp)
        elif energy<em+latent: temp=melt
        else: temp=melt+(energy-em-latent)/(mass*cp)
        temp=max(150.0,temp)
        # Conservative illustrative efficiency derating; must be replaced with measured curve.
        eta=efficiency*(0.75+0.25*max(0,min(1,(temp-low)/(high-low))))*eta_pmad
        qsolar=dish_area*i["solar_flux_w_m2"]*i["optical_efficiency"]*optical_factor*illumination if day else 0.0
        qloss=max(0,k*area*(temp-150)/i["berm_thickness_m"])
        if day or aperture_open: qloss+=SIGMA*aperture*max(0,temp**4-150**4)
        received=qsolar*dt
        # Can cool below minimum useful operating temperature down to ambient.
        available=energy+received
        loss=min(qloss*dt,max(0,available+mass*cp*(low-150)))
        available-=loss
        max_heat=0.95*effective_emissivity*emitter_area*SIGMA*max(0,temp**4-300**4)
        draw=0.0 if day else min(load_kw*1000/eta*dt,max_heat*dt,max(0,available))
        raw=available-draw
        spill=max(0,raw-cap); energy=raw-spill
        power=draw*eta/dt/1000
        if not day: night_powers.append(power)
        total_in+=received;total_out+=draw;total_loss+=loss;curtail+=spill
        if step%max(1,int(3600/dt))==0: records.append([step*dt/3600,temp,power,energy])
    residual=start+total_in-total_out-total_loss-curtail-energy
    return {"min_night_kw":min(night_powers),"mean_night_kw":sum(night_powers)/len(night_powers),
            "unserved_kwh":sum(max(0,load_kw-p)*dt/3600 for p in night_powers),
            "night_service_fraction":sum(p>=load_kw-1e-8 for p in night_powers)/len(night_powers),
            "balance_residual_j":residual,"relative_balance_error":abs(residual)/max(1,total_in+abs(start)),
            "final_enthalpy_j":energy,"records":records}

def commissioning(cfg):
    i=cfg["inputs"]; mass=59020
    heating=mass*(i["regolith_cp_j_kgk"]*(i["core_temp_max_k"]-150)+i["regolith_latent_j_kg"])
    daily=33.03*i["solar_flux_w_m2"]*i["optical_efficiency"]*354*3600
    return {"battery_hours":i["keep_alive_battery_kwh"]/0.4,"required_battery_kwh":0.4*354,
            "minimum_heating_gj":heating/1e9,"minimum_illumination_periods":heating/daily,
            "minimum_rover_kg_per_hour":239000/(14*24)}

def reliability(cfg, trials=100, seed=42):
    """Exploratory scenario ensemble, not a calibrated probability of mission success."""
    rng=random.Random(seed); results=[]
    for _ in range(trials):
        r=simulate(cfg,efficiency=rng.uniform(.20,.34)*(.9965**10),
                   illumination=rng.uniform(.55,1),conductivity=rng.uniform(.03,.07),
                   optical_factor=.996**10,aperture_open=False,cycles=1,dt=3600)
        results.append(r["min_night_kw"])
    results.sort()
    return {"trials":trials,"seed":seed,"scenario_min_kw":results[0],
            "scenario_median_min_kw":results[len(results)//2],
            "scenario_full_service_fraction":sum(x>=10-1e-8 for x in results)/trials,
            "warning":"Exploratory bounds, not empirically calibrated reliability."}

def main():
    cfg=json.loads(Path("parameter_lock.json").read_text(encoding="utf-8-sig"))
    cases={}
    for name,kw in {"baseline_open":{},"shutter_closed":{"aperture_open":False},
                    "low_efficiency":{"aperture_open":False,"efficiency":.25},
                    "shadowed":{"aperture_open":False,"illumination":.65},
                    "cold_start":{"initial_fraction":0,"aperture_open":False}}.items():
        r=simulate(cfg,**kw); r.pop("records"); cases[name]=r
    result={"status":"PRELIMINARY_NOT_VALIDATED","cases":cases,"commissioning":commissioning(cfg),
            "scenario_ensemble":reliability(cfg)}
    Path("r4_results.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__": main()
