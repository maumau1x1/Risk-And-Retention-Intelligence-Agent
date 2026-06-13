<div align="center">

# 🛡️ Risk & Retention Intelligence Agent

**Enterprise AI Agent for Microsoft 365 Copilot**

[![Hackathon](https://img.shields.io/badge/Hackathon-Enterprise%20Agents%20for%20M365%20Copilot-0078D4?style=for-the-badge&logo=microsoft)](https://aka.ms/m365copilot)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.x-FF6B35?style=for-the-badge)](https://github.com/jlowin/fastmcp)
[![Fabric IQ](https://img.shields.io/badge/Microsoft%20Fabric%20IQ-Grounded-F2C811?style=for-the-badge&logo=microsoftazure)](https://learn.microsoft.com/fabric)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

*Empowering Risk Analysts and Financial Controllers with governed, AI-driven portfolio insights grounded in Microsoft Fabric IQ semantic models.*

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Features & Tools](#-features--tools)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Testing with MCP Inspector](#-testing-with-mcp-inspector)
- [Adaptive Card Previewer](#-adaptive-card-previewer)
- [Environment Variables](#-environment-variables)
- [Security](#-security)
- [Hackathon Rubric Alignment](#-hackathon-rubric-alignment)

---

## 🎯 Overview

The **Risk & Retention Intelligence Agent** is an enterprise-grade AI agent built for the **"Enterprise Agents for Microsoft 365 Copilot"** hackathon track. It serves **Risk Analysts** and **Financial Controllers** by surfacing real-time portfolio risk KPIs, customer churn drivers, loss recovery metrics, and retention prioritisation — all grounded in **Microsoft Fabric IQ semantic models**.

Users interact through natural language in Microsoft 365 Copilot chat. The agent calls a **Python FastMCP backend** that queries Fabric IQ and returns rich **Adaptive Card v1.6 widgets** directly in the chat window. Governed write operations (creating retention tasks, flagging risk tiers) are protected by **Microsoft Entra ID OAuth 2.1**.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Microsoft 365 Copilot                     │
│                                                             │
│   👤 Risk Analyst  ──▶  💬 Copilot Chat                    │
│                              │                              │
│                    📋 Declarative Agent                     │
│                    (declarativeAgent.json)                  │
│                              │                              │
│                    🔌 MCP Plugin Descriptor                 │
│                    (risk-retention-plugin.json)             │
└──────────────────────────────┼──────────────────────────────┘
                               │  HTTP /mcp
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python FastMCP Backend                      │
│                                                             │
│   ⚙️  FastMCP Server  (main.py)                            │
│        │                                                    │
│        ├── 🛠️  Tool Registry (7 tools)                     │
│        │         ├── 📊 get_risk_dashboard                  │
│        │         ├── 🔍 analyze_churn_drivers               │
│        │         ├── 💰 get_loss_recovery_metrics           │
│        │         ├── ⚠️  list_at_risk_accounts              │
│        │         ├── 📈 get_retention_trend                 │
│        │         ├── ✏️  create_retention_task   ──▶ 🔐 Auth│
│        │         └── 🏷️  flag_account_risk_tier  ──▶ 🔐 Auth│
│        │                                                    │
│        ├── 🎨 Adaptive Card Widgets (dashboard.py)         │
│        ├── 🔐 Entra ID Auth (entra.py + PyJWT RS256)       │
│        └── 📊 Fabric IQ Client (iq_client.py)             │
└──────────────────────────────┼──────────────────────────────┘
                               │  DAX executeQueries
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   Microsoft Fabric IQ                        │
│                                                             │
│   📐 Semantic Model: RiskRetentionMetrics                  │
│      ├── Measures: ChurnRate · RetentionScore              │
│      │            NPLRatio · LossRecoveryRate              │
│      │            ChurnDriverImpact · RetentionTrend       │
│      └── Dimensions: Segment · Region · Period             │
│                                                             │
│   🧠 Ontology: EnterpriseRiskRetention                     │
│      └── Entities: Customer · RiskSignal                   │
│                    ChurnDriver · RetentionAction           │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend** | Microsoft 365 Agents Toolkit — Declarative Agent | Natural language interface in Copilot chat |
| **Backend** | Python 3.12 · FastMCP 2.x | MCP server with HTTP transport |
| **Intelligence** | Microsoft Fabric IQ | Semantic model queries (DAX) |
| **UI Widgets** | Adaptive Card v1.6 JSON | Rich visual cards rendered in Copilot |
| **Security** | Microsoft Entra ID · PyJWT RS256 | OAuth 2.1 token validation for write ops |
| **Containerisation** | Docker · docker-compose | Portable deployment |
| **Dev Tunnel** | ngrok | Expose local server for Copilot testing |

---

## 🛠️ Features & Tools

The agent exposes **7 MCP tools** across two categories:

### 📊 Read Tools — return Adaptive Card widgets

| Tool | Description | Widget Type |
|---|---|---|
| `get_risk_dashboard` | Portfolio KPIs: ChurnRate, RetentionScore, NPLRatio, LossRecoveryRate | FactSet KPI grid |
| `analyze_churn_drivers` | Top N churn drivers ranked by Fabric IQ ChurnDriverImpact score | Impact bar chart card |
| `get_loss_recovery_metrics` | Loss recovery rate, write-off ratio, collection efficiency by region | Structured JSON |
| `list_at_risk_accounts` | Accounts above risk threshold with churn probability, region, tenure | Colour-coded table card |
| `get_retention_trend` | 12-month churn & retention trend with 🔴🟢 traffic-light indicators | Monthly trend table |

### ✏️ Write Tools — require `Retention.Write` scope

| Tool | Description | Auth Required |
|---|---|---|
| `create_retention_task` | Create governed retention outreach task for an at-risk account | ✅ Entra OAuth |
| `flag_account_risk_tier` | Update account risk tier with justification (audit trail) | ✅ Entra OAuth |

> **Demo mode**: When `USE_MOCK_FABRIC_DATA=true` and Entra is not configured, write tools automatically bypass auth with a `dev-user` claim — no setup needed for hackathon demos.

---

## 📁 Project Structure

```
Microsoft Risk Agent/
│
├── 📋 agent/                            # Microsoft 365 Agents Toolkit
│   ├── appPackage/
│   │   ├── declarativeAgent.json        # DA manifest (schema v1.7)
│   │   ├── manifest.json                # Teams app manifest (v1.19)
│   │   ├── risk-retention-plugin.json   # MCP plugin descriptor (7 tools)
│   │   ├── color.png                    # App icon 192×192
│   │   └── outline.png                  # App icon 32×32
│   ├── env/
│   │   ├── .env.dev                     # ATK env (auto-filled by provision)
│   │   └── .env.dev.user                # Local overrides — set MCP_SERVER_URL here
│   └── m365agents.yml                   # Provision + deploy lifecycle
│
├── ⚙️  mcp-server/                      # Python FastMCP backend
│   ├── src/risk_agent_mcp/
│   │   ├── main.py                      # FastMCP server entrypoint
│   │   ├── config.py                    # Pydantic-settings (all secrets via .env)
│   │   ├── auth/
│   │   │   └── entra.py                 # Entra ID OAuth + PyJWT RS256 validation
│   │   ├── fabric/
│   │   │   └── iq_client.py             # Fabric IQ mock + production client
│   │   ├── tools/
│   │   │   └── registry.py              # 7 MCP tool registrations
│   │   └── widgets/
│   │       └── dashboard.py             # Adaptive Card v1.6 widget builders
│   ├── tests/
│   │   └── test_tools.py                # 15+ tests (client, widgets, auth)
│   ├── Dockerfile                       # Container image
│   └── pyproject.toml                   # Dependencies (FastMCP, PyJWT, etc.)
│
├── 🧠 fabric/
│   ├── semantic-models/
│   │   └── risk-retention-measures.json # DAX measure reference
│   └── ontologies/
│       └── risk-retention-ontology.json # EnterpriseRiskRetention entity model
│
├── 📜 scripts/
│   ├── setup.ps1                        # Bootstrap (venv, deps, env files)
│   ├── dev.ps1                          # Start MCP server in dev mode
│   ├── package-agent.ps1                # Build appPackage.zip (fast path)
│   ├── quick-provision.ps1              # One-click ATK provision
│   └── discover-mcp-tools.ps1          # List live tools from running server
│
├── docker-compose.yml                   # One-command Docker deployment
├── .env.example                         # Environment template (copy to .env)
└── README.md                            # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for npx / ATK CLI)
- PowerShell 5.1+

### 1. Bootstrap the project

```powershell
cd "Microsoft Risk Agent"
.\scripts\setup.ps1
```

This creates the virtual environment, installs all Python dependencies, and copies `.env` templates.

### 2. Configure environment *(optional for mock demo)*

```powershell
notepad .env
```

```env
# Leave these blank to use mock data (recommended for demo)
FABRIC_WORKSPACE_ID=
FABRIC_SEMANTIC_MODEL_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=

# Mock mode is ON by default
USE_MOCK_FABRIC_DATA=true
```

### 3. Start the MCP server

```powershell
.\scripts\dev.ps1
```

The server starts at **`http://localhost:8080/mcp`**

### 4. (Optional) Expose publicly via ngrok

Required only if testing with Microsoft 365 Copilot:

```powershell
ngrok http 8080
```

Copy the `https://` URL into `agent/env/.env.dev.user`:
```env
MCP_SERVER_URL=https://<your-id>.ngrok-free.app/mcp
```

### 5. Package the agent

```powershell
.\scripts\package-agent.ps1
# → agent/appPackage/build/appPackage.dev.zip
```

Upload to [dev.teams.microsoft.com/apps](https://dev.teams.microsoft.com/apps) → **Import App** → **Preview in Teams**

> ⚠️ Requires a **Microsoft 365 Copilot licence**. Use MCP Inspector (below) for licence-free testing.

---

## 🔬 Testing with MCP Inspector

Test all 7 tools locally **without any Microsoft licence**.

### Launch Inspector

```powershell
# Terminal 1 — MCP Server must be running
.\scripts\dev.ps1

# Terminal 2 — Launch Inspector
npx @modelcontextprotocol/inspector
```

Open **[http://localhost:5173](http://localhost:5173)** → set Transport to `Streamable HTTP` → URL: `http://localhost:8080/mcp` → **Connect**

### Sample Inputs

**`get_risk_dashboard`**
```json
{ "segment": "enterprise", "period": "QTD" }
```

**`analyze_churn_drivers`**
```json
{ "segment": "all", "top_n": 5 }
```

**`list_at_risk_accounts`**
```json
{ "min_risk_score": 80, "limit": 5 }
```

**`get_retention_trend`**
```json
{ "region": "APAC", "period": "L12M" }
```

**`create_retention_task`** *(write — dev bypass active)*
```json
{ "account_id": "ACC-1042", "priority": "critical", "notes": "Contract renewal due in 14 days" }
```

**`flag_account_risk_tier`** *(write — dev bypass active)*
```json
{ "account_id": "ACC-2087", "tier": "Critical", "justification": "Missed 3 consecutive SLA targets" }
```

---

## 🎨 Adaptive Card Previewer

The tool responses are **Adaptive Card v1.6 JSON**. To see them rendered visually (exactly as they appear in Teams/Copilot):

1. Run a tool in MCP Inspector and **copy the JSON output**
2. Go to **[adaptivecards.io/designer](https://adaptivecards.io/designer/)**
3. Paste the JSON into the **Card Payload Editor** (bottom-left panel)
4. The rendered card appears live on the right ✅

---

## 🔧 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MCP_SERVER_HOST` | `0.0.0.0` | Server bind address |
| `MCP_SERVER_PORT` | `8080` | Server port |
| `MCP_SERVER_URL` | `http://localhost:8080/mcp` | Public URL (set to ngrok URL for Copilot) |
| `USE_MOCK_FABRIC_DATA` | `true` | Use mock data instead of live Fabric IQ |
| `AZURE_TENANT_ID` | *(blank)* | Entra tenant ID for OAuth validation |
| `AZURE_CLIENT_ID` | *(blank)* | Entra app client ID |
| `AZURE_CLIENT_SECRET` | *(blank)* | Entra app client secret |
| `AZURE_API_AUDIENCE` | *(blank)* | OAuth audience (defaults to client ID) |
| `FABRIC_WORKSPACE_ID` | *(blank)* | Fabric workspace GUID |
| `FABRIC_SEMANTIC_MODEL_ID` | *(blank)* | Semantic model GUID |
| `FABRIC_API_BASE_URL` | `https://api.fabric.microsoft.com/v1` | Fabric REST API base |

> **Never commit real values.** All secrets must live in `.env` which is excluded from git.

---

## 🔐 Security

| Practice | Implementation |
|---|---|
| **Zero hardcoded secrets** | All config via `pydantic-settings` from `.env` |
| **Write operation gating** | `create_retention_task` + `flag_account_risk_tier` require `Retention.Write` scope |
| **Production JWT validation** | RS256 signature + JWKS endpoint + `iss`/`aud`/`exp` checks via PyJWT |
| **Explicit dev bypass** | Dev mode logs a `WARNING` — never silently skips auth |
| **Git exclusions** | `.env`, `.venv`, `*.zip`, `__pycache__` all in `.gitignore` |

---

## 📊 Hackathon Rubric Alignment

| Evaluation Criterion | Our Implementation |
|---|---|
| **Declarative Agent** | `declarativeAgent.json` schema v1.7 with 4 conversation starters, full Fabric IQ grounding instructions, and explicit tool guidance |
| **External MCP Server** | FastMCP Python server, 7 registered tools, HTTP `/mcp` endpoint, containerised with Docker |
| **Fabric IQ Integration** | `FabricIQClient` maps to `ChurnRate`, `RetentionScore`, `NPLRatio`, `LossRecoveryRate`, `ChurnDriverImpact`, `RetentionTrend` measures with proper DAX `executeQueries` API shape |
| **Interactive UI (MCP Apps)** | All read tools return **Adaptive Card v1.6 JSON** with FactSet grids, colour-coded risk scores, impact bars, and 12-month trend tables |
| **Governed Write Operations** | Two write tools gated by `Retention.Write` OAuth scope via Entra OIDC JWKS RS256 validation; clean dev bypass for demos |
| **Enterprise Security** | pydantic-settings for all config, PyJWT production validation, dev bypass warns loudly, no secrets in source |
| **Enterprise Persona** | Targets Risk Analysts + Financial Controllers; portfolio-level KPIs, regional breakdowns, at-risk prioritisation, audit-trailed writes |
| **Documentation** | Full README with architecture diagram, rubric table, tool reference, and step-by-step guides |

---

## 🐳 Docker Deployment

```powershell
# Start with Docker Compose
docker compose up --build

# Server available at http://localhost:8080/mcp
```

---

## 🧪 Run Tests

```powershell
cd mcp-server
.\.venv\Scripts\Activate.ps1
pytest tests/ -v
```

**Test coverage includes:**
- ✅ Fabric IQ client — all read operations
- ✅ Fabric IQ client — write operations (valid + invalid tier)
- ✅ All 4 Adaptive Card widget schemas
- ✅ Auth scope guard — pass / fail / dev-bypass scenarios

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with ❤️ for the **Microsoft 365 Copilot Hackathon**

*Microsoft Fabric IQ · FastMCP · Adaptive Cards · Microsoft Entra ID*

</div>
