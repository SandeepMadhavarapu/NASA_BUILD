import os
import vtk
from PIL import Image, ImageDraw, ImageFont

def render_stl_view(stl_path: str, out_png: str, cam_pos, focal_pt, elev_deg=0):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(stl_path)
    reader.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    prop = actor.GetProperty()
    prop.SetColor(0.84, 0.89, 0.95)
    prop.SetMetallic(0.35)
    prop.SetRoughness(0.45)

    ren = vtk.vtkRenderer()
    ren.AddActor(actor)
    ren.SetBackground(0.06, 0.09, 0.16)

    light = vtk.vtkLight()
    light.SetPosition(25000, -15000, 30000)
    light.SetFocalPoint(0, 0, 4000)
    light.SetIntensity(1.15)
    ren.AddLight(light)

    cam = ren.GetActiveCamera()
    cam.SetPosition(*cam_pos)
    cam.SetFocalPoint(*focal_pt)
    cam.SetViewUp(0, 0, 1)
    ren.ResetCamera()
    cam.Zoom(1.18)

    ren_win = vtk.vtkRenderWindow()
    ren_win.SetOffScreenRendering(1)
    ren_win.SetSize(1200, 950)
    ren_win.AddRenderer(ren)
    ren_win.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(ren_win)
    w2i.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(out_png)
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()

def compose_master_plate():
    stl_file = "HELIOS_R3_Aerospace_Assembly.stl"
    if not os.path.exists(stl_file):
        print("[WARN] STL not found; skipping CAD render.")
        return

    render_stl_view(stl_file, "cad_iso.png", cam_pos=(22000, -22000, 14500), focal_pt=(0, 0, 5200))
    render_stl_view(stl_file, "cad_core.png", cam_pos=(7500, -7500, 4200), focal_pt=(0, 0, 2400))

    if not os.path.exists("HELIOS_R3_Visual_Aid_Plate.png"):
        return

    charts = Image.open("HELIOS_R3_Visual_Aid_Plate.png").convert("RGB")
    iso = Image.open("cad_iso.png").convert("RGB")
    core = Image.open("cad_core.png").convert("RGB")

    # Build a 3-column wide landscape plate: Left 2/3 = 4 Physics Plots, Right 1/3 = 2 Shaded 3D CAD Views
    cw, ch = charts.size
    cad_w = int(cw * 0.44)
    total_w = cw + cad_w
    canvas = Image.new("RGB", (total_w, ch), (255, 255, 255))
    canvas.paste(charts, (0, 0))

    half_h = (ch - 140) // 2
    iso_r = iso.resize((cad_w - 40, half_h - 35), Image.Resampling.LANCZOS)
    core_r = core.resize((cad_w - 40, half_h - 35), Image.Resampling.LANCZOS)

    canvas.paste(iso_r, (cw + 20, 110))
    canvas.paste(core_r, (cw + 20, 110 + half_h + 15))

    draw = ImageDraw.Draw(canvas)
    draw.text((cw + 25, 82), "E. HELIOS-R3 Multi-Body CAD (12m Mast + Heliostat)", fill=(15, 23, 42))
    draw.text((cw + 25, 97 + half_h), "F. Core Cutaway: 32-Fin SiC Matrix & 1-DOF Sleeve", fill=(15, 23, 42))

    canvas.save("HELIOS_R3_Master_Visual_Plate.png", dpi=(300, 300))
    print("Generated HELIOS_R3_Master_Visual_Plate.png (4 Physics Panels + 2 Shaded 3D CAD Renders).")

if __name__ == "__main__":
    compose_master_plate()
