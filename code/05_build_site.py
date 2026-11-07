"""index.html from code/page_template.html: numbers from data/results.json, sources, the full-screen snippet."""
import time
from common import *

R = jload(f"{DATA}/results.json")
t = open(f"{ROOT}/code/page_template.html", encoding="utf-8").read()
for sp, key in (("stork", "SRC_STORK"), ("osprey", "SRC_OSPREY"), ("cuckoo", "SRC_CUCKOO"), ("harrier", "SRC_HARRIER")):
    t = t.replace("{{" + key + "}}", SOURCES[sp]["cite"])
t = fill(t, R)
t = t.replace("/*RESULTS*/", json.dumps({k: R[k] for k in ("total",)}, ensure_ascii=False))
t = t.replace("/*VER*/", time.strftime("%Y%m%d%H%M"))
t = t.replace("/*FULLSCREEN*/", open(f"{ROOT}/code/fullscreen_snippet.html", encoding="utf-8").read())
left = re.findall(r"\{\{[^}]+\}\}", t)
assert set(left) <= {"10.5281/zenodo.24043676", "https://doi.org/10.5281/zenodo.24043676", "https://blog.tristanhotham.com/2026/10/31/bird-migration/"}, set(left)
vis = re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S))
visible_ok(vis)
open(f"{ROOT}/index.html", "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")
