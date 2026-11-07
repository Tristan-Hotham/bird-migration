"""Read the four raw tracking datasets, clean them and write one table of fixes per species.

Cleaning:
- GPS (storks, marsh harriers, cuckoo Lotek GPS): rows marked visible, with coordinates, not flagged as outliers.
  Thinned to the first fix per animal per hour (the storks' tags took a fix every 5 minutes in daylight).
- Argos (ospreys, cuckoo PTTs): location classes 3, 2 and 1 only (stated error under about 1.5 km); rows that Movebank's
  Douglas filter or the data owner marked as outliers are dropped.
- Speed filter for every species: a fix is dropped if reaching it from the previous kept fix needs more than
  SPEED_MAX km/h over at least 5 km (repeated until nothing changes).
- Daily positions (for the page and for daily distances): per animal and UTC day, the fix nearest to 12:00 UTC
  (for Argos the best location class first).
Outputs: WORK/fix_<species>.csv.gz (hourly, every clean fix for Argos), data/daily_<species>.csv (one per animal per day),
data/animals_raw.json (reference data used later).
"""
import io, zipfile, glob
import numpy as np, pandas as pd
from common import *

SPEED_MAX = {"stork": 120, "harrier": 120, "osprey": 120, "cuckoo": 150}
LOG = {}


def speed_filter(df, vmax):
    """Iteratively drop fixes that need more than vmax km/h from the previous kept fix (over >= 5 km)."""
    out = []
    for aid, g in df.groupby("animal", sort=False):
        g = g.sort_values("t")
        lon, lat, t = g.lon.to_numpy(), g.lat.to_numpy(), (g.t - pd.Timestamp("1970-01-01")).dt.total_seconds().to_numpy() / 3600
        keep = np.ones(len(g), bool)
        for _ in range(20):
            idx = np.flatnonzero(keep)
            if len(idx) < 2:
                break
            d = hav(lon[idx[:-1]], lat[idx[:-1]], lon[idx[1:]], lat[idx[1:]])
            dt = np.maximum(t[idx[1:]] - t[idx[:-1]], 1 / 60)
            bad = (d > 5) & (d / dt > vmax)
            # also catch single spikes: the fix after a bad jump is checked against the fix before it in the next pass
            if not bad.any():
                break
            keep[idx[1:][bad]] = False
        out.append(g[keep])
    return pd.concat(out, ignore_index=True)


def hourly(df):
    df = df.sort_values(["animal", "t"])
    h = df.t.dt.floor("h")
    return df[~pd.DataFrame({"a": df.animal, "h": h}).duplicated()].reset_index(drop=True)


def thin10(df):
    df = df.sort_values(["animal", "t"])
    h = df.t.dt.floor("10min")
    return df[~pd.DataFrame({"a": df.animal, "h": h}).duplicated()].reset_index(drop=True)


def daily(df, argos=False):
    df = df.copy()
    df["day"] = df.t.dt.floor("D")
    df["off"] = (df.t - df.day - pd.Timedelta(hours=12)).abs()
    keys = ["lcr", "off"] if argos else ["off"]
    df = df.sort_values(["animal", "day"] + keys)
    d = df.drop_duplicates(["animal", "day"]).sort_values(["animal", "day"])
    d = d.assign(hour=((d.t - d.day).dt.total_seconds() / 3600).round(2))
    return d[["animal", "day", "hour", "lon", "lat"]].reset_index(drop=True)


# ---------------- storks (stream the 312 MB file from the zip)
cols = ["visible", "timestamp", "location-long", "location-lat", "study-specific-measurement", "individual-local-identifier"]
parts = []
with zipfile.ZipFile(f"{RAW}/storks_flack_gps.csv.zip") as z:
    name = [n for n in z.namelist() if n.endswith("-gps.csv") and not n.startswith("__MACOSX")][0]
    with z.open(name) as f:
        n_raw = 0
        for ch in pd.read_csv(f, usecols=cols, chunksize=500_000, dtype={"visible": str}):
            n_raw += len(ch)
            ch = ch[(ch.visible.str.lower() == "true") & ch["location-long"].notna() & ch["location-lat"].notna()]
            ch = ch.rename(columns={"timestamp": "t", "location-long": "lon", "location-lat": "lat",
                                    "study-specific-measurement": "pop", "individual-local-identifier": "animal"})
            ch["t"] = pd.to_datetime(ch.t)
            # thin inside the chunk to one fix per 10 minutes (finished below across chunk edges)
            parts.append(thin10(ch))
st10 = thin10(pd.concat(parts, ignore_index=True))
st = hourly(st10)
LOG["stork"] = {"raw_rows": n_raw, "hourly_before_speed": len(st)}
st = speed_filter(st, SPEED_MAX["stork"])
LOG["stork"]["clean_hourly"] = len(st)
st["species"] = "stork"
pops = st.groupby("animal")["pop"].first().to_dict()

# ---------------- ospreys (Argos)
o = pd.read_csv(f"{RAW}/osprey_martell_gps.csv.gz", usecols=["visible", "timestamp", "location-long", "location-lat", "algorithm-marked-outlier",
                                                             "argos:lc", "manually-marked-outlier", "individual-local-identifier", "tag-local-identifier"],
                dtype={"argos:lc": str, "visible": str, "algorithm-marked-outlier": str, "manually-marked-outlier": str, "tag-local-identifier": str})
LOG["osprey"] = {"raw_rows": len(o), "lc_counts": o["argos:lc"].value_counts().to_dict()}


