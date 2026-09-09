#!/usr/bin/env python3
"""设计灵感采集器：截图 + 元数据 + 取色，输出 data/sites-data.json
纯标准库实现（无 Pillow 依赖），适配系统 python3。

用法：
  python3 scripts/collect.py            # 全量（已有截图则跳过）
  python3 scripts/collect.py --force    # 全量重截
  python3 scripts/collect.py --only <id> # 只抓指定站点，合并进已有数据
"""
import json, os, re, signal, struct, subprocess, sys, time, urllib.request, zlib
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SHOTS = os.path.join(BASE, "screenshots")
os.makedirs(SHOTS, exist_ok=True)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SCREENSHOT_TIMEOUT = 45
FETCH_TIMEOUT = 20

HEX_RE = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
FONT_RE = re.compile(r"font-family\s*:\s*([^;}\"']+)", re.I)


def run_chrome(cmd, timeout):
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, start_new_session=True)
    try:
        _, stderr = proc.communicate(timeout=timeout)
        return proc.returncode, stderr
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass
        return -1, b"TIMEOUT"


def screenshot(site, force=False):
    out = os.path.join(SHOTS, f"{site['id']}.png")
    if os.path.exists(out) and os.path.getsize(out) > 5000 and not is_blank(out) and not force:
        return out
    base = ["--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check", "--disable-extensions",
            "--mute-audio", "--force-device-scale-factor=1", "--no-proxy-server"]
    webgl = base + ["--enable-unsafe-swiftshader", "--use-gl=angle",
                    "--use-angle=swiftshader-webgl"]
    for flags in (base, webgl):
        cmd = [CHROME] + flags + ["--window-size=1440,900", f"--screenshot={out}",
                                  "--virtual-time-budget=10000", f"--user-agent={UA}",
                                  site["url"]]
        run_chrome(cmd, SCREENSHOT_TIMEOUT)
        if os.path.exists(out) and os.path.getsize(out) > 5000 and not is_blank(out):
            return out
        if os.path.exists(out):
            try:
                os.remove(out)
            except Exception:
                pass
    return None


def fetch_meta(url):
    meta = {"title": "", "description": "", "fonts": [], "css_colors": [], "og_image": ""}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
            html = r.read(4096 * 1024).decode("utf-8", "ignore")
    except Exception as e:
        meta["fetch_error"] = str(e)[:120]
        return meta
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        meta["title"] = re.sub(r"\s+", " ", m.group(1)).strip()
    for name in ("description", "og:description"):
        m = re.search(r'<meta[^>]+(?:name|property)=["\']' + name + r'["\'][^>]+content=["\'](.*?)["\']', html, re.I)
        if m:
            meta["description"] = m.group(1)[:300]
            break
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\'](.*?)["\']', html, re.I)
    if m:
        meta["og_image"] = m.group(1)
    fonts = FONT_RE.findall(html)
    if fonts:
        seen, names = set(), []
        for f in fonts:
            for part in f.split(",")[:2]:
                part = part.strip().strip("'\"")
                if part and part.lower() not in seen:
                    seen.add(part.lower())
                    names.append(part)
        meta["fonts"] = names[:6]
    colors = HEX_RE.findall(html)
    if colors:
        meta["css_colors"] = [c.lower() for c, _ in Counter(colors).most_common(6)]
    return meta


def download(url, path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r, open(path, "wb") as f:
            f.write(r.read())
        return os.path.exists(path) and os.path.getsize(path) > 3000
    except Exception:
        return False


def decode_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos, width, height, channels, bit_depth, color_type = 8, 0, 0, 0, 0, 0
    idat = b""
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break
        pos += 12 + length
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type, 3)
    if bit_depth != 8:
        raise ValueError("unsupported bit depth %d" % bit_depth)
    raw = zlib.decompress(idat)
    stride = width * channels
    out = bytearray()
    prev = bytearray(stride)
    p = 0
    for _ in range(height):
        ft = raw[p]; p += 1
        line = bytearray(raw[p:p + stride]); p += stride
        if ft == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xff
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xff
        elif ft == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xff
        elif ft == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                pr = a + b - c
                pa, pb, pc = abs(pr - a), abs(pr - b), abs(pr - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pred) & 0xff
        out += line
        prev = line
    return width, height, channels, bytes(out)


