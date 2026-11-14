"""Field Shift Compass - FastAPI backend.

Serves the analytics API and the static farmer/agronomist web app.
Run from project root:  uvicorn backend.main:app --reload
or:                     python backend/main.py
"""

import json
import os
import sys
from datetime import datetime

# Make backend/ importable no matter where Vercel/uicron loads this from
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import config
from analytics import advice_engine, risk, shift_detector, twin_matcher

app = FastAPI(title="Field Shift Compass", version="1.0")

STATE = {}
FEEDBACK_FILE = os.path.join(config.DATA_DIR, "feedback.json")


# ---------------------------------------------------------------------------
# Startup: load cached NASA data and run the three analytics layers once.
# ---------------------------------------------------------------------------
def _load_home_files(home):
    """Resolve cached daily + climatology for the configured home district."""
    daily_path = os.path.join(config.DATA_DIR, f"daily_{home['id']}.json")
    if not os.path.exists(daily_path):
        daily_path = os.path.join(config.DATA_DIR, "home_daily.json")
    clim_path = os.path.join(config.DATA_DIR, f"cand_{home['id']}.json")
    if not os.path.exists(clim_path):
        clim_path = os.path.join(config.DATA_DIR, "home_climatology.json")
    with open(daily_path) as f:
        home_daily = json.load(f)
    with open(clim_path) as f:
        payload = json.load(f)
    home_clim = payload if "parameters" in payload and payload.get("district") == home["id"] \
        else json.load(open(clim_path))
    # cand_* files nest parameters one level down
    home_clim_params = home_clim["parameters"] if "parameters" in home_clim else home_clim
    return home_daily, {"parameters": home_clim_params}


def load_state():
    home = config.HOME_DISTRICT
    deltas = config.FUTURE_DELTAS_2040

    home_daily, home_clim = _load_home_files(home)

    # Layer 1: Shift Detector
    shifts = shift_detector.detect(home_daily["parameters"], home)

    # Seasonal risk profile + farmer-memory back-test (same daily record)
    cal = risk.risk_calendar(home_daily["parameters"])
    bt = risk.backtest(shifts)

    # Layer 2: Climate Twin Matcher
    candidates = []
    for c in config.TWIN_CANDIDATES:
        path = os.path.join(config.DATA_DIR, f"cand_{c['id']}.json")
        if not os.path.exists(path):
            continue
        with open(path) as f:
            payload = json.load(f)
        feats = twin_matcher.features_from_climatology(payload["parameters"])
        candidates.append({**c, "features": feats})

    home_feats_now = twin_matcher.features_from_climatology(home_clim["parameters"])
    future_clim = twin_matcher.scale_features(deltas, home_clim["parameters"])
    home_feats_future = twin_matcher.features_from_climatology(
        future_clim,
        temp_add=0.0,          # deltas already applied in scale_features
        rh_add=0.0,
    )
    matches, _ = twin_matcher.match(home_feats_future, candidates, top_k=3)

    # Layer 3: Shift Advisor
    advice = advice_engine.build_advice(shifts, matches, deltas, home)

    # Climate Path: which region is your twin along the 2026 -> 2040 path?
    # Run across low / medium / high delta ranges so the twin match is not
    # true by construction under a single linear scenario.
    path_steps = [("2026", 0.0), ("2029", 0.25), ("2032", 0.5),
                  ("2036", 0.75), ("2040", 1.0)]
    scenario_multipliers = {
        "low":    {"temp_add_c": deltas["temp_add_c"] * 0.5,
                   "rain_mult_annual": 1 + (deltas["rain_mult_annual"] - 1) * 0.5,
                   "rain_mult_monsoon": 1 + (deltas["rain_mult_monsoon"] - 1) * 0.5,
                   "onset_shift_days": deltas["onset_shift_days"] * 0.5,
                   "rh_add_pct": deltas["rh_add_pct"] * 0.5},
        "medium": {"temp_add_c": deltas["temp_add_c"],
                   "rain_mult_annual": deltas["rain_mult_annual"],
                   "rain_mult_monsoon": deltas["rain_mult_monsoon"],
                   "onset_shift_days": deltas["onset_shift_days"],
                   "rh_add_pct": deltas["rh_add_pct"]},
        "high":   {"temp_add_c": deltas["temp_add_c"] * 1.5,
                   "rain_mult_annual": 1 + (deltas["rain_mult_annual"] - 1) * 1.5,
                   "rain_mult_monsoon": 1 + (deltas["rain_mult_monsoon"] - 1) * 1.5,
                   "onset_shift_days": deltas["onset_shift_days"] * 1.5,
                   "rh_add_pct": deltas["rh_add_pct"] * 1.5},
    }
    timeline = []
    for year_label, frac in path_steps:
        step_scenarios = []
        for scen_name, scen in scenario_multipliers.items():
            fc_i = twin_matcher.scale_features(scen, home_clim["parameters"], frac=frac)
            feats_i = twin_matcher.features_from_climatology(fc_i)
            ms_i, _ = twin_matcher.match(feats_i, candidates, top_k=2)
            step_scenarios.append({
                "scenario": scen_name,
                "top": ms_i[0],
                "runner": ms_i[1],
                "temp_add": round(scen["temp_add_c"] * frac, 2),
            })
        timeline.append({"year": year_label, "frac": frac,
                         "scenarios": step_scenarios})

    STATE.update({
        "home": home,
        "deltas": deltas,
        "home_daily": home_daily,
        "home_clim": home_clim,
        "future_clim": future_clim,
        "candidates": candidates,
        "home_feats_now": home_feats_now,
        "home_feats_future": home_feats_future,
        "shifts": shifts,
        "matches": matches,
        "advice": advice,
        "risk_calendar": cal,
        "backtest": bt,
        "timeline": timeline,
        "computed_at": datetime.now().isoformat(timespec="seconds"),
    })


