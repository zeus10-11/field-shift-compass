"""Seasonal risk calendar + farmer-memory back-test.

Both derive from the same cached daily NASA POWER record.
"""

import datetime as dt

import numpy as np


def _parse_daily(series):
    out = []
    for k, v in series.items():
        try:
            if v is None or v < -900:
                continue
            d = dt.datetime.strptime(k, "%Y%m%d").date()
            out.append((d, float(v)))
        except (ValueError, TypeError):
            continue
    out.sort()
    return out


def risk_calendar(daily_params):
    """Month-by-month seasonal risk profile for Jun..Oct.

    For each month, over all years:
      - longest dry spell (rain < 1 mm) inside the month
      - heavy-rain days (>= 50 mm)
      - mean daily max temperature
      - mean monthly rainfall total
    Aggregated to probabilities / means.
    """
    rain = _parse_daily(daily_params["PRECTOTCORR"])
    tmax = _parse_daily(daily_params["T2M_MAX"])
    tmax_by_date = dict(tmax)

    per_month = {m: {"dry": [], "heavy": [], "tmax": [], "total": []}
                 for m in range(6, 11)}
    for year in sorted({d.year for d, _ in rain}):
        for m in range(6, 11):
            pairs = [(d, r) for d, r in rain if d.year == year and d.month == m]
            if not pairs:
                continue
            best = cur = 0
            for _, r in pairs:
                if r < 1.0:
                    cur += 1
                    best = max(best, cur)
                else:
                    cur = 0
            heavy = sum(1 for _, r in pairs if r >= 50.0)
            temps = [tmax_by_date[d] for d, _ in pairs if d in tmax_by_date]
            per_month[m]["dry"].append(best)
            per_month[m]["heavy"].append(heavy)
            per_month[m]["total"].append(sum(r for _, r in pairs))
            if temps:
                per_month[m]["tmax"].append(float(np.mean(temps)))

    out = []
    labels = {6: "June", 7: "July", 8: "August", 9: "September", 10: "October"}
    for m in range(6, 11):
        d = per_month[m]
        out.append({
            "month": labels[m],
            "month_num": m,
            "p_dryspell8": round(float(np.mean([1 if x >= 8 else 0 for x in d["dry"]])), 2),
            "p_heavy": round(float(np.mean([1 if x >= 1 else 0 for x in d["heavy"]])), 2),
            "mean_tmax": round(float(np.mean(d["tmax"])), 1) if d["tmax"] else None,
            "mean_total": round(float(np.mean(d["total"])), 0),
        })
    return out


def backtest(shifts):
    """Would the sowing rule have flagged late-onset years?

    Flags a year when onset is late (ordinal > mean + 0.75 sigma) or the
    longest dry spell exceeds mean + 0.75 sigma. This is an internal
    consistency check within the same POWER record; an independent check
    against district rainfall/yield records is recommended.
    """
    import datetime as _dt

    def ordinal(s):
        d = _dt.date.fromisoformat(s)
        return (d - _dt.date(d.year, 6, 1)).days

    onset = {int(y): ordinal(v) for y, v in shifts["onset"].items()}
    dry = {int(y): v for y, v in shifts["dry_spell"].items()}
    years = sorted(set(onset) & set(dry))

    o_mean = float(np.mean(list(onset.values())))
    o_sd = float(np.std(list(onset.values())))
    d_mean = float(np.mean(list(dry.values())))
    d_sd = float(np.std(list(dry.values())))

    rows = []
    for y in years:
        late = onset[y] > o_mean + 0.75 * o_sd
        dryflag = dry[y] > d_mean + 0.75 * d_sd
        rows.append({
            "year": y,
            "onset": shifts["onset"][str(y)],
            "onset_days": onset[y],
            "onset_anom": round(onset[y] - o_mean, 1),
            "dry_spell": dry[y],
            "dry_anom": round(dry[y] - d_mean, 1),
            "flagged": bool(late or dryflag),
            "reason": ("late onset" if late else "") +
                      (" + long dry spell" if late and dryflag else
                       ("long dry spell" if dryflag else "")),
        })

    flagged = [r["year"] for r in rows if r["flagged"]]
    hit_rate = round(len(flagged) / len(years), 2) if years else 0
    return {
        "rows": rows,
        "onset_mean_days": round(o_mean, 1),
        "onset_sd_days": round(o_sd, 1),
        "dry_mean": round(d_mean, 1),
        "dry_sd": round(d_sd, 1),
        "flagged_years": flagged,
        "n_years": len(years),
        "summary": f"{len(flagged)} of {len(years)} seasons flagged for "
                   f"late onset or long dry spell (internal consistency check).",
    }
