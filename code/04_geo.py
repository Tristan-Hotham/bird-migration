"""Base map geometry for the page's parchment map, and the Inked World lettering and palette.
Natural Earth 1:50m countries (coast, borders, country names), 1:10m populated places (town names), and the Inked World's
river and lake lines (Natural Earth, as prepared for https://maps.tristanhotham.com/ink-map/). Fonts: IM Fell (OFL) as
MapLibre glyphs, from The Inked World."""
import shutil, geopandas as gpd, shapely
from shapely.ops import unary_union
from common import *

G = os.path.join(DATA, "geo"); os.makedirs(G, exist_ok=True)


def fc(geoms, props=None, prec=0.01):
    feats = []
    for i, g in enumerate(geoms):
        if g is None or g.is_empty:
            continue
        g = shapely.set_precision(g, prec)
        if g.is_empty:
            continue
        feats.append({"type": "Feature", "properties": (props[i] if props else {}), "geometry": json.loads(shapely.to_geojson(g))})
    return {"type": "FeatureCollection", "features": feats}


cty = gpd.read_file(f"{GEO}/ne_50m_admin_0_countries.geojson")
land = unary_union([g.buffer(0) for g in cty.geometry.values])
land = shapely.simplify(land, 0.02, preserve_topology=True)
# exterior rings counter-clockwise, so a positive line-offset falls on the sea side (the coast ripples)
polys = [shapely.geometry.polygon.orient(p, 1.0) for p in getattr(land, "geoms", [land]) if p.area > 0.02]
jsave(fc(polys), f"{G}/land.json")
# borders: country outlines minus the coast
coast = land.boundary.buffer(0.03)
bl = unary_union([g.boundary for g in cty.geometry.values]).difference(coast)
bl = shapely.simplify(bl, 0.05)
bl = [g for g in getattr(bl, "geoms", [bl]) if g.length > 0.2]
jsave(fc(bl, prec=0.02), f"{G}/borders.json")
# country names at Natural Earth's label points (bigger countries first)
cty = cty.sort_values("LABELRANK")
cn = [{"type": "Feature", "properties": {"n": r.NAME_EN, "r": int(r.LABELRANK)}, "geometry": {"type": "Point", "coordinates": [round(r.LABEL_X, 2), round(r.LABEL_Y, 2)]}}
      for r in cty.itertuples() if r.POP_EST and r.POP_EST > 300000 or r.LABELRANK <= 3]
jsave({"type": "FeatureCollection", "features": cn}, f"{G}/countries.json")
# towns: capitals and big cities, ranked
pp = gpd.read_file(f"{GEO}/ne_10m_populated_places_simple.geojson")
pp = pp[(pp.scalerank <= 3) | (pp.featurecla == "Admin-0 capital")]
pp = pp.sort_values(["scalerank", "pop_max"], ascending=[True, False])
tw = [{"type": "Feature", "properties": {"n": r.name, "r": int(r.scalerank), "c": 1 if "capital" in str(r.featurecla).lower() and "Admin-0" in str(r.featurecla) else 0},
       "geometry": {"type": "Point", "coordinates": [round(r.geometry.x, 3), round(r.geometry.y, 3)]}} for r in pp.itertuples()]
jsave({"type": "FeatureCollection", "features": tw}, f"{G}/towns.json")
# rivers and lakes from The Inked World (major ones only)
rv = jload(f"{INK}/data/rivers.geojson")
keep = []
for f in rv["features"]:
    if f["properties"].get("z", 9) <= 4.0:
        g = shapely.simplify(shapely.geometry.shape(f["geometry"]), 0.02)
        keep.append((g, {"n": f["properties"].get("n", ""), "z": f["properties"].get("z")}))
jsave(fc([k[0] for k in keep], [k[1] for k in keep]), f"{G}/rivers.json")
if not os.path.exists(LAKES):
    import urllib.request
    os.makedirs(os.path.dirname(LAKES), exist_ok=True)
    urllib.request.urlretrieve(LAKES_URL, LAKES)
lk = jload(LAKES)
keep = []
for f in lk["features"]:
    g = shapely.geometry.shape(f["geometry"]).buffer(0)
    if g.area > 0.08:
        keep.append((shapely.simplify(g, 0.02), {"n": f["properties"].get("name") or ""}))
jsave(fc([k[0] for k in keep], [k[1] for k in keep]), f"{G}/lakes.json")

# fonts (MapLibre glyph ranges for Latin text) and the palette
for fam in ("Ink Roman", "Ink Italic", "Ink Caps"):
    os.makedirs(f"{ROOT}/fonts/{fam}", exist_ok=True)
    for rg in ("0-255", "256-511", "8192-8447"):
        src = f"{INK}/fonts/{fam}/{rg}.pbf"
        if os.path.exists(src):
            shutil.copy(src, f"{ROOT}/fonts/{fam}/{rg}.pbf")
os.makedirs(f"{ROOT}/fonts/ttf", exist_ok=True)
for fn in os.listdir(f"{INK}/fonts/ttf"):
    shutil.copy(f"{INK}/fonts/ttf/{fn}", f"{ROOT}/fonts/ttf/{fn}")
os.makedirs(f"{ROOT}/js", exist_ok=True)
shutil.copy(f"{INK}/js/ink-palette.js", f"{ROOT}/js/ink-palette.js")
for fn in sorted(os.listdir(G)):
    print(fn, os.path.getsize(f"{G}/{fn}") // 1024, "KB")
