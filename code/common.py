"""Shared paths and helpers for the bird-migration study ("Where the storks go").

Raw inputs (read only, never copied into the repo; all CC0 from the Movebank Data Repository and Zenodo):
  RAW/storks_flack_gps.csv.zip            MPIO white stork lifetime tracking data (2013-2014), GPS, Flack et al. 2015,
                                          doi:10.5441/001/1.78152p3q (312 MB unzipped, streamed)
  RAW/storks_flack_reference-data.csv     the 72 tagged storks (population, fate)
  RAW/osprey_martell_gps.csv.gz           Osprey in North and South America 1995-2002 (Martell), Argos,
                                          doi:10.5441/001/1.sv6335t3
  RAW/osprey_martell_reference-data.csv
  RAW/cuckoo_rybachy_argos.csv            Common Cuckoos from Rybachy, Argos and Lotek GPS, Thorup et al. 2020,
  RAW/cuckoo_rybachy_gps.csv              doi:10.5441/001/1.vk36vq82
  RAW/cuckoo_rybachy_reference-data.csv
  RAW/harrier_MH_ANTWERPEN-gps-20xx.csv.gz  MH_ANTWERPEN western marsh harriers (INBO), GPS 2018 to 2022,
  RAW/harrier_MH_ANTWERPEN-reference-data.csv  doi:10.5281/zenodo.3550094
  GEO/ne_50m_land, ne_50m_admin_0_countries, ne_10m_populated_places (Natural Earth, public domain)
  LAKES = Natural Earth ne_50m_lakes.geojson (downloaded from github.com/nvkelso/natural-earth-vector, public domain)
"""
import json, gzip, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = "/home/claude/newdata/raw_new6/birds"
GEO = "/home/claude/newdata/raw/geo"
LAKES = "/home/claude/work/new6/bird-migration/dl/ne_50m_lakes.geojson"
LAKES_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_lakes.geojson"
INK = "/home/claude/studies/ink-map"          # The Inked World: palette, fonts (read only)
DATA = os.path.join(ROOT, "data")
WORK = os.environ.get("BIRDTMP", "/home/claude/work/new6/bird-migration/work")   # big intermediates, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "bird-migration"
PAGE = "https://maps.tristanhotham.com/bird-migration/"
REPO = "https://github.com/Tristan-Hotham/bird-migration"
DOI = "10.5281/zenodo.24043676"
DOI_URL = "https://doi.org/10.5281/zenodo.24043676"
BLOG = "https://blog.tristanhotham.com/2026/10/31/bird-migration/"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

SPECIES = {   # key: (common name, latin, colour on paper)
    "stork": ("White stork", "Ciconia ciconia", "#A3261B"),
    "osprey": ("Osprey", "Pandion haliaetus", "#3D6E9E"),
    "cuckoo": ("Common cuckoo", "Cuculus canorus", "#5E7A3A"),
    "harrier": ("Western marsh harrier", "Circus aeruginosus", "#9C6A1E"),
}
SOURCES = {
    "stork": {"cite": "Flack A, Fiedler W, Blas J, Pokrovski I, Mitropolsky M, Kaatz M, Aghababyan K, Khachatryan A, Fakriadis Y, Makrigianni E, Jerzak L, Shamin M, Shamina C, Azafzaf H, Feltrup-Azafzaf C, Mokotjomela T, Wikelski M (2015) Data from: Migration costs of eight Eurasian white stork populations. Movebank Data Repository.",
              "doi": "10.5441/001/1.78152p3q", "short": "Flack et al. (2015), Movebank Data Repository"},
    "osprey": {"cite": "Martell MS, Douglas D (2019) Data from: Fall migration routes, timing, and wintering sites of North American ospreys as determined by satellite telemetry. Movebank Data Repository.",
               "doi": "10.5441/001/1.sv6335t3", "short": "Martell and Douglas (2019), Movebank Data Repository"},
    "cuckoo": {"cite": "Thorup K, Vega ML, Snell KRS, Lubkovskaia R, Willemoes M, Sjöberg S, Sokolov LV, Bulyuk V (2020) Data from: Flying on their own wings: young and adult cuckoos respond similarly to long-distance displacement during migration. Movebank Data Repository.",
               "doi": "10.5441/001/1.vk36vq82", "short": "Thorup et al. (2020), Movebank Data Repository"},
    "harrier": {"cite": "Research Institute for Nature and Forest (INBO) (2023) MH_ANTWERPEN: Western marsh harriers (Circus aeruginosus, Accipitridae) breeding near Antwerp (Belgium). Zenodo, version 5 (GPS tracking with UvA-BiTS).",
                "doi": "10.5281/zenodo.8238402", "short": "INBO MH_ANTWERPEN (Zenodo)"},
}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """House style: no em or en dashes and no double hyphens in text."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


R_EARTH = 6371.0088


def hav(lon1, lat1, lon2, lat2):
    """Great-circle distance in km (numpy friendly)."""
    import numpy as np
    lon1, lat1, lon2, lat2 = map(np.radians, (lon1, lat1, lon2, lat2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw":
        return str(v)
    if f == "int":
        return f"{round(float(v)):,}"
    if f == "pc":
        return f"{round(float(v))}%"
    if f == "f1":
        return f"{float(v):.1f}"
    if f == "f2":
        return f"{float(v):.2f}"
    raise ValueError(f)


def fill(text, R):
    """Replace {{path|fmt}} tokens with numbers from results.json (IMG tokens and publisher placeholders left alone)."""
    keep = {"DOI", "DOI_URL", "BLOG_URL"}

    def rep(m):
        key = m.group(1)
        if key in keep:
            return m.group(0)
        return fmt(get(R, key), m.group(3))
    return re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", rep, text)


def visible_ok(s):
    vis = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    return True
