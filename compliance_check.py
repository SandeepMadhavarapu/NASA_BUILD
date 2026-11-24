import os
import re
import sys
import zipfile
import zlib

BANNED_PATTERNS = [
    r"SandeepMadhavarapu",
    r"github\.com/",
    r"NASA_BUILD",
    r"@gmail\.com",
    r"@outlook\.com",
    r"\.edu\b",
]

def extract_searchable_text(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    with open(filepath, "rb") as f:
        data = f.read()

    chunks = [data.decode("utf-8", errors="ignore")]
    if ext == ".pdf":
        for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, flags=re.DOTALL):
            try:
                chunks.append(zlib.decompress(m.group(1)).decode("latin-1", errors="ignore"))
            except Exception:
                pass
    elif ext == ".docx" and zipfile.is_zipfile(filepath):
        with zipfile.ZipFile(filepath, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".xml"):
                    chunks.append(zf.read(name).decode("utf-8", errors="ignore"))
    return "\n".join(chunks)

def audit_file(filepath: str, extra_names=None):
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        sys.exit(1)

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Auditing: {filepath} ({size_mb:.2f} MB)")
    if size_mb > 6.0:
        print(f"  [FAIL] Exceeds 6.0 MB limit ({size_mb:.2f} MB)!")
    else:
        print("  [PASS] File size under 6.0 MB limit.")

    full_text = extract_searchable_text(filepath)
    patterns = list(BANNED_PATTERNS) + [re.escape(n) for n in (extra_names or []) if n]
    hits = []
    for pat in patterns:
        for m in re.finditer(pat, full_text, flags=re.IGNORECASE):
            hits.append(m.group(0))

    if hits:
        print(f"  [FAIL] Potential anonymity/identifying strings found: {sorted(set(hits))}")
    else:
        print("  [PASS] Zero banned identifying strings detected (including compressed streams & metadata).")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compliance_check.py <submission.pdf|docx|md> [TeammateName1] [SchoolName]")
        sys.exit(0)
    audit_file(sys.argv[1], sys.argv[2:])
