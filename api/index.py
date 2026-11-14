"""Vercel Python serverless handler for Field Shift Compass API.

All /api/* routes are rewritten here by vercel.json. Data is precomputed at
build time (scripts/build.py) and embedded in api/_data.py, so each invocation
just returns JSON — no startup loading, no writable disk, no long-running
process.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mangum import Mangum

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

app = FastAPI(title="Field Shift Compass API", version="1.0")


@app.get("/api/meta")
def meta():
    return META


@app.get("/api/shifts")
def shifts():
    return SHIFTS


@app.get("/api/twin")
def twin():
    return TWIN


@app.get("/api/advice")
def advice():
    return ADVICE


@app.get("/api/climatology")
def climatology():
    return CLIMATOLOGY


@app.get("/api/candidates")
def candidates():
    return CANDIDATES


@app.get("/api/risk-calendar")
def risk_calendar():
    return RISK_CALENDAR


@app.get("/api/backtest")
def backtest():
    return BACKTEST


@app.get("/api/timeline")
def timeline():
    return TIMELINE


@app.get("/api/season-plan")
@app.post("/api/season-plan")
async def season_plan(request: Request):
    return SEASON_PLAN


@app.get("/api/feedback")
def list_feedback():
    return FEEDBACK


@app.post("/api/feedback")
async def add_feedback(request: Request):
    # No writable disk on serverless — acknowledge but do not persist.
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "note": "Feedback accepted (not persisted on serverless free tier).",
        },
    )


@app.get("/health")
def health():
    return {"ok": True}


handler = Mangum(app)
