"""Independent R4 engineering gates. Never treats a missing result as a pass."""
import ast
import json
import math
from pathlib import Path
from r4_physics import simulate, commissioning

def audit(cfg):
    i=cfg["inputs"]; c=cfg["computed"]; findings=[]
    def gate(name,passed,detail):
        findings.append(dict(gate=name,status="PASS" if passed else "BLOCK",detail=detail))
    # Agent 1: numerical closure and adversarial tests
    base=simulate(cfg)
    gate("thermal energy conservation",base["relative_balance_error"]<1e-9,base["relative_balance_error"])
    gate("uninterrupted 10 kW",base["min_night_kw"]>=10-1e-8,base["min_night_kw"])
    # Agent 2: analytical CAD volume/mass cross-check (not collision analysis)
    r=c["core_diameter_m"]/2; h=c["core_height_m"]
    gross=math.pi*r*r*h
    # CAD uses 20 mm thick radial fins and 18 mm thick concentric rings.
    fin_volume=i["radial_fin_count"]*(r-.160)*.020*(h-.200)
    ring_volume=sum(math.pi*((r*j/(i["concentric_ring_count"]+.6)+.018)**2-(r*j/(i["concentric_ring_count"]+.6))**2)*(h-.280) for j in range(1,i["concentric_ring_count"]+1))
    gate("CAD material mass reconciliation",False,{"gross_core_m3":gross,"fin_volume_m3":fin_volume,"ring_volume_m3":ring_volume,"note":"overlaps and liner require full solid union; stowed envelope and collision checks pending"})
    # Agent 6: analytical bounds, explicitly not FEA
    R=.028; wall=.004; E=135e9; I=math.pi/4*(R**4-(R-wall)**4)
    local=math.pi**2*E*I/1.0**2
    load=65*9.81*4.5
    gate("structural finite element validation",False,{"single_1m_member_pinned_buckling_n":local,"head_axial_load_n":load,"note":"load paths, stowed geometry, local/global buckling and thermal stresses require solver"})
    # Agent 9: independently check arithmetic and commissioning
    com=commissioning(cfg)
    gate("startup battery",com["battery_hours"]>=354,com)
    gate("mass budget arithmetic",abs(sum(cfg["mass_budget_kg"].values())-c["earth_launched_mass_kg"])<1e-8,sum(cfg["mass_budget_kg"].values()))
    # Agent 10: evidence manifest; no invented citations
    gate("research provenance",False,"No verified temperature-dependent TPV, regolith properties, optical efficiency, degradation distributions or site illumination datasets attached.")
    # Agent 12: environment and deployment
    gate("deployment and site validation",False,"No site horizon profile, rover traction/productivity or cold-start demonstration.")
    gate("molten core containment",False,"No refractory compatibility, creep, melt leakage or cycle-life data.")
    gate("heat pipe eligibility",False,"Obtain written challenge ruling on sealed working-fluid components.")
    return findings

def main():
    cfg=json.loads(Path("parameter_lock.json").read_text(encoding="utf-8-sig"))
    findings=audit(cfg)
    out={"status":"BLOCKED" if any(f["status"]=="BLOCK" for f in findings) else "PASS","findings":findings}
    Path("r4_gate_report.json").write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
    return 1 if out["status"]=="BLOCKED" else 0
if __name__=="__main__": raise SystemExit(main())
