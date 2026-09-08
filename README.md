# 设计灵感墙 · Design Inspiration Gallery

自动采集优秀设计网站案例，生成可公开访问的灵感画廊（GitHub Pages 托管）。悬停卡片可查看设计分析与配色提取。

## 结构

| 路径 | 作用 |
|------|------|
| `data/sites.json` | 站点清单（**人工维护**，新增案例改这里） |
| `data/sites-data.json` | 采集输出（截图路径 / 元数据 / 配色，自动生成） |
| `screenshots/` | 截图源文件 |
| `assets/screenshots/` | 部署用截图副本（generate 时自动拷贝） |
| `scripts/collect.py` | 采集脚本：截图 + 元数据 + 取色 |
| `scripts/generate.py` | 生成画廊 `index.html` |
| `index.html` | 生成的画廊（Pages 入口） |

## 用法

**新增一个站点**
```bash
# 1. 编辑 data/sites.json，加一条 {id,name,url,tags,note,analysis}
python3 scripts/collect.py --only <id> --force   # 2. 抓取该站
python3 scripts/generate.py                       # 3. 生成画廊
git add -A && git commit -m "add <id>" && git push
```

**全量刷新（保持缩略图最新）**
```bash
python3 scripts/collect.py --force && python3 scripts/generate.py
git add -A && git commit -m "refresh" && git push
```

## 采集逻辑

- 截图：Chrome headless 两步式（常规 → WebGL/swiftshader），带空白页检测
- 兜底：截图失败则下载站点 og:image 作为预览图
- 元数据：title / description / 字体族 / CSS 配色 / og:image
- 配色：从截图 PNG 原生解码提取主色（纯标准库，无 Pillow 依赖）