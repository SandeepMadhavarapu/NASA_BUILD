"""Audit STEP geometry using build123d. Compound intersections require engineering review."""
import argparse
import json
from build123d import import_step

def audit(path):
    shape=import_step(path); solids=list(shape.solids()); bounds=shape.bounding_box()
    overlaps=[]
    for i,a in enumerate(solids):
        for j in range(i+1,len(solids)):
            b=solids[j]
            aa=a.bounding_box();bb=b.bounding_box()
            if any(getattr(aa.max,k)<=getattr(bb.min,k) or getattr(bb.max,k)<=getattr(aa.min,k) for k in ("X","Y","Z")):continue
            overlap=a.intersect(b)
            vol=0 if overlap is None else (sum(x.volume for x in overlap) if isinstance(overlap,list) else overlap.volume)
            if vol>1:overlaps.append([i,j,vol])
    return {"solids":len(solids),"sum_solid_volume_mm3":sum(s.volume for s in solids),"bounding_box_mm":[bounds.size.X,bounds.size.Y,bounds.size.Z],"intersections_over_1mm3":overlaps,"status":"geometry screening only; intentional joints and cutaways must be classified; no material mass without mapping"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("step");a=p.parse_args();print(json.dumps(audit(a.step),indent=2))
