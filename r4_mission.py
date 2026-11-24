"""Chronological lunar power screening. Requires actual visibility CSV for site claims.
Synthetic schedules are stress tests, not lunar ephemeris. SI units internally."""
import csv
import json
import math
import argparse
from pathlib import Path
from datetime import datetime

SIGMA=5.670374419e-8

def mission(visibility,dt=3600,mass=125000,collector=100,pv_area=70,peak_eta=.25,
            load_kw=10,aux_kw=.5,initial_fraction=1,shutter_leak=.01,k=.045):
    if not 0<=initial_fraction<=1 or dt<=0 or mass<=0 or collector<0 or not 0<peak_eta<=1: raise ValueError("invalid inputs")
    lo,hi,mel,cp,latent=1250,1660,1435,1400,161200*mass
    em=mass*cp*(mel-lo);cap=mass*cp*(hi-lo)+latent
    area=1.5*math.pi*(4*mass/(math.pi*2600))**(2/3)
    energy=cap*initial_fraction;start=energy
    received=losses=drawn=spill=0.;unserved=0.;powers=[];temps=[]
    for sunlight in visibility:
        if not 0<=sunlight<=1: raise ValueError("visibility must be 0..1")
        t=lo+energy/(mass*cp) if energy<em else mel if energy<em+latent else mel+(energy-em-latent)/(mass*cp)
        t=max(150,t)
        eta=peak_eta*(.75+.25*max(0,min(1,(t-lo)/(hi-lo))))*.975
        # PV independent of thermal optics, assumed tracking and system derating.
        pv=pv_area*1365*.28*.8*sunlight/1000
        demand=load_kw+aux_kw
        qsolar=collector*1365*.84*sunlight*dt
        qloss=(k*area*(t-150)/1.5+SIGMA*math.pi*.24**2*(t**4-150**4)*(shutter_leak+(1-shutter_leak)*sunlight))*dt
        avail=energy+qsolar
        loss=min(max(0,qloss),max(0,avail+mass*cp*(lo-150)))
        avail-=loss
        need=max(0,demand-pv)
        thermal_limit=.95*.8*3*SIGMA*max(0,t**4-300**4)*dt
        draw=min(need*1000*dt/eta,thermal_limit,max(0,avail))
        raw=avail-draw;curtail=max(0,raw-cap);energy=raw-curtail
        delivered=min(demand,pv+draw*eta/dt/1000)
        powers.append(delivered);temps.append(t)
        unserved+=(demand-delivered)*dt/3600
        received+=qsolar;losses+=loss;drawn+=draw;spill+=curtail
    if not powers:raise ValueError("empty timeline")
    return {"minimum_bus_kw":min(powers),"mean_bus_kw":sum(powers)/len(powers),"demand_kw":load_kw+aux_kw,"unserved_kwh":unserved,"service_fraction":sum(x>=load_kw+aux_kw-1e-8 for x in powers)/len(powers),"relative_energy_residual":abs(start+received-losses-drawn-spill-energy)/max(1,start+received),"final_storage_fraction":energy/cap}

def load_site(path):
    rows=list(csv.DictReader(open(path,encoding="utf-8")))
    if len(rows)<2:raise ValueError("need timestamped samples")
    ts=[datetime.fromisoformat(x["utc"].replace("Z","+00:00")) for x in rows]
    if any(t.tzinfo is None for t in ts):raise ValueError("UTC offsets required")
    dt=(ts[1]-ts[0]).total_seconds()
    if dt<=0 or any((b-a).total_seconds()!=dt for a,b in zip(ts,ts[1:])):raise ValueError("timestamps must be uniform and increasing")
    return [float(x["visible"]) for x in rows],dt

def main():
    p=argparse.ArgumentParser();p.add_argument("--site");a=p.parse_args()
    if a.site:
        v,dt=load_site(a.site);result={"status":"USER_DATA_PROVENANCE_UNVERIFIED","result":mission(v,dt)}
    else:
        # Equal illumination fraction can conceal much longer uninterrupted outages.
        schedules={"regular":([1]*354+[0]*354)*3,"fragmented":([1]*177+[0]*177)*6,"long_outage":([1]*708+[0]*708)+[1]*354+[0]*354,"derated":([.8]*354+[0]*354)*3}
        result={"status":"SYNTHETIC_STRESS_TEST_ONLY","results":{k:mission(v) for k,v in schedules.items()}}
    Path("r4_mission_results.json").write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=="__main__":main()
