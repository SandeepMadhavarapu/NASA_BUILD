"""Linear 3D pin-jointed bar finite elements; deployed illustrative mast only.
No bending, joints, nonlinear buckling, stowed configuration or flight qualification."""
import numpy as np
import json
import math

def solve(nodes, bars, fixed, loads, E, A):
    nodes=np.asarray(nodes,float); K=np.zeros((nodes.size,nodes.size))
    for a,b in bars:
        d=nodes[b]-nodes[a]; L=np.linalg.norm(d); u=d/L
        B=np.r_[-u,u]; idx=np.r_[np.arange(3*a,3*a+3),np.arange(3*b,3*b+3)]
        K[np.ix_(idx,idx)]+=E*A/L*np.outer(B,B)
    free=np.setdiff1d(np.arange(nodes.size),fixed); F=np.asarray(loads,float).ravel()
    u=np.zeros(nodes.size); u[free]=np.linalg.solve(K[np.ix_(free,free)],F[free])
    stresses=[]
    for a,b in bars:
        d=nodes[b]-nodes[a]; L=np.linalg.norm(d)
        stresses.append(E*np.dot(u[3*b:3*b+3]-u[3*a:3*a+3],d/L)/L)
    return u.reshape(-1,3),np.array(stresses),float(np.linalg.norm((K@u-F)[free]))

def mast(bays=12):
    nodes=[(.54*math.cos(2*math.pi*j/3),.54*math.sin(2*math.pi*j/3),12*k/bays) for k in range(bays+1) for j in range(3)]
    bars=[]
    for k in range(bays+1):
        for j in range(3):
            a=3*k+j;b=3*k+(j+1)%3
            bars.append((a,b))
            if k<bays: bars.extend([(a,a+3),(a,b+3),(b,a+3)])
    bars=list(set(tuple(sorted(x)) for x in bars))
    F=np.zeros((len(nodes),3));F[-3:,0]=65*1.62*.1/3;F[-3:,2]=-65*1.62/3
    A=math.pi*(.028**2-.024**2)
    u,s,res=solve(nodes,bars,list(range(9)),F,135e9,A)
    return {"nodes":len(nodes),"elements":len(bars),"max_displacement_m":float(np.max(np.linalg.norm(u,axis=1))),"max_abs_axial_stress_pa":float(max(abs(s))),"free_dof_residual_n":res,"status":"illustrative deployed linear truss FEA only"}
if __name__=="__main__":print(json.dumps(mast(),indent=2))
