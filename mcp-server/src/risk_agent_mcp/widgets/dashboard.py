"""Interactive MCP App widgets — Adaptive Card v1.6 JSON for Copilot chat."""

from __future__ import annotations

import json
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _usd(value: float) -> str:
    return f"${value:,.0f}"


def wrap_as_adaptive_card(card: dict[str, Any]) -> str:
    """Serialize an Adaptive Card dict to the MCP text content string."""
    return json.dumps(card, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Risk Dashboard Widget
# ---------------------------------------------------------------------------

def build_risk_dashboard_widget(kpis: dict[str, Any]) -> str:
    """Portfolio risk KPI card with key metrics in a FactSet grid."""
    segment = kpis.get("segment", "all").upper()
    period = kpis.get("period", "QTD")

    churn_rate = _pct(kpis.get("churn_rate", 0))
    retention_score = f"{kpis.get('retention_score', 0):.1f} / 100"
    npl_ratio = _pct(kpis.get("npl_ratio", 0))
    loss_recovery = _pct(kpis.get("loss_recovery_rate", 0))
    high_risk = str(kpis.get("high_risk_accounts", 0))
    source_tag = "🟡 Mock Data" if kpis.get("source") == "mock_semantic_model" else "🟢 Fabric IQ Live"

    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "bleed": True,
                "items": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "📊 Portfolio Risk Dashboard",
                                        "weight": "Bolder",
                                        "size": "Large",
                                        "color": "Light",
                                    }
                                ],
                            },
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": source_tag,
                                        "size": "Small",
                                        "color": "Light",
                                        "horizontalAlignment": "Right",
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "type": "TextBlock",
                        "text": f"Segment: **{segment}** · Period: **{period}**",
                        "color": "Light",
                        "size": "Small",
                        "spacing": "None",
                    },
                ],
            },
            {
                "type": "FactSet",
                "spacing": "Medium",
                "facts": [
                    {"title": "🔴 Churn Rate", "value": churn_rate},
                    {"title": "🟢 Retention Score", "value": retention_score},
                    {"title": "🟠 NPL Ratio", "value": npl_ratio},
                    {"title": "💰 Loss Recovery Rate", "value": loss_recovery},
                    {"title": "⚠️ High-Risk Accounts", "value": high_risk},
                ],
            },
            {
                "type": "TextBlock",
                "text": "Powered by Microsoft Fabric IQ · Risk & Retention Intelligence",
                "size": "Small",
                "color": "Accent",
                "horizontalAlignment": "Right",
                "spacing": "Small",
            },
        ],
    }
    return wrap_as_adaptive_card(card)


# ---------------------------------------------------------------------------
# Churn Drivers Widget
# ---------------------------------------------------------------------------

def build_churn_drivers_widget(drivers: list[dict[str, Any]], segment: str) -> str:
    """Bar-style churn driver card with impact rankings."""
    rows = []
    for i, d in enumerate(drivers, 1):
        impact_pct = int(d.get("impact_score", 0) * 100)
        bar = "█" * (impact_pct // 5) + "░" * (20 - impact_pct // 5)
        rows.append(
            {
                "type": "ColumnSet",
                "spacing": "Small",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": f"**#{i}**",
                                "weight": "Bolder",
                                "color": "Warning" if i <= 2 else "Default",
                            }
                        ],
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": d.get("driver", "Unknown"),
                                "weight": "Bolder",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"`{bar}` {impact_pct}% · {d.get('affected_accounts', 0)} accounts",
                                "size": "Small",
                                "color": "Accent",
                                "spacing": "None",
                            },
                        ],
                    },
                ],
            }
        )

    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
        "body": [
            {
                "type": "Container",
                "style": "attention",
                "bleed": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "🔍 Top Churn Drivers",
                        "weight": "Bolder",
                        "size": "Large",
                        "color": "Light",
                    },
                    {
                        "type": "TextBlock",
                        "text": f"Segment: **{segment.upper()}** · Ranked by Fabric IQ impact score",
                        "color": "Light",
                        "size": "Small",
                        "spacing": "None",
                    },
                ],
            },
            *rows,
            {
                "type": "TextBlock",
                "text": "Source: Fabric IQ · ChurnDriverImpact measure",
                "size": "Small",
                "color": "Accent",
                "horizontalAlignment": "Right",
                "spacing": "Medium",
            },
        ],
    }
    return wrap_as_adaptive_card(card)


# ---------------------------------------------------------------------------
# At-Risk Accounts Table Widget
# ---------------------------------------------------------------------------

