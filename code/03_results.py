"""results.json (every number quoted anywhere), page data (data/site.json, data/tracks.json) and the bird stories."""
import numpy as np, pandas as pd
from common import *

AJ = jload(f"{WORK}/analysis.json")
LOG = jload(f"{WORK}/clean_log.json")
AN = pd.read_csv(f"{DATA}/animals.csv", keep_default_na=False, na_values=[""])
MG = pd.read_csv(f"{DATA}/migrations.csv")
SC = pd.read_csv(f"{DATA}/sea_crossings.csv")
WIN = {(r["species"], str(r["animal"])): r.get("winters", []) for r in AJ["animals"]}
AN["animal"] = AN.animal.astype(str)
DAILY = {sp: pd.read_csv(f"{DATA}/daily_{sp}.csv", parse_dates=["day"]).assign(animal=lambda x: x.animal.astype(str)) for sp in SPECIES}
SP = list(SPECIES)
R = {}
r1 = lambda v: round(float(v), 1)
ri = lambda v: int(round(float(v)))


def med(s):
    return r1(np.median(s)) if len(s) else None


# ---------------- the data
R["data"] = {}
for sp in SP:
    a = AN[AN.species == sp]
    L = LOG[sp]
    R["data"][sp] = {"animals": len(a), "raw_rows": L.get("raw_rows", L.get("raw_rows_argos", 0) + L.get("raw_rows_gps", 0)),
                     "clean_fixes": L.get("clean_hourly", L.get("clean")), "daily": L["daily"],
                     "first_year": int(a.first_day.min()[:4]), "last_year": int(a.last_day.max()[:4]),
                     "doi": SOURCES[sp]["doi"]}
R["data"]["cuckoo"]["raw_rows"] = LOG["cuckoo"]["raw_rows_argos"] + LOG["cuckoo"]["raw_rows_gps"]
R["data"]["osprey"]["good_class_rows"] = LOG["osprey"]["good_class_rows"]
R["data"]["osprey"]["good_class_pct"] = r1(100 * LOG["osprey"]["good_class_rows"] / LOG["osprey"]["raw_rows"])
R["data"]["cuckoo"]["good_class_rows"] = LOG["cuckoo"]["good_class_rows"]
R["data"]["stork"]["raw_fixes"] = LOG["stork"]["raw_rows"]
R["data"]["harrier"]["raw_fixes"] = LOG["harrier"]["raw_rows"]
R["total"] = {"animals": len(AN), "daily": int(sum(LOG[sp]["daily"] for sp in SP)),
              "raw_rows": int(sum(R["data"][sp]["raw_rows"] for sp in SP)),
              "path_km": ri(AN.path_km_daily.sum())}

# ---------------- migrations (well covered only: a position on at least half the days and no gap over 5 days)
R["migr"] = {}
for sp in SP:
    for kind in ("autumn", "spring"):
        m = MG[(MG.species == sp) & (MG.kind == kind)]
        g = m[(m.cover >= 0.5) & (m.max_gap <= 5)]
        R["migr"][f"{sp}_{kind}"] = {"n_all": len(m), "n": len(g), "path_km": med(g.path_km), "straight_km": med(g.straight_km), "days": med(g.days),
                                     "km_per_day": med(g.km_per_day), "travel_days": med(g.travel_days),
                                     "detour_pct": r1(100 * (np.median(g.path_km / g.straight_km) - 1)) if len(g) else None,
                                     "fastest_km_per_day": r1(g.km_per_day.max()) if len(g) else None}