def is_blank(path, sample=64):
    """采样网格，若几乎无颜色变化（<=3 种粗色）判定为空白/纯色页。"""
    try:
        width, height, channels, pix = decode_png(path)
    except Exception:
        return False
    step_x = max(1, width // sample)
    step_y = max(1, height // sample)
    colors = set()
    for y in range(0, height, step_y):
        row = y * width * channels
        for x in range(0, width, step_x):
            o = row + x * channels
            colors.add((pix[o] >> 5, pix[o + 1] >> 5, pix[o + 2] >> 5))
    return len(colors) <= 3


def dominant_colors(path, n=5):
    try:
        width, height, channels, pix = decode_png(path)
    except Exception:
        return []
    counter = Counter()
    sums = {}
    step_x = max(1, width // 160)
    step_y = max(1, height // 100)
    for y in range(0, height, step_y):
        row = y * width * channels
        for x in range(0, width, step_x):
            o = row + x * channels
            r, g, b = pix[o], pix[o + 1], pix[o + 2]
            if channels >= 4 and pix[o + 3] < 128:
                continue
            key = ((r >> 4) << 8) | ((g >> 4) << 4) | (b >> 4)
            counter[key] += 1
            if key in sums:
                s = sums[key]; s[0] += r; s[1] += g; s[2] += b; s[3] += 1
            else:
                sums[key] = [r, g, b, 1]
    out = []
    for key, cnt in counter.most_common():
        s = sums[key]
        r, g, b = s[0] // cnt, s[1] // cnt, s[2] // cnt
        mx, mn = max(r, g, b), min(r, g, b)
        if mx < 245 and mn > 12 and (mx - mn) > 18:
            out.append("#%02x%02x%02x" % (r, g, b))
        if len(out) >= n:
            break
    if len(out) < n:
        for key, cnt in counter.most_common():
            s = sums[key]
            c = "#%02x%02x%02x" % (s[0] // cnt, s[1] // cnt, s[2] // cnt)
            if c not in out:
                out.append(c)
            if len(out) >= n:
                break
    return out


def capture_one(site, force):
    print(f"[shot] {site['id']}  <- {site['url']}")
    t0 = time.time()
    shot = screenshot(site, force=force)
    meta = fetch_meta(site["url"])
    if shot is None and meta.get("og_image"):
        fallback = os.path.join(SHOTS, f"{site['id']}.png")
        if download(meta["og_image"], fallback):
            shot = fallback
    rec = {
        "id": site["id"], "name": site["name"], "url": site["url"],
        "orig_url": site.get("orig_url", site["url"]),
        "tags": site.get("tags", []), "note": site.get("note", ""),
        "analysis": site.get("analysis", ""),
        "screenshot": f"screenshots/{site['id']}.png" if shot else None,
        "title": meta.get("title", ""), "description": meta.get("description", ""),
        "fonts": meta.get("fonts", []), "css_colors": meta.get("css_colors", []),
        "og_image": meta.get("og_image", ""), "fetch_error": meta.get("fetch_error", ""),
        "colors": dominant_colors(shot) if shot else [],
        "captured_at": time.strftime("%Y-%m-%d %H:%M"),
        "elapsed_s": round(time.time() - t0, 1),
    }
    print(f"    -> {'OK' if shot else 'FAIL'}  {'' if shot else meta.get('fetch_error','')}")
    return rec


def main():
    with open(os.path.join(DATA, "sites.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    force = "--force" in sys.argv
    only = None
    if "--only" in sys.argv:
        try:
            only = sys.argv[sys.argv.index("--only") + 1]
        except IndexError:
            only = None
    records = []
    for site in cfg["sites"]:
        if only and site["id"] != only:
            continue
        records.append(capture_one(site, force))
    if only:
        data_path = os.path.join(DATA, "sites-data.json")
        try:
            with open(data_path, encoding="utf-8") as f:
                existing = {s["id"]: s for s in json.load(f)["sites"]}
        except Exception:
            existing = {}
        for rec in records:
            existing[rec["id"]] = rec
        records = [existing[s["id"]] for s in cfg["sites"] if s["id"] in existing]
    out_path = os.path.join(DATA, "sites-data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"updated_at": time.strftime("%Y-%m-%d %H:%M"), "sites": records},
                  f, ensure_ascii=False, indent=2)
    print(f"\nWrote {out_path}  ({len(records)} sites)")


if __name__ == "__main__":
    main()