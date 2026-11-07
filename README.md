# Where the storks go

Four species of migratory bird followed across three continents, from four open tracking data sets cleaned in the same way: 72 young white storks from eight populations (GPS, 2013 to 2014), 111 North American ospreys (Argos, 1995 to 2002), 42 common cuckoos from a displacement experiment (Argos and GPS, 2015 to 2020) and 3 western marsh harriers from Belgium (GPS, 2018 to 2022): 25,236 daily positions, drawn as animated pen-drawn birds on a hand-inked map in the style of The Inked World.

Interactive page: https://maps.tristanhotham.com/bird-migration/
Paper: https://doi.org/10.5281/zenodo.24043676
Blog post: https://blog.tristanhotham.com/2026/10/31/bird-migration/
Code and data: https://github.com/Tristan-Hotham/bird-migration

## Headline results

- Two roads to Africa: of the 18 storks from Germany and Spain that left home, 13 crossed the Strait of Gibraltar; of the 23 from Poland, Greece and Moscow, 21 crossed the Bosporus or Dardanelles and 20 flew down the Levant. No stork used the other side's funnel. 7 Tunisian storks crossed the Sahara directly; the Uzbek storks did not migrate.
- Around the sea or across it: storks flew 0.61% of their distance over open sea (longest stretch 82 km), marsh harriers 3.7%, cuckoos 5.4% and ospreys 22.0%; 4 ospreys crossed 300 km or more of open sea, mostly the Caribbean.
- Speed: autumn migrations took a median 61 days for storks (79 km a day), 51 for harriers and 23.5 for ospreys (170 km a day). Best single day: 871 km, a marsh harrier from Spain to Morocco. A young cuckoo went from Poland to Chad, 4,347 km, in 4.8 days.
- Distance: 17 storks followed for a year covered a median 12,724 km between daily positions, up to 23,680 km.
- Winter: 18 of 34 storks with a winter position wintered in the Sahel; one reached Zimbabwe, 9,186 km from its nest. A marsh harrier returned to within 2.6 km of the same site near Dakar in three winters.
- Fates: 30 of 72 young storks (42%) were confirmed dead within the year, 16 before leaving home; 5 of 7 Tunisian storks that set out across the Sahara died, against 3 of 23 on the eastern route.

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

Needs Python 3 with numpy, pandas, scipy, shapely, geopandas, matplotlib, Pillow and fontTools, xelatex and pdftotext; node with Playwright for `code/sprites.js` and `code/qa.js`. Raw files are read from `/home/claude/newdata/raw_new6/birds/` and Natural Earth from `/home/claude/newdata/raw/geo/` (set in `code/common.py`); Natural Earth lakes are downloaded from GitHub. Intermediate files go to `/home/claude/work/new6/bird-migration/work` (set `BIRDTMP` to change).

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

- Flack A, Fiedler W, Blas J, Pokrovski I, Mitropolsky M, Kaatz M, Aghababyan K, Khachatryan A, Fakriadis Y, Makrigianni E, Jerzak L, Shamin M, Shamina C, Azafzaf H, Feltrup-Azafzaf C, Mokotjomela T, Wikelski M (2015) Data from: Migration costs of eight Eurasian white stork populations. Movebank Data Repository. https://doi.org/10.5441/001/1.78152p3q. CC0.
- Martell MS, Douglas D (2019) Data from: Fall migration routes, timing, and wintering sites of North American ospreys as determined by satellite telemetry. Movebank Data Repository. https://doi.org/10.5441/001/1.sv6335t3. CC0.
- Thorup K, Vega ML, Snell KRS, Lubkovskaia R, Willemoes M, Sjöberg S, Sokolov LV, Bulyuk V (2020) Data from: Flying on their own wings: young and adult cuckoos respond similarly to long-distance displacement during migration. Movebank Data Repository. https://doi.org/10.5441/001/1.vk36vq82. CC0.
- Research Institute for Nature and Forest (INBO) (2023) MH_ANTWERPEN: Western marsh harriers (Circus aeruginosus, Accipitridae) breeding near Antwerp (Belgium). Zenodo, version 5 (GPS tracking with UvA-BiTS). https://doi.org/10.5281/zenodo.8238402. CC0.
- Natural Earth countries, lakes and populated places (public domain); rivers as prepared for The Inked World (https://maps.tristanhotham.com/ink-map/).
- IM Fell types by Igino Marini, SIL Open Font License (`fonts/ttf/OFL-IMFell.txt`).
- Optional layers on the page: relief tiles © Esri; modern map © OpenStreetMap contributors, © CARTO.

## Citation

Hotham, T. (2026) Where the storks go: routes, funnels, sea crossings, winter quarters and fates of four migratory bird species in four open tracking data sets. Zenodo. https://doi.org/10.5281/zenodo.24043676

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
