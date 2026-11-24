# Running the branch on a teammate's laptop
Stop the original daemon safely (Ctrl+C in its terminal). Do not discard local edits. Check git status first. Then:
```
git fetch origin
git switch --track origin/manns-branch
python -m pip install -r requirements-r4.txt
python r4_run_all.py
```
If branch already exists locally use git switch manns-branch and git pull --ff-only origin manns-branch. Do not run legacy agents_pipeline.py as an R4 runner. The new runner records exact commit, time, job return codes and output in r4_runtime_status.json. A nonzero red-team status is expected until missing evidence is addressed. Review status before using generated artifacts. No laptop process is remotely started by committing to GitHub.
