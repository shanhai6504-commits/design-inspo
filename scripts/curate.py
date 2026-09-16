#!/usr/bin/env python3
"""一次性策展：给现有站点补 category 字段，并追加 lusion 同类高交互站点。"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

# 分类顺序（generate.py 依此分组渲染）
CATEGORY_ORDER = ["WebGL·沉浸式", "创意机构·个性", "交互·动效标杆", "个人作品集", "品牌·建筑", "灵感画廊·工具"]

# 现有站点 → 分类
EXISTING_CAT = {
    "godly-website": "灵感画廊·工具",
    "unicorn-studio": "WebGL·沉浸式",
    "reactbits": "灵感画廊·工具",
    "reactbits-pro": "灵感画廊·工具",
    "huy-phan": "个人作品集",
    "illoca-unseen": "WebGL·沉浸式",
    "merlin-studio": "创意机构·个性",
    "sadu-media": "品牌·建筑",
    "counter-forms": "创意机构·个性",
    "snohetta": "品牌·建筑",
    "mobbin": "灵感画廊·工具",
    "refokus": "创意机构·个性",
    "warren-mahoney": "品牌·建筑",
    "patrick-mason-studio": "个人作品集",
    "viens-la": "创意机构·个性",
    "middle-name-co": "创意机构·个性",
    "astro-dither": "WebGL·沉浸式",
    "nothing-to-watch": "WebGL·沉浸式",
    "cathy-dolle": "个人作品集",
    "dirtverse": "创意机构·个性",
    "harry-atkins": "个人作品集",
}

NEW_SITES = [
    {"id": "lusion", "name": "Lusion", "url": "https://www.lusion.co/", "orig_url": "https://www.lusionstudio.com/",
     "category": "WebGL·沉浸式", "tags": ["WebGL", "沉浸式", "创意工作室", "交互动效"],
     "note": "你给的 lusionstudio.com 的现行主域名",
     "analysis": "Lusion 官方主站。WebGL 实时渲染的感性地标——定制十字光标、加载进度条即作品、12 个项目的 hover 图片流，把「交互即内容」做到极致，高级创意工作室的图腾级标杆。"},
    {"id": "active-theory", "name": "Active Theory", "url": "https://activetheory.net/",
     "category": "WebGL·沉浸式", "tags": ["WebGL", "沉浸式", "创意工作室"],
     "note": "同 Lusion 同档的体验优先工作室", "analysis": "面向顶级品牌的沉浸式 WebGL 工作室，整站本身就是一段实时渲染体验，场景过渡极考究，是与 Lusion 同档的「体验优先」工作室范本。"},
    {"id": "immersive-garden", "name": "Immersive Garden", "url": "https://immersive-g.com/",
     "category": "WebGL·沉浸式", "tags": ["WebGL", "沉浸式", "品牌叙事"],
     "note": "", "analysis": "WebGL 场景化开场 + 叙事型动效，用实时三维讲品牌故事，是商业 WebGL「沉浸但克制」的代表。"},
    {"id": "makemepulse", "name": "makemepulse", "url": "https://makemepulse.com/",
     "category": "WebGL·沉浸式", "tags": ["WebGL", "Three.js", "创意工作室"],
     "note": "", "analysis": "Three.js 驱动的全球创意工作室，擅长粒子/流体/动态几何。把实验感握在「不过火」的分寸里，适合当 WebGL 项目的交付参考。"},
    {"id": "unseen-studio", "name": "Unseen Studio", "url": "https://unseen.co/",
     "category": "WebGL·沉浸式", "tags": ["WebGL", "品牌", "动态", "工作室"],
     "note": "旗下 illoca.unseen.co 项目站已在画廊中", "analysis": "Unseen Studio 主站，WebGL + 电影级动态的品牌叙事，沉稳高级，是「沉浸但克制」的机构官网范本。"},
    {"id": "obys-agency", "name": "Obys Agency", "url": "https://www.obys.agency/",
     "category": "创意机构·个性", "tags": ["创意机构", "排版", "动效", "WebGL"],
     "note": "", "analysis": "乌克兰 Obys Agency，超大字号 + 克制的交互过渡，排版与动效极具辨识度，Dribbble/Awwwards 常客，机构官网的个性标杆。"},
    {"id": "resn", "name": "Resn", "url": "https://resn.co.nz/",
     "category": "创意机构·个性", "tags": ["创意机构", "交互", "幽默", "动效"],
     "note": "", "analysis": "新西兰 Resn，全网最会「整活」的创意机构——官网风格随项目轮换、幽默感拉满，每次访问都是新体验，性格 > 炫技的典范。"},
    {"id": "basement-studio", "name": "Basement Studio", "url": "https://basement.studio/",
     "category": "创意机构·个性", "tags": ["创意机构", "街头风", "微交互"],
     "note": "", "analysis": "「We make cool shit that performs.」暗黑街头风 + 密集微交互，年轻化机构官网的潮流范本。"},
    {"id": "hello-monday", "name": "Hello Monday", "url": "https://www.hellomonday.com/",
     "category": "创意机构·个性", "tags": ["创意机构", "动效", "玩趣"],
     "note": "", "analysis": "明亮玩趣的创意机构，鼠标跟随互动 + 活泼动效，记忆点强，做「有情绪」的官网参考。"},
    {"id": "dogstudio", "name": "Dogstudio", "url": "https://dogstudio.co/",
     "category": "创意机构·个性", "tags": ["创意机构", "复古", "动效"],
     "note": "", "analysis": "复古霓虹 + 强运动感的创意工作室，Awwwards 常客，把复古情调做出当代质感。"},
    {"id": "stink-studios", "name": "Stink Studios", "url": "https://stinkstudios.com/",
     "category": "创意机构·个性", "tags": ["创意机构", "WebGL", "影视"],
     "note": "", "analysis": "WebGL 场景 + 锐利动效的全球创意厂牌，商业创意与技术的平衡范本。"},
    {"id": "exo-ape", "name": "Exo Ape", "url": "https://www.exoape.com/",
     "category": "创意机构·个性", "tags": ["创意机构", "品牌", "数字设计"],
     "note": "", "analysis": "全球数字设计工作室，动效 + 品牌定位成熟，通用型创意机构的落地范本。"},
    {"id": "locomotive", "name": "Locomotive", "url": "https://locomotive.ca/",
     "category": "交互·动效标杆", "tags": ["交互", "平滑滚动", "动效", "工作室"],
     "note": "", "analysis": "蒙特利尔网页工作室，「平滑滚动」交互范式的开创者，滚动节奏与惯性物理打磨到极致，无数站点抄它的手感。"},
    {"id": "cuberto", "name": "Cuberto", "url": "https://cuberto.com/",
     "category": "交互·动效标杆", "tags": ["交互动效", "流体动效", "UI"],
     "note": "", "analysis": "流体形变动效 + 极致顺滑的滚动过渡，数字产品动效的标杆，适合当 UI/交互动效参考。"},
    {"id": "14islands", "name": "14islands", "url": "https://14islands.com/",
     "category": "交互·动效标杆", "tags": ["Three.js", "工作室", "匠心", "极简"],
     "note": "", "analysis": "斯德哥尔摩匠心工作室，Three.js + 细节至上的手工质感，北欧「克制的精致」代表。"},
    {"id": "media-monks", "name": "Monks (MediaMonks)", "url": "https://mediamonks.com/",
     "category": "交互·动效标杆", "tags": ["创意厂牌", "WebGL", "商业项目"],
     "note": "原 MediaMonks，现已更名 Monks", "analysis": "全球创意制作巨头，商业级 WebGL/交互动效项目的最高水准样本，看行业「天花板」怎么做。"},
    {"id": "ueno", "name": "Ueno", "url": "https://ueno.co/",
     "category": "交互·动效标杆", "tags": ["创意机构", "极简", "产品"],
     "note": "", "analysis": "旧金山战略设计与创新机构，极简但每个交互细节质感顶级，服务型机构的精致范本。"},
    {"id": "bruno-simon", "name": "Bruno Simon", "url": "https://bruno-simon.com/",
     "category": "个人作品集", "tags": ["Three.js", "作品集", "3D", "游戏"],
     "note": "", "analysis": "用 Three.js 做了一个可以「开车逛」的 3D 世界作品集，方向键驾驶。个人站里最出圈的一个，交互即内容。"},
    {"id": "aristide-benoist", "name": "Aristide Benoist", "url": "https://aristidebenoist.com/",
     "category": "个人作品集", "tags": ["WebGL", "作品集", "交互实验"],
     "note": "", "analysis": "独立开发者的 WebGL 作品集，进去就是纯交互实验，标新立异又克制，个人技术型作品集的标志。"},
    {"id": "david-heckhoff", "name": "David Heckhoff", "url": "https://david-hckh.com/",
     "category": "个人作品集", "tags": ["WebGL", "作品集", "着色器"],
     "note": "", "analysis": "WebGL 开发者个人站，粒子/着色器实验玩得花，前端创意技术方向的作品集样本。"},
    {"id": "niccolo-miranda", "name": "Niccolò Miranda", "url": "https://niccolomiranda.com/",
     "category": "个人作品集", "tags": ["作品集", "滚动叙事", "创意"],
     "note": "", "analysis": "「Paper Portfolio」——纸张撕开翻转的卷轴式滚动叙事，创意叙事个人站的标杆。"},
]

def main():
    with open(os.path.join(DATA, "sites.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    sites = cfg["sites"]
    ids = set()
    for s in sites:
        ids.add(s["id"])
        s["category"] = EXISTING_CAT.get(s["id"], "创意机构·个性")
    added = 0
    for n in NEW_SITES:
        if n["id"] in ids:
            print("skip duplicate", n["id"])
            continue
        sites.append(n)
        added += 1
    with open(os.path.join(DATA, "sites.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"done: {len(sites)} sites total, +{added} new")

if __name__ == "__main__":
    main()
