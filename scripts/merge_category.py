#!/usr/bin/env python3
"""把 sites.json 里的 category 合并进 sites-data.json（避免重跑采集/联网）。"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

with open(os.path.join(DATA, "sites.json"), encoding="utf-8") as f:
    cfg = json.load(f)
cat = {s["id"]: s.get("category", "") for s in cfg["sites"]}

with open(os.path.join(DATA, "sites-data.json"), encoding="utf-8") as f:
    data = json.load(f)

for s in data["sites"]:
    s["category"] = cat.get(s["id"], s.get("category", ""))

with open(os.path.join(DATA, "sites-data.json"), "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

n = sum(1 for s in data["sites"] if s.get("category"))
print(f"merged category into {len(data['sites'])} sites, {n} have category")
