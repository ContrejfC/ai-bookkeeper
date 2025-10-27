"""
Root-level main.py for Render/Cloud Run deployment.

This file serves as the entry point for the FastAPI application when deployed
to cloud platforms (Google Cloud Run, Render, etc.).

Purpose:
--------
- Imports the FastAPI app instance from the main application module
- Exposes the app for ASGI servers (Uvicorn, Gunicorn) to run
- Keeps the root directory clean while maintaining separation of concerns

Deployment Context:
------------------
The actual FastAPI application is defined in app/api/main.py. This file simply
re-exports it to provide a consistent entry point for cloud platforms.

Usage:
------
When running the server:
    uvicorn main:app --host 0.0.0.0 --port 8000

The ASGI server looks for the 'app' variable in this main.py file.
"""
from app.api.main import app

__all__ = ["app"]

