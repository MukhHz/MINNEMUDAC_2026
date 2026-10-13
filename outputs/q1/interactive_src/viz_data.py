"""Prepare data for the Q1 interactive page (cross-county map, distance map, cutoff slider)."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import shapefile

ROOT = Path(r"C:\Users\eirfa\Documents\UW_Madison_Edu\MINNEMUDAC_2026")
PROC, LOCAL = ROOT / "Data" / "processed", ROOT / "Data" / "local"
METRICS = ["visits", "pounds", "individuals"]

# ------------------------------------------------------------------ projection (simple conic-ish for MN)
LAT0, LON0 = 46.3, -93.3
K = np.cos(np.radians(LAT0))
def proj(lon, lat):
    return (np.asarray(lon) - LON0) * K, -(np.asarray(lat) - LAT0)

r = shapefile.Reader(str(LOCAL / "county_shapes" / "cb_2023_us_county_500k"))
shapes = [(s.record["GEOID"], s.record["NAME"], s.shape) for s in r.iterShapeRecords() if s.record["STATEFP"] == "27"]
allx, ally = [], []
for _, _, sh in shapes:
    x, y = proj(*np.array(sh.points).T); allx += list(x); ally += list(y)
minx, maxx, miny, maxy = min(allx), max(allx), min(ally), max(ally)
W = 600.0
S = W / (maxx - minx)
H = (maxy - miny) * S
def px(lon, lat):
    x, y = proj(lon, lat)
    return (x - minx) * S, (y - miny) * S

counties = {}
for geoid, name, sh in shapes:
    pts = np.array(sh.points)
    parts = list(sh.parts) + [len(pts)]
    d = []
    for a, b in zip(parts[:-1], parts[1:]):
        x, y = px(pts[a:b, 0], pts[a:b, 1])
        keep = [0]
        for i in range(1, len(x)):   # drop points closer than 0.6 px to the previous kept point
            if abs(x[i] - x[keep[-1]]) + abs(y[i] - y[keep[-1]]) > 0.6:
                keep.append(i)
        if len(keep) < 3:
            continue
        d.append("M" + "L".join(f"{x[i]:.1f},{y[i]:.1f}" for i in keep) + "Z")
    bx, by = px(pts[:, 0], pts[:, 1])
    counties[geoid] = {"fips": geoid, "name": name, "path": "".join(d),
                       "bbox": [round(float(bx.min()), 1), round(float(by.min()), 1), round(float(bx.max()), 1), round(float(by.max()), 1)]}
print("counties:", len(counties), "| map size:", W, round(H, 1))

# ------------------------------------------------------------------ block groups + fixed food shelf sites (same rules as notebook 28a)
bg = pd.read_csv(LOCAL / "CenPop2020_Mean_BG27.txt", encoding="utf-8-sig", dtype=str)
bg = bg.assign(fips=bg.STATEFP + bg.COUNTYFP, population=bg.POPULATION.astype(int),
               lat=bg.LATITUDE.astype(float), lon=bg.LONGITUDE.astype(float))
org = pd.read_excel(ROOT / "Data" / "Organization.xlsx", usecols=["__ID", "block_geoid", "AgencySubType"])
site_all = pd.read_csv(PROC / "foodshelf_site_month.csv", dtype={"fips": str}, low_memory=False)
site_all = site_all[(site_all.site_group != "meal") & site_all.year.between(2022, 2024)]
sites = (site_all.groupby("site_id")
         .agg(fips=("fips", lambda x: x.mode().iat[0]),
              agency_type=("agency_type", lambda x: x.mode().iat[0] if x.notna().any() else None),
              visits=("visits", "sum"))
         .reset_index().merge(org, left_on="site_id", right_on="__ID", how="left", validate="one_to_one"))
sites["block"] = sites.block_geoid.map(lambda v: f"{int(v):015d}" if pd.notna(v) else None)
sites["block_fips"] = sites.block.str[:5]
xy = pd.read_csv(LOCAL / "foodshelf_block_coords.csv", dtype={"GEOID": str})
sites = sites.merge(xy, left_on="block", right_on="GEOID", how="left", validate="many_to_one")
FIXED = ["Food Shelf", "Brick and Mortar Site", "Tribal Program", "College Campus Program"]
loc = sites[sites.agency_type.isin(FIXED) & (sites.visits > 0) & sites.lat.notna() & (sites.block_fips == sites.fips)].reset_index(drop=True)
print("fixed sites used:", len(loc), "(notebook: 435)")

def miles(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(a))
dm = miles(bg.lat.values[:, None], bg.lon.values[:, None], loc.lat.values[None, :], loc.lon.values[None, :])
near = dm.argmin(axis=1)
bg["dist"] = dm[np.arange(len(bg)), near]
bg["near_fips"] = loc.block_fips.values[near]

# flows: share of each county's residents whose nearest fixed food shelf is in county X
fl = bg.groupby(["fips", "near_fips"]).population.sum()
fl = (fl / fl.groupby(level=0).transform("sum") * 100).rename("share").reset_index()
chk = fl[(fl.fips == "27103")]
print("Nicollet flows:", chk.round(1).values.tolist())

# geographic center of each county (area-weighted centroid of its largest polygon), used for labels and arrows
for geoid, name, sh in shapes:
    pts = np.array(sh.points); parts = list(sh.parts) + [len(pts)]
    best = None
    for a, b in zip(parts[:-1], parts[1:]):
        x, y = px(pts[a:b, 0], pts[a:b, 1])
        cr = x[:-1] * y[1:] - x[1:] * y[:-1]
        A = cr.sum() / 2
        if best is None or abs(A) > abs(best[0]):
            best = (A, ((x[:-1] + x[1:]) * cr).sum() / (6 * A), ((y[:-1] + y[1:]) * cr).sum() / (6 * A))
    counties[geoid]["cx"], counties[geoid]["cy"] = round(float(best[1]), 1), round(float(best[2]), 1)

# ------------------------------------------------------------------ county profiles
prof = pd.read_csv(PROC / "q1_county_profiles.csv", dtype={"fips": str})
prof["status"] = prof.direction.map({"lower than expected": "lower", "higher than expected": "higher"}).fillna("none")
prof.loc[prof.county == "Wilkin", "status"] = "nofs"
for _, p in prof.iterrows():
    c = counties[p.fips]
    c.update({
        "status": p.status, "shortlist": p.priority == "shortlist",
        "times": None if pd.isna(p.times_expected_all) else round(float(p.times_expected_all), 2),
        "other": round(float(p.pct_nearest_other_county), 0), "dist": round(float(p.mean_dist_mi), 1),
        "far": round(float(p.pct_over_10mi), 0),
        "sites10k": round(float(p.sites_per_10k), 2),
        "vps": None if pd.isna(p.visits_per_site_month) else round(float(p.visits_per_site_month), 0),
        "bank": "" if pd.isna(p.main_food_bank) else p.main_food_bank,
        "poverty": round(float(p.poverty_rate), 1),
        "mobile": bool(p.has_mobile) if pd.notna(p.has_mobile) else False,
        "mobilePct": 0 if pd.isna(p.pct_visits_mobile) else round(float(p.pct_visits_mobile), 0),
    })

FOCUS = list(prof.loc[prof.priority == "shortlist", "fips"]) + ["27167"]   # 12 shortlisted + Wilkin
flows = {}
for f in FOCUS:
    sub = fl[(fl.fips == f) & (fl.near_fips != f) & (fl.share >= 3)].sort_values("share", ascending=False)
    own = fl[(fl.fips == f) & (fl.near_fips == f)].share.sum()
    flows[f] = {"own": round(float(own), 0),
                "to": [{"fips": t, "share": round(float(s), 0)} for t, s in zip(sub.near_fips, sub.share)]}

# ------------------------------------------------------------------ dots
bgx, bgy = px(bg.lon.values, bg.lat.values)
band = np.select([bg.dist <= 5, bg.dist <= 10], [0, 1], 2)
bg_dots = [[round(float(a), 1), round(float(b), 1), int(c)] for a, b, c in zip(bgx, bgy, band)]
sx, sy = px(loc.lon.values, loc.lat.values)
mvis = loc.visits / 36.0
site_dots = [[round(float(a), 1), round(float(b), 1), round(float(v), 0)] for a, b, v in zip(sx, sy, mvis)]
print("residents in each distance band (%):",
      (bg.groupby(band).population.sum() / bg.population.sum() * 100).round(1).to_dict())

# ------------------------------------------------------------------ cutoff slider: re-run the shortlist rules at several cutoffs
yr = pd.read_csv(PROC / "q1_county_year_mismatch.csv", dtype={"fips": str})
yr = yr[yr.visits.notna()].copy()

def classify(h, l):
    if h >= 1 and l >= 1: return "changes"
    if h >= 2: return "ph"
    if l >= 2: return "pl"
    return "x"

def shortlist_at(T):
    rows = []
    for (f, cname), g in yr.groupby(["fips", "county"]):
        n_low = n_high = 0; agree = []; gaps = []
        for m in METRICS:
            gap, gb, gc = g[f"{m}_gap"], g[f"{m}_gap_B"], g[f"{m}_gap_C"]
            flag = np.select([gap >= T, gap <= -T], [1, -1], 0)
            low_c = g.incomplete.astype(bool) | ((m == "visits") & (g.typo_fixed_rows.fillna(0) > 0))
            high_c = g[f"{m}_share_suspect"].fillna(0) >= 0.20
            concern = ((flag == -1) & low_c) | ((flag == 1) & high_c)
            ch, cl = int(((flag == 1) & ~concern).sum()), int(((flag == -1) & ~concern).sum())
            h, l = int((flag == 1).sum()), int((flag == -1).sum())
            pat, pat_clean = classify(h, l), classify(ch, cl)
            gaps.append(gap.mean())
            if pat_clean in ("ph", "pl"):
                hb, lb = int((gb >= T).sum()), int((gb <= -T).sum())
                hc, lc = int((gc >= T).sum()), int((gc <= -T).sum())
                d = 1 if pat == "ph" else -1 if pat == "pl" else 0
                agree.append(1 + (hb >= 2) + (hc >= 2) if d == 1 else 1 + (lb >= 2) + (lc >= 2) if d == -1 else 0)
                if pat_clean == "pl": n_low += 1
                else: n_high += 1
        mean_gap = float(np.mean(gaps))
        if n_low and n_high: continue
        n = max(n_low, n_high)
        if n >= 2 and min(agree) >= 2 and abs(mean_gap) >= T:
            rows.append({"fips": f, "county": cname, "dir": "lower" if n_low else "higher", "times": round(2 ** mean_gap, 2)})
    return pd.DataFrame(rows)

CUTS = [1.5, 1.75, 2.0, 2.5, 3.0]
cutoffs = []
for t in CUTS:
    s = shortlist_at(np.log2(t))
    cutoffs.append({"t": t, "lower": s[s.dir == "lower"].sort_values("times").fips.tolist(),
                    "higher": s[s.dir == "higher"].sort_values("times", ascending=False).fips.tolist()})
    print(f"{t}x: {len(s)} ->", s.sort_values("times").county.tolist())
base = set(prof.loc[prof.priority == "shortlist", "fips"])
at2 = set(cutoffs[2]["lower"] + cutoffs[2]["higher"])
assert at2 == base, ("2x does not reproduce the notebook shortlist", at2 ^ base)
print("2x reproduces the notebook shortlist: OK")

out = {"W": W, "H": round(H, 1), "counties": list(counties.values()), "flows": flows, "focus": FOCUS,
       "bg": bg_dots, "sites": site_dots, "cutoffs": cutoffs}
Path(__file__).with_name("viz_data.json").write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
print("json KB:", round(len(json.dumps(out, separators=(",", ":"))) / 1024))