# ---------------- per species: daily distances, best year, sea
R["sp"] = {}
for sp in SP:
    a = AN[AN.species == sp]
    by = a.dropna(subset=["best_year_km"]).sort_values("best_year_km", ascending=False)
    md = a.dropna(subset=["max_day_km"]).sort_values("max_day_km", ascending=False)
    sc = SC[SC.species == sp].sort_values("km", ascending=False)
    R["sp"][sp] = {"name": SPECIES[sp][0], "latin": SPECIES[sp][1], "n": len(a),
                   "max_day_km": r1(md.max_day_km.iloc[0]) if len(md) else None, "max_day_animal": md.animal.iloc[0] if len(md) else None,
                   "n_full_year": len(by), "best_year_km": r1(by.best_year_km.iloc[0]) if len(by) else None,
                   "best_year_animal": by.animal.iloc[0] if len(by) else None,
                   "best_year_animal_hourly_total_km": r1(by.path_km_hourly.iloc[0]) if len(by) and not pd.isna(by.path_km_hourly.iloc[0]) else None,
                   "best_year_animal_span": int(by.span_days.iloc[0]) if len(by) else None,
                   "median_full_year_km": med(by.best_year_km),
                   "sea_pct": AJ["sea_share"][sp]["pct"], "sea_km": AJ["sea_share"][sp]["sea_km"], "flown_km": AJ["sea_share"][sp]["km"],
                   "longest_sea_km": r1(sc.km.iloc[0]) if len(sc) else 0, "longest_sea_animal": sc.animal.iloc[0] if len(sc) else None,
                   "longest_sea_date": sc.date.iloc[0] if len(sc) else None,
                   "n_cross_100": int(sc[sc.km >= 100].animal.nunique()), "n_cross_300": int(sc[sc.km >= 300].animal.nunique()),
                   "max_gap_h": AJ["maxgap_h"][sp], "dead": int(a.confirmed_dead.sum())}
# a day's flight for storks: median over storks of their best day (birds that migrated)
st = AN[AN.species == "stork"]
R["sp"]["stork"]["median_best_day_km"] = med(st[st.flyway.isin(["western", "eastern", "central (Sahara)"])].max_day_km.dropna())

# ---------------- storks
pops = ["SW Germany", "Spain (Doñana)", "Tunisia", "Poland", "Greece (Evros Delta)", "Russia (Moscow)", "Armenia", "Uzbekistan", "South Africa"]


def stork_region(lon, lat):
    if pd.isna(lat):
        return None
    if lat < 5 and lon > 0:
        return "East and southern Africa"
    if 5 <= lat < 20 and -20 < lon < 50:
        return "Sahel"
    if lat >= 20 and lon < 15:
        return "Europe and Morocco"
    if lat >= 20 and lon >= 15:
        return "Middle East and Asia"
    return "other"


st = st.assign(left=st.max_from_tag_km >= 300, region=[stork_region(x, y) for x, y in zip(st.winter_lon, st.winter_lat)])
P = {}
for p in pops:
    x = st[st.population == p]
    P[p] = {"n": len(x), "dead": int(x.confirmed_dead.sum()), "left": int(x.left.sum()), "gib": int(x.gate_gibraltar.sum()),
            "straits": int(x.gate_turkish_straits.sum()), "levant": int(x.gate_levant.sum()), "wintered": int(x.winter_lat.notna().sum()),
            "winter_lat": med(x.winter_lat.dropna()), "max_from_tag_km": r1(x.max_from_tag_km.max()),
            "median_max_from_tag_km": med(x.max_from_tag_km),
            "tag_lon": r1(x.tag_lon.iloc[0]), "tag_lat": r1(x.tag_lat.iloc[0]),
            "regions": x.region.value_counts().to_dict()}
