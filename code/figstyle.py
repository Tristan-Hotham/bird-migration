"""Static figures in the house ink style: parchment, iron-gall ink coasts with ripple lines, IM Fell lettering
(The Inked World), the pen-drawn birds (img/sprites, rendered from js/pen-birds.js by code/sprites.js)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Polygon as MPoly
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.patheffects as pe
import numpy as np, shapely
from PIL import Image
from common import *

FONTS = "/home/claude/ref/fonts"
FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": 900, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-Black.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
FELL = fm.FontProperties(fname=f"{ROOT}/fonts/ttf/IMFeENrm28P.ttf")
FELLI = fm.FontProperties(fname=f"{ROOT}/fonts/ttf/IMFeGPit28P.ttf")
FELLSC = fm.FontProperties(fname=f"{ROOT}/fonts/ttf/IMFeENsc28P.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#6E6150", "axes.labelcolor": "#2B2119",
                     "xtick.color": "#6E6150", "ytick.color": "#6E6150"})
PAPER, SEA, INK, MUT, RULE, RED, BLUE, BLUES = "#F3E5BF", "#DCDDCB", "#2B2119", "#6E6150", "#E2D5B4", "#A3261B", "#3D6E9E", "#6F9DC6"
BG = "#F7F0DE"
COL = {sp: SPECIES[sp][2] for sp in SPECIES}
HALO = [pe.withStroke(linewidth=3.2, foreground=PAPER)]

LANDG = shapely.from_geojson(json.dumps(jload(f"{DATA}/geo/land.json")))
BORD = jload(f"{DATA}/geo/borders.json")
RIV = jload(f"{DATA}/geo/rivers.json")
LAKE = jload(f"{DATA}/geo/lakes.json")


def _polys(g):
    return list(getattr(g, "geoms", [g])) if g.geom_type in ("Polygon", "MultiPolygon", "GeometryCollection") else []


def _lines(g):
    out = []
    for x in getattr(g, "geoms", [g]):
        if x.geom_type == "LineString":
            out.append(np.asarray(x.coords))
        elif x.geom_type in ("MultiLineString", "LinearRing"):
            out += _lines(x) if x.geom_type == "MultiLineString" else [np.asarray(x.coords)]
        elif x.geom_type == "Polygon":
            out.append(np.asarray(x.exterior.coords)); out += [np.asarray(i.coords) for i in x.interiors]
        elif hasattr(x, "geoms"):
            out += _lines(x)
    return out


_RIP = {}


def ink_map(ax, ext, ripples=(0.35, 0.75, 1.2), borders=True, rivers=True, scale=1.0):
    """Parchment map of ext = (lon0, lon1, lat0, lat1): sea wash, paper land with grain, ink coast and ripples."""
    box = shapely.box(ext[0] - 3, ext[2] - 3, ext[1] + 3, ext[3] + 3)
    land = LANDG.intersection(box)
    ax.set_facecolor(SEA)
    pat = [MPoly(np.asarray(p.exterior.coords), closed=True) for p in _polys(land) if p.area > 0.01]
    ax.add_collection(PatchCollection(pat, fc=PAPER, ec="none", zorder=1))
    # grain
    rs = np.random.default_rng(3)
    n = int(3500 * scale)
    gx, gy = rs.uniform(ext[0], ext[1], n), rs.uniform(ext[2], ext[3], n)
    ax.scatter(gx, gy, s=rs.uniform(.2, 1.4, n), c="#8A6A3A", alpha=.08, lw=0, zorder=1.1)
    # ripples: rings outside the coast, black first then blue
    k = (ext[1] - ext[0]) / 60
    for i, d in enumerate(ripples):
        key = (round(d * k, 3), tuple(np.round(ext, 1)))
        if key not in _RIP:
            simple = shapely.simplify(land, 0.05 * k)
            _RIP[key] = _lines(simple.buffer(d * k, quad_segs=4).boundary)
        ax.add_collection(LineCollection(_RIP[key], colors=[INK if i == 0 else (BLUE if i == 1 else BLUES)], linewidths=.45 * scale, alpha=.5 if i == 0 else .4, zorder=1.2))
    if rivers:
        rl = []
        for f in RIV["features"]:
            rl += _lines(shapely.from_geojson(json.dumps(f["geometry"])))
        ax.add_collection(LineCollection(rl, colors=BLUE, linewidths=.55 * scale, alpha=.65, zorder=1.3))
        lk = [MPoly(np.asarray(p.exterior.coords), closed=True) for f in LAKE["features"] for p in _polys(shapely.from_geojson(json.dumps(f["geometry"])))]
        ax.add_collection(PatchCollection(lk, fc="#C9D4D0", ec=INK, lw=.4 * scale, zorder=1.3))
    if borders:
        bl = []
        for f in BORD["features"]:
            bl += _lines(shapely.from_geojson(json.dumps(f["geometry"])))
        ax.add_collection(LineCollection(bl, colors=INK, linewidths=.4 * scale, alpha=.35, linestyles=(0, (5, 2, 1, 2)), zorder=1.4))
    ax.add_collection(LineCollection(_lines(land.boundary), colors=INK, linewidths=.8 * scale, zorder=1.5))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect(1 / np.cos(np.radians((ext[2] + ext[3]) / 2)))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(INK); s.set_linewidth(1.2 * scale)


_SPR = {}


def sprite(ax, kind, x, y, px=40, rot=0, z=6, dpi=100):
    """A pen-drawn bird at (x, y), px pixels wide at the figure's dpi, rotated rot degrees clockwise from north."""
    if kind not in _SPR:
        _SPR[kind] = Image.open(f"{ROOT}/img/sprites/{kind}.png").convert("RGBA")
    im = _SPR[kind].rotate(-rot, resample=Image.BICUBIC, expand=False)
    ab = AnnotationBbox(OffsetImage(np.asarray(im), zoom=px / im.size[0]), (x, y), frameon=False, zorder=z)
    ax.add_artist(ab)
    return ab


