"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24043676, https://doi.org/10.5281/zenodo.24043676 and https://blog.tristanhotham.com/2026/10/31/bird-migration/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
import pandas as pd
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Where_the_Storks_Go"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
S = R["stork"]

# numbers written in words or in alt text (blog, collage, page)
assert (round(R["sp"]["stork"]["sea_pct"], 2), round(R["sp"]["osprey"]["sea_pct"]), round(R["sp"]["cuckoo"]["sea_pct"], 1), round(R["sp"]["harrier"]["sea_pct"], 1)) == (0.61, 22, 5.4, 3.7)
assert (S["gib_total"], S["straits_total"], S["levant_total"]) == (13, 21, 20)
P = S["pops"]
assert [(P[p]["dead"], P[p]["n"]) for p in ("SW Germany", "Tunisia", "Armenia", "Uzbekistan", "Russia (Moscow)")] == [(6, 13), (7, 9), (5, 8), (4, 6), (1, 10)]
sp = {}
for m in SITE["migs"]:
    sp.setdefault(m[0], []).append(m[2])
assert round(min(sp["stork"])) == 18 and round(max(sp["stork"])) == 256 and sum(v < 120 for v in sp["stork"]) > len(sp["stork"]) / 2
assert round(min(sp["osprey"])) == 47 and round(max(sp["osprey"])) == 350 and round(min(sp["harrier"])) == 58 and round(max(sp["harrier"])) == 144 and "cuckoo" not in sp
wl = {}
for p, lat, dead, a in SITE["winlat"]:
    wl.setdefault(p, []).append(lat)
assert all(8 <= v <= 16 for v in wl["Tunisia"]) and sum(8 <= v <= 16 for v in wl["Russia (Moscow)"]) > len(wl["Russia (Moscow)"]) / 2
assert S["far_country"] == "Zimbabwe" and S["far_pop"] == "Russia (Moscow)" and R["cuckoo"]["fast"][0]["date"] == "2017-09-27"
assert R["cuckoo"]["fast"][0]["from"] == "Poland" and R["cuckoo"]["fast"][0]["to"] == "Chad"
an = pd.read_csv(f"{DATA}/animals.csv")
assert an[(an.species == "harrier") & (an.animal == "H197169")].max_day_km.iloc[0] == R["sp"]["harrier"]["max_day_km"]   # Lilla's record day
assert R["sp"]["osprey"]["longest_sea_animal"] == "KD"
assert len(R["harrier"]["birds"]["Lilla"]["winters"]) == 3 and len(R["harrier"]["birds"]["Lillo"]["winters"]) == 2   # "three winters", "twice"
dh = pd.read_csv(f"{DATA}/daily_harrier.csv"); dh = dh[dh.animal == "H197169"].reset_index(drop=True)
k = int(hav(dh.lon[:-1].values, dh.lat[:-1].values, dh.lon[1:].values, dh.lat[1:].values).argmax())
assert dh.day[k] == "2019-09-11" and dh.lat[k] > 38 and dh.lat[k + 1] < 33          # left central Spain 11 September 2019, Morocco next noon

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
visible_ok(post)
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Where the storks go: four migratory birds on one hand-inked map",
        "slug": "bird-migration",
        "excerpt": f"I followed {R['total']['animals']} tagged birds across three continents. Young storks flew {R['sp']['stork']['sea_pct']:.1f}% of their distance over the sea and squeezed through Gibraltar and the Bosporus; ospreys and cuckoos cross the open sea without a second thought.",
        "seo_description": "Storks, ospreys, cuckoos and marsh harriers tracked by satellite across three continents: routes, funnels, sea crossings, winter quarters and fates.",
        "tags": ["birds", "migration", "white stork", "osprey", "cuckoo", "marsh harrier", "maps", "data visualisation", "Movebank"],
        "header_alt": f"Title card reading 'Where the storks go' in black and red hand lettering on parchment, beside a hand-inked map of Europe and Africa with the red tracks of young white storks funnelling through Gibraltar and the Levant to the Sahel, and pen-drawn storks flying along them. Text: {R['total']['animals']} tagged birds of four species; storks flew {R['sp']['stork']['sea_pct']:.1f}% of their distance over water, ospreys {R['sp']['osprey']['sea_pct']:.0f}%."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/bird-migration_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "data/geo", "js", "img/sprites"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            fp = os.path.join(ROOT, d, fn)
            if fn.endswith(".pyc") or fn == "__pycache__" or os.path.isdir(fp):
                continue
            z.write(fp, f"bird-migration/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"bird-migration/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "bird-migration/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = re.sub(r"\\textit\{([^}]*)\}", r"\1", ab).replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Where the Storks Go: Routes, Funnels, Sea Crossings, Winter Quarters and Fates of Four Migratory Bird Species in Four Open Tracking Data Sets",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Sources (all CC0): " + "; ".join(f"{SOURCES[s]['short']}, https://doi.org/{SOURCES[s]['doi']}" for s in SPECIES) + ". Natural Earth (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["bird migration", "animal tracking", "white stork", "osprey", "common cuckoo", "marsh harrier", "flyways", "Movebank", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}] +
                                [{"identifier": f"https://doi.org/{SOURCES[s]['doi']}", "relation": "isDerivedFrom", "resource_type": "dataset"} for s in SPECIES] +
                                [{"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
visible_ok(sj)
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
