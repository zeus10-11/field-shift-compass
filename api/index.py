"""Vercel Python serverless handler for Field Shift Compass API.

All /api/* routes return precomputed data from api/_data.py (generated at
build time by scripts/build.py). No framework, no Mangum, no writable disk —
just pure Python returning JSON dicts that Vercel serializes.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _data import (
    ADVICE,
    BACKTEST,
    CANDIDATES,
    CLIMATOLOGY,
    FEEDBACK,
    META,
    RISK_CALENDAR,
    SEASON_PLAN,
    SHIFTS,
    TIMELINE,
    TWIN,
)

GET_ROUTES = {
    "/api/meta": META,
    "/api/shifts": SHIFTS,
    "/api/twin": TWIN,
    "/api/advice": ADVICE,
    "/api/climatology": CLIMATOLOGY,
    "/api/candidates": CANDIDATES,
    "/api/risk-calendar": RISK_CALENDAR,
    "/api/backtest": BACKTEST,
    "/api/timeline": TIMELINE,
    "/api/season-plan": SEASON_PLAN,
    "/api/feedback": FEEDBACK,
    "/health": {"ok": True},
}


def _req_attr(request, name, default=None):
    """Read an attribute from a Vercel request object or dict."""
    if hasattr(request, name):
        return getattr(request, name)
    if isinstance(request, dict):
        return request.get(name, default)
    return default


def _respond(response, status, body):
    """Send a JSON response, trying common Vercel response APIs."""
    if hasattr(response, "json"):
        response.status = status
        response.json(body)
    elif hasattr(response, "send"):
        response.status = status
        response.headers = {"Content-Type": "application/json"}
        response.send(json.dumps(body))
    return body


def handler(request, response):
    method = _req_attr(request, "method", "GET").upper()
    path = _req_attr(request, "path", "/")

    # POST /api/feedback — acknowledge, do not persist (no writable disk)
    if method == "POST" and path == "/api/feedback":
        return _respond(
            response,
            200,
            {"status": "ok", "note": "Feedback accepted (not persisted on serverless free tier)."},
        )

    body = GET_ROUTES.get(path)
    if body is None:
        return _respond(response, 404, {"error": "not found"})

    return _respond(response, 200, body)
