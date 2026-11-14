# 🧭 Field Shift Compass

**A climate twin for every farm.** It shows how the local climate has shifted, finds the place whose *present* looks like your farm's *future*, and tells the farmer what to change — in plain language, with evidence and confidence.

> NASA Space Apps Challenge 2026 · Challenge: **Field Shift: Adapting Farms with NASA Data**

---

## 1. The problem (30-second version)

Climate change is moving the farming calendar: monsoon onset drifts, rain arrives in heavier bursts, heat windows move. Most "agri-dashboards" fail farmers twice — nobody opens them, and nobody trusts an "AI says so" answer (surveys report only ~6% of farmers cite AI as a trusted decision source, vs ~56% for technical agronomists).

**Field Shift Compass** answers the three questions a farmer actually asks:

1. **What changed here?** (Shift Detector)
2. **Who already farms my future?** (Climate Twin)
3. **What should I do this season?** (Shift Advisor)

## 2. What it does

- **Shift Detector** — 25+ years of daily NASA POWER data → monsoon onset dates, sowing-window start, mid-season dry spells, heat-stress days, monsoon totals, heavy-rain days, rain-day counts — each with an honest trend line and strength rating.
- **Climate Twin Matcher** — builds the farm's *projected 2040 climate* (documented NEX-GDDP-CMIP6 ensemble deltas applied to observed climatology) and nearest-neighbour matches it against 36 regions' *current* NASA climatology. The output is a concrete answer: *"Your 2040 climate is an 87% match to Raipur, Chhattisgarh today — here's what farmers there grow."*
- **Shift Advisor** — deterministic, rule-based advice cards, each with **evidence bullets, the dataset they came from, and a transparent confidence score** (trend strength × record length). Nothing is hidden behind a model.
- **Trust loop** — farmer voice notes/photos/confirmations go to an **Agronomist Console**; approvals become broadcasts, corrections recalibrate the rule thresholds.
- **Delivery** — WhatsApp-style chat with voice playback (browser speech; the pilot uses recorded local-language notes) and a **printable one-page Season Plan** for farmers without smartphones.
- **Product-grade dashboard** — sidebar shell, six headline KPI cards, light/dark theme, gradient area + rounded-bar charts, a diverging onset-anomaly chart, map labels with the twin connection drawn, and toast feedback. Deep links (`#twin`, `#proof`) make the demo recording one click per screen.
- **Instant, offline-safe dashboard** — the backend injects all analytics + the India vector outline into the page at serve time (`window.__BOOT__`, and `window.__AGRO_BOOT__` for the console), so both apps paint with data on the first frame with zero fetch round-trips (slow-venue Wi-Fi proof).

### Demo story (Nagpur district, Vidarbha, Maharashtra — real data)

| Finding (NASA POWER, 2000–2025) | Value |
|---|---|
| Monsoon onset (hydrologic definition) | ~**+2.3 days/decade** later (7 Jun 2000 vs 25 Jun 2025 at record extremes) |
| Sowing-window start | ~**+2.3 days/decade** later (≈ +6 days since 2000) |
| Monsoon rainfall Jun–Sep | **+143 mm/decade** (r² = 0.29) |
| Rain days (≥2.5 mm) | **+8.2 days/decade** (r² = 0.35) — more active days, heavier bursts |
| Longest mid-season dry spell | −0.5 days/decade (honest: flat) |
| Heat-stress days (Mar–May) | −2.3 days/decade (honest: declining) |
| Climate twin for 2040 | **Raipur, Chhattisgarh (~87%)** · Rewa (79%) · Lucknow (78%) |

The weak trends are shown as weak. Judges see uncertainty, not overclaiming — that's the trust design principle.

### Four features most teams won't have

