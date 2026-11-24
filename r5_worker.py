"""Resumable, bounded local worker. No automatic source edits or Git operations."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from itertools import product
from r5_engineering import BASE, evaluate, construction
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'r5_work'
FILES=('r5_engineering.py','r5_candidate.py','r5_worker.py','r5_requirements.json','test_r5_worker.py')
def save(path,obj):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf-8')
    os.replace(tmp,path)
def fingerprints():
    return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}
def candidates():
    return [BASE|dict(mass=m,collector=a,modules=n,solid=s,shutter_backup=b) for m,a,n,s,b in product((125000,175000,250000),(100,150),(1,4),(False,True),(False,True))]
def compare(d, baseline):
    r=evaluate(d)
    return dict(design=d,cases=r,construction=construction(d),worst_kwh=max(x['unserved_kwh'] for x in r.values()),nonregression=all(r[k]['unserved_kwh']<=baseline[k]['unserved_kwh']+1e-6 for k in baseline))
def convergence(d):
    a,b=evaluate(d,1800),evaluate(d,900)
    diffs={k:abs(a[k]['unserved_kwh']-b[k]['unserved_kwh']) for k in a}
    return dict(delta_kwh=diffs,pass_screen=all(v<=max(2,.005*max(a[k]['unserved_kwh'],b[k]['unserved_kwh'])) for k,v in diffs.items()))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reset',action='store_true');args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    lock=OUT/'worker.lock'
    try: fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError: print('Worker locked; check existing process before manually clearing lock.');return 1
    os.close(fd)
    state_path=OUT/'state.json'
    state={}
    try:
        hashes=fingerprints()
        if state_path.exists() and not args.reset:
            state=json.loads(state_path.read_text(encoding='utf-8'))
            if state['hashes']!=hashes: raise RuntimeError('Inputs changed; archive report and use --reset after review')
            if state['status']!='PAUSED': print(state['status']);return 2
        else:
            state=dict(status='PAUSED',hashes=hashes,baseline=evaluate(BASE),rows=[])
        test=subprocess.run([sys.executable,'-m','unittest','-v','test_r4','test_r4_advanced','test_r5_supervisor','test_r5_worker'],cwd=ROOT,capture_output=True,text=True,timeout=180)
        state['tests']=dict(exit=test.returncode,stdout=test.stdout,stderr=test.stderr)
        if test.returncode: raise RuntimeError('Regression tests failed')
        queue=candidates()
        for d in queue[len(state['rows']):]:
            if (OUT/'STOP').exists(): save(state_path,state);print('PAUSED');return 2
            state['rows'].append(compare(d,state['baseline']))
            save(state_path,state)
            print(f"Completed {len(state['rows'])}/{len(queue)}",flush=True)
        baseline_worst=max(x['unserved_kwh'] for x in state['baseline'].values())
        eligible=[x for x in state['rows'] if x['nonregression'] and x['worst_kwh']<baseline_worst-1e-6]
        best=min(eligible,key=lambda x:(x['worst_kwh'],x['construction']['local_material_kg'],x['design']['collector'])) if eligible else None
        state['selected']=best
        if best:
            d=best['design'];state['convergence']=convergence(d)
            if state['convergence']['pass_screen']:
                from r5_candidate import cad,structure
                state['structure']=structure(d);state['cad']=cad(d,OUT)
        state['open_requirements']=[x['id'] for x in json.loads((ROOT/'r5_requirements.json').read_text()) if x['status']!='VERIFIED' or not x.get('evidence')]
        state['status']='REVIEW_REQUIRED'
        state['limitations']='Exploratory lumped model; no flight validation, autonomous source changes or automatic promotion.'
        save(state_path,state);print('REVIEW_REQUIRED',state_path);return 2
    except Exception as exc:
        state['status']='ERROR';state['error']=repr(exc);save(state_path,state);print(state['error']);return 1
    finally: lock.unlink(missing_ok=True)
if __name__=='__main__':raise SystemExit(main())
