"""
Future-facing auth / tenancy hooks.

MVP has no authentication. These stubs document where Auth, RBAC,
workspace scoping, and audit logging will plug in without refactoring
repositories or route signatures.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status


@dataclass(frozen=True)
class Principal:
    """Authenticated actor — replace with JWT/session claims later."""

    user_id: str
    email: str | None = None
    roles: tuple[str, ...] = ()
    workspace_id: str | None = None


async def get_current_principal() -> Principal | None:
    """
    MVP: anonymous access (returns None).

    Future: parse Bearer token → Principal. Routes that require auth will
    switch to `require_principal` without changing service constructors.
    """
    return None


async def require_principal(
    principal: Principal | None = Depends(get_current_principal),
) -> Principal:
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return principal


def require_roles(*roles: str):
    """Factory for RBAC checks (unused in MVP)."""

    async def _checker(
        principal: Principal = Depends(require_principal),
    ) -> Principal:
        if roles and not any(r in principal.roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return principal

    return _checker
