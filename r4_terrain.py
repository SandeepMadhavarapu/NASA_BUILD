"""Terrain horizon and solar visibility from user-supplied LOLA DEM and ephemeris.
DEM must be a local projected metric grid; ephemeris azimuth clockwise from north.
No synthetic horizon is represented as measured lunar terrain."""
import numpy as np
import csv
import argparse
import json

def horizon(dem, row, col, spacing_m, mast_m=12, bins=360):
    if spacing_m<=0 or not np.isfinite(dem).all(): raise ValueError("invalid DEM")
    rr,cc=np.indices(dem.shape)
    north=(row-rr)*spacing_m; east=(cc-col)*spacing_m
    dist=np.hypot(north,east); mask=dist>0
    # Moon curvature correction, local spherical approximation.
    dz=dem-dem[row,col]-mast_m-dist**2/(2*1737400)
    az=(np.degrees(np.arctan2(east[mask],north[mask]))+360)%360
    el=np.degrees(np.arctan2(dz[mask],dist[mask]))
    idx=np.floor(az*bins/360).astype(int)
    h=np.full(bins,-90.0); np.maximum.at(h,idx,el)
    if np.any(h==-90): raise ValueError("DEM angular coverage insufficient")
    return h

def visibility(h,az,el):
    idx=np.floor((np.asarray(az)%360)*len(h)/360).astype(int)
    # Conservative full-disc visibility; solar angular radius approximately 0.27 deg.
    return np.asarray(el)>h[idx]+.27

def main():
    p=argparse.ArgumentParser();p.add_argument("dem");p.add_argument("ephemeris");p.add_argument("--row",type=int,required=True);p.add_argument("--col",type=int,required=True);p.add_argument("--spacing",type=float,required=True);p.add_argument("--mast",type=float,default=12);a=p.parse_args()
    h=horizon(np.load(a.dem),a.row,a.col,a.spacing,a.mast)
    rows=list(csv.DictReader(open(a.ephemeris)));v=visibility(h,[float(r["az_deg"]) for r in rows],[float(r["el_deg"]) for r in rows])
    with open("r4_site_visibility.csv","w",newline="") as f:
        w=csv.writer(f);w.writerow(["utc","visible"]);w.writerows((r["utc"],int(x)) for r,x in zip(rows,v))
    print(json.dumps({"samples":len(v),"visible_fraction":float(v.mean()),"warning":"Requires validated DEM projection, ephemeris cadence, terrain extent and provenance."}))
if __name__=="__main__":main()
