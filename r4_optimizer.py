"""Agent 11: constrained screening optimization, not a flight mass optimum."""
import json
from pathlib import Path
from r4_physics import simulate

def optimize(cfg):
    rows=[]
    for mass in (59020,75000,100000,125000):
        for area in (33.03,45,60,80):
            r=simulate(cfg,mass=mass,dish_area=area,aperture_open=False,
                       efficiency=.25,illumination=.8,cycles=3,dt=3600)
            rows.append(dict(regolith_kg=mass,dish_m2=area,
                             min_kw=r["min_night_kw"],unserved_kwh=r["unserved_kwh"],
                             feasible=r["unserved_kwh"]<1e-6))
    return sorted(rows,key=lambda r:(not r["feasible"],r["unserved_kwh"],r["dish_m2"],r["regolith_kg"]))
if __name__=="__main__":
    cfg=json.loads(Path("parameter_lock.json").read_text(encoding="utf-8-sig"))
    Path("r4_trade_space.json").write_text(json.dumps(optimize(cfg),indent=2))
