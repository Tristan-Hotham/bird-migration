"""Figures: blog (release/blog/b_*.png), paper (release/paper/f_*.png) and the social card (header.png)."""
import sys
from figstyle import *

R = jload(f"{DATA}/results.json")
AN = pd.read_csv(f"{DATA}/animals.csv")
AN["animal"] = AN.animal.astype(str)
MG = pd.read_csv(f"{DATA}/migrations.csv")
SC = pd.read_csv(f"{DATA}/sea_crossings.csv")
WA = jload(f"{DATA}/winter_areas.geojson")
BLOG, PAP = f"{ROOT}/release/blog", f"{ROOT}/release/paper"
os.makedirs(BLOG, exist_ok=True); os.makedirs(PAP, exist_ok=True)
D = {sp: tracks(sp) for sp in SPECIES}
EXT = {"stork": (-20, 75, -36, 58), "osprey": (-128, -35, -22, 56), "cuckoo": (-2, 58, -22, 62), "harrier": (-24, 12, 6, 54)}
POPCOL = {"SW Germany": "#8C2E1E", "Spain (Doñana)": "#C9622E", "Tunisia": "#C9A24A", "Poland": "#6E8250", "Greece (Evros Delta)": "#3D6E9E",
          "Russia (Moscow)": "#664C36", "Armenia": "#9C5A8A", "Uzbekistan": "#4E6A4C", "South Africa": "#7A6A52"}


