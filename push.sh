#!/usr/bin/env bash
# 只创建分支 + 开 PR，绝不直接推 main。
# 用法: ./push.sh <org> [branch]
set -euo pipefail

ORG="${1:?用法: ./push.sh <org> [branch]}"
BRANCH="${2:-init/scaffold}"
REPO="canon"

if ! gh api "/orgs/$ORG" >/dev/null 2>&1; then
  echo "组织 $ORG 不存在。先到 https://github.com/organizations/plan 创建它。"
  exit 1
fi

# 1) 建仓库：让 GitHub 只生成一个空 README 到 main（不是我们的文档）
if ! gh repo view "$ORG/$REPO" >/dev/null 2>&1; then
  gh repo create "$ORG/$REPO" --public --add-readme \
    --description "柳德米拉世界：正典、设定与旁支（Lyudmila World canon）"
else
  echo "仓库 $ORG/$REPO 已存在，跳过创建。"
fi

# 2) 本地：在独立分支上提交骨架（不碰 main）
git init 2>/dev/null || true
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
git add -A
git commit -m "scaffold: 正典仓库骨架（待审）" 2>/dev/null || echo "（无改动可提交）"
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$ORG/$REPO.git"

# 3) 只推分支
git push -u origin "$BRANCH"

# 4) 开 PR，不合并
gh pr create --repo "$ORG/$REPO" --base main --head "$BRANCH" \
  --title "scaffold: 正典仓库骨架（请逐条审阅）" \
  --body "本 PR 只新增骨架，不改任何既有文档。合并前请先运行 protect.sh 配置分支保护。"

echo
echo "已开 PR（未合并）："
gh pr view --repo "$ORG/$REPO" --json url --jq .url
echo
echo "下一步："
echo "  1) 逐条审阅这个 PR"
echo "  2) ./protect.sh $ORG   配置 main 保护 + canon-lint 必需检查"
echo "  3) 确认无误后，在网页上点 Merge"
