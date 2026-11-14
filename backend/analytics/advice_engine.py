"""Layer 3 - Shift Advisor.

Deterministic, transparent rules that convert detected shifts + the climate
twin into ranked, confidence-scored advice. No black-box model: every card
carries its evidence and the dataset it came from.

Crop knowledge base is curated for Indian kharif cropping systems and is
intended to be reviewed by an agronomist (the trust loop in the product).
"""

# ---------------------------------------------------------------------------
# Crop knowledge base -------------------------------------------------------
# ---------------------------------------------------------------------------

PADDY_VARIETIES = {
    "long":  {"name": "MTU-7029 (Swarna)", "duration_days": 145,
              "notes": "high-yielding long-duration paddy"},
    "medium": {"name": "BPT-5204 (Samba Mahsuri)", "duration_days": 135,
               "notes": "fine-grain medium-duration paddy"},
    "short": {"name": "MTU-1010", "duration_days": 115,
              "notes": "short-duration paddy, escapes late-season drought"},
    "very_short": {"name": "Sahbhagi Dhan", "duration_days": 105,
                   "notes": "drought-tolerant short-duration paddy"},
    "flood": {"name": "DRR Dhan 44", "duration_days": 120,
              "notes": "submergence-tolerant paddy (Swarna-Sub1 type)"},
    "heat": {"name": "NDR-8001", "duration_days": 115,
             "notes": "heat-tolerant paddy for hotter districts"},
}

