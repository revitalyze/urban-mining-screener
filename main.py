"""
Main entry point for the Building Materials Estimator FastAPI application.

Configures middleware, database, and API routers for the backend service.
"""

import os
from fastapi import FastAPI, Request, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from itsdangerous import URLSafeSerializer, BadSignature
from pydantic import BaseModel

from app.routes.building_estimation import building_estimation_router
from app.routes import csv_router, estimation_router
from app.routes.archetype_options import router as archetype_options_router
from app.routes.archetype_compute import router as archetype_compute_router
from app.routes import refurbishment_options as refurbishment_options_router
from app.config import settings
from app.database import Base, engine

# Setup for serving frontend in container/production (Docker)
ENV = os.environ.get("ENV", "development")
if ENV in ("docker", "production"):
    STATIC_ROOT = "/app/static_root"
    INDEX_FILE = os.path.join(STATIC_ROOT, "index.html")
else:
    STATIC_ROOT = None
    INDEX_FILE = None

# Tag grouping and descriptions for the OpenAPI UI
tags_metadata = [
    {
        "name": "CSV Upload",
        "description": "Upload CSVs for Products, Components, Archetypes and relations. Drops and recreates tables, then ingests data in the correct order.",
    },
    {
        "name": "Material Estimation",
        "description": "Estimate materials for a target building referencing an archetype and target dimensions. Returns transparent factors and category breakdowns.",
    },
    {
        "name": "Building Estimation",
        "description": "Estimate building ground area, perimeter and height based on geospatial data for the given address.",
    },
    {
        "name": "archetype",
        "description": "Compute the appropriate archetype ID based on address (country), typology, construction type, and energy class.",
    },
]

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Building Materials Estimator API.\n\n"
        "This backend provides endpoints to:\n"
        "• Upload reference datasets (products, components, archetypes)\n"
        "• Compute building metrics for an address (area, perimeter, height)\n"
        "• Determine an archetype from address and parameters\n"
        "• Estimate material quantities for a target building\n\n"
    ),
    openapi_tags=tags_metadata,
    docs_url="/docs",
)

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

# ----------------------------
# Simple password auth (cookie)
# ----------------------------
COOKIE_NAME = "ums_auth"
_serializer = URLSafeSerializer(settings.AUTH_SECRET, salt="ums-cookie")


def _is_cookie_secure() -> bool:
    # Secure cookie only in production, per user approval
    return settings.ENV == "production"


class LoginBody(BaseModel):
    password: str


def verify_session(request: Request):
    """Dependency to protect API routes with a signed cookie."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = _serializer.loads(token)
        if payload.get("ok") is True:
            return True
    except BadSignature:
        pass
    raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/auth/login", include_in_schema=False)
def auth_login(body: LoginBody, response: Response):
    """Login by validating password and issuing signed session cookie."""
    if body.password != settings.APP_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = _serializer.dumps({"ok": True})
    # Use SameSite='none' when cookies are Secure (production/HTTPS) to allow cross-site contexts.
    # In non-secure environments (development/docker), fall back to 'lax' to avoid rejection.
    same_site = "none" if _is_cookie_secure() else "lax"
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite=same_site,
        secure=_is_cookie_secure(),
        path="/",
    )
    return {"success": True}


@app.post("/auth/logout", include_in_schema=False)
def auth_logout(response: Response):
    """Logout by clearing the session cookie."""
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"success": True}


@app.get("/auth/status", include_in_schema=False)
def auth_status(request: Request):
    """Public endpoint to check whether the current cookie is valid."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return {"authenticated": False}
    try:
        _serializer.loads(token)
        return {"authenticated": True}
    except BadSignature:
        return {"authenticated": False}


# Add CORS middleware to allow cross-origin requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
    ],
    allow_origin_regex=r"^https?://(localhost(:\d+)?|.*\.azurewebsites\.net)$",
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["set-cookie"],  # expose Set-Cookie for debugging if needed
)

# Include API routers for different functional areas
app.include_router(csv_router, prefix="/api", dependencies=[Depends(verify_session)])
app.include_router(
    estimation_router, prefix="/api", dependencies=[Depends(verify_session)]
)
app.include_router(
    building_estimation_router, prefix="/api", dependencies=[Depends(verify_session)]
)
app.include_router(archetype_options_router, dependencies=[Depends(verify_session)])
app.include_router(
    archetype_compute_router, prefix="/api", dependencies=[Depends(verify_session)]
)
app.include_router(
    refurbishment_options_router.router,
    dependencies=[Depends(verify_session)],
)


# Serve frontend static files at root, using StaticFiles with html=True for SPA support.
if STATIC_ROOT and os.path.exists(STATIC_ROOT):
    app.mount("/", StaticFiles(directory=STATIC_ROOT, html=True), name="frontend")

    # Expose health check at /health since "/" is handled by static mount
    @app.get("/health", include_in_schema=False)
    def health_check():
        return {"status": "ok"}
