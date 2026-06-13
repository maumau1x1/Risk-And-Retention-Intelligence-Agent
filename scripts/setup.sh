#!/usr/bin/env bash
# Bootstrap the Risk & Retention Intelligence Agent hackathon project.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Risk & Retention Intelligence Agent — Setup"
echo "    Root: $ROOT"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "[ok] Created .env from template"
fi

mkdir -p agent/env
[[ -f agent/env/.env.dev ]] || cat > agent/env/.env.dev <<'EOF'
TEAMSFX_ENV=dev
APP_NAME_SUFFIX=-dev
MCP_SERVER_URL=http://localhost:8080/mcp
EOF

[[ -f agent/env/.env.dev.user ]] || cat > agent/env/.env.dev.user <<'EOF'
MCP_SERVER_URL=http://localhost:8080/mcp
EOF

cd mcp-server
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev,apps]"
[[ -f .env ]] || cp .env.example .env
cd "$ROOT"

npx -y --package @microsoft/m365agentstoolkit-cli atk --version || true

echo ""
echo "Next: fill .env values, run ./scripts/dev.sh, then ATK Provision in agent/"
