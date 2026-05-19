"""Domain exception base classes. Layer-agnostic — no FastAPI imports.

Translated to HTTP responses by an exception handler registered in main.py.
"""


class DomainError(Exception):
    """Base for all domain-level errors."""

    code: str = "domain_error"
    http_status: int = 400


class NotFoundError(DomainError):
    code = "not_found"
    http_status = 404


class ConflictError(DomainError):
    code = "conflict"
    http_status = 409


class AuthError(DomainError):
    code = "unauthorized"
    http_status = 401


class ForbiddenError(DomainError):
    code = "forbidden"
    http_status = 403


class ValidationError(DomainError):
    code = "validation_error"
    http_status = 422
