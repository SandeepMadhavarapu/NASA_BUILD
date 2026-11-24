"""Generate full conceptual storage envelope and segmented collector; not flight hardware."""
import math
from build123d import Cylinder, Box, Compound, Pos, Rot, Align, export_step, export_stl
MASS=125000; DENSITY=2600; AREA=100
D=(4*MASS/(math.pi*DENSITY))**(1/3)*1000
R=D/2
core=Cylinder(R,D,align=(Align.CENTER,Align.CENTER,Align.MIN))
core.label="Gross storage envelope, before fin displacement"
berm=Cylinder(R+1500,D,align=(Align.CENTER,Align.CENTER,Align.MIN))-core
berm.label="Side insulation envelope"
parts=[core,berm]
# Ten independent 10 m2 conceptual flat collector tiles, not an optical raytrace.
for j in range(10):
    tile=Pos(8000+(j%5)*3500, (j//5)*3500,1500)*Box(3162.278,3162.278,50)
    tile.label=f"Collector tile {j+1} gross aperture";parts.append(tile)
assembly=Compound(children=parts,label="R4 candidate envelopes")
export_step(assembly,"HELIOS_R4_Candidate_Envelope.step")
export_stl(assembly,"HELIOS_R4_Candidate_Envelope.stl")
print("Envelope exported; no packaging, optical or mass qualification.")
