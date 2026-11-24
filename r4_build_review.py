"""Build clearly marked internal review deliverables, not contest submission."""
import json
from pathlib import Path
import matplotlib.pyplot as plt
from fpdf import FPDF
from pptx import Presentation
from pptx.util import Inches,Pt

data=json.loads(Path("r4_extended_trade.json").read_text())
rows=data["rows"]
masses=sorted({r["mass"] for r in rows});areas=sorted({r["collector_m2"] for r in rows})
z=[[next(r["unserved_kwh"] for r in rows if r["mass"]==m and r["collector_m2"]==a) for a in areas] for m in masses]
fig,ax=plt.subplots(figsize=(8,5));im=ax.imshow(z,aspect="auto");ax.set_xticks(range(len(areas)),areas);ax.set_yticks(range(len(masses)),[m/1000 for m in masses]);ax.set(xlabel="Collector area (m2)",ylabel="Regolith mass (t)",title="R4 conditional screening: unmet nighttime energy");fig.colorbar(im,label="Unserved kWh / 3 nights");fig.tight_layout();fig.savefig("HELIOS_R4_Trade.png",dpi=180);plt.close(fig)
sections=[
("Candidate and assumptions","125 tonnes gross regolith; 100 m2 collector aperture; 25% peak TPV efficiency; 80% illumination; nighttime shutter. Three cycles with fully charged initial storage."),
("Conditional model outcome","22 of 25 explored configurations met the nighttime target in the simplified model. No verified daytime electrical supply, startup, hardware mass or site-specific data."),
("Outstanding evidence","Independent structural solver cross-check, heat transfer mesh convergence, containment testing, optical raytrace, site illumination, mass and deployment, regulatory review."),
("Decision","HOLD submission. Existing R3 artifacts are historical. This document is an internal review, not a competition paper.")]
pdf=FPDF();pdf.set_margins(20,20,20);pdf.add_page();pdf.set_font("Helvetica","B",18);pdf.set_x(pdf.l_margin);pdf.multi_cell(0,9,"HELIOS-R4 | INTERNAL REVIEW");pdf.set_font("Helvetica",size=11)
for title,body in sections:
    pdf.set_font("Helvetica","B",12);pdf.set_x(pdf.l_margin);pdf.multi_cell(0,7,title);pdf.set_font("Helvetica",size=11);pdf.set_x(pdf.l_margin);pdf.multi_cell(0,6,body);pdf.ln(2)
pdf.add_page();pdf.image("HELIOS_R4_Trade.png",x=20,y=25,w=170);pdf.output("HELIOS_R4_Internal_Review.pdf")
prs=Presentation()
for title,body in sections:
    slide=prs.slides.add_slide(prs.slide_layouts[1]);slide.shapes.title.text=title;slide.placeholders[1].text=body;slide.placeholders[1].text_frame.paragraphs[0].font.size=Pt(22)
slide=prs.slides.add_slide(prs.slide_layouts[5]);slide.shapes.title.text="Conditional trade study";slide.shapes.add_picture("HELIOS_R4_Trade.png",Inches(1.5),Inches(1.5),width=Inches(7))
prs.save("HELIOS_R4_Internal_Review.pptx")