def save(fig, name, blog=True, paper=True):
    if blog:
        fig.savefig(f"{BLOG}/b_{name}.png", dpi=110, facecolor=fig.get_facecolor())
    if paper:
        fig.savefig(f"{PAP}/f_{name}.png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def winter(ax, sp, lw=1.0):
    for f in WA["features"]:
        p = f["properties"]
        if p["species"] != sp:
            continue
        g = shapely.from_geojson(json.dumps(f["geometry"]))
        for poly in getattr(g, "geoms", [g]):
            xy = np.asarray(poly.exterior.coords)
            if p["level"] == 50:
                ax.add_patch(MPoly(xy, closed=True, fc="none", ec=COL[sp], lw=lw, hatch="////", alpha=.75, zorder=3))
            else:
                ax.plot(xy[:, 0], xy[:, 1], color=COL[sp], lw=lw * .8, ls=(0, (2, 2)), alpha=.7, zorder=3)


def draw_tracks(ax, sp, color=None, by=None, lw=.7, alpha=.45, sel=None):
    d = D[sp]
    for aid, g in d.groupby("animal"):
        if sel is not None and aid not in sel:
            continue
        c = color or COL[sp]
        if by is not None:
            c = by.get(aid, c)
        for s in segs(g):
            ax.plot(s[:, 0], s[:, 1], color=c, lw=lw, alpha=alpha, solid_capstyle="round", zorder=4)


def birds_on(ax, sp, n=6, px=34, seed=1, day_frac=None):
    """A few pen birds sitting on their tracks, pointing along them (mid-migration positions)."""
    m = MG[(MG.species == sp) & (MG.kind == "autumn")]
    rs = np.random.default_rng(seed)
    picks = m.sample(min(n, len(m)), random_state=seed) if len(m) else []
    for r in (picks.itertuples() if len(m) else []):
        g = D[sp][D[sp].animal == str(r.animal)].set_index("day").sort_index()
        g = g[(g.index >= r.depart) & (g.index <= r.arrive)]
        if len(g) < 4:
            continue
        i = int(len(g) * (day_frac if day_frac is not None else rs.uniform(.25, .75)))
        i = max(1, min(len(g) - 2, i))
        a, b = g.iloc[i - 1][["lon", "lat"]].values, g.iloc[i + 1][["lon", "lat"]].values
        sprite(ax, sp, *g.iloc[i][["lon", "lat"]].values, px=px, rot=screen_bearing(ax, a, b))


# ---------------- 1. the four flyways
def flyways(fig, axs, px=32, title=True):
    for ax, sp in zip(axs, ["stork", "osprey", "cuckoo", "harrier"]):
        ink_map(ax, EXT[sp], scale=.9)
        winter(ax, sp)
        draw_tracks(ax, sp, alpha=.35 if sp in ("stork", "osprey") else .55, lw=.65 if sp != "harrier" else 1.0)
        birds_on(ax, sp, n={"stork": 6, "osprey": 6, "cuckoo": 3, "harrier": 3}[sp], px=px, seed=4)
        if title:
            n = R["sp"][sp]["n"]
            ax.set_title(f"{SPECIES[sp][0]}s · {n}", fontproperties=FELLI, fontsize=19, color=COL[sp], pad=6)


fig = paper_fig(13, 10.5)
axs = [fig.add_axes(r) for r in ([0.02, 0.5, 0.47, 0.45], [0.51, 0.5, 0.47, 0.45], [0.02, 0.02, 0.47, 0.45], [0.51, 0.02, 0.47, 0.45])]
flyways(fig, axs)
save(fig, "flyways")

# ---------------- 2. stork routes by population, with the funnels
fig = paper_fig(12, 11)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
ext = (-20, 72, -36, 58)
ink_map(ax, ext)
pops = AN[AN.species == "stork"].set_index("animal").population.to_dict()
draw_tracks(ax, "stork", by={a: POPCOL[p] for a, p in pops.items()}, alpha=.55, lw=.8)
for p, (x, y) in {"SW Germany": (8.9, 47.8), "Spain (Doñana)": (-6.0, 37.4), "Tunisia": (10.3, 36.8), "Poland": (15.5, 51.9),
                  "Greece (Evros Delta)": (26.2, 40.9), "Russia (Moscow)": (37.4, 55.6), "Armenia": (44.5, 40.2), "Uzbekistan": (69.0, 41.0)}.items():
    sprite(ax, "nest", x, y, px=44)
LBL = {"SW Germany": (-1, 52.5, "left"), "Spain (Doñana)": (-13.5, 36.3, "center"), "Tunisia": (6.5, 39.2, "center"), "Poland": (12, 56.2, "center"),
       "Greece (Evros Delta)": (19.5, 43.8, "center"), "Russia (Moscow)": (40, 54.6, "left"), "Armenia": (50.5, 44.5, "center"), "Uzbekistan": (66.5, 45, "center")}
for p, (x, y, ha) in LBL.items():
    hand(ax, x, y, p, size=15, color=POPCOL[p], ha=ha)
for nm, (x, y, s, lx, ly) in {"Strait of Gibraltar": (-5.6, 35.95, R["stork"]["gib_total"], -14.5, 40.5), "Bosporus and Dardanelles": (27.8, 40.7, R["stork"]["straits_total"], 34.6, 43.4),
                              "The Levant": (35.2, 31.6, R["stork"]["levant_total"], 28.5, 33.6)}.items():
    sprite(ax, "gate", x, y, px=46, z=7)
    hand(ax, lx, ly, f"{nm}\n{s} storks", size=15, color=RED)
for i, (x, y) in enumerate([(-2, 19), (14, 14), (30, 13)]):
    pass
caps(ax, 10, 21, "Sahara", size=16)
caps(ax, 14, 10.5, "Sahel", size=13)
caps(ax, 17, 35.0, "Mediterranean Sea", size=10, color=BLUE)
d = AN[(AN.species == "stork") & (AN.confirmed_dead)]
for r in d.itertuples():
    sprite(ax, "cross", r.last_lon, r.last_lat, px=30, z=7)
hand(ax, 52, -24, "Young white storks tagged\nin the nest in 2013,\ndaily positions to July 2014.\nCrosses: found dead.", size=15, ha="left")
save(fig, "storks")

# ---------------- 3. share over the sea (bars) and the osprey crossings
fig = paper_fig(10, 4.6)
ax = fig.add_axes([0.27, 0.18, 0.68, 0.72]); spines(ax)
sps = ["stork", "osprey", "cuckoo", "harrier"]
v = [R["sp"][s]["sea_pct"] for s in sps]
ax.barh(range(4), v, color=[COL[s] for s in sps], height=.6)
for i, x in enumerate(v):
    ax.text(x + .3, i, f"{x:.1f}%" if x >= 1 else f"{x:.2f}%", va="center", fontsize=12)
ax.set_yticks(range(4)); ax.set_yticklabels([SPECIES[s][0] for s in sps], fontproperties=FELLI, fontsize=16)
ax.invert_yaxis(); ax.set_xlim(0, 25); ax.set_xlabel("share of distance flown over the open sea")
ax.set_title("Who crosses the sea", fontproperties=FELLI, fontsize=22, loc="left", color=INK)
save(fig, "sea")

# ---------------- 4. migration speeds
fig = paper_fig(10, 4.6)
ax = fig.add_axes([0.27, 0.17, 0.69, 0.72]); spines(ax)
mg = MG[(MG.cover >= .5) & (MG.max_gap <= 5)]
rs = np.random.default_rng(2)
for i, s in enumerate(sps):
    m = mg[mg.species == s]
    for kind, fc in (("autumn", COL[s]), ("spring", "none")):
        x = m[m.kind == kind]
        ax.scatter(x.km_per_day, i + rs.uniform(-.18, .18, len(x)), s=46, facecolor=fc, edgecolor=COL[s], lw=1.4, zorder=3)
    if not len(m):
        ax.text(5, i, "too few well-covered migrations", va="center", color=MUT, fontsize=11)
ax.set_yticks(range(4)); ax.set_yticklabels([SPECIES[s][0] for s in sps], fontproperties=FELLI, fontsize=16)
ax.invert_yaxis(); ax.set_xlim(0, 400); ax.set_xlabel("km a day, departure to arrival (filled: autumn, open: spring)")
ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
ax.set_title("How fast they migrate", fontproperties=FELLI, fontsize=22, loc="left", color=INK)
save(fig, "speed")

# ---------------- 5. stork winter latitude and fate by population
fig = paper_fig(10, 5.6)
ax = fig.add_axes([0.24, 0.13, 0.72, 0.78]); spines(ax)
order = ["SW Germany", "Spain (Doñana)", "Tunisia", "Poland", "Greece (Evros Delta)", "Russia (Moscow)", "Armenia", "Uzbekistan", "South Africa"]
st = AN[AN.species == "stork"]
ax.axvspan(5, 20, color=RED, alpha=.07, lw=0)
ax.text(12.5, -0.9, "Sahel belt", ha="center", color=MUT, fontsize=10)
for i, p in enumerate(order):
    x = st[(st.population == p) & st.winter_lat.notna()]
    for j, r in enumerate(x.itertuples()):
        y = i + ((j % 3) - 1) * .15
        if r.confirmed_dead:
            ax.plot(r.winter_lat, y, marker="+", ms=11, mew=2.2, color=INK, zorder=4)
        else:
            ax.plot(r.winter_lat, y, "o", ms=8, color=POPCOL[p], mec=PAPER, zorder=4)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontproperties=FELLI, fontsize=15)
