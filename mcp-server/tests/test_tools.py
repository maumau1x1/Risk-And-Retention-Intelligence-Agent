"""Tests for MCP tools and Fabric IQ client."""

import json
import pytest

from risk_agent_mcp.fabric.iq_client import FabricIQClient
from risk_agent_mcp.config import Settings
from risk_agent_mcp.widgets.dashboard import (
    build_risk_dashboard_widget,
    build_churn_drivers_widget,
    build_at_risk_table_widget,
    build_retention_trend_widget,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_client():
    settings = Settings(USE_MOCK_FABRIC_DATA=True)
    return FabricIQClient(settings=settings)


# ---------------------------------------------------------------------------
# Fabric IQ Client — Read operations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dashboard_kpis_keys(mock_client):
    kpis = await mock_client.get_dashboard_kpis(segment="enterprise", period="QTD")
    assert "churn_rate" in kpis
    assert "retention_score" in kpis
    assert "npl_ratio" in kpis
    assert "loss_recovery_rate" in kpis
    assert kpis["segment"] == "enterprise"
    assert kpis["period"] == "QTD"


@pytest.mark.asyncio
async def test_churn_drivers_count(mock_client):
    drivers = await mock_client.get_churn_drivers(top_n=3)
    assert len(drivers) == 3
    assert "driver" in drivers[0]
    assert "impact_score" in drivers[0]
    assert "affected_accounts" in drivers[0]


@pytest.mark.asyncio
async def test_at_risk_accounts_filter(mock_client):
    accounts = await mock_client.list_at_risk_accounts(min_risk_score=85)
    assert all(a["risk_score"] >= 85 for a in accounts)
    # enriched fields present
    assert all("region" in a for a in accounts)
    assert all("contract_tenure_months" in a for a in accounts)


@pytest.mark.asyncio
async def test_retention_trend_months(mock_client):
    trend = await mock_client.get_retention_trend(region="all", period="L12M")
    months = trend.get("months", [])
    assert len(months) == 12
    assert "churn_rate" in months[0]
    assert "loss_recovery_rate" in months[0]
    assert "retention_score" in months[0]


@pytest.mark.asyncio
async def test_loss_recovery_structure(mock_client):
    data = await mock_client.get_loss_recovery(region="APAC", period="YTD")
    assert "loss_recovery_rate" in data
    assert "write_off_ratio" in data
    assert "collection_efficiency" in data


# ---------------------------------------------------------------------------
# Fabric IQ Client — Write operations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_flag_risk_tier_valid(mock_client):
    result = await mock_client.flag_account_risk_tier("ACC-1042", "Critical")
    assert result["success"] is True
    assert result["account_id"] == "ACC-1042"
    assert result["tier"] == "Critical"


@pytest.mark.asyncio
async def test_flag_risk_tier_invalid(mock_client):
    result = await mock_client.flag_account_risk_tier("ACC-1042", "Unknown")
    assert result["success"] is False
    assert "Invalid tier" in result["error"]


# ---------------------------------------------------------------------------
# Widgets — Adaptive Card schema assertions
# ---------------------------------------------------------------------------

def _parse_card(raw: str) -> dict:
    """Parse the JSON string returned by widget builders."""
    return json.loads(raw)


def test_risk_dashboard_widget_schema():
    kpis = {
        "segment": "all", "period": "QTD",
        "churn_rate": 0.124, "retention_score": 78.5,
        "npl_ratio": 0.031, "loss_recovery_rate": 0.67,
        "high_risk_accounts": 3, "source": "mock_semantic_model",
    }
    card = _parse_card(build_risk_dashboard_widget(kpis))
    assert card["type"] == "AdaptiveCard"
    assert card["version"] == "1.6"
    assert any(b.get("type") == "FactSet" for b in card["body"])


def test_churn_drivers_widget_schema():
    drivers = [
        {"driver": "Low adoption", "impact_score": 0.34, "affected_accounts": 128},
        {"driver": "SLA breaches", "impact_score": 0.22, "affected_accounts": 87},
    ]
    card = _parse_card(build_churn_drivers_widget(drivers, "enterprise"))
    assert card["type"] == "AdaptiveCard"
    # Should have at least the header container + 2 driver rows
    assert len(card["body"]) >= 3


def test_at_risk_table_widget_schema():
    accounts = [
        {
            "account_id": "ACC-1042", "name": "Northwind", "risk_score": 91,
            "churn_prob": 0.78, "region": "APAC", "contract_tenure_months": 14,
        }
    ]
    card = _parse_card(build_at_risk_table_widget(accounts))
    assert card["type"] == "AdaptiveCard"
    # Header container must be first element
    assert card["body"][0]["type"] == "Container"


def test_retention_trend_widget_schema():
    months = [
        {"month": "Jan 2025", "churn_rate": 0.12, "loss_recovery_rate": 0.67, "retention_score": 79}
        for _ in range(12)
    ]
    trend = {"region": "all", "period": "L12M", "months": months}
    card = _parse_card(build_retention_trend_widget(trend))
    assert card["type"] == "AdaptiveCard"
    # Header + column labels + 12 rows + footer = 15 items
    assert len(card["body"]) == 15


# ---------------------------------------------------------------------------
# Auth — scope guard
# ---------------------------------------------------------------------------

from risk_agent_mcp.auth.entra import TokenClaims, require_write_scope, AuthenticationError


def test_require_write_scope_passes_with_scope():
    claims = TokenClaims(subject="user1", name="Test", scopes=("Retention.Write",), roles=())
    require_write_scope(claims)  # should not raise


def test_require_write_scope_passes_with_role():
    claims = TokenClaims(subject="user1", name="Test", scopes=(), roles=("Retention.Write",))
    require_write_scope(claims)  # should not raise


def test_require_write_scope_dev_bypass():
    claims = TokenClaims(subject="dev-user", name="Dev", scopes=(), roles=())
    require_write_scope(claims)  # dev-user always passes


def test_require_write_scope_fails_no_scope():
    claims = TokenClaims(subject="real-user-no-scope", name="User", scopes=(), roles=())
    with pytest.raises(AuthenticationError, match="Insufficient scope"):
        require_write_scope(claims)