west = st[st.population.isin(["SW Germany", "Spain (Doñana)"])]
east = st[st.population.isin(["Greece (Evros Delta)", "Poland", "Russia (Moscow)"])]
reg = st.region.value_counts().to_dict()
far = st.sort_values("max_from_tag_km", ascending=False).iloc[0]
R["stork"] = {
    "n": len(st), "n_pops": 8, "pops": P, "dead": int(st.confirmed_dead.sum()), "dead_pct": ri(100 * st.confirmed_dead.mean()),
    "left": int(st.left.sum()),
    "west_left": int(west.left.sum()), "west_gib": int(west.gate_gibraltar.sum()), "west_stayed_europe": int((west.flyway == "western, stayed in Europe").sum()),
    "west_morocco": int((west.winter_country == "Morocco").sum()), "west_france": int((west.winter_country == "France").sum()),
    "east_left": int(east.left.sum()), "east_straits": int(east.gate_turkish_straits.sum()), "east_levant": int(east.gate_levant.sum()),
    "gib_total": int(st.gate_gibraltar.sum()), "straits_total": int(st.gate_turkish_straits.sum()), "levant_total": int(st.gate_levant.sum()),
    "tunisia_sahara": int((st.flyway == "central (Sahara)").sum()),
    "wintered": int(st.winter_lat.notna().sum()), "regions": {k: int(v) for k, v in reg.items()},
    "south_of_equator": int((st.winter_lat < 0).sum()),
    "far_animal": far.animal, "far_pop": far.population, "far_km": r1(far.max_from_tag_km), "far_country": far.winter_country,
    "uzbek_max_km": P["Uzbekistan"]["max_from_tag_km"], "armenia_left": P["Armenia"]["left"],
    "dead_by_flyway": st[st.confirmed_dead].flyway.value_counts().to_dict(),
    "dead_before_leaving": int((st.confirmed_dead & ~st.left).sum()),
    "dead_in_africa": int((st.confirmed_dead & (st.last_continent == "Africa")).sum()),
    "transmitting_end": int((st.last_day >= "2014-06-15").sum()),
    "last_day": st.last_day.max(),
    "hourly_vs_daily_pct": ri(100 * (st.path_km_hourly.sum() / st.path_km_daily.sum() - 1)),
}
# deaths: early (before 1 Oct 2013, the first weeks out of the nest and the first migration) vs later
dd = st[st.confirmed_dead]
R["stork"]["dead_by_1oct"] = int((dd.last_day < "2013-10-01").sum())
R["stork"]["dead_by_1oct_pct"] = ri(100 * R["stork"]["dead_by_1oct"] / len(dd))
# Sahel winterers vs those that stayed north of the Sahara (birds that reached a winter area)
w = st[st.winter_lat.notna()]
R["stork"]["winter_n"] = len(w)
# deaths among the storks that left home, by direction
for grp, pp_ in (("west", ["SW Germany", "Spain (Doñana)"]), ("east", ["Greece (Evros Delta)", "Poland", "Russia (Moscow)"]), ("tunisia", ["Tunisia"])):
    x = st[st.population.isin(pp_) & st.left]
    R["stork"][f"leave_{grp}_n"] = len(x); R["stork"][f"leave_{grp}_dead"] = int(x.confirmed_dead.sum())
    R["stork"][f"leave_{grp}_dead_pct"] = ri(100 * x.confirmed_dead.mean())

# ---------------- ospreys
os_ = AN[AN.species == "osprey"]
south = {}
for aid, d in DAILY["osprey"].groupby("animal"):
    d = d[d.day.dt.month.isin([10, 11, 12, 1, 2, 3])]
    if len(d) and d.lat.min() < 25:
        k = d.lat.idxmin()
        south[aid] = (d.loc[k, "lon"], d.loc[k, "lat"])
import geopandas as gpd, shapely
from shapely.geometry import Point
cty = gpd.read_file(f"{GEO}/ne_50m_admin_0_countries.geojson")[["NAME_EN", "geometry"]]
tree = shapely.STRtree(cty.geometry.values)


def ctry(lon, lat):
    p = Point(lon, lat); h = tree.query(p, predicate="intersects")
    n = cty.NAME_EN.iloc[h[0]] if len(h) else cty.NAME_EN.iloc[tree.nearest(p)]
    if n == "France" and lon < -40:
        n = "French Guiana"
    return {"United States of America": "United States"}.get(n, n)


southc = pd.Series({a: ctry(*v) for a, v in south.items()})
os_ = os_.assign(south_country=os_.animal.map(southc), south_lat=os_.animal.map({a: v[1] for a, v in south.items()}),
                 south_lon=os_.animal.map({a: v[0] for a, v in south.items()}))
sa = os_[os_.south_lat < 13]
fates = []
for _, x in os_[os_.confirmed_dead].iterrows():
    fates.append({"animal": x.animal, "note": x.fate_note, "last_day": x.last_day, "country": x.last_country})