ax.set_ylim(len(order) - .4, -1.3); ax.set_xlim(45, -38)
ax.set_xticks([40, 20, 0, -20, -35]); ax.set_xticklabels(["40°N", "20°N", "equator", "20°S", "35°S"])
ax.grid(axis="x", color=RULE); ax.set_axisbelow(True)
ax.set_title("Where the young storks spent the winter", fontproperties=FELLI, fontsize=22, loc="left", color=INK)
ax.text(1, -.1, "Median December and January latitude of each stork; +: later found dead", transform=ax.transAxes, ha="right", fontsize=10, color=MUT)
save(fig, "winter")

# ---------------- 6. fates of the storks by population (stacked bars)
fig = paper_fig(10, 5.2)
ax = fig.add_axes([0.24, 0.12, 0.72, 0.78]); spines(ax)
for i, p in enumerate(order):
    x = st[st.population == p]
    left = x.max_from_tag_km >= 300
    a = int((x.confirmed_dead & ~left).sum()); b = int((x.confirmed_dead & left).sum()); c = len(x) - a - b
    ax.barh(i, a, color=INK, height=.62); ax.barh(i, b, left=a, color=RED, height=.62); ax.barh(i, c, left=a + b, color="#D9C9A0", height=.62)
    ax.text(len(x) + .2, i, f"{a + b} of {len(x)}", va="center", fontsize=11)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontproperties=FELLI, fontsize=15); ax.invert_yaxis()
ax.set_xlabel("young storks tagged")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=INK, label="died before leaving home"), Patch(color=RED, label="died after leaving"), Patch(color="#D9C9A0", label="not known dead")],
          loc="lower right", frameon=False, fontsize=10)
ax.set_title("The cost of the first year", fontproperties=FELLI, fontsize=22, loc="left", color=INK)
save(fig, "fates")

