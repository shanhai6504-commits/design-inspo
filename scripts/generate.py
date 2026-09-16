#!/usr/bin/env python3
"""由 data/sites-data.json 生成画廊网站 index.html（含截图资源拷贝）。"""
import html, json, os, shutil, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SHOTS = os.path.join(BASE, "screenshots")
ASSETS = os.path.join(BASE, "assets", "screenshots")
COVERS = os.path.join(BASE, "covers")

# 分类展示顺序（covers.py / curate.py 与此保持一致）
CATEGORY_ORDER = ["WebGL·沉浸式", "创意机构·个性", "交互·动效标杆", "个人作品集", "品牌·建筑", "灵感画廊·工具"]


def esc(s):
    return html.escape(str(s or ""))


def swatches(colors, fallback, n=6):
    palette = colors or fallback or []
    return "".join(
        f'<span class="swatch" style="background:{c}" title="{c}"></span>'
        for c in palette[:n]
    ) or '<span class="swatch" style="background:#333" title="—"></span>'


def card(s):
    sid = esc(s["id"])
    name = esc(s["name"])
    shot = esc(s["screenshot"] or "")
    url = esc(s["url"])
    tags = "".join(f'<span class="tag">{esc(t)}</span>' for t in s.get("tags", []))
    analysis = esc(s.get("analysis", ""))
    desc = esc(s.get("description", ""))
    fonts = s.get("fonts", [])
    cssc = s.get("css_colors", [])
    colors = s.get("colors", [])
    fonts_html = "".join(f'<span class="font-chip">{esc(f)}</span>' for f in fonts[:4])
    extra = ""
    if fonts_html:
        extra += f'<div class="detail-row"><span class="k">字体</span>{fonts_html}</div>'
    if cssc:
        extra += (f'<div class="detail-row"><span class="k">CSS 配色</span>'
                  f'{swatches(cssc, [])}</div>')
    img_html = (f'<div class="shot" style="background-image:url(\'assets/screenshots/{sid}.png\')"></div>'
                if shot else '<div class="shot empty">无截图</div>')
    return f'''
    <article class="card" tabindex="0">
      {img_html}
      <div class="card-overlay">
        <h3 class="card-name">{name}</h3>
        {f'<p class="card-analysis">{analysis}</p>' if analysis else ""}
        {f'<p class="card-desc">{desc[:140]}</p>' if desc else ""}
        <div class="swatches">{swatches(colors, cssc)}</div>
        {extra}
        <a class="visit" href="{url}" target="_blank" rel="noopener">访问站点 ↗</a>
      </div>
      <div class="card-tags">{tags}<span class="card-idx">#{esc(s.get('id',''))}</span></div>
    </article>'''


def main():
    with open(os.path.join(DATA, "sites-data.json"), encoding="utf-8") as f:
        data = json.load(f)
    sites = data.get("sites", [])
    updated = esc(data.get("updated_at", ""))

    # 拷贝封面资源（优先 covers/ 的优化封面，回退 screenshots/ 原图）
    os.makedirs(ASSETS, exist_ok=True)
    copied = 0
    for s in sites:
        src = os.path.join(COVERS, f"{s['id']}.png")
        if not os.path.exists(src):
            src = os.path.join(SHOTS, f"{s['id']}.png")
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(ASSETS, f"{s['id']}.png"))
            copied += 1

    # 按分类分组渲染
    groups = {c: [] for c in CATEGORY_ORDER}
    groups["其他"] = []
    for s in sites:
        cat = s.get("category", "") or "其他"
        if cat in groups:
            groups[cat].append(s)
        else:
            groups["其他"].append(s)
    sections = []
    for cat in CATEGORY_ORDER + ["其他"]:
        items = groups.get(cat, [])
        if not items:
            continue
        inner = "\n".join(card(s) for s in items)
        sections.append(
            f'<section class="cat"><h2 class="cat-title">{esc(cat)}'
            f'<span class="cat-count">{len(items)}</span></h2>'
            f'<div class="grid">{inner}</div></section>')
    cards_html = "\n".join(sections)

    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>设计灵感墙 · Design Inspiration</title>
