"""Strict PDF gate. Requires PyMuPDF; official rules must be confirmed separately."""
import argparse
import re
import sys
from pathlib import Path
import fitz

def check(path, names=()):
    issues=[]
    if Path(path).stat().st_size>6_000_000: issues.append("File exceeds conservative 6 MB threshold")
    with fitz.open(path) as doc:
        if not 7<=len(doc)<=9: issues.append("Expected 1 cover + 5–7 concept pages + 1 visual page; verify official rules")
        text=" ".join(p.get_text() for p in doc)
        if not text.strip(): issues.append("No extractable text")
        if "TEAM-ID-PENDING" in text: issues.append("Placeholder team ID")
        if not re.search(r"AI.{0,30}(disclosure|usage)",text,re.I): issues.append("AI disclosure not detected")
        for name in (*names,"SandeepMadhavarapu","NASA_BUILD"):
            if name and name.casefold() in (text+str(doc.metadata)).casefold(): issues.append("Identifying string: "+name)
        for idx,p in enumerate(doc):
            if idx==0 or idx==len(doc)-1: continue
            for b in p.get_text("dict")["blocks"]:
                for line in b.get("lines",[]):
                    for s in line["spans"]:
                        if not s["text"].strip(): continue
                        if s["size"]<10.99: issues.append(f"Page {idx+1}: text under 11 pt")
                        x0,y0,x1,y1=s["bbox"]
                        if min(x0,y0,p.rect.width-x1,p.rect.height-y1)<53.5: issues.append(f"Page {idx+1}: text inside 0.75 inch margin")
    return sorted(set(issues))

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("pdf");p.add_argument("--name",action="append",default=[]);a=p.parse_args()
    errors=check(a.pdf,a.name)
    print("\n".join(errors) if errors else "Automated checks passed; human visual and official-rule review still required.")
    sys.exit(bool(errors))
