"""Agent 13: deterministic reliability screen, not a calibrated mission probability.
Run on each revision. Never overwrites R4 parameters or certifies flight readiness."""
import hashlib
import json
import math
from pathlib import Path
from r4_mission import mission

def evaluate():
    regular=([1]*354+[0]*354)*3
    cases={
        "nominal":(regular,{}),
        "extended_darkness":([1]*708+[0]*708+[1]*354+[0]*354,{}),
        "optical_derating":(regular,{"collector":80}),
        "pv_derating":(regular,{"pv_area":49}),
        "tpv_derating":(regular,{"peak_eta":.20}),
        "shutter_stuck_open":(regular,{"shutter_leak":1}),
        "insulation_degraded":(regular,{"k":.07}),
        "partial_charge":(regular,{"initial_fraction":.5}),
        "combined_derating":(regular,{"collector":80,"pv_area":49,"peak_eta":.20,"k":.07}),
    }
    results={}
    for name,(schedule,kwargs) in cases.items():
        r=mission(schedule,**kwargs)
        ok=all(math.isfinite(v) for v in r.values()) and r["relative_energy_residual"]<1e-9 and r["unserved_kwh"]<1e-6 and r["minimum_bus_kw"]>=10.5-1e-8
        results[name]={"status":"PASS" if ok else "BLOCK",**r}
    evidence=json.loads(Path("r5_requirements.json").read_text(encoding="utf-8"))
    missing=[r["id"] for r in evidence if r["status"]!="VERIFIED"]
    hashes={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ("r4_mission.py","r5_requirements.json","r5_reliability.py")}
    return {"status":"BLOCKED" if missing or any(r["status"]!="PASS" for r in results.values()) else "SCREEN_PASS_NOT_FLIGHT_CERTIFICATION","cases":results,"open_requirements":missing,"input_sha256":hashes,"limitations":"Synthetic stress cases, not probability estimates. Full failure-mode and common-cause analysis still required."}

if __name__=="__main__":
    result=evaluate()
    Path("r5_reliability_report.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    raise SystemExit(2 if result["status"]=="BLOCKED" else 0)
