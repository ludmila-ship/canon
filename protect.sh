#!/usr/bin/env bash
# 给 main 加保护：禁止直推、必须 PR、必须过 canon-lint、必须 Owner 审。
# 用法: ./protect.sh <org>
set -euo pipefail
ORG="${1:?用法: ./protect.sh <org>}"
REPO="canon"

echo "配置 $ORG/$REPO 的 main 分支保护..."

gh api -X PUT "repos/$ORG/$REPO/branches/main/protection" --input - <<JSON
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["canon"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "完成。验证："
gh api "repos/$ORG/$REPO/branches/main/protection" --jq '{
  pr_reviews: .required_pull_request_reviews.required_approving_review_count,
  codeowners: .required_pull_request_reviews.require_code_owner_reviews,
  status: .required_status_checks.contexts,
  enforce_admins: .enforce_admins.enabled,
  force_push: .allow_force_pushes.enabled
}'
