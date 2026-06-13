"""MCP tool registration — risk metrics, Fabric IQ, and MCP Apps (Adaptive Cards)."""

from __future__ import annotations

import logging
from typing import Any

from fastmcp import FastMCP

from risk_agent_mcp.auth.entra import AuthenticationError, require_write_scope, validate_bearer_token
from risk_agent_mcp.fabric.iq_client import FabricIQClient
from risk_agent_mcp.widgets.dashboard import (
    build_at_risk_table_widget,
    build_churn_drivers_widget,
    build_retention_trend_widget,
    build_risk_dashboard_widget,
)

logger = logging.getLogger(__name__)

# In-memory task store for hackathon demo (replace with Dataverse / Fabric pipeline)
_retention_tasks: list[dict[str, Any]] = []


def register_tools(mcp: FastMCP) -> None:  # noqa: C901
    fabric = FabricIQClient()

    # ------------------------------------------------------------------
    # READ tools — no auth required, return Adaptive Card widgets
    # ------------------------------------------------------------------

    @mcp.tool()
    async def get_risk_dashboard(segment: str = "all", period: str = "QTD") -> str:
        """
        Interactive portfolio risk dashboard grounded in Fabric IQ semantic model KPIs.

        Returns an Adaptive Card with: ChurnRate, RetentionScore, NPLRatio,
        LossRecoveryRate, and high-risk account count.

        segment: all | enterprise | smb | high_risk
        period:  MTD | QTD | YTD | L12M
        """
        kpis = await fabric.get_dashboard_kpis(segment=segment, period=period)
        return build_risk_dashboard_widget(kpis)

    @mcp.tool()
    async def analyze_churn_drivers(segment: str = "all", top_n: int = 5) -> str:
        """
        Analyze top churn drivers ranked by Fabric IQ impact score.

        Returns an Adaptive Card showing each driver, its impact percentage,
        and the number of affected accounts.

        segment: all | enterprise | smb | high_risk
        top_n: number of drivers to return (1-10)
        """
        if top_n < 1:
            top_n = 1
        if top_n > 10:
            top_n = 10
        drivers = await fabric.get_churn_drivers(segment=segment, top_n=top_n)
        return build_churn_drivers_widget(drivers, segment)

    @mcp.tool()
    async def get_loss_recovery_metrics(region: str = "all", period: str = "YTD") -> dict[str, Any]:
        """
        Retrieve loss recovery rate, write-off ratio, and collection efficiency from Fabric IQ.

        region: all | AMER | EMEA | APAC
        period: MTD | QTD | YTD | L12M
        """
        metrics = await fabric.get_loss_recovery(region=region, period=period)
        return {
            "title": "Loss Recovery Metrics",
            "region": metrics.get("region", region),
            "period": metrics.get("period", period),
            "loss_recovery_rate": f"{metrics.get('loss_recovery_rate', 0) * 100:.1f}%",
            "write_off_ratio": f"{metrics.get('write_off_ratio', 0) * 100:.1f}%",
            "collection_efficiency": f"{metrics.get('collection_efficiency', 0) * 100:.1f}%",
            "total_recovered_usd": f"${metrics.get('total_recovered_usd', 0):,.0f}",
            "total_at_risk_usd": f"${metrics.get('total_at_risk_usd', 0):,.0f}",
            "source": "Fabric IQ · LossRecoveryRate measure",
        }

    @mcp.tool()
    async def list_at_risk_accounts(min_risk_score: float = 70.0, limit: int = 10) -> str:
        """
        List accounts exceeding risk thresholds, ranked by retention priority score.

        Returns an Adaptive Card table with account name, region, tenure,
        risk score, and churn probability.

        min_risk_score: minimum RiskScore threshold (0-100, default 70)
        limit: maximum accounts to return (default 10)
        """
        if limit < 1:
            limit = 1
        if limit > 50:
            limit = 50
        accounts = await fabric.list_at_risk_accounts(
            min_risk_score=min_risk_score, limit=limit
        )
        return build_at_risk_table_widget(accounts)

    @mcp.tool()
    async def get_retention_trend(region: str = "all", period: str = "L12M") -> str:
        """
        Show 12-month retention and churn trend vs prior period from Fabric IQ.

        Returns an Adaptive Card table with monthly ChurnRate, LossRecoveryRate,
        and RetentionScore — with traffic-light indicators.

        region: all | AMER | EMEA | APAC
        period: L12M | YTD
        """
        trend = await fabric.get_retention_trend(region=region, period=period)
        return build_retention_trend_widget(trend)

    # ------------------------------------------------------------------
    # WRITE tools — require Entra OAuth bearer token
    # ------------------------------------------------------------------

    @mcp.tool()
    async def create_retention_task(
        account_id: str,
        priority: str,
        notes: str = "",
        authorization: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a governed retention outreach task for an at-risk account.

        Requires: Authorization: Bearer <token> with Retention.Write scope.
        priority: critical | high | medium | low

        In dev mode (no Entra configured), the auth check is bypassed automatically.
        """
        try:
            claims = await validate_bearer_token(authorization)
            require_write_scope(claims)
        except AuthenticationError as exc:
            return {"success": False, "error": str(exc)}

        task = {
            "account_id": account_id,
            "priority": priority,
            "notes": notes,
            "created_by": claims.subject,
            "status": "open",
        }
        _retention_tasks.append(task)
        logger.info("Retention task created for %s by %s", account_id, claims.subject)
        return {
            "success": True,
            "task": task,
            "message": f"Retention task created for {account_id} with priority '{priority}'.",
        }

    @mcp.tool()
    async def flag_account_risk_tier(
        account_id: str,
        tier: str,
        justification: str = "",
        authorization: str | None = None,
    ) -> dict[str, Any]:
        """
        Update the risk tier classification for an account. Requires auth.

        Requires: Authorization: Bearer <token> with Retention.Write scope.
        tier: Critical | High | Elevated | Normal
        justification: reason for tier change (audit trail)

        In dev mode (no Entra configured), the auth check is bypassed automatically.
        """
        try:
            claims = await validate_bearer_token(authorization)
            require_write_scope(claims)
        except AuthenticationError as exc:
            return {"success": False, "error": str(exc)}

        result = await fabric.flag_account_risk_tier(account_id=account_id, tier=tier)
        if result.get("success"):
            result["updated_by"] = claims.subject
            result["justification"] = justification
            result["message"] = (
                f"Risk tier for {account_id} updated to '{tier}' by {claims.subject}."
            )
            logger.info(
                "Risk tier flagged: %s → %s by %s (reason: %s)",
                account_id, tier, claims.subject, justification,
            )
        return result
