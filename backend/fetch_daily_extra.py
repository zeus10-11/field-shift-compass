"""Fetch daily NASA POWER series for several candidate home districts so the
team can compare which district tells the most compelling (honest) shift
story before the demo."""

import data_fetch as df
import config

CANDIDATE_HOMES = [
    {"id": "nalgonda_tg",        "name": "Nalgonda, Telangana",        "lat": 17.05, "lon": 79.27},
    {"id": "nagpur_mh",          "name": "Nagpur, Maharashtra",        "lat": 21.15, "lon": 79.09},
    {"id": "anantapur_ap",       "name": "Anantapur, Andhra Pradesh",  "lat": 14.68, "lon": 77.29},
    {"id": "varanasi_up",        "name": "Varanasi, Uttar Pradesh",    "lat": 25.32, "lon": 82.99},
    {"id": "cuttack_od",         "name": "Cuttack, Odisha",            "lat": 20.46, "lon": 85.88},
    {"id": "purba_bardhaman_wb", "name": "Purba Bardhaman, West Bengal", "lat": 23.23, "lon": 87.86},
    {"id": "ranchi_jh",          "name": "Ranchi, Jharkhand",          "lat": 23.34, "lon": 85.31},
]

for c in CANDIDATE_HOMES:
    try:
        daily = df.fetch_daily(c["lat"], c["lon"], *config.DATA_YEARS,
                               config.DAILY_PARAMS)
        df.save(f"daily_{c['id']}.json", {
            "district": c["id"],
            "name": c["name"],
            "lat": c["lat"],
            "lon": c["lon"],
            "years": list(config.DATA_YEARS),
            "source": "NASA POWER daily (AG community, MERRA-2 assimilation)",
            "parameters": daily,
        })
    except RuntimeError as e:
        print(f"SKIPPED {c['id']}: {e}")