@app.on_event("startup")
def startup():
    load_state()
    _ensure_feedback()


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.get("/api/meta")
def meta():
    return {
        "district": STATE["home"],
        "deltas": STATE["deltas"],
        "computed_at": STATE["computed_at"],
        "data_source": STATE["home_daily"]["source"],
        "record_years": STATE["shifts"]["years"],
        "data_note": "All analytics are computed offline from cached NASA POWER "
        "(MERRA-2 reanalysis) data; no live API needed "
                     "during the demo.",
    }


@app.get("/api/shifts")
def shifts():
    return STATE["shifts"]


@app.get("/api/twin")
def twin():
    top = STATE["matches"][0] if STATE["matches"] else None
    return {
        "home_now": STATE["home_feats_now"],
        "home_future": STATE["home_feats_future"],
        "deltas": STATE["deltas"],
        "matches": STATE["matches"],
        "candidates_considered": len(STATE["candidates"]),
        "practice": advice_engine.TWIN_PRACTICE.get(top["id"],
                                                    advice_engine.DEFAULT_PRACTICE)
                   if top else None,
    }


@app.get("/api/advice")
def advice():
    return {
        "cards": STATE["advice"],
        "region_note": STATE["home"].get("language"),
    }


@app.get("/api/climatology")
def climatology():
    """Monthly curves for the comparison chart: home observed vs home future
    vs current climate of the top twin."""
    months = twin_matcher.MONTH_ORDER
    top = STATE["matches"][0]
    twin_path = os.path.join(config.DATA_DIR, f"cand_{top['id']}.json")
    with open(twin_path) as f:
        twin_clim = json.load(f)["parameters"]

    days = twin_matcher.MONTH_DAYS

    def rain_monthly(params):
        """POWER climatology rain is mm/day -> show honest monthly totals (mm)."""
        return [round(float(params["PRECTOTCORR"][m]) * d, 0)
                for m, d in zip(months, days)]

    def tmean(params):
        """Use monthly mean T2M (the T2M_MAX climatology product carries a
        ~+7 C bias versus POWER's own daily record)."""
        return [round(float(params["T2M"][m]), 1) for m in months]

    return {
        "months": months,
        "home_observed_rain": rain_monthly(STATE["home_clim"]["parameters"]),
        "home_future_rain": rain_monthly(STATE["future_clim"]),
        "twin_rain": rain_monthly(twin_clim),
        "home_observed_tmax": tmean(STATE["home_clim"]["parameters"]),
        "home_future_tmax": tmean(STATE["future_clim"]),
        "twin_tmax": tmean(twin_clim),
        "twin_name": top["name"],
    }


