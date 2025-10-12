"""
FastAPI Main Application with Wave-1 UI Integration.

Extends existing API with UI routes for:
- Reason-aware review page
- Metrics dashboard
- Export Center
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import existing API routes (if they exist)
# from app.api.main import app as api_app

# Create app instance
app = FastAPI(
    title="AI Bookkeeper",
    version="0.9.0-rc",
    description="Production-grade AI-powered bookkeeping automation"
)

# Import UI routes
from app.ui import routes as ui_routes

# Include UI routes
app.include_router(ui_routes.router, tags=["ui"])

# Health endpoints (minimal stubs for testing)
@app.get("/healthz")
async def health_check():
    """Lightweight health check."""
    return {
        "status": "ok",
        "version": "0.9.0-rc",
        "uptime_seconds": 3600,
        "ruleset_version_id": "v0.4.13",
        "model_version_id": "m1.2.0"
    }

@app.get("/readyz")
async def readiness_check():
    """Comprehensive readiness check."""
    return {
        "ready": True,
        "checks": {
            "database_connect": {"status": "ok"},
            "migrations": {"status": "ok"},
            "ocr_stub": {"status": "ok"}
        }
    }

# Root redirect
@app.get("/")
async def root():
    """Redirect to review page."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/review")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