# What grows successfully today in each candidate district (curated,
# district-agriculture-office style summaries; agronomist-reviewable).
TWIN_PRACTICE = {
    "thanjavur_tn": "Cauvery delta paddy: short-duration varieties (CO 51, ~105-110 d) transplanted after mid-August onset; canal-supported, so sowing is timed late and tight.",
    "cuddalore_tn": "Northeast-monsoon paddy: sowing delayed into Aug-Sep; flood-tolerant varieties; raised-bed pulses (blackgram) after paddy.",
    "nagpur_mh": "Late-onset districts sow paddy/soybean in late June-July; cotton + short-duration paddy mix; deep soils buffer mid-season dry spells.",
    "raipur_cg": "Chhattisgarh paddy (IGKV varieties): medium-duration types sown late June; rainfed bunded fields; farmers keep 2-week seedling nursery buffer.",
    "cuttack_od": "Odisha coastal paddy: flood-tolerant (Swarna-Sub1 type) for Aug floods; short-duration rabi pulses after early harvest.",
    "bhubaneswar_od": "Similar to Cuttack; farmers stagger sowing across two windows to spread cyclone/flood risk.",
    "purba_bardhaman_wb": "Bengal rice bowl: medium-duration paddy after mid-June onset; boro paddy in Feb-May uses residual heat; strong extension network.",
    "hooghly_wb": "West Bengal: jute-paddy rotation, paddy sown late June-July; drainage channels critical in monsoon peaks.",
    "patna_br": "Bihar: medium-duration paddy (Rajendra Mahsuri) sown late June; flood-prone north Bihar uses submergence-tolerant types.",
    "muzaffarpur_br": "North Bihar: flood-adapted paddy plus summer makhana/vegetables in wet lowlands.",
    "varanasi_up": "Eastern UP: late-monsoon paddy in July; farmers transplant up to mid-July without yield loss using short-duration types.",
    "lucknow_up": "Central UP: paddy sowing tracks monsoon arrival in late June; wheat follows by mid-November, so short-duration paddy protects the wheat window.",
    "kamrup_as": "Assam valley: deepwater/flood-tolerant paddy systems; Sali paddy transplanted June-July around flood peaks.",
    "nagaon_as": "Assam: flood-prone paddy plus jute; staggered sowing across flood calendar.",
    "kolhapur_mh": "Western Ghats fringes: high-rainfall paddy, monsoon-fed; growers manage excess water with bund drainage.",
    "pune_mh": "Western Maharashtra: onset near mid-June; onion-sugar cane-paddy mix; drip adoption high; water budgeting is normal practice.",
    "nashik_mh": "Nashik: grape-onion-paddy mix; reliable June onset; drip and mulching widespread.",
    "indore_mp": "Malwa plateau: soybean-paddy-pulse rotations sown with late-June onset; black soils hold moisture through dry spells.",
    "bhopal_mp": "Central MP: paddy in valley lands sown late June; soybean/wheat rotations dominate uplands.",
    "rewa_mp": "Vindhyan MP: rainfed paddy sown with late-June/July onset; drought-escaping short varieties common.",
    "ranchi_jh": "Jharkhand plateau: rainfed upland paddy sown late June-July; Sahbhagi-type drought escapers widely promoted.",
    "raipur_cg": "Chhattisgarh plains: rice bowl varieties (IGKV) timed to a late-June onset; nursery stagger standard.",
    "kota_rj": "Hadoti, Rajasthan: paddy in Chambal command sown July; cotton/soybean uplands tolerate hotter, later monsoons.",
    "belagavi_ka": "North Karnataka malnad fringes: paddy+sugarcane; late-June onset; farmers use 25-30 d old seedlings to bridge delayed onset.",
    "ballari_ka": "Rayalaseema-adjacent: canal paddy sown July-Aug; hot flowering window handled with heat-tolerant types.",
    "davangere_ka": "Central Karnataka: paddy under Bhadra canal, sown July; aromatic short-duration types.",
    "vijayapura_ka": "Dry north Karnataka: mostly pulses/sunflower, not paddy - signals a drier analog.",
    "nashik_mh": "Nashik: paddy+grapes+onion; June onset reliable; drip/mulching widespread.",
    "nalgonda_tg": "Telangana: late-onset paddy (Kharif sowing often slips to July); tank-fed; short-duration varieties standard.",
    "kurnool_ap": "Rayalaseema: late and erratic onset; paddy only under Tungabhadra canal; rainfed zones grow pulses/sunflower.",
    "anantapur_ap": "India's driest district cluster: groundnut/pulses, no paddy - a strong dryness analog.",
    "vizianagaram_ap": "North coastal AP: paddy similar to Krishna but onset ~1 week later; farmers transplant through mid-July.",
    "madurai_tn": "Tamil Nadu interior: paddy under tank/river systems, often two short seasons managed around water availability.",
    "coimbatore_tn": "Western TN: paddy in command areas only; millets/pulses in rainfed tracts - a moderate dryness analog.",
    "surat_gj": "South Gujarat: paddy+cashewn+sugarcane with strong June onset; high monsoon totals managed with drainage.",
    "rajkot_gj": "Saurashtra: groundnut/cotton belt, paddy rare - a dry, hot analog.",
    "ludhiana_pb": "Punjab: paddy transplanted mid-June with canal/tube wells; heat-tolerant types; straw management issue.",
    "karnal_hr": "Haryana: paddy mid-June; direct-seeded rice adoption to cut labour and water; strong extension.",
}

DEFAULT_PRACTICE = ("Neighbouring districts with this climate today run paddy "
                    "with locally adjusted sowing dates and short/medium "
                    "duration varieties; confirm specifics with the local "
                    "agriculture office.")


def _confidence(trend, n_years):
    """Transparent confidence score from trend strength + record length."""
    score = 0.0
    if n_years >= 20:
        score += 0.35
    elif n_years >= 12:
        score += 0.2
    score += min(0.45, trend["r2"] * 0.9)
    if trend["strength"] == "strong":
        score += 0.15
    score = min(1.0, score)
    if score >= 0.65:
        label = "High"
    elif score >= 0.45:
        label = "Medium-High"
    elif score >= 0.28:
        label = "Medium"
    else:
        label = "Low"
    return round(score, 2), label


def _card(rec, why, confidence, twin, action_type):
    return {
        "recommendation": rec,
        "why": why,                      # list of {text, dataset}
        "confidence": confidence,        # (score, label)
        "twin_reference": twin,
        "action_type": action_type,
    }