# ---------------- 7. Lilla and Lillo: the same road every year
fig = paper_fig(8, 10.5)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
ext = (-24, 10, 6, 54)
ink_map(ax, ext)
cols = {"autumn": RED, "spring": BLUE}
for nm, aid, ls in (("Lilla", "H197169", "-"), ("Lillo", "L177801", (0, (4, 2)))):
    g = D["harrier"][D["harrier"].animal == aid].set_index("day").sort_index()
    for m in MG[(MG.species == "harrier") & (MG.animal == aid)].itertuples():
        x = g[(g.index >= m.depart) & (g.index <= m.arrive)]
        ax.plot(x.lon, x.lat, color=cols[m.kind], lw=1.4, ls=ls, alpha=.85, zorder=4)
    for w in R["harrier"]["birds"][nm]["winters"][:1]:
        sprite(ax, "harrier", w["lon"] + (1.6 if nm == "Lilla" else 1.4), w["lat"] + .8, px=70, rot=200)
hand(ax, -21.5, 16.6, "Lilla's winters\nnear Dakar", size=16, ha="left", color=RED)
hand(ax, -11.2, 8.4, "Lillo's winters\nin Guinea", size=16, ha="left", color=RED)
hand(ax, 2.5, 53.2, "the nests, near Antwerp", size=15)
hand(ax, -22.5, 50, "Two marsh harriers,\nfive autumns (red)\nand three springs (blue).\nSolid: Lilla. Dashed: Lillo.", size=16, ha="left")
caps(ax, -3, 23, "Sahara", size=15)
save(fig, "harriers")

# ---------------- 8. the cuckoo experiment
fig = paper_fig(10, 9.5)
ax = fig.add_axes([0.01, 0.01, 0.98, 0.98])
ext = (5, 60, -22, 62)
ink_map(ax, ext)
disp = set(AN[(AN.species == "cuckoo") & (AN.displaced.astype(str) == "True")].animal)
for aid, g in D["cuckoo"].groupby("animal"):
    c = "#8C2E1E" if aid in disp else "#5E7A3A"
    for s in segs(g, maxgap=12):
        ax.plot(s[:, 0], s[:, 1], color=c, lw=1.0, alpha=.7, zorder=4)
sprite(ax, "nest", 20.86, 55.15, px=24); sprite(ax, "nest", 49.09, 55.62, px=24)
hand(ax, 20.5, 58.7, "Rybachy:\nreleased at home", size=15, color="#5E7A3A")
hand(ax, 49, 59, "Kazan: released after\nbeing carried east", size=15, color="#8C2E1E")
sprite(ax, "cuckoo", 18.4, 38.7, px=40, rot=185)
hand(ax, 30.5, 30, "One young cuckoo:\nPoland to Chad\nin under five days", size=15, ha="left")
caps(ax, 18, 22, "Sahara", size=15)
save(fig, "cuckoos")

# ---------------- social card 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([0.44, 0.0, 0.56, 1.0])
ink_map(ax, (-22, 60, -36, 60), scale=.9)
draw_tracks(ax, "stork", alpha=.45, lw=.75)
draw_tracks(ax, "harrier", alpha=.6, lw=.9)
winter(ax, "stork")
birds_on(ax, "stork", n=6, px=42, seed=4)
for s in ax.spines.values():
    s.set_visible(False)
fig.text(0.04, 0.80, "Where the", fontproperties=DISP, fontsize=50, color=INK)
fig.text(0.04, 0.64, "storks go", fontproperties=FELLI, fontsize=70, color=RED)
fig.text(0.04, 0.50, f"{R['total']['animals']} tagged birds of four species:\nwhite storks, ospreys, cuckoos\nand marsh harriers, followed\nacross three continents.", fontsize=15, color=INK, va="top", linespacing=1.4)
fig.text(0.04, 0.215, f"Storks fly round the sea: {R['sp']['stork']['sea_pct']:.1f}% of their\nflying was over water. Ospreys: {R['sp']['osprey']['sea_pct']:.0f}%.", fontsize=13, color=MUT, va="top", linespacing=1.4)
fig.text(0.04, 0.035, "maps.tristanhotham.com/bird-migration", fontsize=11, color=RED)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=BG)
plt.close(fig)
print(sorted(os.listdir(BLOG)), sorted(f for f in os.listdir(PAP) if f.endswith(".png")))
