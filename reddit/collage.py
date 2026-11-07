"""Reddit collage (r/dataisbeautiful): the four flyways drawn in ink on parchment, with pen-drawn birds, the funnels,
winter quarters and a full legend. Every number from data/results.json. Output: reddit/where_the_storks_go.png"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *

R = jload(f"{DATA}/results.json")
AN = pd.read_csv(f"{DATA}/animals.csv"); AN["animal"] = AN.animal.astype(str)
MG = pd.read_csv(f"{DATA}/migrations.csv")
WA = jload(f"{DATA}/winter_areas.geojson")
D = {sp: tracks(sp) for sp in SPECIES}
DPI = 100
fig = plt.figure(figsize=(27, 33), dpi=DPI, facecolor=BG)


def winter(ax, sp):
    for f in WA["features"]:
        p = f["properties"]
        if p["species"] != sp:
            continue
        g = shapely.from_geojson(json.dumps(f["geometry"]))
        for poly in getattr(g, "geoms", [g]):
            xy = np.asarray(poly.exterior.coords)
            if p["level"] == 50:
                ax.add_patch(MPoly(xy, closed=True, fc="none", ec=COL[sp], lw=1.6, hatch="////", alpha=.8, zorder=3))
            else:
                ax.plot(xy[:, 0], xy[:, 1], color=COL[sp], lw=1.3, ls=(0, (2, 2)), alpha=.75, zorder=3)


def draw(ax, sp, alpha, lw):
    for aid, g in D[sp].groupby("animal"):
        for s in segs(g):
            ax.plot(s[:, 0], s[:, 1], color=COL[sp], lw=lw, alpha=alpha, solid_capstyle="round", zorder=4)


def birds(ax, sp, picks, px):
    """Pen birds on chosen autumn migrations, part way along, pointing along the track."""
    placed = []
    for aid, frac in picks:
        m = MG[(MG.species == sp) & (MG.animal.astype(str) == aid) & (MG.kind == "autumn")].iloc[0]
        g = D[sp][D[sp].animal == aid].set_index("day").sort_index()
        g = g[(g.index >= m.depart) & (g.index <= m.arrive)]
        i = max(1, min(len(g) - 2, int(len(g) * frac)))
        a, b = g.iloc[i - 1][["lon", "lat"]].values, g.iloc[i + 1][["lon", "lat"]].values
        xy = g.iloc[i][["lon", "lat"]].values
        if any(np.hypot(xy[0] - q[0], xy[1] - q[1]) < 7 for q in placed):
            continue                                   # never let two birds overlap
        placed.append(xy)
        sprite(ax, sp, *xy, px=px, rot=screen_bearing(ax, a, b), z=9)


def note(ax, x, y, s, size=28, color=INK, ha="center"):
    return ax.text(x, y, s, fontproperties=FELLI, fontsize=size, color=color, ha=ha, va="center", zorder=10, linespacing=1.15,
                   path_effects=[pe.withStroke(linewidth=6, foreground=SEA)])


def pick(sp, n, seed):
    m = MG[(MG.species == sp) & (MG.kind == "autumn") & (MG.cover >= .5)]
    s = m.sample(min(n, len(m)), random_state=seed)
    return [(str(a), f) for a, f in zip(s.animal, np.linspace(.3, .7, len(s)))]


# title (subtitle set well below the title's descenders)
fig.text(0.035, 0.977, "Where the storks go", fontproperties=DISP, fontsize=78, color=INK, va="top")
fig.text(0.035, 0.922, f"{R['total']['animals']} birds of four species, tracked by satellite and GPS across three continents. "
         "Faint lines: daily positions; hatched: where each species spent the winter.", fontproperties=SERP, fontsize=27, color=MUT, va="top")
PANELS = [("stork", [0.025, 0.525, 0.47, 0.33], (-20, 62, -36, 58)), ("osprey", [0.505, 0.525, 0.47, 0.33], (-128, -34, -22, 56)),
          ("cuckoo", [0.025, 0.135, 0.47, 0.285], (0, 58, -22, 62)), ("harrier", [0.505, 0.135, 0.47, 0.285], (-26, 14, 6, 54))]
SUB = {"stork": f"{R['stork']['n']} young storks, 8 populations, 2013 to 2014. {R['sp']['stork']['sea_pct']:.1f}% of their flying was over the sea.",
       "osprey": f"{R['osprey']['n']} ospreys, eastern, midwestern and western USA, 1995 to 2002. {R['sp']['osprey']['sea_pct']:.0f}% over the sea.",
       "cuckoo": f"{R['cuckoo']['n']} cuckoos from the Baltic, {R['cuckoo']['displaced']} of them first carried {R['cuckoo']['displace_km']:,} km east to Kazan.",
       "harrier": f"{R['harrier']['n']} marsh harriers from Antwerp, 2018 to 2022: {R['harrier']['n_migr']} complete migrations."}
# what each map shows, written in the paper margin under the map (no label sits on land or on the tracks)
NOTES = {"stork": [(RED, f"Red chevrons, the funnels: Gibraltar {R['stork']['gib_total']} storks, Bosporus and Dardanelles {R['stork']['straits_total']}, the Levant {R['stork']['levant_total']}."),
                   (INK, f"Crosses: {R['stork']['dead']} of the {R['stork']['n']} young storks were found dead within the year.")],
         "osprey": [(RED, f"Red chevron: {R['osprey']['cuba']} ospreys passed Florida and Cuba."),
                    (BLUE, f"{R['osprey']['carib_n']} flew 300 km or more of open sea, mostly over the Caribbean; {R['osprey']['n_south_america']} reached South America.")],
         "cuckoo": [("#5E7A3A", "Nests: released at Rybachy on the Baltic (left) or at Kazan (right)."),
                    (BLUE, f"{R['cuckoo']['n_cross_med']} crossed the Mediterranean; one flew Poland to Chad, {R['cuckoo']['fast'][0]['km']:,.0f} km, in {R['cuckoo']['fast'][0]['days']:.1f} days.")],
         "harrier": [(RED, f"Lilla flew {R['sp']['harrier']['max_day_km']:,.0f} km in a day, central Spain to Morocco."),
                     (INK, f"She wintered near Dakar three years running, all within {R['harrier']['lilla_max_shift']:.1f} km.")]}
import textwrap
for sp, rect, ext in PANELS:
    ax = fig.add_axes(rect)
    ink_map(ax, ext, scale=1.6)
    winter(ax, sp)
    draw(ax, sp, .38 if sp in ("stork", "osprey") else .6, 1.1 if sp != "harrier" else 1.7)
    ax.set_title(f"{SPECIES[sp][0]}  ({SPECIES[sp][1]})", fontproperties=FELLI, fontsize=40, color=COL[sp], pad=46, loc="left")
    ax.text(0, 1.012, SUB[sp], transform=ax.transAxes, fontproperties=SERP, fontsize=21, color=MUT, va="bottom")
    if sp == "stork":
        birds(ax, sp, pick(sp, 6, 3), 76)
        for x, y in ((-5.6, 35.95), (27.8, 40.7), (35.2, 31.6)):
            sprite(ax, "gate", x, y, px=62, z=8)
        for r in AN[(AN.species == "stork") & AN.confirmed_dead].itertuples():
            sprite(ax, "cross", r.last_lon, r.last_lat, px=34, z=8)
    if sp == "osprey":
        birds(ax, sp, pick(sp, 6, 5), 62)
        sprite(ax, "gate", -81.2, 23.6, px=56, z=8)
    if sp == "cuckoo":
        birds(ax, sp, [(a, .5) for a, _ in pick(sp, 3, 1)], 54)
        sprite(ax, "nest", 20.86, 55.15, px=40); sprite(ax, "nest", 49.09, 55.62, px=40)
    if sp == "harrier":
        birds(ax, sp, [("H197169", .35), ("L177801", .6), ("H197169", .75)], 64)
    ax.apply_aspect()
    pos = ax.get_position()
    y = pos.y0 - 0.006
    width_chars = int(pos.width * 27 * 72 / 22 * 1.9)
    for col, txt in NOTES[sp]:
        lines = textwrap.wrap(txt, width_chars)
        fig.text(pos.x0, y, "\n".join(lines), fontproperties=FELLI, fontsize=24, color=col, va="top", ha="left", linespacing=1.1)
        y -= 0.0095 * len(lines) + 0.003

# legend
lg = fig.add_axes([0.025, 0.033, 0.95, 0.04]); lg.set_xlim(0, 100); lg.set_ylim(0, 10); lg.axis("off")
x = 0.5
for k, t, w in [("stork", "White stork", 14), ("osprey", "Osprey", 10.5), ("cuckoo", "Common cuckoo", 17), ("harrier", "Western marsh harrier", 22)]:
    sprite(lg, k, x + 1.3, 5.5, px=64, z=9); lg.text(x + 3.5, 5.5, t, fontproperties=FELLI, fontsize=30, color=COL[k], va="center"); x += w
lg.add_patch(plt.Rectangle((x, 3.9), 2.0, 3.2, fc="none", ec=INK, hatch="////", lw=1.2)); lg.text(x + 2.6, 5.5, "winter quarters", fontsize=19, va="center"); x += 15
sprite(lg, "cross", x, 5.5, px=40); lg.text(x + 1.3, 5.5, "found dead", fontsize=19, va="center"); x += 11.5
sprite(lg, "gate", x, 5.5, px=48); lg.text(x + 1.5, 5.5, "funnel", fontsize=19, va="center")
fig.text(0.035, 0.022, "Data (all CC0): Flack et al. 2015, Movebank Data Repository, doi:10.5441/001/1.78152p3q; Martell and Douglas 2019, doi:10.5441/001/1.sv6335t3;", fontsize=14, color=MUT)
fig.text(0.035, 0.009, "Thorup et al. 2020, doi:10.5441/001/1.vk36vq82; INBO MH_ANTWERPEN, doi:10.5281/zenodo.8238402. Base map: Natural Earth. Lettering: IM Fell.", fontsize=14, color=MUT)
fig.text(0.965, 0.013, "maps.tristanhotham.com/bird-migration", fontsize=22, color=RED, ha="right")
fig.text(0.965, 0.977, "Dr Tristan Hotham", fontsize=19, color=MUT, ha="right", va="top")
out = os.path.join(ROOT, "reddit", "where_the_storks_go.png")
fig.savefig(out, dpi=DPI, facecolor=BG)
print(out, Image.open(out).size)