<style>
  :root {{
    --bg:#0d0f12; --panel:#15181d; --line:#23272e; --text:#e8eaed;
    --muted:#9aa0a6; --accent:#f39917; --accent2:#002fa7;
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  html,body {{ background:var(--bg); color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
    -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:1240px; margin:0 auto; padding:48px 24px 96px; }}
  header {{ padding:40px 0 8px; }}
  header .kicker {{ color:var(--accent); font-size:13px; letter-spacing:.18em;
    text-transform:uppercase; margin-bottom:10px; font-weight:600; }}
  header h1 {{ font-size:clamp(28px,5vw,46px); font-weight:800; letter-spacing:-.02em; }}
  header p.sub {{ color:var(--muted); margin-top:12px; font-size:15px; line-height:1.6; max-width:640px; }}
  .meta {{ margin-top:18px; color:var(--muted); font-size:13px; }}
  .meta b {{ color:var(--text); }}
  .grid {{ display:grid; gap:22px; margin-top:36px;
    grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); }}
  .cat {{ margin-top:44px; }}
  .cat-title {{ font-size:20px; font-weight:700; letter-spacing:-.01em;
    display:flex; align-items:center; gap:10px; }}
  .cat-title::before {{ content:""; width:9px; height:9px; border-radius:3px;
    background:var(--accent); box-shadow:0 0 12px rgba(243,153,23,.55); }}
  .cat-count {{ font-size:12px; font-weight:600; color:var(--muted);
    background:var(--panel); border:1px solid var(--line); border-radius:20px;
    padding:2px 10px; }}
  .cat .grid {{ margin-top:18px; }}
  .card {{ position:relative; border-radius:14px; overflow:hidden; background:var(--panel);
    border:1px solid var(--line); cursor:pointer; transition:transform .25s,border-color .25s,box-shadow .25s; }}
  .card:hover,.card:focus {{ transform:translateY(-4px); border-color:#3a4048;
    box-shadow:0 12px 40px rgba(0,0,0,.5); }}
  .shot {{ aspect-ratio:16/10; background-size:cover; background-position:top center;
    transition:transform .5s ease; }}
  .card:hover .shot {{ transform:scale(1.04); }}
  .shot.empty {{ display:flex; align-items:center; justify-content:center;
    color:var(--muted); background:#1b1f25; }}
  .card-overlay {{ position:absolute; inset:0; padding:18px 20px;
    background:linear-gradient(to top,rgba(7,9,12,.96) 0%,rgba(7,9,12,.72) 45%,rgba(7,9,12,0) 80%);
    opacity:0; transform:translateY(8px); transition:opacity .28s,transform .28s;
    display:flex; flex-direction:column; justify-content:flex-end; gap:8px; }}
  .card:hover .card-overlay,.card:focus .card-overlay {{ opacity:1; transform:translateY(0); }}
  .card-name {{ font-size:20px; font-weight:700; letter-spacing:-.01em; }}
  .card-analysis,.card-desc {{ font-size:13px; color:#c3c8cf; line-height:1.55; }}
  .swatches {{ display:flex; gap:6px; flex-wrap:wrap; }}
  .swatch {{ width:18px; height:18px; border-radius:5px; border:1px solid rgba(255,255,255,.14); }}
  .detail-row {{ display:flex; align-items:center; gap:8px; margin-top:2px; }}
  .detail-row .k {{ color:var(--muted); font-size:12px; white-space:nowrap; }}
  .font-chip {{ font-size:11px; color:#c3c8cf; background:rgba(255,255,255,.08);
    padding:2px 7px; border-radius:5px; }}
  .visit {{ align-self:flex-start; margin-top:4px; font-size:13px; font-weight:600;
    color:var(--accent); text-decoration:none; }}
  .visit:hover {{ text-decoration:underline; }}
  .card-tags {{ position:absolute; left:12px; top:12px; right:12px; display:flex;
    gap:6px; flex-wrap:wrap; }}
  .tag {{ font-size:11px; color:#e8eaed; background:rgba(13,15,18,.62);
    backdrop-filter:blur(4px); padding:3px 9px; border-radius:20px;
    border:1px solid rgba(255,255,255,.12); }}
  .card-idx {{ margin-left:auto; font-size:11px; color:rgba(255,255,255,.55); }}
  footer {{ margin-top:56px; color:var(--muted); font-size:12px; text-align:center;
    border-top:1px solid var(--line); padding-top:24px; }}
  @media (max-width:560px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="kicker">Curated Design Inspiration</div>
    <h1>设计灵感墙</h1>
    <p class="sub">精选全球优秀的、酷炫的、前沿的网站案例。悬停卡片查看设计分析与配色提取；持续自动更新。</p>
    <div class="meta">共 <b>{len(sites)}</b> 个案例 · 更新于 <b>{updated}</b></div>
  </header>
  <div class="grid">
{cards_html}
  </div>
  <footer>Design Inspiration Gallery · 自动采集 + GitHub Pages 托管</footer>
</div>
</body>
</html>'''

    out = os.path.join(BASE, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"Wrote {out}  ({len(sites)} cards, {copied} screenshots copied)")


if __name__ == "__main__":
    main()