def build_at_risk_table_widget(accounts: list[dict[str, Any]]) -> str:
    """At-risk account table with risk score heat indicator."""

    def risk_color(score: int) -> str:
        if score >= 90:
            return "Attention"
        if score >= 80:
            return "Warning"
        return "Default"

    rows = []
    for a in accounts:
        score = a.get("risk_score", 0)
        churn_prob = _pct(a.get("churn_prob", 0))
        region = a.get("region", "—")
        tenure = a.get("contract_tenure_months", "—")

        rows.append(
            {
                "type": "ColumnSet",
                "spacing": "Small",
                "separator": True,
                "columns": [
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": f"**{a.get('name', a.get('account_id', ''))}**",
                                "weight": "Bolder",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"{a.get('account_id', '')} · {region} · {tenure}mo tenure",
                                "size": "Small",
                                "color": "Accent",
                                "spacing": "None",
                            },
                        ],
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": f"**{score}**",
                                "color": risk_color(score),
                                "weight": "Bolder",
                                "horizontalAlignment": "Right",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Churn: {churn_prob}",
                                "size": "Small",
                                "color": risk_color(score),
                                "horizontalAlignment": "Right",
                                "spacing": "None",
                            },
                        ],
                    },
                ],
            }
        )

    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
        "body": [
            {
                "type": "Container",
                "style": "warning",
                "bleed": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "⚠️ At-Risk Accounts",
                        "weight": "Bolder",
                        "size": "Large",
                        "color": "Light",
                    },
                    {
                        "type": "TextBlock",
                        "text": f"{len(accounts)} accounts requiring retention attention",
                        "color": "Light",
                        "size": "Small",
                        "spacing": "None",
                    },
                ],
            },
            {
                "type": "ColumnSet",
                "spacing": "Medium",
                "columns": [
                    {"type": "Column", "width": "stretch", "items": [{"type": "TextBlock", "text": "**ACCOUNT**", "size": "Small", "weight": "Bolder"}]},
                    {"type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": "**RISK / CHURN**", "size": "Small", "weight": "Bolder", "horizontalAlignment": "Right"}]},
                ],
            },
            *rows,
            {
                "type": "TextBlock",
                "text": "Source: Fabric IQ · RiskScore measure",
                "size": "Small",
                "color": "Accent",
                "horizontalAlignment": "Right",
                "spacing": "Medium",
            },
        ],
    }
    return wrap_as_adaptive_card(card)


# ---------------------------------------------------------------------------
# Retention Trend Widget (new)
# ---------------------------------------------------------------------------

def build_retention_trend_widget(trend: dict[str, Any]) -> str:
    """12-month retention & churn trend table card."""
    months = trend.get("months", [])
    region = trend.get("region", "all").upper()
    period = trend.get("period", "L12M")

    table_rows = []
    for m in months:
        churn = _pct(m.get("churn_rate", 0))
        recovery = _pct(m.get("loss_recovery_rate", 0))
        ret = f"{m.get('retention_score', 0):.0f}"
        trend_icon = "🔴" if m.get("churn_rate", 0) > 0.13 else "🟢"
        table_rows.append(
            {
                "type": "ColumnSet",
                "spacing": "ExtraSmall",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [{"type": "TextBlock", "text": trend_icon, "spacing": "None"}],
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [{"type": "TextBlock", "text": f"**{m.get('month', '')}**", "size": "Small", "spacing": "None"}],
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [{"type": "TextBlock", "text": churn, "size": "Small", "spacing": "None", "horizontalAlignment": "Right"}],
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [{"type": "TextBlock", "text": recovery, "size": "Small", "spacing": "None", "horizontalAlignment": "Right"}],
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [{"type": "TextBlock", "text": ret, "size": "Small", "spacing": "None", "horizontalAlignment": "Right"}],
                    },
                ],
            }
        )

    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.6",
        "body": [
            {
                "type": "Container",
                "style": "good",
                "bleed": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "📈 Retention & Churn Trend",
                        "weight": "Bolder",
                        "size": "Large",
                        "color": "Light",
                    },
                    {
                        "type": "TextBlock",
                        "text": f"Region: **{region}** · Period: **{period}**",
                        "color": "Light",
                        "size": "Small",
                        "spacing": "None",
                    },
                ],
            },
            {
                "type": "ColumnSet",
                "spacing": "Medium",
                "columns": [
                    {"type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": " ", "size": "Small"}]},
                    {"type": "Column", "width": "stretch", "items": [{"type": "TextBlock", "text": "**MONTH**", "size": "Small", "weight": "Bolder"}]},
                    {"type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": "**CHURN**", "size": "Small", "weight": "Bolder", "horizontalAlignment": "Right"}]},
                    {"type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": "**RECOVERY**", "size": "Small", "weight": "Bolder", "horizontalAlignment": "Right"}]},
                    {"type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": "**RET.**", "size": "Small", "weight": "Bolder", "horizontalAlignment": "Right"}]},
                ],
            },
            *table_rows,
            {
                "type": "TextBlock",
                "text": "🔴 >13% churn  🟢 ≤13% churn · Source: Fabric IQ · RetentionTrend measure",
                "size": "Small",
                "color": "Accent",
                "spacing": "Medium",
            },
        ],
    }
    return wrap_as_adaptive_card(card)
