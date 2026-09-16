#!/bin/bash
# 设计灵感墙：定时刷新（重截 + 生成 + 提交部署）
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
echo "[1/4] 采集（重截全部站点）"
python3 scripts/collect.py --force
echo "[2/4] 生成封面（显著度裁剪）"
python3 scripts/covers.py
echo "[3/4] 生成画廊"
python3 scripts/generate.py
echo "[4/4] 提交并推送"
git add -A
if git diff --cached --quiet; then
  echo "结果：无内容变更，未推送"
else
  git commit -q -m "auto refresh $(date '+%F %R')"
  git -c http.proxy= -c https.proxy= push origin main 2>&1 | tail -3
  echo "结果：已刷新并推送"
fi