@app.get("/api/series/year/{year}")
def year_series(year: int):
    """Daily monsoon-season rainfall + max temp for one year (for charts)."""
    params = STATE["home_daily"]["parameters"]
    rain = shift_detector._parse_daily(params["PRECTOTCORR"])
    tmax = shift_detector._parse_daily(params["T2M_MAX"])
    out_rain = [{"date": d.isoformat(), "value": round(v, 2)}
                for d, v in rain if d.year == year]
    out_tmax = [{"date": d.isoformat(), "value": round(v, 1)}
                for d, v in tmax if d.year == year]
    if not out_rain:
        raise HTTPException(404, f"No data for {year}")
    return {"year": year, "rain": out_rain, "tmax": out_tmax}


@app.get("/api/onsets")
def onsets():
    return STATE["shifts"]["onset"]


@app.get("/api/candidates")
def candidates_ep():
    """All candidate regions with features, for the Twin Explorer."""
    return [
        {"id": c["id"], "name": c["name"], "lat": c["lat"], "lon": c["lon"],
         "features": c["features"]}
        for c in STATE["candidates"]
    ]


@app.get("/api/risk-calendar")
def risk_calendar_ep():
    return {
        "calendar": STATE["risk_calendar"],
        "district": STATE["home"]["name"],
        "record_years": STATE["shifts"]["years"],
    }


@app.get("/api/backtest")
def backtest_ep():
    return STATE["backtest"]


@app.get("/api/timeline")
def timeline_ep():
    return {
        "deltas": STATE["deltas"],
        "steps": STATE["timeline"],
    }


class SeasonPlanRequest(BaseModel):
    name: str = "Farmer"


@app.get("/api/season-plan")
@app.post("/api/season-plan")
def season_plan(req: SeasonPlanRequest | None = None):
    """A printable one-page season plan the farmer can take home."""
    req = req or SeasonPlanRequest()
    s = STATE["shifts"]
    t = s["trends"]
    onset = s["onset"]
    last_year = max(onset, key=lambda y: int(y))
    top = STATE["matches"][0]
    cards = STATE["advice"]
    return {
        "farmer": req.name,
        "district": STATE["home"]["name"],
        "crop": STATE["home"]["crop"],
        "season": f"{max(int(y) for y in onset) + 1} kharif season",
        "headline_shift": {
            "text": f"Sowing window shifted about "
                    f"{abs(round(t['onset']['slope_per_year'] * (t['onset']['last_year'] - t['onset']['first_year'])))} days "
                    f"since {t['onset']['first_year']}.",
            "last_onset": onset[last_year],
            "based_on_year": last_year,
        },
        "sowing_advice": cards[0]["recommendation"] if cards else "",
        "twin": {"name": top["name"], "note":
                 advice_engine.TWIN_PRACTICE.get(top["id"],
                                                 advice_engine.DEFAULT_PRACTICE)},
        "watch_for": _watch_for(),
        "data_sources": ["NASA POWER (daily, MERRA-2 reanalysis)",
                         "NEX-GDDP-CMIP6 future deltas (approx.)"],
    }


def _watch_for():
    """Actionable watch-outs straight from the 26-year record."""
    t = STATE["shifts"]["trends"]
    risk = {m["month"]: m for m in STATE["risk_calendar"]}
    pct = lambda month, key: round(risk[month][key] * 100)
    return [
        f"Late onset: {t['onset']['change_per_decade']:+.1f} days/decade — "
        f"sow on soil moisture and keep a 25–30 day nursery backup.",
        f"June: an 8+ day dry spell in {pct('June', 'p_dryspell8')}% of years — "
        f"hold water and mulch after sowing.",
        f"July: a 50 mm+ burst day in {pct('July', 'p_heavy')}% of years — "
        f"clear field drains before the first heavy week.",
        f"October: effectively dry in {pct('October', 'p_dryspell8')}% of years — "
        f"plan harvest moisture and storage early.",
    ]


# ---------------------------------------------------------------------------
# Farmer feedback loop (trust layer). Persisted to disk so the agronomist
# dashboard survives restarts.
# ---------------------------------------------------------------------------
class Feedback(BaseModel):
    advice_type: str
    farmer_note: str = ""
    decision: str                     # follow | modify | reject | question
    source: str = "farmer"            # farmer | agronomist
    created_at: str | None = None