def build_advice(shifts, twin_match, deltas, home, farmer_region_note=None):
    """shifts: shift_detector output; twin_match: top matches list."""
    cards = []
    t = shifts["trends"]
    onset, dry, heat, rain, sow = (t["onset"], t["dry_spell"], t["heat_days"],
                                   t["monsoon_rain"], t["sowing_window"])
    top = twin_match[0] if twin_match else None
    twin_note = TWIN_PRACTICE.get(top["id"], DEFAULT_PRACTICE) if top else None

    # --- 1. Sowing date -------------------------------------------------
    onset_shift = round(onset["change_per_decade"])
    years_span = onset["last_year"] - onset["first_year"]
    total_shift = round(onset["slope_per_year"] * years_span)
    if abs(total_shift) >= 4:
        conf_score, conf_label = _confidence(onset, onset["n_years"])
        sow_shift = round(sow["change_per_decade"])
        why = [
            {"text": f"Monsoon onset has arrived ~{abs(total_shift)} days "
                     f"later since {onset['first_year']} "
                     f"({onset_shift:+d} days/decade, R²={onset['r2']}).",
             "dataset": "NASA POWER daily precipitation (MERRA-2 reanalysis)"},
            {"text": f"Soil-moisture-based sowing window moved "
                     f"{sow_shift:+d} days/decade.",
             "dataset": "NASA POWER daily precipitation"},
            {"text": f"Your 2040 projected climate adds ~+{deltas['temp_add_c']} °C "
                     f"and shifts onset another ~+{deltas['onset_shift_days']} days.",
             "dataset": "NEX-GDDP-CMIP6 ensemble deltas (approx.)"},
        ]
        rec = (f"Plan sowing ~{abs(total_shift) + deltas['onset_shift_days']} days "
               f"later than your old calendar (and expect a further shift by 2040). "
               f"Raise 25-30 day old seedlings so transplanting can wait out a "
               f"delayed onset without yield loss.")
        cards.append(_card(rec, why, (conf_score, conf_label),
                           f"Climate twin: {top['name']}" if top else None,
                           "sowing_date"))

    # --- 2. Variety switch ----------------------------------------------
    if dry["change_per_decade"] > 0.4 or rain["change_per_decade"] > 15:
        flood_risk = rain["change_per_decade"] > 15
        if flood_risk:
            v = PADDY_VARIETIES["flood"]
            rec = (f"Consider {v['name']} ({v['duration_days']} d, "
                   f"{v['notes']}) for flood-prone fields, keeping your current "
                   f"variety on higher fields.")
            why = [
                {"text": f"Monsoon rainfall trending "
                         f"{rain['change_per_decade']:+.0f} mm/decade - more "
                         f"submergence risk in peak weeks.",
                 "dataset": "NASA POWER daily precipitation"},
            ]
        else:
            v = PADDY_VARIETIES["short"]
            rec = (f"Switch part of your area to {v['name']} "
                   f"({v['duration_days']} d, {v['notes']}) to escape "
                   f"lengthening mid-season dry spells.")
            why = [
                {"text": f"Longest dry spell within the monsoon trending "
                         f"{dry['change_per_decade']:+.1f} days/decade.",
                 "dataset": "NASA POWER daily precipitation"},
            ]
        conf_score, conf_label = _confidence(dry, dry["n_years"])
        if top:
            why.append({"text": f"Farmers in your climate twin ({top['name']}) "
                                f"already use this approach: {twin_note}",
                        "dataset": "District agronomy practice (curated)"})
        cards.append(_card(rec, why, (conf_score, conf_label),
                           f"Climate twin: {top['name']}" if top else None,
                           "variety"))

    # --- 3. Stagger sowing across two windows (onset variability) --------
    onset_vals = [ordinal_days(v) for v in shifts["onset"].values()]
    if len(onset_vals) >= 10:
        spread = max(onset_vals) - min(onset_vals)
        if spread >= 18.0:
            n_years = len(onset_vals)
            conf_score = 0.35 + (0.35 if n_years >= 20 else 0.2)
            conf_score = min(1.0, conf_score)
            conf_label = ("Medium-High" if conf_score >= 0.45 else "Medium")
            rec = (f"Your monsoon onset has swung across a {spread:.0f}-day range "
                   f"over the record. Stagger sowing across two windows "
                   f"(e.g., 60% at the first good moisture window, 40% two "
                   f"weeks later) so a single bad onset can't wipe out the "
                   f"season.")
            why = [
                {"text": f"Year-to-year onset spread of {spread:.0f} days "
                         f"across {n_years} years (NASA POWER daily record).",
                 "dataset": "NASA POWER daily precipitation"},
                {"text": "Staggered nursery raising is standard practice in "
                         "districts with erratic onset - it spreads risk "
                         "without needing more land.",
                 "dataset": "District agronomy practice (curated)"},
            ]
            cards.append(_card(rec, why, (round(conf_score, 2), conf_label),
                               f"Climate twin: {top['name']}" if top else None,
                               "stagger"))

    # --- 4. Heat management ---------------------------------------------
    if heat["change_per_decade"] >= 0.8:
        v = PADDY_VARIETIES["heat"]
        conf_score, conf_label = _confidence(heat, heat["n_years"])
        rec = (f"Protect flowering from heat: where possible transplant so "
               f"flowering avoids the hottest fortnight; {v['name']} "
               f"({v['notes']}) is an option for late plantings.")
        why = [
            {"text": f"Heat-stress days (>=35 °C, Mar-May) trending "
                     f"{heat['change_per_decade']:+.1f} days/decade "
                     f"(R²={heat['r2']}).",
             "dataset": "NASA POWER daily max temperature"},
            {"text": "Heat at flowering can cut paddy spikelet fertility "
                     "sharply (>35 °C for 3+ days).",
             "dataset": "Agronomy literature"},
        ]
        cards.append(_card(rec, why, (conf_score, conf_label),
                           f"Climate twin: {top['name']}" if top else None,
                           "heat"))

    # --- 5. Water management --------------------------------------------
    if rain["change_per_decade"] < -10 or dry["change_per_decade"] > 0.6:
        conf_score, conf_label = _confidence(dry, dry["n_years"])
        rec = ("Add moisture insurance: mulching + alternate wetting-drying "
               "irrigation; keep a 2-week nursery buffer for re-planting "
               "after a failed sowing window.")
        why = [
            {"text": f"Monsoon rainfall trending {rain['change_per_decade']:+.0f} "
                     f"mm/decade with longer dry spells "
                     f"({dry['change_per_decade']:+.1f} d/decade).",
             "dataset": "NASA POWER daily precipitation"},
        ]
        cards.append(_card(rec, why, (conf_score, conf_label),
                           f"Climate twin: {top['name']}" if top else None,
                           "water"))

    # --- 6. Alternate crop from the twin --------------------------------
    if top and top["id"] in ("anantapur_ap", "rajkot_gj", "kurnool_ap",
                             "vijayapura_ka", "coimbatore_tn", "madurai_tn"):
        conf_score, conf_label = (0.5, "Medium")
        rec = (f"Your 2040 climate matches a drier region ({top['name']}). "
               f"Consider a field-level rotation with a drought-hardy crop "
               f"(groundnut, pulses, millets) to spread risk.")
        why = [
            {"text": f"Climate twin match: {top['name']} today ≈ your "
                     f"{deltas['target_year']} projection "
                     f"(similarity {top['similarity']:.0%}).",
             "dataset": "NASA POWER climatology + NEX-GDDP-CMIP6 deltas"},
            {"text": f"What works there: {twin_note}",
             "dataset": "District agronomy practice (curated)"},
        ]
        cards.append(_card(rec, why, (conf_score, conf_label),
                           f"Climate twin: {top['name']}", "crop_change"))

    # Rank: strongest-confidence, highest-impact first
    order = {"sowing_date": 0, "stagger": 1, "variety": 2, "water": 3,
             "heat": 4, "crop_change": 5}
    cards.sort(key=lambda c: (order.get(c["action_type"], 9),
                              -c["confidence"][0]))
    return cards


def ordinal_days(date_str):
    """'2024-06-15' -> days after Jun 1 of that year (ISO string input)."""
    import datetime as _dt
    d = _dt.date.fromisoformat(date_str)
    return (d - _dt.date(d.year, 6, 1)).days


def _std(values):
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5
