"""FastAPI composition root.

Wires:
- Cross-cutting middleware (request-id, CORS, rate limit)
- DB lifespan
- Domain-error → HTTP translator
- Module routers
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIDMiddleware
from app.core.rate_limit import limiter
from app.db import close_db, init_db, ping_db
from app.modules.analytics.interfaces.http.router import router as analytics_router
from app.modules.auth.interfaces.http.router import router as auth_router
from app.modules.budgets.interfaces.http.router import router as budgets_router
from app.modules.categories.interfaces.http.router import router as categories_router
from app.modules.chat.interfaces.http.router import router as chat_router
from app.modules.transactions.interfaces.http.router import router as transactions_router

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", env=settings.env)
    await init_db()
    yield
    await close_db()
    logger.info("shutdown")


app = FastAPI(
    title="FinTrack API",
    version="0.1.0",
    description="AI-powered Finance & Expense Tracking Platform",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


# ---- Exception handlers ----------------------------------------------------
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=exc.http_status,
        content={"detail": str(exc) or exc.code, "code": exc.code},
    )


# ---- Meta endpoints --------------------------------------------------------
@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/ready", tags=["meta"])
async def ready() -> dict:
    db_ok = await ping_db()
    settings = get_settings()
    openai_configured = bool(settings.openai_api_key)
    return {
        "status": "ok" if db_ok else "degraded",
        "dependencies": {
            "database": db_ok,
            "openai": openai_configured,
        },
    }


# ---- Module routers --------------------------------------------------------
app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(transactions_router)
app.include_router(budgets_router)
app.include_router(analytics_router)
app.include_router(chat_router)
