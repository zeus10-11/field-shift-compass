"""Central configuration for Field Shift Compass."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DIR = os.path.join(os.path.dirname(BASE_DIR), "web")

# ---------------------------------------------------------------------------
# Study area: Nagpur district, Maharashtra, India (Vidarbha; kharif paddy).
# CHANGE THESE VALUES to retarget the whole app to another district.
# (Daily data for several alternative districts is cached in backend/data/
#  as daily_<id>.json — see compare_districts.py to evaluate alternatives.)
# ---------------------------------------------------------------------------
HOME_DISTRICT = {
    "id": "nagpur_mh",
    "name": "Nagpur district, Maharashtra (Vidarbha)",
    "short": "Nagpur (MH)",
    "crop": "Kharif paddy (with cotton/soybean uplands)",
    "lat": 21.15,
    "lon": 79.09,
    "sowing_month": 6,          # June = kharif sowing
    "harvest_month": 11,        # November
    "language": "Hindi / English (Marathi voice support is unreliable in browsers)",
}

# Candidate districts used by the Climate Twin Matcher. Coordinates are
# district-headquarters points; monthly climatology is fetched from NASA POWER.
TWIN_CANDIDATES = [
    {"id": "nalgonda_tg",     "name": "Nalgonda, Telangana",        "lat": 17.05, "lon": 79.27},
    {"id": "kurnool_ap",      "name": "Kurnool, Andhra Pradesh",    "lat": 15.83, "lon": 78.03},
    {"id": "anantapur_ap",    "name": "Anantapur, Andhra Pradesh",  "lat": 14.68, "lon": 77.29},
    {"id": "vizianagaram_ap", "name": "Vizianagaram, Andhra Pradesh", "lat": 18.11, "lon": 83.41},
    {"id": "thanjavur_tn",    "name": "Thanjavur, Tamil Nadu",      "lat": 10.79, "lon": 79.14},
    {"id": "cuddalore_tn",    "name": "Cuddalore, Tamil Nadu",      "lat": 11.75, "lon": 79.75},
    {"id": "madurai_tn",      "name": "Madurai, Tamil Nadu",        "lat": 9.93,  "lon": 78.12},
    {"id": "coimbatore_tn",   "name": "Coimbatore, Tamil Nadu",     "lat": 11.02, "lon": 76.96},
    {"id": "belagavi_ka",     "name": "Belagavi, Karnataka",        "lat": 15.85, "lon": 74.50},
    {"id": "ballari_ka",      "name": "Ballari, Karnataka",         "lat": 15.14, "lon": 76.92},
    {"id": "davangere_ka",    "name": "Davangere, Karnataka",       "lat": 14.23, "lon": 75.92},
    {"id": "nashik_mh",       "name": "Nashik, Maharashtra",        "lat": 19.99, "lon": 73.79},
    {"id": "pune_mh",         "name": "Pune, Maharashtra",          "lat": 18.52, "lon": 73.86},
    {"id": "vijayapura_ka",   "name": "Vijayapura, Karnataka",      "lat": 16.82, "lon": 75.71},
    {"id": "kolhapur_mh",     "name": "Kolhapur, Maharashtra",      "lat": 16.70, "lon": 74.24},
    {"id": "surat_gj",        "name": "Surat, Gujarat",             "lat": 21.17, "lon": 72.83},
    {"id": "rajkot_gj",       "name": "Rajkot, Gujarat",            "lat": 22.30, "lon": 70.80},
    {"id": "indore_mp",       "name": "Indore, Madhya Pradesh",     "lat": 22.72, "lon": 75.86},
    {"id": "bhopal_mp",       "name": "Bhopal, Madhya Pradesh",     "lat": 23.26, "lon": 77.41},
    {"id": "rewa_mp",         "name": "Rewa, Madhya Pradesh",       "lat": 24.53, "lon": 81.30},
    {"id": "raipur_cg",       "name": "Raipur, Chhattisgarh",       "lat": 21.25, "lon": 81.63},
    {"id": "cuttack_od",      "name": "Cuttack, Odisha",            "lat": 20.46, "lon": 85.88},
    {"id": "bhubaneswar_od",  "name": "Bhubaneswar, Odisha",        "lat": 20.30, "lon": 85.82},
    {"id": "ranchi_jh",       "name": "Ranchi, Jharkhand",          "lat": 23.34, "lon": 85.31},
    {"id": "varanasi_up",     "name": "Varanasi, Uttar Pradesh",    "lat": 25.32, "lon": 82.99},
    {"id": "lucknow_up",      "name": "Lucknow, Uttar Pradesh",     "lat": 26.85, "lon": 80.95},
    {"id": "patna_br",        "name": "Patna, Bihar",               "lat": 25.59, "lon": 85.14},
    {"id": "muzaffarpur_br",  "name": "Muzaffarpur, Bihar",         "lat": 26.12, "lon": 85.39},
    {"id": "purba_bardhaman_wb", "name": "Purba Bardhaman, West Bengal", "lat": 23.23, "lon": 87.86},
    {"id": "hooghly_wb",      "name": "Hooghly, West Bengal",       "lat": 22.90, "lon": 88.39},
    {"id": "malda_wb",        "name": "Malda, West Bengal",         "lat": 25.01, "lon": 88.14},
    {"id": "kamrup_as",       "name": "Kamrup (Metro), Assam",      "lat": 26.14, "lon": 91.74},
    {"id": "nagaon_as",       "name": "Nagaon, Assam",              "lat": 26.35, "lon": 92.68},
    {"id": "kota_rj",         "name": "Kota, Rajasthan",            "lat": 25.18, "lon": 75.83},
    {"id": "ludhiana_pb",     "name": "Ludhiana, Punjab",           "lat": 30.90, "lon": 75.85},
    {"id": "karnal_hr",       "name": "Karnal, Haryana",            "lat": 29.69, "lon": 76.99},
]

# ---------------------------------------------------------------------------
# Future-climate deltas for the home district around 2040 under SSP2-4.5,
# expressed as scenario-informed deltas applied uniformly to the home
# climatology. These are approximate CMIP6 ensemble-median deltas for
# peninsular India — NOT pulled from actual NEX-GDDP grid-cell files in this
# prototype. A pilot would run the actual NEX-GDDP-CMIP6 files per grid cell.
# ---------------------------------------------------------------------------
FUTURE_DELTAS_2040 = {
    "target_year": 2040,
    "scenario": "SSP2-4.5 (scenario-informed CMIP6 ensemble-median deltas, approximate)",
    "temp_add_c": 1.1,          # added to every month's mean/max/min temperature
    "rain_mult_annual": 1.08,   # annual precipitation multiplier
    "rain_mult_monsoon": 1.05,  # Jun-Sep precipitation multiplier
    "onset_shift_days": 6,      # monsoon onset delayed by this many days
    "rh_add_pct": -1.0,         # relative humidity change (percentage points)
}

# NASA POWER daily parameters fetched for the home district
DAILY_PARAMS = ["PRECTOTCORR", "T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS2M", "ALLSKY_SFC_SW_DWN"]
CLIMATOLOGY_PARAMS = ["PRECTOTCORR", "T2M", "T2M_MAX", "RH2M", "WS2M"]

DATA_YEARS = (2000, 2025)

POWER_BASE = "https://power.larc.nasa.gov/api/temporal"
USER_AGENT = "FieldShiftCompass/1.0 (NASA Space Apps 2026)"