def hand(ax, x, y, s, size=14, color=INK, italic=True, ha="center", va="center", z=8, halo=True, **kw):
    return ax.text(x, y, s, fontproperties=FELLI if italic else FELL, fontsize=size, color=color, ha=ha, va=va, zorder=z,
                   path_effects=HALO if halo else None, **kw)


def caps(ax, x, y, s, size=11, color="#6E5A44", z=7, **kw):
    return ax.text(x, y, " ".join(s.upper()), fontproperties=FELLSC, fontsize=size, color=color, ha="center", va="center", zorder=z, path_effects=HALO, **kw)


def bearing(a, b):
    l1, l2, dl = np.radians(a[1]), np.radians(b[1]), np.radians(b[0] - a[0])
    return (np.degrees(np.arctan2(np.sin(dl) * np.cos(l2), np.cos(l1) * np.sin(l2) - np.sin(l1) * np.cos(l2) * np.cos(dl))) + 360) % 360


def screen_bearing(ax, a, b):
    """Bearing on the drawn map (accounts for the axis aspect), for rotating sprites."""
    asp = 1 / np.cos(np.radians(np.mean(ax.get_ylim())))
    dx, dy = (b[0] - a[0]), (b[1] - a[1]) * asp
    return (np.degrees(np.arctan2(dx, dy)) + 360) % 360


def tracks(sp):
    d = pd.read_csv(f"{DATA}/daily_{sp}.csv", parse_dates=["day"])
    d["animal"] = d.animal.astype(str)
    return d


def segs(g, maxgap=8):
    """Line pieces of one animal's daily track, broken at gaps longer than maxgap days."""
    out, cur = [], []
    prev = None
    for r in g.itertuples():
        if prev is not None and (r.day - prev).days > maxgap and len(cur) > 1:
            out.append(np.array(cur)); cur = []
        cur.append((r.lon, r.lat)); prev = r.day
    if len(cur) > 1:
        out.append(np.array(cur))
    return out


import pandas as pd  # noqa: E402  (used by tracks)


def paper_fig(w, h, dpi=100):
    fig = plt.figure(figsize=(w, h), dpi=dpi, facecolor=BG)
    return fig


def spines(ax):
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
