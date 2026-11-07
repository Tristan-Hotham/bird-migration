"""The paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/Hotham_Where_the_Storks_Go.pdf and .tex (figures f_*.png beside them)."""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Where_the_Storks_Go"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
assert R["stork"]["pops"]["Uzbekistan"]["left"] == 0 and R["stork"]["pops"]["Armenia"]["levant"] == 0
assert all(R["stork"]["pops"][p]["straits"] == 0 for p in ("SW Germany", "Spain (Doñana)")) and all(R["stork"]["pops"][p]["gib"] == 0 for p in ("Poland", "Greece (Evros Delta)", "Russia (Moscow)"))
assert 0.35 <= R["stork"]["dead"] / R["stork"]["n"] < 0.45      # "four young storks in ten"
assert R["migr"]["cuckoo_autumn"]["n"] == 0                      # "too sparse for this measure"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


P = R["stork"]["pops"]
order = ["SW Germany", "Spain (Doñana)", "Tunisia", "Poland", "Greece (Evros Delta)", "Russia (Moscow)", "Armenia", "Uzbekistan", "South Africa"]
rows = "".join(f"{tex(p)} & {P[p]['n']} & {P[p]['left']} & {P[p]['gib']} & {P[p]['straits']} & {P[p]['levant']} & {P[p]['wintered']} & {P[p]['winter_lat'] if P[p]['winter_lat'] is not None else ''} & {P[p]['dead']}\\\\\n" for p in order)
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{Young white storks by population: tagged, left home (at least 300 km), funnels crossed, with a winter position, median winter latitude (degrees) and confirmed dead.}\\label{tab:pops}"
      "\\begin{tabular}{lrrrrrrrr}\\toprule Population & Tagged & Left & Gibraltar & Straits & Levant & Wintered & Lat. & Dead\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
M = R["migr"]
rows = ""
for sp in ("stork", "osprey", "harrier"):
    for k in ("autumn", "spring"):
        m = M[f"{sp}_{k}"]
        if m["n"]:
            rows += f"{SPECIES[sp][0]} & {k} & {m['n']} & {m['path_km']:,.0f} & {m['straight_km']:,.0f} & {m['days']:.0f} & {m['km_per_day']:.0f} & {m['travel_days']:.0f}\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Well-covered migrations: number, and medians of the distance between daily positions (km), the straight distance between anchors (km), days, km a day and days with more than 50 km of flight.}\\label{tab:migr}"
      "\\begin{tabular}{llrrrrrr}\\toprule Species & Season & n & Path & Straight & Days & km/day & Travel days\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
A = pd.read_csv(f"{DATA}/animals.csv")
A = A[A.species == "stork"].sort_values(["population", "animal"])
rows = "".join(f"{tex(r.animal)} & {tex(r.population)} & {r.first_day} & {r.last_day} & {r.path_km_daily:,.0f} & {r.max_from_tag_km:,.0f} & {tex(r.winter_country) if isinstance(r.winter_country, str) else ''} & {'dead' if r.confirmed_dead else ''}\\\\\n" for r in A.itertuples())
TS = ("{\\footnotesize\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{llllrrll}\\caption{The " + str(len(A)) + " young storks: first and last daily position, distance between daily positions (km), farthest distance from the nest (km), winter country and confirmed deaths.}\\label{tab:storks}\\\\"
      "\\toprule Stork & Population & First & Last & km & Farthest & Winter & Fate\\\\\\midrule\\endfirsthead\\toprule Stork & Population & First & Last & km & Farthest & Winter & Fate\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("POPS", TP), ("MIGR", TM), ("STORKS", TS)):
    t = t.replace("{{TABLE_%s}}" % k, v)
assert "{{" not in t.replace("\\{\\{DOI\\}\\}", "") and "--" not in t and "—" not in t and "–" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(3):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
