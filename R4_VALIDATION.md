# HELIOS-R4 validation branch
This is a development branch, NOT a submission-ready design. Existing R3 PDF, PPTX, CAD and charts are historical artifacts. Do not submit them as R4.
 
## Run
```sh
python -m unittest -v test_r4
python r4_physics.py
python r4_optimizer.py
python r4_redteam.py
pip install pymupdf
python r4_pdf_gate.py HELIOS_R3_Phase1_Submission.pdf
```
The red-team gate intentionally exits nonzero when evidence is missing. All new physical modelling is preliminary and requires student review, measured material inputs and independent validation. No claim of flight readiness or mission reliability is authorized.

## Agent upgrade map
1. Physics: independent enthalpy model, unmet demand, energy ledger, temperature-dependent illustrative efficiency.
2. CAD: analytical geometry/mass cross-check; actual solids, material assignment, collision and stowed packaging still outstanding.
3. Plots: existing R3 plots historical; new results JSON supplies failure-aware data for future R4 plots.
4. Compliance: new PDF parser checks font, margins, page count, metadata and exits nonzero; human review required.
5. Rendering: existing render retained; separate complete geometry and cutaway needed.
6. Structures: independent local-member analytical bound; true finite-element model still outstanding.
7. Uncertainty: reproducible scenario ensemble, no unsupported probability claim.
8. Pitch: removed optimistic numeric defaults; legacy regeneration blocked by default.
9. Independent red team: fail-closed gates.
10. Provenance: evidence gate blocks missing material and technology sources; literature database not yet populated.
11. Optimization: 16 candidate storage/collector combinations, conditional service screening only.
12. Deployment: cold-start heating, battery and rover throughput lower bounds; site-specific illumination and traction model outstanding.

## Required evidence before merge / submission
- Source-backed TPV efficiency and power density versus emitter and cell temperature.
- Refractory containment and SiC compatibility across melt cycles.
- Actual lunar site illumination and optical geometry; PV derating and parasitic loads.
- Coupled spatial thermal solution and structural analysis, stowed launch load cases.
- Real rover throughput and safe commissioning, aperture shutter hardware.
- CAD volume/mass reconciliation, true assembly and stowed packaging.
- Written rule clarification, final PDF and visual inspection.
- Student authors must review code, results and AI disclosure; do not imply independent human verification until performed.

## Known model limitations
The R4 screening model uses an illustrative linear efficiency derating, lumped temperature, simple aperture emissivity and berm loss, fixed emitter area, uniform illumination factor and no daytime electrical load model. The optimization scales the idealized core surface area but does not recompute CAD or launched mass for candidate regolith masses. It ranks screening cases, not flight designs. No statistical distributions are calibrated to lunar field data.