1. **Climate Path timeline** — drag 2026→2040 and watch the twin hold steady (Raipur stays #1 the whole way): the advice is robust, not a one-year fluke.
2. **Season Risk Calendar** — month-by-month probabilities straight from the 26-year record: June has a 35% chance of an 8+ day dry spell; July carries a 73% chance of ≥50 mm/day bursts; October is 92% dry. This is the "when to worry" strip farmers actually use.
3. **Farmer-memory back-test (Proof tab)** — the sowing rule replayed over all 26 seasons flags 8 of them (2005, 2006, 2009, 2010, 2017, 2019, 2023, 2025). Judges ask "how do you know it works?" — this answers before they ask.
4. **WhatsApp broadcast preview + one-click copy** — the exact message the extension office sends, evidence included, in the local language.

## 3. How it works (architecture)

```
[NASA POWER daily + climatology  ·  NEX-GDDP-CMIP6 deltas]   ← cached offline in backend/data/
                │
       FastAPI (backend/main.py)
   ├─ analytics/shift_detector.py   → trends, onset dates, anomaly series
   ├─ analytics/twin_matcher.py     → standardized-Euclidean nearest neighbour
   └─ analytics/advice_engine.py    → transparent rules + curated crop knowledge base
                │
   ┌──────────────┴───────────────┐
   ▼                              ▼
Farmer web app (web/index.html)   Agronomist Console (web/agronomist.html)
map · charts · twin · advice      review queue · approve/edit · recalibration
chat + voice · season plan                ▲
   └────── farmer feedback ────────────────┘  (feedback.json)
```

- **Stack:** Python 3, FastAPI, pandas/numpy, scikit-learn-style nearest neighbour (implemented directly), vanilla JS + hand-rolled SVG charts (zero build step), Leaflet map.
- **Zero live API dependency:** all data is cached in `backend/data/` before the demo; charts are pure SVG so the app keeps working without internet (only map tiles need a connection).
- **Deterministic core:** no black-box model anywhere in the recommendation path. An LLM could *phrase* advice; it never *decides* it.

## 4. Quick start

```bash
cd field-shift-compass
pip install -r requirements.txt

# (optional) refresh data from NASA POWER — the app ships pre-cached:
python backend/data_fetch.py

python backend/main.py
# open http://localhost:8000          → farmer app
# open http://localhost:8000/agronomist → expert console
```

## 5. NASA data used (submission field answer)

- **NASA POWER** (Prediction Of Worldwide Energy Resources), AG community — daily meteorology 2000–2025 for the home district (parameters `PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`) and 22-year monthly climatology for 37 Indian districts. POWER's MERRA-2 assimilation incorporates NASA satellite observations (GPM, MODIS and others). This is the dataset for **every trend, twin feature and advice trigger** in the app.
- **NEX-GDDP-CMIP6** (NASA Earth Exchange Global Daily Downscaled Projections) — ensemble-median deltas for ~2040 under SSP2-4.5 (temperature +1.1 °C, annual rainfall ×1.08 with monsoon ×1.05, onset shift +6 days) define the home farm's *projected future* in the twin match. Documented, approximate, and cited in-app as such.
- **Pipeline-ready (not yet wired into the live demo):** GPM IMERG (onset), SMAP (root-zone soil moisture), MODIS/HLS NDVI (green-up), ECOSTRESS (plant water stress), NISAR (cloud-proof radar monitoring of monsoon fields). The `data_fetch.py` module is structured so each is a drop-in cached layer.

## 6. Space agency & partner data

No partner-agency datasets were required for the prototype. Architecture accommodates ESA Sentinel-1/2 (via HLS) and ISRO/NISAR products for the pilot's cloud-gap filling.

## 7. Use of Super Intelligence (SI) — disclosure

SI tools (coding assistance) were used to accelerate implementation of this project, in accordance with the Space Apps 2026 rules. SI was used for: code generation/refactoring of the FastAPI backend, web UI code, and this documentation's drafts. SI was **not** used to fabricate data: every displayed number is computed from cached NASA POWER/CMIP6-derived values by the deterministic analytics modules in `backend/analytics/`, and can be reproduced from the raw cached API responses. No SI-generated images, audio, or branding elements appear in the project. Any AI-phrased text would carry a visible watermark; the rule-based advice engine and all charts are deterministic outputs.

## 8. Validation & limitations (say it before the judges do)

**Validation**
- Onset definition follows the simplified IMD hydrologic rule (5-day sum ≥ 30 mm followed by ≥ 25 mm in 10 days) — detected onset dates for Vidarbha (early-to-late June) match IMD crop-calendar expectations.
- Back-test: the sowing rule flags the late-onset years (e.g., 2025) that farmers in the district remember as bad sowing years.
- Trend significance is shown openly (r², strength label); confidence scores degrade honestly.

**Limitations (stated, not hidden)**
- POWER point data ≈ district headquarters, not field-level; a pilot would add district polygons and farmer-submitted ground truth.
- Future deltas are ensemble-medians applied uniformly; a pilot would run the actual NEX-GDDP-CMIP6 files per grid cell.
- Crop knowledge base is curated for Indian kharif systems and meant for agronomist review — it is a starting point, not a final authority.
- Demo region: Vidarbha; the pipeline is region-agnostic (`backend/config.py`).

## 9. Repo layout

```
field-shift-compass/
├── backend/
│   ├── main.py                 FastAPI app (API + serves web)
│   ├── config.py               home district, twin candidates, future deltas
│   ├── data_fetch.py           NASA POWER downloader (cache builder)
│   ├── fetch_daily_extra.py    daily series for candidate home districts
│   ├── compare_districts.py    choose the home district on honest trends
│   ├── analytics/
│   │   ├── shift_detector.py   Layer 1
│   │   ├── twin_matcher.py     Layer 2
│   │   └── advice_engine.py    Layer 3 (rules + crop KB)
│   └── data/                   cached NASA JSON (offline demo)
├── web/
│   ├── index.html              farmer app
│   ├── agronomist.html         expert console
│   ├── css/style.css
│   └── js/app.js               charts + interactions (no framework)
├── docs/
│   ├── pitch-deck-outline.md   7-slide deck
│   └── demo-video-script.md    2-minute demo script
└── README.md
```

## 10. Team roles mapping

| Role | Where it lives in the repo |
|---|---|
| Data/GIS engineer | `data_fetch.py`, `backend/data/` |
| Climate/analytics lead | `analytics/shift_detector.py`, `twin_matcher.py` |
| Full-stack developer | `main.py`, `web/js/app.js` |
| UX/UI designer | `web/css/style.css`, advice cards, chat flow |
| Agronomy/domain researcher | `advice_engine.py` crop KB + agronomist console |
| Storyteller/pitch lead | `docs/`, demo script, season-plan output |

## 11. Submission checklist (from the official Project Submission Guide)

- [ ] Project page created via **My Team → Project** tab (submission opens Nov 14, 9 a.m., closes Nov 15, 11:59 p.m.)
- [ ] **Project Name:** Field Shift Compass — Climate Twins for Adapting Farms
- [ ] **High-Level Project Summary:** see §1–2 above
- [ ] **Link to Project Demo:** 2-minute video (script in `docs/demo-video-script.md`) — **do not require password/permission**; host on YouTube/Drive/GitHub with public link; strong demo raises the score
- [ ] **Detailed Project Description:** what/how/benefits/hopes/tools → §2–3, §9
- [ ] **Use of SI:** disclosure written → §7
- [ ] **NASA Data:** POWER + NEX-GDDP-CMIP6 details → §5 (at least one NASA data resource is mandatory for Global Award eligibility)
- [ ] **Space Agency Data:** §6
- [ ] Tags: climate, agriculture, food security, machine learning (if applicable), SI usage declared
- [ ] Images ≤ 10 MB (JPG/PNG/GIF); upload files to a public-accessible cloud service
- [ ] Save Progress → **Submit for Judging** before local deadline; edits locked after

---

*Built for NASA Space Apps Challenge 2026. All trends reproducible from cached NASA POWER responses in `backend/data/`.*
