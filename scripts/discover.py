#!/usr/bin/env python3
"""自主搜集：从灵感源抓取候选站点，输出去重后的待策展列表。
用法：python3 scripts/discover.py
灵感源状态：awwwards 200✓ ｜ httpster 200(解析待调) ｜ siteinspire 429 ｜ land-book 403
"""
import json, os, re, urllib.request, urllib.parse
from collections import OrderedDict

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

SOURCES = [
    ("awwwards", "https://www.awwwards.com/"),
    ("httpster", "https://httpster.net/"),
]

URL_RE = re.compile(r'https?://[a-zA-Z0-9.-]+\.(?:com|io|co|design|dev|ai|app|studio|agency|net|org|xyz|me|site|cc|world|art|club)\b')
EXCLUDE = re.compile(
    r'(awwwards|siteinspire|land-book|httpster|onepagelove|google|facebook|twitter|instagram|x\.com|'
    r'youtube|vimeo|cloudflare|jsdelivr|unpkg|github|w3\.org|schema|gstatic|doubleclick|'
    r'typekit|fonts\.google|readymag|plausible|kit\.com|rightclicklogo)', re.I)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read(2 * 1024 * 1024).decode("utf-8", "ignore")


def extract(html):
    seen = OrderedDict()
    for m in URL_RE.finditer(html):
        host = urllib.parse.urlparse(m.group(0)).netloc.lower()
        if EXCLUDE.search(host) or host in seen:
            continue
        seen[host] = m.group(0).rstrip('/')
    return list(seen.values())


def existing():
    try:
        with open(os.path.join(DATA, "sites.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        return {urllib.parse.urlparse(s["url"]).netloc.lower() for s in cfg.get("sites", [])}
    except Exception:
        return set()


def main():
    known = existing()
    print(f"已知 {len(known)} 个站点，去重后输出候选：\n")
    total = 0
    for name, url in SOURCES:
        try:
            html = fetch(url)
        except Exception as e:
            print(f"[{name}] FAIL: {e}\n")
            continue
        cands = [u for u in extract(html) if urllib.parse.urlparse(u).netloc not in known]
        total += len(cands)
        print(f"[{name}] {len(cands)} 个候选：")
        for u in cands[:15]:
            print(f"  {u}")
        print()
    print(f"共 {total} 个新候选，需人工策展后加入 data/sites.json")


if __name__ == "__main__":
    main()