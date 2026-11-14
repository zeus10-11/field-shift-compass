"""Compare candidate home districts on honest 26-year NASA POWER trends."""
import json
import sys

sys.path.insert(0, ".")
import config
from analytics import shift_detector as sd

ids = ["krishna_ap", "nalgonda_tg", "nagpur_mh", "anantapur_ap",
       "varanasi_up", "cuttack_od", "purba_bardhaman_wb", "ranchi_jh"]

print(f"{'district':<18}{'onset d/d':>10}{'dry d/d':>9}{'heat d/d':>9}"
      f"{'rain d/d':>10}{'xtreme d/d':>11}{'raindays':>9}{'sow d/d':>9}  score")
rows = []
for did in ids:
    fn = "home_daily.json" if did == "krishna_ap" else f"daily_{did}.json"
    try:
        daily = json.load(open(f"data/{fn}"))
    except FileNotFoundError:
        print(f"{did:<18} (not downloaded)")
        continue
    s = sd.detect(daily["parameters"], config.HOME_DISTRICT)
    t = s["trends"]
    # demo-impact score: magnitude of trends weighted by explanatory power
    score = sum(abs(t[k]["change_per_decade"]) * (1 + t[k]["r2"])
                for k in ("onset", "dry_spell", "heat_days", "monsoon_rain",
                          "extreme_rain", "rain_days", "sowing_window"))
    rows.append((score, did, t))
    print(f"{did:<18}"
          f"{t['onset']['change_per_decade']:>+9.1f}"
          f"{t['dry_spell']['change_per_decade']:>+9.1f}"
          f"{t['heat_days']['change_per_decade']:>+9.1f}"
          f"{t['monsoon_rain']['change_per_decade']:>+10.0f}"
          f"{t['extreme_rain']['change_per_decade']:>+11.1f}"
          f"{t['rain_days']['change_per_decade']:>+9.1f}"
          f"{t['sowing_window']['change_per_decade']:>+9.1f}"
          f"  {score:6.0f}")

rows.sort(reverse=True)
print("\nBest demo-impact order:", [r[1] for r in rows])
best = rows[0][1]
t = rows[0][2]
print(f"\nDetail for winner ({best}):")
for k, v in t.items():
    print(f"  {k}: {v['change_per_decade']:+.2f} {v['unit']}/decade, r2={v['r2']}, strength={v['strength']}")
