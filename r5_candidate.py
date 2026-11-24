"""Candidate-specific conceptual CAD and illustrative structural load screening."""
import math
from pathlib import Path
from r5_engineering import geometry

def structure(d):
    from r4_truss_fem import solve
    import numpy as np
    g=geometry(d)
    # Assumed collector mass density, not a hardware mass estimate.
    head_mass=15*g['collector_per_module_m2']
    nodes=[(.54*math.cos(2*math.pi*j/3),.54*math.sin(2*math.pi*j/3),k) for k in range(13) for j in range(3)]
    bars=set()
    for k in range(13):
        for j in range(3):
            a=3*k+j;b=3*k+(j+1)%3
            bars.add(tuple(sorted((a,b))))
            if k<12:
                for x,y in ((a,a+3),(a,b+3),(b,a+3)):bars.add(tuple(sorted((x,y))))
    loads=np.zeros((39,3));loads[-3:,0]=head_mass*1.62*.1/3;loads[-3:,2]=-head_mass*1.62/3
    u,s,res=solve(nodes,sorted(bars),list(range(9)),loads,135e9,math.pi*(.028**2-.024**2))
    return dict(assumed_head_mass_kg=head_mass,max_displacement_m=float(np.max(np.linalg.norm(u,axis=1))),max_axial_stress_pa=float(max(abs(s))),residual_n=res,status='ILLUSTRATIVE_ONLY')

def cad(d,folder):
    from build123d import Cylinder, Box, Compound, Pos, Align, export_step
    g=geometry(d); D=g['diameter_m']*1000; side=math.sqrt(g['collector_per_module_m2'])*1000
    pitch=max(D+3000,side)+4000
    parts=[]
    for j in range(d['modules']):
        x=j*pitch
        core=Pos(x,0,0)*Cylinder(D/2,D,align=(Align.CENTER,Align.CENTER,Align.MIN))
        core.label=f'Module {j+1} gross regolith'
        tile=Pos(x,D+side,1500)*Box(side,side,50);tile.label=f'Collector {j+1} envelope'
        parts.extend([core,tile])
    path=Path(folder)/'R5_candidate_envelope.step'
    export_step(Compound(children=parts),str(path))
    return dict(path=str(path),modules=d['modules'],status='ENVELOPE_ONLY')
