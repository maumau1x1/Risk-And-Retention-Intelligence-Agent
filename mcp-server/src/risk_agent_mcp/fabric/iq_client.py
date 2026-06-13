"""Microsoft Fabric IQ client — semantic model queries for risk & retention KPIs."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from risk_agent_mcp.config import Settings, get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mock datasets aligned to the RiskRetentionMetrics semantic model
# ---------------------------------------------------------------------------

_MOCK_CHURN_DRIVERS = [
    {"driver": "Low product adoption", "impact_score": 0.34, "affected_accounts": 128},
    {"driver": "Support SLA breaches", "impact_score": 0.22, "affected_accounts": 87},
    {"driver": "Contract renewal within 30d", "impact_score": 0.18, "affected_accounts": 64},
    {"driver": "Pricing sensitivity", "impact_score": 0.15, "affected_accounts": 51},
    {"driver": "Competitive displacement", "impact_score": 0.11, "affected_accounts": 39},
]

_MOCK_LOSS_RECOVERY = {
    "loss_recovery_rate": 0.67,
    "write_off_ratio": 0.08,
    "collection_efficiency": 0.82,
    "total_recovered_usd": 4_250_000,
    "total_at_risk_usd": 6_340_000,
}

_MOCK_AT_RISK = [
    {
        "account_id": "ACC-1042",
        "name": "Northwind Traders",
        "risk_score": 91,
        "churn_prob": 0.78,
        "region": "APAC",
        "contract_tenure_months": 14,
        "risk_tier": "Critical",
    },
    {
        "account_id": "ACC-2087",
        "name": "Contoso Pharma",
        "risk_score": 86,
        "churn_prob": 0.71,
        "region": "EMEA",
        "contract_tenure_months": 22,
        "risk_tier": "High",
    },
    {
        "account_id": "ACC-3156",
        "name": "Fabrikam Logistics",
        "risk_score": 84,
        "churn_prob": 0.69,
        "region": "AMER",
        "contract_tenure_months": 8,
        "risk_tier": "High",
    },
    {
        "account_id": "ACC-4201",
        "name": "Adventure Works",
        "risk_score": 79,
        "churn_prob": 0.62,
        "region": "APAC",
        "contract_tenure_months": 31,
        "risk_tier": "Elevated",
    },
    {
        "account_id": "ACC-5334",
        "name": "Tailspin Toys",
        "risk_score": 74,
        "churn_prob": 0.55,
        "region": "AMER",
        "contract_tenure_months": 5,
        "risk_tier": "Elevated",
    },
]

# 12-month trend mock (Jul 2024 → Jun 2025)
_MOCK_TREND_MONTHS = [
    {"month": "Jul 2024", "churn_rate": 0.108, "loss_recovery_rate": 0.71, "retention_score": 82},
    {"month": "Aug 2024", "churn_rate": 0.112, "loss_recovery_rate": 0.69, "retention_score": 81},
    {"month": "Sep 2024", "churn_rate": 0.119, "loss_recovery_rate": 0.68, "retention_score": 80},
    {"month": "Oct 2024", "churn_rate": 0.126, "loss_recovery_rate": 0.66, "retention_score": 79},
    {"month": "Nov 2024", "churn_rate": 0.134, "loss_recovery_rate": 0.64, "retention_score": 77},
    {"month": "Dec 2024", "churn_rate": 0.141, "loss_recovery_rate": 0.62, "retention_score": 76},
    {"month": "Jan 2025", "churn_rate": 0.137, "loss_recovery_rate": 0.63, "retention_score": 77},
    {"month": "Feb 2025", "churn_rate": 0.133, "loss_recovery_rate": 0.65, "retention_score": 78},
    {"month": "Mar 2025", "churn_rate": 0.129, "loss_recovery_rate": 0.66, "retention_score": 79},
    {"month": "Apr 2025", "churn_rate": 0.124, "loss_recovery_rate": 0.67, "retention_score": 79},
    {"month": "May 2025", "churn_rate": 0.121, "loss_recovery_rate": 0.68, "retention_score": 80},
    {"month": "Jun 2025", "churn_rate": 0.124, "loss_recovery_rate": 0.67, "retention_score": 78},
]

# In-memory risk tier overrides (demo write store)
_RISK_TIER_OVERRIDES: dict[str, str] = {}


class FabricIQClient:
    """Query Fabric IQ semantic models / ontologies for governed risk metrics."""

    def __init__(self, settings: Settings | None = None, access_token: str | None = None) -> None:
        self._settings = settings or get_settings()
        self._token = access_token

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_dashboard_kpis(self, segment: str = "all", period: str = "QTD") -> dict[str, Any]:
        if self._should_use_mock():
            return {
                "segment": segment,
                "period": period,
                "churn_rate": 0.124,
                "retention_score": 78.5,
                "npl_ratio": 0.031,
                "loss_recovery_rate": 0.67,
                "high_risk_accounts": len([a for a in _MOCK_AT_RISK if a["risk_score"] >= 80]),
                "source": "mock_semantic_model",
            }
        return await self._execute_semantic_query(
            measures=["ChurnRate", "RetentionScore", "NPLRatio", "LossRecoveryRate"],
            filters={"Segment": segment, "Period": period},
        )

    async def get_churn_drivers(self, segment: str = "all", top_n: int = 5) -> list[dict[str, Any]]:
        if self._should_use_mock():
            return _MOCK_CHURN_DRIVERS[:top_n]
        return await self._execute_semantic_query(
            measures=["ChurnDriverImpact"],
            dimensions=["ChurnDriver"],
            filters={"Segment": segment},
            top=top_n,
        )

    async def get_loss_recovery(self, region: str = "all", period: str = "YTD") -> dict[str, Any]:
        if self._should_use_mock():
            return {**_MOCK_LOSS_RECOVERY, "region": region, "period": period}
        return await self._execute_semantic_query(
            measures=["LossRecoveryRate", "WriteOffRatio", "CollectionEfficiency"],
            filters={"Region": region, "Period": period},
        )

    async def list_at_risk_accounts(
        self, min_risk_score: float = 70.0, limit: int = 10
    ) -> list[dict[str, Any]]:
        if self._should_use_mock():
            results = [a for a in _MOCK_AT_RISK if a["risk_score"] >= min_risk_score][:limit]
            # Apply any tier overrides from write operations
            for acct in results:
                if acct["account_id"] in _RISK_TIER_OVERRIDES:
                    acct = dict(acct)
                    acct["risk_tier"] = _RISK_TIER_OVERRIDES[acct["account_id"]]
            return results
        return await self._execute_semantic_query(
            measures=["RiskScore", "ChurnProbability"],
            dimensions=["AccountId", "AccountName"],
            filters={"MinRiskScore": min_risk_score},
            top=limit,
        )

    async def get_retention_trend(
        self, region: str = "all", period: str = "L12M"
    ) -> dict[str, Any]:
        """Return 12-month retention / churn trend data."""
        if self._should_use_mock():
            return {
                "region": region,
                "period": period,
                "months": _MOCK_TREND_MONTHS,
                "source": "mock_semantic_model",
            }
        return await self._execute_semantic_query(
            measures=["ChurnRate", "LossRecoveryRate", "RetentionScore"],
            dimensions=["Month"],
            filters={"Region": region, "Period": period},
        )

    # ------------------------------------------------------------------
    # Write operations (demo in-memory store)
    # ------------------------------------------------------------------

    async def flag_account_risk_tier(
        self, account_id: str, tier: str
    ) -> dict[str, Any]:
        """Update risk tier for an account — persisted to in-memory store."""
        valid_tiers = {"Critical", "High", "Elevated", "Normal"}
        if tier not in valid_tiers:
            return {
                "success": False,
                "error": f"Invalid tier '{tier}'. Valid values: {', '.join(sorted(valid_tiers))}",
            }
        _RISK_TIER_OVERRIDES[account_id] = tier
        logger.info("Risk tier updated: %s → %s", account_id, tier)
        return {"success": True, "account_id": account_id, "tier": tier}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_use_mock(self) -> bool:
        return self._settings.use_mock_fabric_data or not self._settings.fabric_semantic_model_id

    async def _execute_semantic_query(self, **query: Any) -> Any:
        """
        Execute a DAX/semantic query against Fabric IQ REST API.

        Production: POST /workspaces/{id}/semanticModels/{id}/executeQueries
        Body format: { "queries": [{ "query": "<DAX expression>" }] }

        See: https://learn.microsoft.com/rest/api/fabric/semanticmodel/items/execute-queries
        """
        workspace = self._settings.fabric_workspace_id
        model = self._settings.fabric_semantic_model_id
        url = (
            f"{self._settings.fabric_api_base_url}"
            f"/workspaces/{workspace}/semanticModels/{model}/executeQueries"
        )

        measures = query.get("measures", [])
        filters = query.get("filters", {})
        top = query.get("top", 100)

        # Build a DAX EVALUATE expression from the query params
        evaluate_clause = "EVALUATE\n"
        if measures:
            cols = ", ".join(f'"{m}", [{m}]' for m in measures)
            evaluate_clause += f"  ROW({cols})\n"

        dax_body = {
            "queries": [{"query": evaluate_clause}],
            "serializerSettings": {"includeNulls": True},
            "impersonatedUserName": None,
        }

        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=dax_body)
            response.raise_for_status()
            return response.json()