def argos_clean(o, sp):
    o = o[o["location-long"].notna() & o["location-lat"].notna()]
    o = o[o["argos:lc"].isin(["3", "2", "1"])]
    o = o[(o["algorithm-marked-outlier"].fillna("").str.lower() != "true") & (o["manually-marked-outlier"].fillna("").str.lower() != "true")]
    o = o.rename(columns={"timestamp": "t", "location-long": "lon", "location-lat": "lat", "individual-local-identifier": "animal"})
    o["t"] = pd.to_datetime(o.t)
    o["lcr"] = 3 - o["argos:lc"].astype(int)       # 0 best
    LOG[sp]["good_class_rows"] = len(o)
    o = speed_filter(o, SPEED_MAX[sp])
    LOG[sp]["clean"] = len(o)
    return o


o = argos_clean(o, "osprey")
o["species"] = "osprey"
o["tag"] = o["tag-local-identifier"]

# ---------------- cuckoos (Argos PTTs and Lotek GPS)
ca = pd.read_csv(f"{RAW}/cuckoo_rybachy_argos.csv", dtype={"argos:lc": str, "visible": str, "algorithm-marked-outlier": str, "manually-marked-outlier": str})
LOG["cuckoo"] = {"raw_rows_argos": len(ca), "lc_counts": ca["argos:lc"].value_counts().to_dict()}
ca = ca[["visible", "timestamp", "location-long", "location-lat", "algorithm-marked-outlier", "argos:lc", "manually-marked-outlier", "individual-local-identifier"]]
ca = argos_clean(ca, "cuckoo")
cg = pd.read_csv(f"{RAW}/cuckoo_rybachy_gps.csv", dtype={"visible": str, "manually-marked-outlier": str})
LOG["cuckoo"]["raw_rows_gps"] = len(cg)
cg = cg[(cg.visible.str.lower() == "true") & cg["location-long"].notna() & (cg["manually-marked-outlier"].fillna("").str.lower() != "true")]
cg = cg[cg["gps:fix-type-raw"].isin(["2D", "3D"])]
cg = cg.rename(columns={"timestamp": "t", "location-long": "lon", "location-lat": "lat", "individual-local-identifier": "animal"})
cg["t"] = pd.to_datetime(cg.t)
cg["lcr"] = -1    # a GPS fix beats any Argos fix on the same day
LOG["cuckoo"]["gps_good"] = len(cg)
cu = pd.concat([ca[["animal", "t", "lon", "lat", "lcr"]], cg[["animal", "t", "lon", "lat", "lcr"]]], ignore_index=True)
cu = speed_filter(cu, SPEED_MAX["cuckoo"])
LOG["cuckoo"]["clean"] = len(cu)
cu["species"] = "cuckoo"

# ---------------- marsh harriers (GPS, five yearly files); the one common buzzard in the set is left out
hs = []
n_raw = 0
for fn in sorted(glob.glob(f"{RAW}/harrier_MH_ANTWERPEN-gps-*.csv.gz")):
    h = pd.read_csv(fn, usecols=["visible", "timestamp", "location-long", "location-lat", "import-marked-outlier", "manually-marked-outlier",
                                 "individual-taxon-canonical-name", "individual-local-identifier"],
                    dtype={"visible": str, "import-marked-outlier": str, "manually-marked-outlier": str})
    n_raw += len(h)
    h = h[(h.visible.str.lower() == "true") & h["location-long"].notna()]
    h = h[(h["import-marked-outlier"].fillna("").str.lower() != "true") & (h["manually-marked-outlier"].fillna("").str.lower() != "true")]
    h = h[h["individual-taxon-canonical-name"] == "Circus aeruginosus"]
    h = h.rename(columns={"timestamp": "t", "location-long": "lon", "location-lat": "lat", "individual-local-identifier": "animal"})
    h["t"] = pd.to_datetime(h.t)
    hs.append(thin10(h))
ha10 = thin10(pd.concat(hs, ignore_index=True))
ha = hourly(ha10)
LOG["harrier"] = {"raw_rows": n_raw, "hourly_before_speed": len(ha)}
ha = speed_filter(ha, SPEED_MAX["harrier"])
LOG["harrier"]["clean_hourly"] = len(ha)
ha["species"] = "harrier"

# ---------------- 10-minute GPS tracks (for sea crossings), speed-filtered like the hourly ones
for sp, df in (("stork", st10), ("harrier", ha10)):
    df = speed_filter(df, SPEED_MAX[sp])
    df[["animal", "t", "lon", "lat"]].to_csv(f"{WORK}/fix10_{sp}.csv.gz", index=False, float_format="%.5f")
    LOG[sp]["clean_10min"] = len(df)

# ---------------- write
for sp, df, argos in (("stork", st, False), ("osprey", o, True), ("cuckoo", cu, True), ("harrier", ha, False)):
    df = df.sort_values(["animal", "t"])
    df[["animal", "t", "lon", "lat"]].to_csv(f"{WORK}/fix_{sp}.csv.gz", index=False, float_format="%.5f")
    d = daily(df if argos else df.assign(lcr=0), argos=True)
    d["day"] = d.day.dt.strftime("%Y-%m-%d")
    d.to_csv(f"{DATA}/daily_{sp}.csv", index=False, float_format="%.4f")
    LOG[sp]["daily"] = len(d)
    LOG[sp]["animals"] = int(df.animal.nunique())
    print(sp, LOG[sp])
LOG["stork_pops"] = pops
LOG["osprey_tags"] = o.groupby("animal")["tag"].agg(lambda s: sorted(set(s))).to_dict()
jsave({k: (v if not isinstance(v, dict) else {str(a): b for a, b in v.items()}) for k, v in LOG.items()}, f"{WORK}/clean_log.json", indent=1)
