"""README.md, LICENSE and the Reddit post text, numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
S, O, C, H, M = R["stork"], R["osprey"], R["cuckoo"], R["harrier"], R["migr"]
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.1f} MB"
readme = f"""# Where the storks go

Four species of migratory bird followed across three continents, from four open tracking data sets cleaned in the same way: {S['n']} young white storks from eight populations (GPS, 2013 to 2014), {O['n']} North American ospreys (Argos, 1995 to 2002), {C['n']} common cuckoos from a displacement experiment (Argos and GPS, 2015 to 2020) and {H['n']} western marsh harriers from Belgium (GPS, 2018 to 2022): {R['total']['daily']:,} daily positions, drawn as animated pen-drawn birds on a hand-inked map in the style of The Inked World.

Interactive page: {PAGE}
Paper: https://doi.org/{{10.5281/zenodo.24043676}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/bird-migration/}}
Code and data: {REPO}

## Headline results

- Two roads to Africa: of the {S['west_left']} storks from Germany and Spain that left home, {S['west_gib']} crossed the Strait of Gibraltar; of the {S['east_left']} from Poland, Greece and Moscow, {S['east_straits']} crossed the Bosporus or Dardanelles and {S['east_levant']} flew down the Levant. No stork used the other side's funnel. {S['tunisia_sahara']} Tunisian storks crossed the Sahara directly; the Uzbek storks did not migrate.
- Around the sea or across it: storks flew {R['sp']['stork']['sea_pct']:.2f}% of their distance over open sea (longest stretch {R['sp']['stork']['longest_sea_km']:.0f} km), marsh harriers {R['sp']['harrier']['sea_pct']:.1f}%, cuckoos {R['sp']['cuckoo']['sea_pct']:.1f}% and ospreys {R['sp']['osprey']['sea_pct']:.1f}%; {O['carib_n']} ospreys crossed 300 km or more of open sea, mostly the Caribbean.
- Speed: autumn migrations took a median {M['stork_autumn']['days']:.0f} days for storks ({M['stork_autumn']['km_per_day']:.0f} km a day), {M['harrier_autumn']['days']:.0f} for harriers and {M['osprey_autumn']['days']:.1f} for ospreys ({M['osprey_autumn']['km_per_day']:.0f} km a day). Best single day: {R['sp']['harrier']['max_day_km']:.0f} km, a marsh harrier from Spain to Morocco. A young cuckoo went from Poland to Chad, {C['fast'][0]['km']:,.0f} km, in {C['fast'][0]['days']:.1f} days.
- Distance: {R['sp']['stork']['n_full_year']} storks followed for a year covered a median {R['sp']['stork']['median_full_year_km']:,.0f} km between daily positions, up to {R['sp']['stork']['best_year_km']:,.0f} km.
- Winter: {S['regions']['Sahel']} of {S['wintered']} storks with a winter position wintered in the Sahel; one reached Zimbabwe, {S['far_km']:,.0f} km from its nest. A marsh harrier returned to within {H['lilla_max_shift']:.1f} km of the same site near Dakar in three winters.
- Fates: {S['dead']} of {S['n']} young storks ({S['dead_pct']}%) were confirmed dead within the year, {S['dead_before_leaving']} before leaving home; {S['leave_tunisia_dead']} of {S['leave_tunisia_n']} Tunisian storks that set out across the Sahara died, against {S['leave_east_dead']} of {S['leave_east_n']} on the eastern route.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`): animated birds on a parchment MapLibre map, layers panel, full screen, search, charts. Loads `data/site.json`, `data/tracks.json`, `data/winter_areas.geojson` and `data/geo/`. |
| `header.png` | Social card, 1200 x 630. |
| `data/daily_<species>.csv` | One cleaned position per bird per day (the one nearest 12:00 UTC): animal, day, hour (UTC), lon, lat. |
| `data/animals.csv` | One row per bird: species, population, stage, sex, dates, distances, farthest point, best year, funnels crossed, winter position and country, longest sea crossing, confirmed death and the data owners' note. |
| `data/migrations.csv` | Every detected autumn and spring migration: departure, arrival, days, path and straight distance, speed, travel days, coverage. |
| `data/sea_crossings.csv` | Runs over open sea of at least 20 km. |
| `data/winter_areas.geojson` | Smallest areas holding 50% and 90% of each species' December and January positions. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json`, `data/tracks.json`, `data/geo/` | Page data and base map geometry (Natural Earth). |
| `js/pen-birds.js`, `js/ink-palette.js`, `fonts/`, `img/sprites/` | The pen-drawn birds, The Inked World palette and lettering (IM Fell, OFL), sprite images for the figures. |
| `code/` | Scripts, run in order (below), page, paper and blog templates, `figstyle.py`, `sprites.js` and `qa.js`. |
| `release/` | Paper (`paper/`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Cleaning: rows not visible, without coordinates or flagged as outliers removed; Argos location classes 3, 2 and 1 only; positions needing more than 120 km/h (150 for cuckoos) over more than 5 km dropped. GPS thinned to 10 minutes and one hour; every bird to one position a day.
- Migrations: summer anchor (median June to July position, or the nest) to winter anchor (median December to January), at least 500 km apart; from the last day within 100 km of one to the first within 200 km of the other. Only migrations with a position on half the days and no gap over five days enter the speed figures.
- Funnels: Iberia then Morocco (Gibraltar), Thrace then Anatolia (Turkish straits), any position in Israel, Sinai or western Jordan (Levant).
- Sea: distance between consecutive positions (at most 1 hour apart for GPS, 24 hours for ospreys, 72 for cuckoos) with the midpoint off Natural Earth's 1:10m land.
- Caveats: few birds, specific years; sparse satellite positions make osprey and cuckoo tracks straight lines and all distances lower bounds; a tag that stops is not a dead bird; the cuckoo data come from a displacement experiment.

## How to rerun

Needs Python 3 with numpy, pandas, scipy, shapely, geopandas, matplotlib, Pillow and fontTools, xelatex and pdftotext; node with Playwright for `code/sprites.js` and `code/qa.js`. Raw files are read from `{RAW}/` and Natural Earth from `{GEO}/` (set in `code/common.py`); Natural Earth lakes are downloaded from GitHub. Intermediate files go to `{WORK}` (set `BIRDTMP` to change).

```
python3 code/01_clean.py        # raw tracks to clean hourly and daily positions
python3 code/02_analysis.py     # migrations, funnels, sea crossings, winters, fates
python3 code/03_results.py      # results.json, page data, bird stories
python3 code/04_geo.py          # base map geometry, fonts, palette
python3 code/05_build_site.py   # index.html
node code/sprites.js            # pen-drawn birds as PNG
python3 code/06_figures.py      # header, blog and paper figures
python3 code/07_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/08_readme.py       # README, LICENSE, Reddit post
python3 code/09_release.py      # blog post, Zenodo files
node code/qa.js                 # screenshots and console check
```

## Sources and licences

- {SOURCES['stork']['cite']} https://doi.org/{SOURCES['stork']['doi']}. CC0.
- {SOURCES['osprey']['cite']} https://doi.org/{SOURCES['osprey']['doi']}. CC0.
- {SOURCES['cuckoo']['cite']} https://doi.org/{SOURCES['cuckoo']['doi']}. CC0.
- {SOURCES['harrier']['cite']} https://doi.org/{SOURCES['harrier']['doi']}. CC0.
- Natural Earth countries, lakes and populated places (public domain); rivers as prepared for The Inked World (https://maps.tristanhotham.com/ink-map/).
- IM Fell types by Igino Marini, SIL Open Font License (`fonts/ttf/OFL-IMFell.txt`).
- Optional layers on the page: relief tiles © Esri; modern map © OpenStreetMap contributors, © CARTO.

## Citation

Hotham, T. (2026) Where the storks go: routes, funnels, sea crossings, winter quarters and fates of four migratory bird species in four open tracking data sets. Zenodo. https://doi.org/{{10.5281/zenodo.24043676}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
visible_ok(readme.replace("|---|---|", ""))
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts
(including js/pen-birds.js and js/ink-palette.js). The text of the page, the
figures and the derived data files in data/ are released under CC BY 4.0. The
tracking data they are derived from are CC0 (Movebank Data Repository and
Zenodo; see README.md). Coastlines, borders, lakes and towns are Natural Earth
(public domain). The fonts in fonts/ are IM Fell by Igino Marini under the SIL
Open Font License 1.1 (fonts/ttf/OFL-IMFell.txt).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""## Title

[OC] Where the storks go: {R['total']['animals']} tagged birds of four species on one hand-inked map. Young storks flew just {R['sp']['stork']['sea_pct']:.1f}% of their distance over the sea; ospreys {R['sp']['osprey']['sea_pct']:.0f}%

## Body

I combined four open tracking data sets: {S['n']} young white storks from eight populations, {O['n']} ospreys in the Americas, {C['n']} Baltic cuckoos and {H['n']} Belgian marsh harriers. Storks soar on thermals, which do not form over the sea, so they go round it: {S['west_gib']} western storks squeezed through Gibraltar and {S['east_straits']} eastern ones through the Bosporus and Dardanelles, and none used the other side's crossing. Ospreys cross the Caribbean; a cuckoo went from Poland to Chad in {C['fast'][0]['days']:.1f} days; a marsh harrier flew {R['sp']['harrier']['max_day_km']:.0f} km in a day. {S['dead']} of the {S['n']} young storks were found dead within the year. Caveat: a few hundred birds, sparse satellite fixes, distances are lower bounds. Interactive animated map: {PAGE}

## Source comment

Source: Flack et al. 2015, MPIO white stork lifetime tracking data (doi:10.5441/001/1.78152p3q); Martell and Douglas 2019, ospreys in North and South America (doi:10.5441/001/1.sv6335t3); Thorup et al. 2020, common cuckoos from Rybachy (doi:10.5441/001/1.vk36vq82); INBO MH_ANTWERPEN marsh harriers (doi:10.5281/zenodo.8238402). All CC0, via the Movebank Data Repository and Zenodo. Coastlines: Natural Earth.

Tools: Python (pandas, shapely, matplotlib), MapLibre for the interactive map; the pen-drawn birds are drawn in code.

Interactive version: {PAGE}
Paper: https://doi.org/{{10.5281/zenodo.24043676}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/bird-migration/}}
"""
visible_ok(post)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(readme.split()), "words")
