"""Download and cache NASA POWER data so the demo never depends on live APIs.

Run:  python -m scripts.fetch_data        (from the project root)
or:   python data_fetch.py               (from backend/)
"""

import json
import os
import time

import requests

import config

CACHE_DIR = config.DATA_DIR


def _get(url, params, retries=4, sleep=3):
    """GET with retries; POWER throttles occasionally."""
    last = None
    for _ in range(retries):
        try:
            r = requests.get(url, params=params, timeout=90,
                             headers={"User-Agent": config.USER_AGENT})
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(sleep)
    raise RuntimeError(f"NASA POWER request failed: {url} ({last})")


def daily_url():
    return f"{config.POWER_BASE}/daily/point"


def climatology_url():
    return f"{config.POWER_BASE}/climatology/point"


def fetch_daily(lat, lon, year_start, year_end, params):
    """Daily time series for one point, full years at a time."""
    out = {}
    for y in range(year_start, year_end + 1):
        js = _get(daily_url(), {
            "parameters": ",".join(params),
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": f"{y}0101",
            "end": f"{y}1231",
            "format": "JSON",
        })
        prop = js.get("properties", {}).get("parameter", {})
        for p, series in prop.items():
            out.setdefault(p, {}).update(series)
        time.sleep(0.4)
    return out


def fetch_climatology(lat, lon, params):
    """Monthly climatology (leap-year day basis) for one point."""
    js = _get(climatology_url(), {
        "parameters": ",".join(params),
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    })
    return js.get("properties", {}).get("parameter", {})


def save(name, payload):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, name)
    with open(path, "w") as f:
        json.dump(payload, f)
    print(f"saved {path}")


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    home = config.HOME_DISTRICT
    y0, y1 = config.DATA_YEARS

    # 1. Home district daily series (the Shift Detector's core input)
    daily = fetch_daily(home["lat"], home["lon"], y0, y1, config.DAILY_PARAMS)
    save("home_daily.json", {
        "district": home["id"],
        "lat": home["lat"],
        "lon": home["lon"],
        "years": [y0, y1],
        "source": "NASA POWER daily (AG community, MERRA-2 assimilation)",
        "parameters": daily,
    })

    # 2. Monthly climatology for the home district
    save("home_climatology.json", {
        "district": home["id"],
        "lat": home["lat"],
        "lon": home["lon"],
        "source": "NASA POWER climatology (22-year monthly means)",
        "parameters": fetch_climatology(home["lat"], home["lon"],
                                        config.CLIMATOLOGY_PARAMS),
    })
    time.sleep(0.4)

    # 3. Climatology for every twin candidate
    for c in config.TWIN_CANDIDATES:
        try:
            save(f"cand_{c['id']}.json", {
                "district": c["id"],
                "name": c["name"],
                "lat": c["lat"],
                "lon": c["lon"],
                "source": "NASA POWER climatology (22-year monthly means)",
                "parameters": fetch_climatology(c["lat"], c["lon"],
                                                config.CLIMATOLOGY_PARAMS),
            })
            time.sleep(0.4)
        except RuntimeError as e:
            print(f"SKIPPED {c['id']}: {e}")


if __name__ == "__main__":
    main()