R["osprey"] = {"n": len(os_), "pops": os_.population.value_counts().to_dict(), "n_south": len(south), "south_countries": southc.value_counts().to_dict(),
               "n_south_america": int((os_.south_country.isin(["Venezuela", "Colombia", "Brazil", "French Guiana", "Ecuador", "Peru", "Bolivia", "Guyana", "Suriname"])).sum()),
               "dead": int(os_.confirmed_dead.sum()), "fates": fates,
               "debris": int(os_.fate_note.fillna("").str.contains("debris").sum()),
               "cuba": int((os_["near_Florida Keys and Cuba"] <= 150).sum()),
               "east_cuba": int(((os_["near_Florida Keys and Cuba"] <= 150) & (os_.population == "East")).sum()),
               "east_n": int((os_.population == "East").sum()), "midwest_n": int((os_.population == "Midwest").sum()), "west_n": int((os_.population == "West").sum()),
               "west_south_lat": med(os_[os_.population == "West"].south_lat.dropna()), "east_south_lat": med(os_[os_.population == "East"].south_lat.dropna())}
R["osprey"]["mexico_by_pop"] = os_[os_.south_country == "Mexico"].population.value_counts().to_dict()
car = SC[(SC.species == "osprey") & (SC.km >= 300)]
R["osprey"]["carib_n"] = int(car.animal.nunique())
R["osprey"]["carib_median_km"] = med(car.km)
R["osprey"]["carib_median_h"] = med(car.hours)
kd = SC[(SC.species == "osprey")].sort_values("km").iloc[-1]
R["osprey"]["longest_animal"] = kd.animal
R["osprey"]["longest_km"] = r1(kd.km)
R["osprey"]["longest_h"] = r1(kd.hours)

