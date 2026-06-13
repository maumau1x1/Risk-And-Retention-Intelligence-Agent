"""Microsoft Entra ID token validation for write operations."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from risk_agent_mcp.config import get_settings

logger = logging.getLogger(__name__)

# Simple in-process JWKS cache (avoid fetching on every request)
_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL_SECONDS = 3600  # re-fetch JWKS keys at most once per hour


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    name: str | None
    roles: tuple[str, ...] = field(default_factory=tuple)
    scopes: tuple[str, ...] = field(default_factory=tuple)


class AuthenticationError(Exception):
    """Raised when bearer token is missing or invalid."""


async def validate_bearer_token(authorization: str | None) -> TokenClaims:
    """
    Validate an OAuth 2.1 bearer token issued by Microsoft Entra ID.

    Dev mode (USE_MOCK_FABRIC_DATA=true or Entra not configured):
      → Accepts any token string; returns a synthetic 'dev-user' claim set.

    Production mode (AZURE_TENANT_ID + AZURE_CLIENT_ID configured):
      → Validates JWT signature via Entra OIDC JWKS endpoint (RS256).
      → Checks audience, issuer, and expiry via PyJWT.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1].strip()
    settings = get_settings()

    # Dev bypass — safe for hackathon demo, never use in production
    if not settings.oauth_configured:
        logger.warning(
            "OAuth not fully configured — accepting token in dev-only mode. "
            "Set AZURE_TENANT_ID + AZURE_CLIENT_ID to enable production validation."
        )
        return TokenClaims(
            subject="dev-user",
            name="Developer (Dev Mode)",
            roles=("Retention.Write",),
            scopes=("Retention.Write",),
        )

    # Production: validate via Entra OIDC JWKS
    return await _validate_jwt_production(token, settings)


async def _validate_jwt_production(token: str, settings: Any) -> TokenClaims:
    """Full RS256 JWT validation against Entra JWKS endpoint."""
    try:
        import jwt
        from jwt import PyJWKClient
    except ImportError:
        logger.error("PyJWT not installed — cannot validate token in production mode")
        raise AuthenticationError("JWT validation library not available")

    tenant = settings.azure_tenant_id
    audience = settings.azure_api_audience or settings.azure_client_id
    jwks_url = f"https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys"
    issuer = f"https://login.microsoftonline.com/{tenant}/v2.0"

    try:
        jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidAudienceError:
        raise AuthenticationError("Token audience mismatch")
    except jwt.InvalidIssuerError:
        raise AuthenticationError("Token issuer mismatch")
    except jwt.PyJWTError as exc:
        raise AuthenticationError(f"Token validation failed: {exc}") from exc

    roles_raw = payload.get("roles") or []
    scp_raw = (payload.get("scp") or "").split()

    return TokenClaims(
        subject=payload.get("sub", "unknown"),
        name=payload.get("name"),
        roles=tuple(roles_raw),
        scopes=tuple(scp_raw),
    )


def require_write_scope(claims: TokenClaims) -> None:
    """Enforce Retention.Write scope/role for mutating operations."""
    write_scope = "Retention.Write"
    if write_scope in claims.scopes or write_scope in claims.roles:
        return
    # Dev bypass: synthetic dev-user always has write access
    if claims.subject == "dev-user":
        return
    raise AuthenticationError(
        f"Insufficient scope for write operation ({write_scope} required). "
        f"Current scopes: {', '.join(claims.scopes) or 'none'}"
    )
