"""Layer 2 - Climate Twin Matcher.

Builds a feature vector for the home farm's *projected* climate around 2040
(observed NASA POWER climatology + documented future deltas), then finds the
candidate district whose *current* climatology is the nearest neighbour.

Unit notes (verified against POWER daily data during development):
  - POWER monthly climatology PRECTOTCORR is mm/day -> convert to monthly totals.
  - POWER climatology T2M_MAX showed a systematic +7 C bias vs the daily record,
    so temperature features use monthly mean T2M (which agrees with daily data).

Features:
  - annual precipitation (mm)
  - monsoon (Jun-Sep) precipitation (mm) and its share of the year
  - post-monsoon (Oct-Dec) precipitation (mm)
  - mean temperature of the hottest month (C)
  - mean temperature of the crop's flowering window (Aug-Sep, C)
  - annual mean relative humidity (%)
  - precipitation seasonality (coefficient of variation of monthly totals)
"""

import numpy as np

MONTH_ORDER = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
               "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # non-leap

FEATURE_NAMES = [
    "annual_rain", "monsoon_rain", "monsoon_share", "post_rain",
    "tmean_hottest", "tmean_flower", "rh_mean", "rain_seasonality",
]


def _monthly(param):
    """POWER climatology dict -> ordered 12-month float array."""
    vals = [param.get(m) for m in MONTH_ORDER]
    return np.array([float(v) if v is not None and v > -900 else np.nan
                     for v in vals])


def _monthly_totals(rain_per_day):
    """mm/day -> mm per month."""
    return rain_per_day * np.array(MONTH_DAYS, dtype=float)


def features_from_climatology(params, temp_add=0.0, rh_add=0.0):
    rain_tot = _monthly_totals(_monthly(params["PRECTOTCORR"]))
    tmean_m = _monthly(params["T2M"])
    rh_m = _monthly(params["RH2M"])

    annual = float(np.nansum(rain_tot))
    monsoon = float(np.nansum(rain_tot[5:9]))
    post = float(np.nansum(rain_tot[9:12]))
    share = monsoon / annual if annual > 0 else np.nan
    hottest = float(np.nanmax(tmean_m))
    flower = float(np.nanmean(tmean_m[7:9]))      # Aug-Sep flowering window
    rh = float(np.nanmean(rh_m))
    seasonality = float(np.nanstd(rain_tot) / np.nanmean(rain_tot)) \
        if np.nanmean(rain_tot) > 0 else np.nan

    vec = np.array([annual, monsoon, share, post, hottest, flower, rh,
                    seasonality], dtype=float)
    vec[4] += temp_add
    vec[5] += temp_add
    vec[6] = max(0.0, vec[6] + rh_add)
    return dict(zip(FEATURE_NAMES, [round(float(x), 3) for x in vec]))


def scale_features(deltas, home_clim_params, frac=1.0):
    """Apply documented future deltas to the home climatology.

    frac interpolates along the warming path (0 = today, 1 = target year)."""
    t_add = deltas["temp_add_c"] * frac
    r_ann = 1 + (deltas["rain_mult_annual"] - 1) * frac
    r_mon = 1 + (deltas["rain_mult_monsoon"] - 1) * frac
    rh_add = deltas["rh_add_pct"] * frac
    rain_m = _monthly(home_clim_params["PRECTOTCORR"])
    scaled = {k: dict(v) for k, v in home_clim_params.items()}
    scaled_rain = list(rain_m)
    for i in range(12):
        mult = r_mon if 5 <= i <= 8 else r_ann
        scaled_rain[i] = rain_m[i] * mult
    scaled["PRECTOTCORR"] = dict(zip(MONTH_ORDER, scaled_rain))
    for key in ("T2M", "T2M_MAX"):
        if key in home_clim_params:
            scaled[key] = {m: v + t_add
                           for m, v in home_clim_params[key].items()}
    scaled["RH2M"] = {m: max(0.0, v + rh_add)
                      for m, v in home_clim_params["RH2M"].items()}
    return scaled


def match(home_vec, candidates, top_k=3):
    """Nearest neighbour on standardized features.

    candidates: list of dicts with keys id/name/climatology(features dict).
    Returns ranked matches with per-feature deltas explained.
    """
    ids = [c["id"] for c in candidates]
    X = np.array([list(c["features"].values()) for c in candidates], dtype=float)
    h = np.array(list(home_vec.values()), dtype=float)

    mu = np.vstack([X, h]).mean(axis=0)
    sd = np.vstack([X, h]).std(axis=0)
    sd[sd < 1e-6] = 1.0

    Z = (X - mu) / sd
    zh = (h - mu) / sd
    dist = np.sqrt(((Z - zh) ** 2).sum(axis=1))

    order = np.argsort(dist)
    d_max = float(dist.max()) or 1.0
    out = []
    for rank, i in enumerate(order[:top_k], start=1):
        c = candidates[i]
        delta = {k: round(float(h[j] - X[i, j]), 1)
                 for j, k in enumerate(FEATURE_NAMES)}
        # Relative similarity: best candidate in the pool scores near 100%.
        sim = 1.0 - float(dist[i]) / d_max
        out.append({
            "rank": rank,
            "id": c["id"],
            "name": c["name"],
            "lat": c["lat"],
            "lon": c["lon"],
            "distance": round(float(dist[i]), 3),
            "similarity": round(max(0.0, sim), 3),
            "features": c["features"],
            "home_minus_twin": delta,
        })
    return out, ids