def _ensure_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        seed = [
            {"id": 1, "advice_type": "sowing_date", "decision": "follow",
             "farmer_note": "Waited 8 days more this year - rain came on time. Will do again next year.",
             "source": "farmer", "created_at": "2026-06-12T09:30:00"},
            {"id": 2, "advice_type": "sowing_date", "decision": "approved",
             "farmer_note": "Matches district crop-calendar trial results. Approving for WhatsApp broadcast.",
             "source": "agronomist", "created_at": "2026-06-13T18:05:00"},
        ]
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(seed, f, indent=2)


@app.get("/api/feedback")
def list_feedback():
    with open(FEEDBACK_FILE) as f:
        return json.load(f)


@app.post("/api/feedback")
def add_feedback(fb: Feedback):
    with open(FEEDBACK_FILE) as f:
        items = json.load(f)
    entry = {"id": (max((i["id"] for i in items), default=0) + 1),
             "advice_type": fb.advice_type, "decision": fb.decision,
             "farmer_note": fb.farmer_note, "source": fb.source,
             "created_at": fb.created_at or datetime.now().isoformat(timespec="seconds")}
    items.append(entry)
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(items, f, indent=2)
    return entry


# ---------------------------------------------------------------------------
# Static web app
# ---------------------------------------------------------------------------
app.mount("/web", StaticFiles(directory=config.WEB_DIR), name="web")


def boot_payload():
    """Everything the farmer app needs, injected into the page at serve time.

    This removes the startup fetch race entirely: the dashboard paints with
    data on the first frame, even on a slow/absent connection.
    """
    top = STATE["matches"][0] if STATE["matches"] else None
    payload = {
        "meta": {
            "district": STATE["home"],
            "deltas": STATE["deltas"],
            "computed_at": STATE["computed_at"],
            "data_source": STATE["home_daily"]["source"],
            "record_years": STATE["shifts"]["years"],
        },
        "shifts": STATE["shifts"],
        "twin": {
            "home_now": STATE["home_feats_now"],
            "home_future": STATE["home_feats_future"],
            "deltas": STATE["deltas"],
            "matches": STATE["matches"],
            "candidates_considered": len(STATE["candidates"]),
            "practice": advice_engine.TWIN_PRACTICE.get(
                top["id"], advice_engine.DEFAULT_PRACTICE) if top else None,
        },
        "advice": {"cards": STATE["advice"]},
        "risk": {"calendar": STATE["risk_calendar"]},
        "backtest": STATE["backtest"],
        "timeline": {"steps": STATE["timeline"]},
        "candidates": [
            {"id": c["id"], "name": c["name"], "lat": c["lat"], "lon": c["lon"],
             "features": c["features"]} for c in STATE["candidates"]
        ],
        "climatology": climatology(),
    }
    # Flatten timeline steps so renderTimeline() in app.js can read
    # s.top / s.runner / s.temp_add directly on each step (works for both
    # local dev via python backend/main.py and Vercel via scripts/build.py).
    for step in payload["timeline"]["steps"]:
        medium = step["scenarios"][1]  # medium scenario
        step["top"] = medium["top"]
        step["runner"] = medium["runner"]
        step["temp_add"] = medium["temp_add"]
    return payload


@app.get("/")
def index():
    html = open(os.path.join(config.WEB_DIR, "index.html")).read()
    payload = boot_payload()
    # Inline the (already simplified) India outline so the map paints on the
    # first frame with no extra round-trip.
    geo_path = os.path.join(config.WEB_DIR, "assets", "india_outline.geojson")
    if os.path.exists(geo_path):
        payload["geojson"] = json.load(open(geo_path))
    payload = json.dumps(payload).replace("</", "<\\/")
    html = html.replace(
        '<script src="/web/js/app.js"></script>',
        f"<script>window.__BOOT__={payload};</script>\n"
        '<script src="/web/js/app.js"></script>')
    return HTMLResponse(html)


@app.get("/agronomist")
def agronomist():
    html = open(os.path.join(config.WEB_DIR, "agronomist.html")).read()
    payload = json.dumps({
        "meta": {"district": STATE["home"]},
        "advice": {"cards": STATE["advice"]},
        "feedback": list_feedback(),
        "backtest": STATE["backtest"],
        "risk": {"calendar": STATE["risk_calendar"]},
    }).replace("</", "<\\/")
    html = html.replace(
        "<script>",
        f"<script>window.__AGRO_BOOT__={payload};</script>\n<script>", 1)
    return HTMLResponse(html)


@app.get("/health")
def health():
    return JSONResponse({"ok": True})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
