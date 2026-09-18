"""Concurrency-safe correlation between MCP middleware and tool executors."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from .models import AuditExecutionContext

_CURRENT_AUDIT_CONTEXT: ContextVar[AuditExecutionContext | None] = ContextVar(
    "stata_mcp_audit_context",
    default=None,
)


def current_audit_context() -> AuditExecutionContext | None:
    """Return the audit context bound to the current async or thread context."""
    return _CURRENT_AUDIT_CONTEXT.get()


@contextmanager
def bind_audit_context(context: AuditExecutionContext) -> Iterator[None]:
    """Bind one audit context and restore the prior value afterward."""
    token = _CURRENT_AUDIT_CONTEXT.set(context)
    try:
        yield
    finally:
        _CURRENT_AUDIT_CONTEXT.reset(token)
