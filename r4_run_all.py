"""Run development jobs with individual status and fail closed. No git pull or merge."""
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime,timezone

def main():
    branch=subprocess.check_output(["git","branch","--show-current"],text=True).strip()
    if branch!="manns-branch":raise SystemExit("Run only on manns-branch")
    sha=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
    jobs=[("-m","unittest","-v","test_r4","test_r4_advanced"),("r4_physics.py",),("r4_optimizer.py",),("r4_mission.py",),("r4_truss_fem.py",),("r4_candidate_cad.py",),("r4_build_review.py",),("r4_redteam.py",)]
    status={"commit":sha,"branch":branch,"utc":datetime.now(timezone.utc).isoformat(),"jobs":[]}
    for job in jobs:
        try:
            p=subprocess.run([sys.executable,*job],timeout=900,capture_output=True,text=True)
            item={"job":list(job),"exit":p.returncode,"stdout":p.stdout[-10000:],"stderr":p.stderr[-10000:]}
        except subprocess.TimeoutExpired:item={"job":list(job),"exit":124}
        status["jobs"].append(item)
        Path("r4_runtime_status.json").write_text(json.dumps(status,indent=2))
        print(job,item["exit"],flush=True)
    return int(any(j["exit"] for j in status["jobs"]))
if __name__=="__main__":raise SystemExit(main())