# ---------------- cuckoos
cu = AN[AN.species == "cuckoo"]
ctrl, disp = cu[~cu.displaced.astype(bool)], cu[cu.displaced.astype(bool)]
fast = []
for aid, d in DAILY["cuckoo"].groupby("animal"):
    d = d.sort_values("day").reset_index(drop=True)
    t = (d.day - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy() / 86400 + d.hour.to_numpy() / 24
    for i in range(len(d)):
        for j in range(i + 1, len(d)):
            dt = t[j] - t[i]
            if dt > 6:
                break
            km = float(hav(d.lon[i], d.lat[i], d.lon[j], d.lat[j]))
            if km >= 1500:
                fast.append({"animal": aid, "km": r1(km), "days": r1(dt), "kmd": r1(km / dt), "from": ctry(d.lon[i], d.lat[i]), "to": ctry(d.lon[j], d.lat[j]),
                             "date": str(d.day[i].date()), "lat0": r1(d.lat[i]), "lat1": r1(d.lat[j])})
fast = sorted(fast, key=lambda x: -x["km"])
seen, fast1 = set(), []
for f in fast:
    if f["animal"] not in seen:
        seen.add(f["animal"]); fast1.append(f)
cs = SC[SC.species == "cuckoo"]
DISP_KM = ri(hav(disp.tag_lon.median(), disp.tag_lat.median(), ctrl.tag_lon.median(), ctrl.tag_lat.median()) / 100) * 100
R["cuckoo"] = {"n": len(cu), "displace_km": DISP_KM, "control": len(ctrl), "displaced": len(disp),
               "control_juv": int((ctrl.stage == "juvenile").sum()), "displaced_juv": int((disp.stage == "juvenile").sum()),
               "control_africa": int((ctrl.last_lat < 20).sum()), "displaced_africa": int((disp.last_lat < 20).sum()),
               "control_span": med(ctrl.span_days), "displaced_span": med(disp.span_days),
               "africa": int((cu.last_lat < 20).sum()), "south_equator": int((cu.last_lat < 0).sum()),
               "fast": fast1[:3], "n_cross_med": int(cs[(cs.lat0 > 34) & (cs.lat1 < 34)].animal.nunique()),
               "longest_sea_km": r1(cs.km.max()), "longest_sea_animal": cs.sort_values("km").animal.iloc[-1],
               "winter_n": int(cu.winter_lat.notna().sum())}
# displaced birds: the bearing of their first 500 km from Kazan
def bearing(lon1, lat1, lon2, lat2):
    import math
    l1, l2, dl = math.radians(lat1), math.radians(lat2), math.radians(lon2 - lon1)
    return (math.degrees(math.atan2(math.sin(dl) * math.cos(l2), math.cos(l1) * math.sin(l2) - math.sin(l1) * math.cos(l2) * math.cos(dl))) + 360) % 360


def first_heading(sub):
    out = []
    for aid in sub.animal:
        d = DAILY["cuckoo"][DAILY["cuckoo"].animal == aid].sort_values("day")
        a0 = sub[sub.animal == aid].iloc[0]
        dist = hav(a0.tag_lon, a0.tag_lat, d.lon.values, d.lat.values)
        k = np.flatnonzero(dist >= 500)
        if len(k):
            out.append(bearing(a0.tag_lon, a0.tag_lat, d.lon.values[k[0]], d.lat.values[k[0]]))
    return out


hd, hc = first_heading(disp), first_heading(ctrl)
R["cuckoo"]["disp_heading_n"] = len(hd); R["cuckoo"]["disp_heading_med"] = med(hd)
R["cuckoo"]["disp_sw"] = int(sum(180 <= h <= 270 for h in hd))
R["cuckoo"]["ctrl_heading_n"] = len(hc); R["cuckoo"]["ctrl_heading_med"] = med(hc)

# ---------------- marsh harriers
ha = AN[AN.species == "harrier"]
H = {}
for _, x in ha.iterrows():
    wl = WIN[("harrier", x.animal)]
    fid = [r1(hav(wl[i]["lon"], wl[i]["lat"], wl[i + 1]["lon"], wl[i + 1]["lat"])) for i in range(len(wl) - 1)]
    mm = MG[(MG.species == "harrier") & (MG.animal == x.animal)]
    H[x["name"]] = {"animal": x.animal, "sex": x.sex, "first_day": x.first_day, "last_day": x.last_day, "years": r1(x.span_days / 365.25),
                    "path_daily": r1(x.path_km_daily), "path_hourly": r1(x.path_km_hourly) if not pd.isna(x.path_km_hourly) else None,
                    "winters": [{"year": w["year"], "country": w["country"], "lat": w["lat"], "lon": w["lon"]} for w in wl], "winter_shift_km": fid,
                    "n_migr": len(mm), "autumn_days": [int(v) for v in mm[mm.kind == "autumn"].days], "spring_days": [int(v) for v in mm[mm.kind == "spring"].days],
                    "max_day_km": r1(x.max_day_km) if not pd.isna(x.max_day_km) else None, "best_year_km": r1(x.best_year_km) if not pd.isna(x.best_year_km) else None,
                    "migr_km": [r1(v) for v in mm.path_km]}
R["harrier"] = {"n": len(ha), "birds": H, "n_migr": int((MG.species == "harrier").sum())}
li = H["Lilla"]
R["harrier"]["lilla_max_shift"] = max(li["winter_shift_km"]) if li["winter_shift_km"] else None
R["harrier"]["lilla_autumn_min"] = min(li["autumn_days"]); R["harrier"]["lilla_autumn_max"] = max(li["autumn_days"])
R["harrier"]["autumn_med_days"] = med([d for b in H.values() for d in b["autumn_days"]])
R["harrier"]["spring_med_days"] = med([d for b in H.values() for d in b["spring_days"]])

# ---------------- comparisons across species (autumn)
R["compare"] = {sp: {"autumn_kmd": R["migr"][f"{sp}_autumn"]["km_per_day"], "autumn_days": R["migr"][f"{sp}_autumn"]["days"],
                     "autumn_km": R["migr"][f"{sp}_autumn"]["path_km"], "n": R["migr"][f"{sp}_autumn"]["n"]} for sp in SP}
R["compare"]["osprey_vs_stork_speed"] = r1(R["migr"]["osprey_autumn"]["km_per_day"] / R["migr"]["stork_autumn"]["km_per_day"])
R["compare"]["sea_ratio_osprey_stork"] = ri(R["sp"]["osprey"]["sea_pct"] / R["sp"]["stork"]["sea_pct"])

# ---------------- funnels for the page (position and count of birds that passed within 75 km / gate counts)
R["funnels"] = {"Gibraltar": R["stork"]["gib_total"], "Turkish straits": R["stork"]["straits_total"], "Levant": R["stork"]["levant_total"],
                "Florida and Cuba": R["osprey"]["cuba"]}


# ---------------- stories and page data
def nice(day):
    t = pd.Timestamp(day)
    return f"{t.day} {t.strftime('%B')} {t.year}"


def story(x):
    sp = x.species
    nm = SPECIES[sp][0].lower()
    parts = []
    label = x["name"] if isinstance(x["name"], str) and x["name"] else x.animal
    if sp == "stork":
        parts.append(f"A young white stork from {x.population}, fitted with a GPS tag in the nest in its first summer." if x.population != "South Africa"
                     else "A young white stork tagged in South Africa in its first southern summer.")
    elif sp == "osprey":
        parts.append(f"An {x.stage if isinstance(x.stage, str) else ''} osprey ({'female' if x.sex == 'f' else 'male' if x.sex == 'm' else 'sex not recorded'}) from the {x.population} population, tagged at {x.site}.".replace("An  ", "An ").replace("An nestling", "A nestling"))
    elif sp == "cuckoo":
        parts.append(("A " + str(x.stage) + " cuckoo caught at Rybachy on the Curonian Spit, " +
                      (f"carried about {DISP_KM:,} km east to Kazan and released there, to see whether it could find its way." if x.displaced else "released where it was caught.")))
    else:
        parts.append(f"{label}, a {'female' if x.sex == 'f' else 'male'} marsh harrier breeding near Antwerp.")
    mm = MG[(MG.species == sp) & (MG.animal == x.animal)].sort_values("depart")
    for _, m in mm.head(4).iterrows():
        if m.kind == "autumn":
            parts.append(f"Autumn {m.year}: left on {nice(m.depart)} and reached its winter quarters on {nice(m.arrive)}, {ri(m.path_km):,} km in {m.days} days.")
        else:
            parts.append(f"Spring {m.year}: left on {nice(m.depart)} and was home on {nice(m.arrive)}, {ri(m.path_km):,} km in {m.days} days.")
    if sp == "stork":
        g = []
        if x.gate_gibraltar: g.append("crossed the Strait of Gibraltar")
        if x.gate_turkish_straits: g.append("crossed the Bosporus or the Dardanelles")
        if x.gate_levant: g.append("flew down the Levant into Africa")
        if g:
            parts.append("It " + " and ".join(g) + ".")
    wl = WIN[(sp, x.animal)]
    if wl:
        cs = []
        for w in wl:
            if w["country"] not in cs:
                cs.append(w["country"])
        parts.append("Wintered in " + " and ".join(cs) + ".")
    if not pd.isna(x.best_year_km):
        parts.append(f"In its best-covered year it covered at least {ri(x.best_year_km):,} km.")
    parts.append(f"Followed for {x.span_days:,} days, {ri(x.path_km_daily):,} km between daily positions; farthest {ri(x.max_from_tag_km):,} km from where it was tagged.")
    if x.confirmed_dead:
        note = x.fate_note if sp == "osprey" else "confirmed dead"
        parts.append(f"Last position {nice(x.last_day)} in {x.last_country}: {note}.")
    elif sp == "stork" and x.last_day >= "2014-06-15":
        parts.append(f"Still sending positions when this data set ends ({nice(x.last_day)}, {x.last_country}).")
    else:
        parts.append(f"Last position {nice(x.last_day)} in {x.last_country}; the data do not say what happened next.")
    return " ".join(parts)


AN["story"] = AN.apply(story, axis=1)
tracks, meta = {}, []
for sp in SP:
    d = DAILY[sp]
    a = AN[AN.species == sp]
    for _, x in a.iterrows():
        g = d[d.animal == x.animal].sort_values("day")
        if len(g) < 2:
            continue
        t0 = g.day.iloc[0]
        days = ((g.day - t0).dt.days).tolist()
        lon = (g.lon * 100).round().astype(int).tolist(); lat = (g.lat * 100).round().astype(int).tolist()
        k = f"{sp}:{x.animal}"
        tracks[k] = [str(t0.date()), days, lon, lat]
        nm = x["name"] if isinstance(x["name"], str) and x["name"] else re.sub(r"\s*\(.*\)$", "", x.animal)
        meta.append({"k": k, "sp": sp, "id": x.animal, "nm": nm, "pop": x.population, "dead": bool(x.confirmed_dead), "story": dash(x.story),
                     "fly": x.flyway if isinstance(x.flyway, str) else "", "disp": bool(x.displaced),
                     "last": [r1(x.last_lon), r1(x.last_lat)], "win": [x.winter_lon, x.winter_lat] if not pd.isna(x.winter_lat) else None,
                     "km": ri(x.path_km_daily), "days": int(x.span_days), "n": len(g)})
jsave(tracks, f"{DATA}/tracks.json")
crossings = [{"sp": r.species, "id": str(r.animal), "km": r1(r.km), "c": [[r.lon0, r.lat0], [r.lon1, r.lat1]], "date": r.date} for r in SC[SC.km >= 50].itertuples()]
FUNP = {"Strait of Gibraltar": [-5.6, 35.95, "stork", R["stork"]["gib_total"], "storks crossed here into Africa"],
        "Bosporus and Dardanelles": [27.8, 40.7, "stork", R["stork"]["straits_total"], "storks crossed the Turkish straits"],
        "The Levant": [35.2, 31.6, "stork", R["stork"]["levant_total"], "storks funnelled down the land bridge into Africa"],
        "Florida and Cuba": [-81.2, 23.6, "osprey", R["osprey"]["cuba"], "ospreys passed within 150 km"]}
site = {"species": {sp: {"name": SPECIES[sp][0], "latin": SPECIES[sp][1], "col": SPECIES[sp][2], "src": SOURCES[sp]["short"], "doi": SOURCES[sp]["doi"]} for sp in SP},
        "animals": meta, "crossings": crossings, "funnels": FUNP,
        "pops": {p: [P[p]["tag_lon"], P[p]["tag_lat"], P[p]["n"]] for p in pops},
        "popstats": {p: {k: P[p][k] for k in ("n", "dead", "left", "wintered", "winter_lat")} for p in pops},
        "migs": [[r.species, r.kind, r1(r.km_per_day), int(r.days), ri(r.path_km), str(r.animal)] for r in MG[(MG.cover >= 0.5) & (MG.max_gap <= 5)].itertuples()],
        "years": [[r.species, ri(r.best_year_km), str(r.animal)] for r in AN.dropna(subset=["best_year_km"]).itertuples()],
        "sea": {sp: R["sp"][sp]["sea_pct"] for sp in SP},
        "winlat": [[r.population, r1(r.winter_lat), bool(r.confirmed_dead), str(r.animal)] for r in st.dropna(subset=["winter_lat"]).itertuples()]}
jsave(site, f"{DATA}/site.json")
# reusable tables
AN.drop(columns=["story"]).to_csv(f"{DATA}/animals.csv", index=False)
jsave(R, f"{DATA}/results.json", indent=1)

# ---------------- checks
assert R["stork"]["n"] == 72 and R["stork"]["dead"] == 30 and R["data"]["stork"]["raw_rows"] == 1584192
assert R["sp"]["stork"]["sea_pct"] < 1 < R["sp"]["osprey"]["sea_pct"]
assert R["stork"]["west_gib"] == R["stork"]["gib_total"]
print(json.dumps({k: R[k] for k in ("stork", "migr", "osprey", "cuckoo")}, indent=0, default=str)[:6000])
print("tracks", os.path.getsize(f"{DATA}/tracks.json") // 1024, "KB; site", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
