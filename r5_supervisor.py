"""Bounded local engineering supervisor. Never edits source or promotes designs."""
import hashlib
import itertools
import json
import math
import subprocess
import sys
from pathlib import Path
from r4_mission import mission

ROOT = Path(__file__).resolve().parent
REGULAR = ([1]*354+[0]*354)*3
LONG = [1]*708+[0]*708+[1]*354+[0]*354
BASE = dict(mass=125000, collector=100, pv_area=70)


def scenarios(design, holdout=False):
    c, p = design['collector'], design['pv_area']
    if holdout:
        return {'fragmented': (([1]*177+[0]*177)*6, {}),
                'long_night_first': ([0]*354+[1]*354+[0]*354, {}),
                'combined_holdout': (REGULAR, dict(collector=.75*c, pv_area=.8*p, peak_eta=.19, k=.065))}
    return {'nominal': (REGULAR, {}), 'long': (LONG, {}),
            'optical': (REGULAR, dict(collector=.8*c)),
            'pv': (REGULAR, dict(pv_area=.7*p)),
            'tpv': (REGULAR, dict(peak_eta=.2)),
            'shutter': (REGULAR, dict(shutter_leak=1)),
            'insulation': (REGULAR, dict(k=.07)),
            'partial': (REGULAR, dict(initial_fraction=.5)),
            'combined': (REGULAR, dict(collector=.8*c, pv_area=.7*p, peak_eta=.2, k=.07))}


def screen(design, solver=mission, holdout=False):
    results = {}
    for name, (timeline, fault) in scenarios(design, holdout).items():
        r = solver(timeline, **(design | fault))
        fields = ('minimum_bus_kw','unserved_kwh','relative_energy_residual')
        if not all(math.isfinite(r[k]) for k in fields) or r['relative_energy_residual'] > 1e-9 or r['relative_energy_residual'] < 0 or r['unserved_kwh'] < -1e-6 or not 0 <= r['minimum_bus_kw'] <= 10.5+1e-8:
            raise ValueError('Invalid numerical result: '+name)
        results[name] = {**r, 'pass': r['minimum_bus_kw'] >= 10.5-1e-8 and r['unserved_kwh'] <= 1e-6}
    return results


def improves(candidate, baseline):
    if candidate.keys() != baseline.keys():
        return False
    return all(candidate[k]['unserved_kwh'] <= baseline[k]['unserved_kwh']+1e-6 and candidate[k]['minimum_bus_kw'] >= baseline[k]['minimum_bus_kw']-1e-8 for k in baseline) and any(candidate[k]['unserved_kwh'] < baseline[k]['unserved_kwh']-1e-6 or candidate[k]['minimum_bus_kw'] > baseline[k]['minimum_bus_kw']+1e-8 for k in baseline)


def choose(solver=mission):
    baseline=screen(BASE, solver)
    candidates=[]
    for mass, collector in itertools.product((125000,175000,250000,350000),(100,150,200)):
        design=BASE | dict(mass=mass,collector=collector)
        r=screen(design,solver)
        candidates.append({'design':design,'cases':r,'improves':improves(r,baseline),'all_pass':all(x['pass'] for x in r.values())})
    eligible=sorted((x for x in candidates if x['improves'] and x['all_pass']),key=lambda x:(x['design']['mass'],x['design']['collector']))
    # Holdout is a rejection gate, not used to retune the candidate.
    selected=eligible[0] if eligible else None
    holdout=screen(selected['design'],solver,True) if selected else None
    return {'baseline':baseline,'candidates':candidates,'selected':selected,'holdout':holdout,'screen_pass':bool(holdout and all(x['pass'] for x in holdout.values()))}


def run_job(args, timeout=900):
    p=subprocess.run([sys.executable,*args],cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    return {'job':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}


def main():
    report={'status':'STOPPED_REVIEW_REQUIRED','jobs':[],'limitations':'Synthetic screening; no code edits, automatic adoption, site validation or flight certification.'}
    path=ROOT/'r5_supervisor_report.json'
    try:
        for args in [['-m','unittest','-v','test_r4','test_r4_advanced','test_r5_supervisor'],['r4_physics.py'],['r4_optimizer.py'],['r4_mission.py'],['r4_truss_fem.py'],['r4_candidate_cad.py'],['r4_build_review.py'],['r4_redteam.py'],['r5_reliability.py']]:
            job=run_job(args); report['jobs'].append(job)
            expected={'r4_redteam.py':{0,1},'r5_reliability.py':{0,2}}.get(args[0],{0})
            if job['exit'] not in expected or (job['exit'] and json.loads(job['stdout']).get('status')!='BLOCKED'):
                raise RuntimeError('Unexpected job failure: '+str(args))
        report['trade']=choose()
        req=json.loads((ROOT/'r5_requirements.json').read_text(encoding='utf-8'))
        report['open_requirements']=[x['id'] for x in req if x['status']!='VERIFIED' or not x.get('evidence')]
        report['input_hashes']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('r4_mission.py','r5_supervisor.py','r5_requirements.json','r5_reliability.py')}
        report['reason']='Candidate and evidence require human validation; never automatically promoted.'
    except Exception as exc:
        report['status']='STOPPED_ERROR'; report['reason']=repr(exc)
    finally:
        path.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(report['status'], report['reason'], '\nReport:',path)
    return 1 if report['status']=='STOPPED_ERROR' else 2

if __name__=='__main__':
    raise SystemExit(main())
