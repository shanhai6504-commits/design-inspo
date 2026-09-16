#!/usr/bin/env python3
"""为每个站点生成焦点封面：用 macOS Vision 显著度裁剪出「重要元素」。
输出 covers/{id}.png（16:10）。识别失败时回退复制原截图。"""
import json, os, shutil, subprocess, sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SHOTS = os.path.join(BASE, "screenshots")
COVERS = os.path.join(BASE, "covers")
SCRIPTS = os.path.join(BASE, "scripts")
SWIFT = os.path.join(SCRIPTS, "hero-crop.swift")
BIN = "/tmp/hero-crop"


def ensure_bin():
    if os.path.exists(BIN) and os.path.getmtime(SWIFT) <= os.path.getmtime(BIN):
        return BIN
    r = subprocess.run(["swiftc", "-O", SWIFT, "-o", BIN],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("swiftc fail:", r.stderr[:400], file=sys.stderr)
        sys.exit(1)
    return BIN


def main():
    bin_path = ensure_bin()
    with open(os.path.join(DATA, "sites.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    os.makedirs(COVERS, exist_ok=True)
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    ok = skip = fail = fb = 0
    for site in cfg["sites"]:
        sid = site["id"]
        if only and sid != only:
            continue
        src = os.path.join(SHOTS, f"{sid}.png")
        dst = os.path.join(COVERS, f"{sid}.png")
        if not os.path.exists(src) or os.path.getsize(src) < 5000:
            skip += 1
            continue
        r = subprocess.run([bin_path, src, dst, "16", "10"],
                           capture_output=True, text=True)
        out = (r.stdout or "").strip()
        if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 3000:
            ok += 1
            print(f"[cover] {sid}: {out.splitlines()[-1] if out else 'ok'}")
        else:
            shutil.copy2(src, dst)  # 回退原图
            fb += 1
            print(f"[cover] {sid}: FALLBACK {r.returncode} {out[:80]}")
    print(f"\ncovers done: {ok} ok, {fb} fallback, {skip} skipped, {fail} fail")


if __name__ == "__main__":
    main()