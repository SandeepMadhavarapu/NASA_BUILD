"""R5.1 screening agents: assumptions are exploratory, not qualified material data."""
import math
from itertools import product

SIGMA=5.670374419e-8
BASE=dict(mass=125000, collector=100, pv_area=70, modules=1, solid=False, shutter_backup=False)

def geometry(d):
    m=d['mass']/d['modules']; diameter=(4*m/(math.pi*2600))**(1/3)
    return dict(diameter_m=diameter, height_m=diameter, collector_per_module_m2=d['collector']/d['modules'],
                insulation_area_m2=d['modules']*1.5*math.pi*diameter**2,
                berm_kg=d['modules']*math.pi*((diameter/2+1.5)**2-(diameter/2)**2)*diameter*1600)

def construction(d):
    g=geometry(d); mass=d['mass']+g['berm_kg']
    return dict(local_material_kg=mass, active_days_at_2000kg_per_day=mass/2000,
                ideal_processing_kwh=d['mass']*1000*(1400-250)/3600000 if d['solid'] else 0,
                note='Assumed productivity; excludes travel, downtime, equipment and processing losses.')

def thermal(d, timeline, dt=1800, fault=None, cold=False):
    fault=fault or {}; g=geometry(d); m=d['mass']; cp=1000 if d['solid'] else 1400
    lo,hi=(1000,1400) if d['solid'] else (1250,1660)
    latent=0 if d['solid'] else 161200*m
    melt=m*cp*(1435-lo); cap=m*cp*(hi-lo)+latent
    floor=m*cp*(150-lo); E=floor if cold else cap
    start=E; solar=loss=draw=spill=short=0.; minimum=10.5
    for sun in timeline:
        if not 0<=sun<=1: raise ValueError('invalid sunlight')
        t=lo+E/(m*cp) if not latent or E<melt else 1435 if E<melt+latent else 1435+(E-melt-latent)/(m*cp)
        eta=.25*fault.get('eta_factor',1)*(.75+.25*max(0,min(1,(t-lo)/(hi-lo))))*.975
        incoming=d['collector']*1365*.84*sun*fault.get('optical',1)*dt
        pv=d['pv_area']*1365*.28*.8*sun*fault.get('pv',1)/1000
        leak=.01
        if fault.get('shutter'): leak=.05 if d['shutter_backup'] else 1
        if fault.get('common_shutter'): leak=1
        qloss=(.045*fault.get('insulation',1)*g['insulation_area_m2']*(t-150)/1.5+SIGMA*math.pi*.24**2*d['modules']*(t**4-150**4)*(leak+(1-leak)*sun))*dt
        available=E+incoming; qloss=min(max(0,qloss),max(0,available-floor)); available-=qloss
        # Thin-slab conduction bound: assumed conductivity and 100 K gradient, not a spatial solver.
        k=.6 if d['solid'] else .15
        area=m/2600/.10
        conduct=k*area*100/.05*dt
        radiate=.95*.8*3*d['modules']*SIGMA*max(0,t**4-300**4)*dt
        q=min(max(0,10.5-pv)*1000*dt/eta,max(0,available),conduct,radiate)
        raw=available-q; excess=max(0,raw-cap); E=raw-excess
        delivered=min(10.5,pv+q*eta/dt/1000)
        minimum=min(minimum,delivered); short+=(10.5-delivered)*dt/3600
        solar+=incoming;loss+=qloss;draw+=q;spill+=excess
    residual=abs(start+solar-loss-draw-spill-E)/max(1,abs(start)+solar)
    if not all(math.isfinite(x) for x in (residual,short,E)) or residual>1e-9 or not floor-1<=E<=cap+1: raise ValueError('energy ledger failed')
    return dict(minimum_kw=minimum,unserved_kwh=short,residual=residual,final_usable_fraction=max(0,E)/cap)

def evaluate(d, dt=1800):
    steps=int(354*3600/dt); regular=([1]*steps+[0]*steps)*3
    cases={'nominal':(regular,{},False),'long':([1]*steps*2+[0]*steps*2,{},False),
           'shutter':(regular,{'shutter':True},False),'common_shutter':(regular,{'common_shutter':True},False),
           'combined':(regular,{'optical':.8,'eta_factor':.8,'pv':.7,'insulation':1.55},False),
           'cold_start':(regular,{},True)}
    return {name:thermal(d,t,dt,f,c) for name,(t,f,c) in cases.items()}

def search():
    baseline=evaluate(BASE); rows=[]
    for m,a,n,s,b in product((125000,175000,250000),(100,150),(1,4),(False,True),(False,True)):
        d=BASE|dict(mass=m,collector=a,modules=n,solid=s,shutter_backup=b)
        r=evaluate(d); worst=max(x['unserved_kwh'] for x in r.values())
        nonregression=all(r[k]['unserved_kwh']<=baseline[k]['unserved_kwh']+1e-6 for k in r)
        rows.append(dict(design=d,cases=r,worst_kwh=worst,nonregression=nonregression,construction=construction(d)))
    eligible=[r for r in rows if r['nonregression'] and r['worst_kwh']<max(x['unserved_kwh'] for x in baseline.values())-1e-6]
    best=min(eligible,key=lambda r:(r['worst_kwh'],r['construction']['local_material_kg'],r['design']['collector'])) if eligible else None
    return dict(baseline=baseline,candidates=rows,selected=best,status='REVIEW_REQUIRED')
