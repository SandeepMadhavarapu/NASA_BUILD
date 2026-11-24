"""Run R4 screening in dependency order. Never regenerates legacy deliverables."""
import subprocess
import sys

def main():
    for args in (["-m","unittest","-v","test_r4"],["r4_physics.py"],["r4_optimizer.py"]):
        subprocess.run([sys.executable,*args],check=True)
    return subprocess.run([sys.executable,"r4_redteam.py"]).returncode
if __name__=="__main__": raise SystemExit(main())
