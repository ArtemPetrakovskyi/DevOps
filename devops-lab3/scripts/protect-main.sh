#!/usr/bin/env bash
# Налаштування Branch Protection для main через GitHub CLI (gh).
# Потрібно: gh auth login (акаунт з правами адміністратора репозиторію).
# Використання:  ./scripts/protect-main.sh <owner>/<repo>
# Приклад:       ./scripts/protect-main.sh ivan-petrenko/devops-lab1
set -euo pipefail

REPO="${1:?Вкажіть репозиторій у форматі owner/repo}"

gh api -X PUT "repos/${REPO}/branches/main/protection" --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Build & Test (api)",
      "Build & Test (web)",
      "Docker build & scan (api)",
      "Docker build & scan (web)"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON

echo "Branch protection для main у ${REPO} увімкнено."
