"""Per-animal analysis: migrations, flyways, funnels, sea crossings, wintering areas, fates and distances.
Reads data/daily_<species>.csv, WORK/fix_<species>.csv.gz and the raw reference tables; writes data/animals.csv,
data/migrations.csv, data/sea_crossings.csv, WORK/analysis.json (used by 03_results.py) and data/winter_areas.geojson."""
import numpy as np, pandas as pd, geopandas as gpd, shapely
from shapely.geometry import Point, shape, mapping
from shapely.ops import unary_union
from common import *

SP = ["stork", "osprey", "cuckoo", "harrier"]
# land for the sea-crossing test: the union of Natural Earth 1:10m countries (islands included)
LAND = unary_union(gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson").geometry.values).buffer(0)
shapely.prepare(LAND)
cty = gpd.read_file(f"{GEO}/ne_50m_admin_0_countries.geojson")[["NAME_EN", "ADM0_A3", "CONTINENT", "geometry"]]
cty_tree = shapely.STRtree(cty.geometry.values)


def country(lon, lat):
    p = Point(lon, lat)
    hit = cty_tree.query(p, predicate="intersects")
    r = cty.iloc[hit[0]] if len(hit) else cty.iloc[cty_tree.nearest(p)]     # at sea or on the coast: nearest country
    name = r.NAME_EN
    if name == "France" and lon < -40:
        return "French Guiana", "South America"
    if name == "United States of America":
        name = "United States"
    return name, r.CONTINENT


# ---------------- reference data: population, stage, sex, fate
ref = {}
r = pd.read_csv(f"{RAW}/storks_flack_reference-data.csv")
popname = {"Germany": "SW Germany", "Spain": "Spain (Doñana)", "Greece": "Greece (Evros Delta)", "Russia": "Russia (Moscow)", "Tunisia": "Tunisia",
           "Armenia": "Armenia", "Uzbekistan": "Uzbekistan", "Poland": "Poland", "South Africa": "South Africa"}
for _, x in r.iterrows():
    ref[("stork", x["animal-id"])] = {"pop": popname[x["study-site"]], "stage": "juvenile", "sex": "",
                                      "dead": x["animal-death-comments"] == "confirmed dead", "fate_note": "confirmed dead" if x["animal-death-comments"] == "confirmed dead" else "",
                                      "tag_lon": x["deploy-on-longitude"], "tag_lat": x["deploy-on-latitude"], "displaced": False}
r = pd.read_csv(f"{RAW}/osprey_martell_reference-data.csv")
for aid, g in r.groupby("animal-id"):
    g = g.sort_values("deploy-on-date")
    x = g.iloc[0]
    site = x["study-site"]
    fl = re.search(r"\((\w+)\)", site).group(1)
    death = "; ".join(sorted(set(g["animal-death-comments"].dropna())))
    ref[("osprey", aid)] = {"pop": fl, "site": re.sub(r"\s*\(\w+\)", "", site), "stage": str(x["animal-life-stage"]).lower(), "sex": str(x["animal-sex"]).strip(),
                            "dead": bool(death), "fate_note": death, "tag_lon": x["deploy-on-longitude"], "tag_lat": x["deploy-on-latitude"], "displaced": False,
                            "comments": "; ".join(sorted(set(g["deployment-comments"].dropna())))[:400]}
r = pd.read_csv(f"{RAW}/cuckoo_rybachy_reference-data.csv")
for _, x in r.iterrows():
    disp = x["manipulation-type"] == "relocated"
    ref[("cuckoo", x["animal-id"])] = {"pop": "Displaced to Kazan" if disp else "Rybachy (control)", "stage": x["animal-life-stage"], "sex": str(x["animal-sex"]).strip(),
                                       "dead": False, "fate_note": "", "tag_lon": x["deploy-on-longitude"], "tag_lat": x["deploy-on-latitude"], "displaced": disp}
r = pd.read_csv(f"{RAW}/harrier_MH_ANTWERPEN-reference-data.csv")
for _, x in r[r["animal-taxon"] == "Circus aeruginosus"].iterrows():
    ref[("harrier", x["animal-id"])] = {"pop": "Antwerp, Belgium", "stage": x["animal-life-stage"], "sex": x["animal-sex"], "dead": False, "fate_note": "",
                                        "tag_lon": x["deploy-on-longitude"], "tag_lat": x["deploy-on-latitude"], "displaced": False, "nick": x["animal-nickname"]}

# ---------------- funnels (points every flyway map shows) and the radius that counts as passing through
FUNNELS = {"Gibraltar": (-5.6, 35.95), "Bosporus": (29.05, 41.1), "Dardanelles": (26.45, 40.2), "Suez and Sinai": (32.6, 30.2), "Sicily channel": (11.3, 37.3),
           "Florida Keys and Cuba": (-81.2, 23.6), "Isthmus of Tehuantepec": (-94.9, 16.9)}
FUN_R = 75.0


def gc_samples(lon1, lat1, lon2, lat2, step=5.0):
    """Points every ~step km along the great circle (vectorised for one segment)."""
    d = float(hav(lon1, lat1, lon2, lat2))
    n = max(2, int(d / step) + 1)
    f = np.linspace(0, 1, n)
    la1, lo1, la2, lo2 = map(np.radians, (lat1, lon1, lat2, lon2))
    D = d / R_EARTH
    if D < 1e-9:
        return np.array([lon1]), np.array([lat1]), d
    A = np.sin((1 - f) * D) / np.sin(D); B = np.sin(f * D) / np.sin(D)
    x = A * np.cos(la1) * np.cos(lo1) + B * np.cos(la2) * np.cos(lo2)
    y = A * np.cos(la1) * np.sin(lo1) + B * np.cos(la2) * np.sin(lo2)
    z = A * np.sin(la1) + B * np.sin(la2)
    return np.degrees(np.arctan2(y, x)), np.degrees(np.arctan2(z, np.hypot(x, y))), d


MAXGAP_H = {"stork": 1, "harrier": 1, "osprey": 24, "cuckoo": 72}


def sea_crossings_gps(fx, sp):
    """GPS species, 10-minute tracks: runs of consecutive fixes over open sea, from the last fix on land to the first
    fix back on land, with no gap over MAXGAP_H inside the run."""
    out = []
    onl = shapely.contains_xy(LAND, fx.lon.to_numpy(), fx.lat.to_numpy())
    fx = fx.assign(onl=onl)
    for aid, g in fx.groupby("animal", sort=False):
        lon, lat, on = g.lon.to_numpy(), g.lat.to_numpy(), g.onl.to_numpy()
        th = (g.t - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy() / 3600
        seg = np.r_[0, hav(lon[:-1], lat[:-1], lon[1:], lat[1:])]
        i, n = 1, len(g)
        while i < n:
            if on[i] or not on[i - 1]:
                i += 1
                continue
            j = i                                   # i-1 on land, i at sea: walk to the next fix on land
            while j < n and not on[j]:
                j += 1
            if j >= n:
                break
            km = float(seg[i:j + 1].sum())
            ok = (np.diff(th[i - 1:j + 1]) <= MAXGAP_H[sp]).all()
            if ok and km >= 20:
                out.append({"species": sp, "animal": aid, "km": round(km, 1), "hours": round(float(th[j] - th[i - 1]), 1),
                            "lon0": round(float(lon[i - 1]), 3), "lat0": round(float(lat[i - 1]), 3), "lon1": round(float(lon[j]), 3), "lat1": round(float(lat[j]), 3),
                            "date": str(g.t.iloc[i - 1].date())})
            i = j + 1
    return out


def sea_crossings(fx, sp):
    """Longest runs of open sea along straight lines between consecutive clean fixes (gap <= MAXGAP_H).
    A crossing starts and ends on land; a run that touches a longer gap is not counted."""
    out = []
    for aid, g in fx.groupby("animal", sort=False):
        lon, lat = g.lon.to_numpy(), g.lat.to_numpy()
        th = (g.t - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy() / 3600
        run = 0.0; run_ok = True; start = None; t0 = None
        prev_land = bool(LAND.contains(Point(lon[0], lat[0]))) if len(g) else True
        for i in range(1, len(g)):
            dt = th[i] - th[i - 1]
            sx, sy, d = gc_samples(lon[i - 1], lat[i - 1], lon[i], lat[i])
            if d < 2:
                continue
            onl = shapely.contains_xy(LAND, sx, sy)
            seg = d / max(1, len(sx) - 1)
            for j in range(1, len(sx)):
                if not onl[j]:
                    if run == 0:
                        start = (float(sx[j - 1]), float(sy[j - 1])); t0 = g.t.iloc[i - 1]; run_ok = True
                    run += seg
                    if dt > MAXGAP_H[sp]:
                        run_ok = False
                else:
                    if run > 0:
                        if run_ok and run >= 20:
                            out.append({"species": sp, "animal": aid, "km": round(run, 1), "hours": round(float(th[i] - (t0 - pd.Timestamp("1970-01-01")).total_seconds() / 3600), 1), "lon0": round(start[0], 3), "lat0": round(start[1], 3),
                                        "lon1": round(float(sx[j]), 3), "lat1": round(float(sy[j]), 3), "date": str(t0.date())})
                        run = 0.0
    return out


def anchor(d, m0, d0, m1, d1, year, min_days=10):
    """Median position of daily fixes between (year, m0, d0) and (year or year+1, m1, d1)."""
    a = pd.Timestamp(year, m0, d0); b = pd.Timestamp(year + (1 if (m1, d1) < (m0, d0) else 0), m1, d1)
    w = d[(d.day >= a) & (d.day <= b)]
    if len(w) < min_days:
        return None
    return float(w.lon.median()), float(w.lat.median()), len(w)


def sea_share(fx, sp):
    """Share of the distance between consecutive fixes (gap <= MAXGAP_H) whose midpoint lies over open sea."""
    tot = sea = 0.0
    for aid, g in fx.groupby("animal", sort=False):
        lon, lat = g.lon.to_numpy(), g.lat.to_numpy()
        th = (g.t - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy() / 3600
        ok = np.diff(th) <= MAXGAP_H[sp]
        d = hav(lon[:-1], lat[:-1], lon[1:], lat[1:])[ok]
        mx, my = ((lon[:-1] + lon[1:]) / 2)[ok], ((lat[:-1] + lat[1:]) / 2)[ok]
        at_sea = ~shapely.contains_xy(LAND, mx, my)
        tot += d.sum(); sea += d[at_sea].sum()
    return {"km": round(float(tot), 1), "sea_km": round(float(sea), 1), "pct": round(100 * float(sea) / float(tot), 2)}


A_ROWS, M_ROWS, SEA = [], [], []
SHARE = {}
DAILY = {}
for sp in SP:
    dd = pd.read_csv(f"{DATA}/daily_{sp}.csv", parse_dates=["day"])
    dd["animal"] = dd.animal.astype(str)
    fx = pd.read_csv(f"{WORK}/fix_{sp}.csv.gz", parse_dates=["t"])
    fx["animal"] = fx.animal.astype(str)
    if sp in ("stork", "harrier"):
        f10 = pd.read_csv(f"{WORK}/fix10_{sp}.csv.gz", parse_dates=["t"])
        f10["animal"] = f10.animal.astype(str)
        SEA += sea_crossings_gps(f10, sp)
        SHARE[sp] = sea_share(f10, sp)
    else:
        SEA += sea_crossings(fx, sp)
        SHARE[sp] = sea_share(fx, sp)
    # hourly path length for GPS species (to compare with the daily path)
    hpath = {}
    if sp in ("stork", "harrier"):
        for aid, g in fx.groupby("animal"):
            hpath[aid] = float(hav(g.lon.values[:-1], g.lat.values[:-1], g.lon.values[1:], g.lat.values[1:]).sum())
    for aid, d in dd.groupby("animal"):
        d = d.sort_values("day").reset_index(drop=True)
        DAILY[(sp, aid)] = d
        info = ref.get((sp, aid), {})
        gap = d.day.diff().dt.days.to_numpy()
        step = np.r_[np.nan, hav(d.lon.values[:-1], d.lat.values[:-1], d.lon.values[1:], d.lat.values[1:])]
        d["step"] = step; d["gap"] = gap
        d["dth"] = np.r_[np.nan, np.diff((d.day - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy() / 3600 + d.hour.to_numpy())]
        # a day's flight: consecutive daily positions 18 to 30 hours apart, scaled to 24 hours
        one = d[(d.dth >= 18) & (d.dth <= 30)].assign(step=lambda x: x.step * 24 / x.dth)
        tlon, tlat = info.get("tag_lon"), info.get("tag_lat")
        if tlon is None or pd.isna(tlon):
            tlon, tlat = d.lon.iloc[0], d.lat.iloc[0]
        far = hav(tlon, tlat, d.lon.values, d.lat.values)
        # best 365-day window: summed daily steps (lower bound), needs a fix on at least 60% of days
        best_year = None
        if (d.day.iloc[-1] - d.day.iloc[0]).days >= 364:
            days = d.day.to_numpy()
            cs = np.r_[0, np.nancumsum(step[1:])]
            j = 0
            for i in range(len(d)):
                while j < len(d) and (days[j] - days[i]) / np.timedelta64(1, "D") <= 364:
                    j += 1
                if (days[j - 1] - days[i]) / np.timedelta64(1, "D") < 330:
                    continue
                cov = (j - i) / 365
                if cov < 0.6:
                    continue
                km = cs[j - 1] - cs[i]
                if best_year is None or km > best_year[0]:
                    best_year = (float(km), str(pd.Timestamp(days[i]).date()), round(cov, 2))
        last = d.iloc[-1]
        lc, lcont = country(last.lon, last.lat)
        row = {"species": sp, "animal": aid, "name": info.get("nick", ""), "population": info.get("pop", ""), "site": info.get("site", ""),
               "stage": info.get("stage", ""), "sex": info.get("sex", ""), "displaced": info.get("displaced", False),
               "first_day": str(d.day.iloc[0].date()), "last_day": str(last.day.date()), "span_days": int((last.day - d.day.iloc[0]).days) + 1,
               "days_with_fix": len(d), "path_km_daily": round(float(np.nansum(step)), 1), "path_km_hourly": round(hpath[aid], 1) if aid in hpath else None,
               "max_day_km": round(float(one.step.max()), 1) if len(one) else None, "max_from_tag_km": round(float(far.max()), 1),
               "tag_lon": float(tlon), "tag_lat": float(tlat), "last_lon": float(last.lon), "last_lat": float(last.lat), "last_country": lc, "last_continent": lcont,
               "confirmed_dead": bool(info.get("dead")), "fate_note": info.get("fate_note", ""),
               "best_year_km": round(best_year[0], 1) if best_year else None, "best_year_start": best_year[1] if best_year else None,
               "best_year_cover": best_year[2] if best_year else None}
        # funnels: closest approach of the hourly track (every clean fix for Argos)
        g = fx[fx.animal == aid]
        # gates: a fix on one side and a later fix on the other
        def first(mask):
            k = np.flatnonzero(mask.to_numpy())
            return g.t.iloc[k[0]] if len(k) else None
        iberia = first((g.lat > 36.05) & (g.lon > -10) & (g.lon < 3.5) & (g.lat < 44))
        morocco = first((g.lat < 35.9) & (g.lat > 20) & (g.lon < -1) & (g.lon > -17))
        thrace = first((g.lon > 19) & (g.lon < 29.0) & (g.lat > 40.6) & (g.lat < 48))
        anat = first(((g.lon > 29.1) & (g.lon < 44) & (g.lat > 36) & (g.lat < 41)) | ((g.lon > 26) & (g.lon <= 29.1) & (g.lat > 36) & (g.lat < 40.0)))
        levant = first((g.lat > 29) & (g.lat < 33.5) & (g.lon > 34) & (g.lon < 36.6))
        row["gate_gibraltar"] = bool(iberia is not None and morocco is not None and morocco > iberia)
        row["gate_turkish_straits"] = bool(thrace is not None and anat is not None and anat > thrace)
        row["gate_levant"] = bool(levant is not None)
        for fn, (flon, flat) in FUNNELS.items():
            row["near_" + fn] = round(float(hav(flon, flat, g.lon.values, g.lat.values).min()), 1)
        # winters (1 Dec to 31 Jan), any year
        winters = []
        for y in range(d.day.dt.year.min() - 1, d.day.dt.year.max() + 1):
            w = anchor(d, 12, 1, 1, 31, y)
            if w:
                c, cont = country(w[0], w[1])
                winters.append({"year": y, "lon": round(w[0], 3), "lat": round(w[1], 3), "n": w[2], "country": c, "continent": cont})
        row["winters"] = winters
        # migrations: autumn (summer anchor -> winter anchor) and spring (winter anchor -> next summer anchor)
        migs = []
        for y in range(d.day.dt.year.min() - 1, d.day.dt.year.max() + 1):
            s = anchor(d, 6, 1, 7, 31, y, 5)
            if s is None and y == d.day.dt.year.min() and d.day.iloc[0] <= pd.Timestamp(y, 8, 31) and d.day.iloc[0].month >= 5:
                s = (float(tlon), float(tlat), 0)      # tagged in summer: the tag site is the summer anchor
            w = anchor(d, 12, 1, 1, 31, y)
            s2 = anchor(d, 5, 15, 7, 15, y + 1, 5)
            for kind, A, B, t_from, rA, rB in (("autumn", s, w, pd.Timestamp(y, 6, 15), 100, 200), ("spring", w, s2, pd.Timestamp(y + 1, 1, 15), 200, 100)):
                if not A or not B:
                    continue
                straight = float(hav(A[0], A[1], B[0], B[1]))
                if straight < 500:
                    continue
                x = d[(d.day >= t_from) & (d.day <= t_from + pd.Timedelta(days=200))]
                dA = hav(A[0], A[1], x.lon.values, x.lat.values); dB = hav(B[0], B[1], x.lon.values, x.lat.values)
                arr = np.flatnonzero(dB < rB)
                if not len(arr):
                    continue
                ia = arr[0]
                dep = np.flatnonzero(dA[:ia] < rA)
                if not len(dep):
                    continue
                idp = dep[-1]
                seg = x.iloc[idp:ia + 1]
                dur = int((seg.day.iloc[-1] - seg.day.iloc[0]).days)
                if dur < 1:
                    continue
                path = float(np.nansum(seg.step.values[1:]))
                gaps = seg.gap.values[1:]
                dth = seg.dth.values[1:]
                one_steps = (seg.step.values[1:] * 24 / dth)[(dth >= 18) & (dth <= 30)]
                travel = int((one_steps > 50).sum())
                cover = round(len(seg) / (dur + 1), 2)
                migs.append({"species": sp, "animal": aid, "population": row["population"], "kind": kind, "year": y if kind == "autumn" else y + 1,
                             "depart": str(seg.day.iloc[0].date()), "arrive": str(seg.day.iloc[-1].date()), "days": dur, "path_km": round(path, 1),
                             "straight_km": round(straight, 1), "km_per_day": round(path / dur, 1), "travel_days": travel,
                             "cover": cover, "max_gap": int(np.nanmax(gaps)) if len(gaps) else 0,
                             "from_lon": round(A[0], 3), "from_lat": round(A[1], 3), "to_lon": round(B[0], 3), "to_lat": round(B[1], 3)})
        M_ROWS += migs
        A_ROWS.append(row)
    print(sp, "animals", sum(1 for a in A_ROWS if a["species"] == sp), "migrations", sum(1 for m in M_ROWS if m["species"] == sp))

AN = pd.DataFrame(A_ROWS)
MG = pd.DataFrame(M_ROWS)
SC = pd.DataFrame(SEA)

# ---------------- stork flyways: which funnel each stork that reached Africa or Iberia used
WEST_POPS, EAST_POPS = ("SW Germany", "Spain (Doñana)"), ("Greece (Evros Delta)", "Poland", "Russia (Moscow)")


def flyway(a):
    """Stork flyways, by the gates crossed; birds that died or settled before a gate take their population's direction."""
    if a.species != "stork":
        return ""
    if a.gate_gibraltar:
        return "western"
    if a.gate_turkish_straits or a.gate_levant:
        return "eastern"
    if a.max_from_tag_km < 300:
        return "did not leave"
    if a.population in WEST_POPS:
        return "western, stayed in Europe"
    if a.population in EAST_POPS:
        return "eastern, before the straits"
    if a.population == "Tunisia":
        return "central (Sahara)"
    if a.population == "Armenia":
        return "Middle East"
    return "other"


AN["flyway"] = AN.apply(flyway, axis=1)
AN["winter_lon"] = AN.winters.apply(lambda w: w[0]["lon"] if w else None)
AN["winter_lat"] = AN.winters.apply(lambda w: w[0]["lat"] if w else None)
AN["winter_country"] = AN.winters.apply(lambda w: w[0]["country"] if w else "")
AN["winter_continent"] = AN.winters.apply(lambda w: w[0]["continent"] if w else "")
AN["n_winters"] = AN.winters.apply(len)
SCm = SC.groupby(["species", "animal"]).km.max() if len(SC) else pd.Series(dtype=float)
AN["longest_sea_km"] = [float(SCm.get((s, a), 0.0)) for s, a in zip(AN.species, AN.animal)]

AN.drop(columns=["winters"]).to_csv(f"{DATA}/animals.csv", index=False)
MG.to_csv(f"{DATA}/migrations.csv", index=False)
SC.to_csv(f"{DATA}/sea_crossings.csv", index=False)
jsave({"animals": AN.to_dict("records"), "funnels": FUNNELS, "funnel_r": FUN_R, "sea_share": SHARE, "maxgap_h": MAXGAP_H}, f"{WORK}/analysis.json")
print("sea share", SHARE)

# ---------------- wintering areas: a smoothed density of the Dec to Jan daily fixes, 50% and 90% contours, per species
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
feats = []
for sp in SP:
    pts = []
    for (s, aid), d in DAILY.items():
        if s != sp:
            continue
        m = d.day.dt.month
        w = d[(m == 12) | (m == 1)]
        if len(w) >= 10:
            # each animal and winter weighs the same: up to 40 fixes per animal
            pts.append(w.sample(min(len(w), 40), random_state=1)[["lon", "lat"]].to_numpy())
    if not pts:
        continue
    P = np.vstack(pts)
    x0, x1, y0, y1 = P[:, 0].min() - 5, P[:, 0].max() + 5, P[:, 1].min() - 5, P[:, 1].max() + 5
    res = 0.25
    H, xe, ye = np.histogram2d(P[:, 0], P[:, 1], bins=[np.arange(x0, x1 + res, res), np.arange(y0, y1 + res, res)])
    H = gaussian_filter(H, 1.5 / res)
    v = np.sort(H.ravel())[::-1]; c = np.cumsum(v) / v.sum()
    xc, yc = (xe[:-1] + xe[1:]) / 2, (ye[:-1] + ye[1:]) / 2
    for lev in (0.5, 0.9):
        thr = v[np.searchsorted(c, lev)]
        cs = plt.contour(xc, yc, H.T, levels=[thr])
        polys = []
        for path in cs.get_paths():
            for ring in path.to_polygons():
                if len(ring) >= 4:
                    polys.append(shapely.Polygon(ring).buffer(0))
        plt.close("all")
        if polys:
            geom = unary_union(polys).simplify(0.05)
            feats.append({"type": "Feature", "properties": {"species": sp, "level": int(lev * 100), "n_fixes": int(len(P))},
                          "geometry": json.loads(shapely.to_geojson(shapely.set_precision(geom, 0.01)))})
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/winter_areas.geojson")
print(AN.groupby("species").agg(n=("animal", "size"), dead=("confirmed_dead", "sum"), winters=("n_winters", lambda s: (s > 0).sum())))
print(MG.groupby(["species", "kind"]).agg(n=("animal", "size"), kmd=("km_per_day", "median"), days=("days", "median"), path=("path_km", "median")))
print(AN[AN.species == "stork"].groupby(["population", "flyway"]).size())
print(SC.groupby("species").km.describe())
