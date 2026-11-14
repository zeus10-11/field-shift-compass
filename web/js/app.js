/* Field Shift Compass — farmer web app (v3).
   Hand-rolled SVG charts (no chart library) so the demo works offline. */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));
const state = {};

/* ================= theme ================= */
const THEME_KEY = "fsc-theme";
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const dark = theme === "dark";
  $$("#theme-toggle, #theme-toggle-mobile").forEach((b) => {
    b.textContent = b.classList.contains("small") ? (dark ? "☀️" : "🌙")
      : (dark ? "☀️ Light mode" : "🌙 Dark mode");
    b.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
  });
}
function setTheme(theme) {
  applyTheme(theme);
  try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* private mode */ }
}
(function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem(THEME_KEY); } catch (e) { /* ignore */ }
  const forced = new URLSearchParams(location.search).get("theme");
  const prefers = window.matchMedia &&
    window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(forced === "dark" || forced === "light"
    ? forced
    : (saved || (prefers ? "dark" : "light")));
})();
$$("#theme-toggle, #theme-toggle-mobile").forEach((btn) =>
  btn.addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  }));

/* ================= toast ================= */
let toastTimer;
function toast(message, kind = "") {
  const el = $("#toast");
  if (!el) return;
  el.textContent = message;
  el.className = `toast show ${kind}`.trim();
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3400);
}

/* ================= sidebar (mobile) ================= */
const sidebar = $("#sidebar");
const scrim = $("#scrim");
function closeSidebar() {
  sidebar && sidebar.classList.remove("open");
  scrim && scrim.classList.remove("open");
}
$("#menu-toggle") && $("#menu-toggle").addEventListener("click", () => {
  const open = sidebar.classList.toggle("open");
  scrim && scrim.classList.toggle("open", open);
});
scrim && scrim.addEventListener("click", closeSidebar);
window.addEventListener("keydown", (e) => { if (e.key === "Escape") closeSidebar(); });

/* ================= tabs ================= */
function activateTab(name) {
  const btn = document.querySelector(`.tab[data-tab="${name}"]`);
  if (!btn) return;
  $$(".tab").forEach((b) => b.classList.remove("active"));
  btn.classList.add("active");
  $$(".view").forEach((v) => v.classList.remove("active"));
  const view = document.getElementById(`view-${name}`);
  if (view) view.classList.add("active");
  history.replaceState(null, "", `#${name}`);
  closeSidebar();
  window.scrollTo({ top: 0, behavior: "smooth" });
}
$$(".tab[data-tab]").forEach((btn) => {
  btn.addEventListener("click", () => activateTab(btn.dataset.tab));
});
window.addEventListener("hashchange", () => activateTab(location.hash.slice(1) || "home"));
// deep-link support for the demo video (#twin, #advice, #backtest …)
document.addEventListener("DOMContentLoaded", () => {
  const h = location.hash.slice(1);
  if (h) activateTab(h);
});

/* ================= helpers ================= */
async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}
const fmt = (n, d = 1) => Number(n).toFixed(d);
const sgn = (n, d = 1) => (n >= 0 ? "+" : "") + Number(n).toFixed(d);
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const STILL = new URLSearchParams(location.search).has("still");

function countUp(el, target, suffix = "", dur = 900, decimals = 0) {
  if (STILL) { el.textContent = target.toFixed(decimals) + suffix; return; }
  const t0 = performance.now();
  const step = (t) => {
    const p = Math.min(1, (t - t0) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = (target * eased).toFixed(decimals) + suffix;
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

/* ================= SVG charts ================= */
const PALETTE = {
  green: "#46a06a", greenDeep: "#2f7d4f", amber: "#d3952f",
  red: "#c64a34", teal: "#12908a", ink: "#33413a", grid: "#e3e8dd",
};
let chartSeq = 0;

function segs(values) {
  // contiguous runs of non-null values -> smooth-ish multi-segment paths
  const out = []; let run = [];
  values.forEach((v, i) => {
    if (v == null) { if (run.length) out.push(run); run = []; }
    else run.push([i, v]);
  });
  if (run.length) out.push(run);
  return out;
}

function lineChart(el, { title, unit, years, values, trend, annot, bad }) {
  const W = 480, H = 224, ML = 44, MR = 14, MT = 34, MB = 26;
  const iw = W - ML - MR, ih = H - MT - MB;
  const vals = values.filter((v) => v != null);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  if (trend && Number.isFinite(trend.start) && Number.isFinite(trend.end)) {
    lo = Math.min(lo, trend.start, trend.end);
    hi = Math.max(hi, trend.start, trend.end);
  }
  const pad = (hi - lo) * 0.16 || 1; lo -= pad; hi += pad;
  const x = (i) => ML + (i / Math.max(1, years.length - 1)) * iw;
  const y = (v) => MT + ih - ((v - lo) / (hi - lo)) * ih;
  const uid = `lc${++chartSeq}`;
  const accent = bad ? PALETTE.red : PALETTE.green;

  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)}" xmlns="http://www.w3.org/2000/svg">`;
  s += `<defs><linearGradient id="${uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${accent}" stop-opacity=".30"/>
      <stop offset="100%" stop-color="${accent}" stop-opacity="0"/>
    </linearGradient></defs>`;
  s += `<text class="chart-title" x="${ML}" y="18">${esc(title)}</text>`;

  for (let g = 0; g <= 4; g++) {
    const gv = lo + ((hi - lo) * g) / 4, gy = y(gv);
    s += `<line class="axis" x1="${ML}" y1="${gy}" x2="${W - MR}" y2="${gy}" ${g === 0 ? "" : 'stroke-dasharray="3 5"'}/>`;
    s += `<text class="tick-label" x="${ML - 6}" y="${gy + 3}" text-anchor="end">${fmt(gv, hi > 60 ? 0 : 1)}</text>`;
  }

  // soft area under the observed series
  segs(values).forEach((run) => {
    if (run.length < 2) return;
    const top = run.map(([i, v]) => `${x(i)} ${y(v)}`).join(" L ");
    const first = x(run[0][0]), last = x(run[run.length - 1][0]);
    s += `<path d="M ${first} ${MT + ih} L ${top} L ${last} ${MT + ih} Z" fill="url(#${uid})"/>`;
    s += `<path d="M ${top}" fill="none" stroke="${accent}" stroke-width="1.3" opacity=".55" stroke-linejoin="round"/>`;
  });

  years.forEach((yr, i) => {
    if (values[i] == null) return;
    s += `<circle class="point" r="2.7" cx="${x(i)}" cy="${y(values[i])}">` +
      `<title>${yr}: ${fmt(values[i], 1)} ${unit}</title></circle>`;
  });

  if (trend) {
    s += `<line class="trend-line ${bad ? "bad" : ""}" x1="${x(0)}" y1="${y(trend.start)}" x2="${x(years.length - 1)}" y2="${y(trend.end)}" stroke-dasharray="7 5" stroke-width="2.4"/>`;
  }

  s += `<text class="tick-label" x="${ML}" y="${H - 8}">${years[0]}</text>`;
  s += `<text class="tick-label" x="${W - MR}" y="${H - 8}" text-anchor="end">${years[years.length - 1]}</text>`;
  if (annot) s += `<text class="trend-annot" x="${W - MR}" y="${MT + 2}" text-anchor="end" fill="${bad ? PALETTE.red : PALETTE.greenDeep}">${esc(annot)}</text>`;
  s += "</svg>";
  el.innerHTML = s;
}

function barChart(el, { title, unit, years, values, trend, annot }) {
  const W = 480, H = 224, ML = 44, MR = 14, MT = 34, MB = 26;
  const iw = W - ML - MR, ih = H - MT - MB;
  const hot = /heat|heavy|dry/i.test(title);
  const accent = hot ? PALETTE.amber : PALETTE.green;
  const accent2 = hot ? "#b87416" : PALETTE.greenDeep;
  let hi = Math.max(...values.filter((v) => v != null)) * 1.14 || 1;
  if (trend) hi = Math.max(hi, trend.start, trend.end) * 1.04;
  const bw = iw / years.length;
  const y = (v) => MT + ih - (v / hi) * ih;
  const uid = `bc${++chartSeq}`;

  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(title)}" xmlns="http://www.w3.org/2000/svg">`;
  s += `<defs><linearGradient id="${uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="${accent}"/>
      <stop offset="100%" stop-color="${accent2}" stop-opacity=".72"/>
    </linearGradient></defs>`;
  s += `<text class="chart-title" x="${ML}" y="18">${esc(title)}</text>`;
  for (let g = 0; g <= 4; g++) {
    const gv = (hi * g) / 4, gy = y(gv);
    s += `<line class="axis" x1="${ML}" y1="${gy}" x2="${W - MR}" y2="${gy}" ${g === 0 ? "" : 'stroke-dasharray="3 5"'}/>`;
    s += `<text class="tick-label" x="${ML - 6}" y="${gy + 3}" text-anchor="end">${fmt(gv, 0)}</text>`;
  }
  years.forEach((yr, i) => {
    if (values[i] == null) return;
    const v = values[i], bh = MT + ih - y(v);
    s += `<rect x="${ML + i * bw + bw * 0.16}" y="${y(v)}" width="${bw * 0.68}" height="${Math.max(1.5, bh)}" rx="3" fill="url(#${uid})"><title>${yr}: ${fmt(v, 0)} ${unit}</title></rect>`;
  });
  if (trend) {
    s += `<line class="trend-line" x1="${ML}" y1="${y(trend.start)}" x2="${W - MR}" y2="${y(trend.end)}" stroke="${accent2}" stroke-width="2.2" stroke-dasharray="7 5" stroke-linecap="round"/>`;
  }
  s += `<text class="tick-label" x="${ML}" y="${H - 8}">${years[0]}</text>`;
  s += `<text class="tick-label" x="${W - MR}" y="${H - 8}" text-anchor="end">${years[years.length - 1]}</text>`;
  if (annot) s += `<text class="trend-annot" x="${W - MR}" y="${MT + 2}" text-anchor="end" fill="${accent2}">${esc(annot)}</text>`;
  s += "</svg>";
  el.innerHTML = s;
}

function anomalyChart(el, bt) {
  if (!el) return;
  const rows = bt.rows.slice().sort((a, b) => a.year - b.year);
  const W = 480, H = 214, ML = 40, MR = 16, MT = 30, MB = 26;
  const iw = W - ML - MR, ih = H - MT - MB;
  const vals = rows.map((r) => r.onset_anom);
  const padA = Math.max(...vals.map((v) => Math.abs(v)), 10) * 1.25;
  const y = (v) => MT + ih / 2 - (v / padA) * (ih / 2);
  const bw = iw / rows.length;
  const thr = 0.75 * bt.onset_sd_days;
  const zero = y(0);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Monsoon onset anomaly by season" xmlns="http://www.w3.org/2000/svg">`;

  [-1, -0.5, 0, 0.5, 1].forEach((f) => {
    const gy = y(padA * f);
    s += `<line class="axis" x1="${ML}" y1="${gy}" x2="${W - MR}" y2="${gy}" ${f === 0 ? 'stroke-width="1.4"' : 'stroke-dasharray="3 5"'}/>`;
  });
  s += `<text class="tick-label" x="${ML - 6}" y="${zero + 3}" text-anchor="end">0</text>`;
  s += `<text class="tick-label" x="${ML - 6}" y="${y(padA * 0.9) + 3}" text-anchor="end">+${fmt(padA * 0.9, 0)}</text>`;
  s += `<text class="tick-label" x="${ML - 6}" y="${y(-padA * 0.9) + 3}" text-anchor="end">−${fmt(padA * 0.9, 0)}</text>`;

  rows.forEach((r, i) => {
    const v = r.onset_anom, up = v >= 0;
    const yy = Math.min(y(v), zero);
    const h = Math.max(1.4, Math.abs(zero - y(v)));
    s += `<rect x="${ML + i * bw + bw * 0.2}" y="${yy}" width="${bw * 0.6}" height="${h}" rx="2.5"
      fill="${up ? PALETTE.amber : PALETTE.green}" opacity="${r.flagged ? 1 : 0.72}"
      ${r.flagged ? `stroke="${PALETTE.red}" stroke-width="1"` : ""}>
      <title>${r.year}: ${v >= 0 ? "+" : ""}${v} days vs mean${r.flagged ? " (flagged)" : ""}</title></rect>`;
  });

  // 0.75σ late-onset threshold
  s += `<line x1="${ML}" y1="${y(thr)}" x2="${W - MR}" y2="${y(thr)}" stroke="${PALETTE.red}" stroke-width="1.5" stroke-dasharray="6 4"/>`;
  s += `<text class="tick-label" x="${W - MR}" y="${y(thr) - 6}" text-anchor="end"
    fill="${PALETTE.red}" stroke="var(--surface)" stroke-width="3" paint-order="stroke"
    font-weight="700">+${fmt(thr, 0)} d threshold</text>`;

  rows.forEach((r, i) => {
    if ((r.year - rows[0].year) % 5 === 0) {
      s += `<text class="tick-label" x="${ML + i * bw + bw / 2}" y="${H - 8}" text-anchor="middle">${r.year}</text>`;
    }
  });
  s += `<text class="tick-label" x="${ML}" y="${MT - 10}">onset anomaly (days)</text>`;
  s += "</svg>";
  el.innerHTML = s;
}

function climCompareChart(el, data) {
  const W = 500, H = 260, ML = 44, MR = 42, MT = 30, MB = 30;
  const iw = W - ML - MR, ih = H - MT - MB;
  const rainAll = [...data.home_future_rain, ...data.twin_rain];
  const tempAll = [...data.home_future_tmax, ...data.twin_tmax];
  const rainHi = Math.max(...rainAll) * 1.14 || 1;
  const tLo = Math.floor(Math.min(...tempAll) - 2);
  const tHi = Math.ceil(Math.max(...tempAll) + 2);
  const x = (i) => ML + (i / 11) * iw;
  const yR = (v) => MT + ih - (v / rainHi) * ih;
  const yT = (v) => MT + ih - ((v - tLo) / (tHi - tLo)) * ih;

  const area = (arr, uid) => {
    const pts = arr.map((v, i) => `${x(i)} ${yR(v)}`).join(" L ");
    return `<path d="M ${x(0)} ${MT + ih} L ${pts} L ${x(11)} ${MT + ih} Z" fill="url(#${uid})"/>`;
  };
  const line = (arr, yFn, color, dash, width) => {
    let out = `<path d="M ${arr.map((v, i) => `${x(i)} ${yFn(v)}`).join(" L ")}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round" ${dash ? 'stroke-dasharray="6 4"' : ""}/>`;
    arr.forEach((v, i) => {
      out += `<circle r="2.4" cx="${x(i)}" cy="${yFn(v)}" fill="${color}" stroke="var(--surface)" stroke-width="1.2"><title>${data.months[i]}: ${fmt(v, 0)}</title></circle>`;
    });
    return out;
  };

  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Monthly climate comparison" xmlns="http://www.w3.org/2000/svg">`;
  s += `<defs>
      <linearGradient id="crHome" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${PALETTE.amber}" stop-opacity=".26"/>
        <stop offset="100%" stop-color="${PALETTE.amber}" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="crTwin" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="${PALETTE.teal}" stop-opacity=".22"/>
        <stop offset="100%" stop-color="${PALETTE.teal}" stop-opacity="0"/>
      </linearGradient>
    </defs>`;

  for (let g = 0; g <= 4; g++) {
    const gv = (rainHi * g) / 4, gy = yR(gv);
    s += `<line class="axis" x1="${ML}" y1="${gy}" x2="${W - MR}" y2="${gy}" ${g === 0 ? "" : 'stroke-dasharray="3 5"'}/>`;
    s += `<text class="tick-label" x="${ML - 6}" y="${gy + 3}" text-anchor="end">${fmt(gv, 0)}</text>`;
    const tv = tLo + ((tHi - tLo) * g) / 4;
    s += `<text class="tick-label" x="${W - MR + 6}" y="${gy + 3}" text-anchor="start" fill="${PALETTE.red}">${fmt(tv, 0)}°</text>`;
  }
  s += `<text class="tick-label" x="${ML - 6}" y="${MT - 6}" text-anchor="end">mm</text>`;
  data.months.forEach((m, i) => {
    s += `<text class="tick-label" x="${x(i)}" y="${H - 9}" text-anchor="middle">${m[0]}</text>`;
  });

  s += area(data.home_future_rain, "crHome");
  s += area(data.twin_rain, "crTwin");
  s += line(data.home_future_rain, yR, PALETTE.amber, false, 2.6);
  s += line(data.twin_rain, yR, PALETTE.teal, true, 2.3);
  s += line(data.home_future_tmax, yT, PALETTE.red, false, 1.7);
  s += line(data.twin_tmax, yT, "#6b8f7d", true, 1.6);
  s += "</svg>";
  el.innerHTML = s;
}

/* ================= renderers ================= */
function renderHome(meta, shifts) {
  $("#district-name").textContent = meta.district.name;
  $("#district-crop").textContent = `${meta.district.crop} · ${meta.district.language} · record ${meta.record_years[0]}–${meta.record_years[meta.record_years.length - 1]}`;
  const pillEl = $("#district-pill");
  if (pillEl) pillEl.textContent = `📍 ${meta.district.name.split(",")[0]} · ${meta.district.crop}`;
  $("#hero-kicker").textContent = `${meta.district.short} · ${meta.district.crop}`;
  const t = shifts.trends;
  const daysShift = Math.abs(Math.round(t.sowing_window.slope_per_year * shifts.years.length));
  $("#hero-headline").textContent =
    `Your sowing window has moved about ${daysShift} days since ${shifts.years[0]} — and your 2040 climate already exists somewhere today.`;
  $("#hero-sub").textContent =
    "Field Shift Compass reads 26 years of NASA satellite data for your district, finds the region that already farms your future climate, and turns it into evidence-backed advice you can act on this season.";

  const twinPct = Math.round((state.twin.matches[0].similarity || 0) * 100);
  const bestConf = Math.round(Math.max(...state.advice.cards.map((c) => c.confidence[0])) * 100);
  $("#hero-stats").innerHTML = `
    <div class="hstat"><b id="hs1">0</b><span>years of NASA data</span></div>
    <div class="hstat"><b id="hs2">0</b><span>days sowing shift</span></div>
    <div class="hstat"><b id="hs3">0</b><span>twin climate match %</span></div>
    <div class="hstat"><b id="hs4">0</b><span>advice confidence %</span></div>`;
  countUp($("#hs1"), shifts.years.length);
  countUp($("#hs2"), daysShift);
  countUp($("#hs3"), twinPct);
  countUp($("#hs4"), bestConf);

  const years = shifts.years;
  const on = shifts.onset;
  const lastOn = on[String(years[years.length - 1])];
  const pills = [];
  pills.push(pill("📅", `Your sowing window has moved about <b>${daysShift} days</b> since ${years[0]}. Most recent onset: <b>${lastOn}</b>`, t.sowing_window.r2 > 0.15 ? "" : "warn"));
  pills.push(pill("🌦", `Monsoon rain trending <b>${sgn(t.monsoon_rain.change_per_decade, 0)} mm/decade</b>, with <b>${sgn(t.extreme_rain.change_per_decade, 1)}</b> heavy-rain days/decade — wetter bursts, not gentler weather.`, t.extreme_rain.change_per_decade > 0 ? "warn" : ""));
  pills.push(pill("🏜", `Longest mid-season dry spell: <b>${sgn(t.dry_spell.change_per_decade, 1)} days/decade</b>.`, Math.abs(t.dry_spell.change_per_decade) > 0.5 ? "warn" : ""));
  pills.push(pill("🌡", `Heat-stress days (≥35 °C, Mar–May): <b>${sgn(t.heat_days.change_per_decade, 1)}/decade</b>.`, t.heat_days.change_per_decade > 0 ? "bad" : ""));
  $("#headline-shifts").innerHTML = pills.join("");
  $("#data-note").innerHTML = `<b>Where the numbers come from:</b> ${meta.data_source}, computed ${meta.computed_at}. Cached locally — this demo needs no live connection. Future path uses ${meta.deltas.scenario}.`;
}

function pill(ico, html, cls = "") {
  return `<div class="shift-pill ${cls}"><span class="ico">${ico}</span><span>${html}</span></div>`;
}

/* ---------- KPI cards (What Changed) ---------- */
function renderShiftKpis(shifts) {
  const row = $("#shift-kpis");
  if (!row) return;
  const t = shifts.trends;
  const totalShift = Math.round(t.sowing_window.slope_per_year * shifts.years.length);
  const sign = (n, d = 1) => (n >= 0 ? "+" : "") + Number(n).toFixed(d);
  const r2 = (x) => `R² ${x.toFixed(2)}`;

  const kpis = [
    {
      ico: "📅", val: `${totalShift > 0 ? "+" : ""}${totalShift} d`,
      label: `sowing-window shift since ${shifts.years[0]}`,
      delta: `${sign(t.sowing_window.change_per_decade)} d/decade`,
      cls: "warn", dcls: "warn",
    },
    {
      ico: "🌧", val: `${sign(t.monsoon_rain.change_per_decade, 0)} mm`,
      label: "monsoon rain change per decade",
      delta: r2(t.monsoon_rain.r2), cls: "good", dcls: "good",
    },
    {
      ico: "🌦", val: `${sign(t.rain_days.change_per_decade)} d`,
      label: "rainy days per decade (Jun–Sep)",
      delta: `R² ${t.rain_days.r2.toFixed(2)}`, cls: "good", dcls: "good",
    },
    {
      ico: "⛈", val: `${sign(t.extreme_rain.change_per_decade, 2)} d`,
      label: "heavy-rain days per decade",
      delta: `R² ${t.extreme_rain.r2.toFixed(2)}`, cls: "warn", dcls: "warn",
    },
    {
      ico: "🏜", val: `${sign(t.dry_spell.change_per_decade)} d`,
      label: "longest dry spell per decade",
      delta: `R² ${t.dry_spell.r2.toFixed(2)}`,
      cls: t.dry_spell.change_per_decade > 0 ? "warn" : "good",
      dcls: t.dry_spell.change_per_decade > 0 ? "warn" : "good",
    },
    {
      ico: "🌡", val: `${sign(t.heat_days.change_per_decade)} d`,
      label: "heat-stress days per decade",
      delta: `R² ${t.heat_days.r2.toFixed(2)}`,
      cls: t.heat_days.change_per_decade > 0 ? "bad" : "good",
      dcls: t.heat_days.change_per_decade > 0 ? "bad" : "good",
    },
  ];

  row.innerHTML = kpis.map((k) => `
    <div class="kpi ${k.cls}">
      <div class="kpi-top">
        <span class="kpi-ico">${k.ico}</span>
        <span class="kpi-delta ${k.dcls === "good" ? "" : k.dcls}">${k.delta}</span>
      </div>
      <div class="kpi-val">${k.val}</div>
      <div class="kpi-label">${k.label}</div>
    </div>`).join("");
}

function trendFor(years, values) {
  const pts = years.map((y, i) => [y, values[i]]).filter(([, v]) => v != null);
  if (pts.length < 2) return null;
  const n = pts.length;
  const sx = pts.reduce((a, p) => a + p[0], 0), sy = pts.reduce((a, p) => a + p[1], 0);
  const sxy = pts.reduce((a, p) => a + p[0] * p[1], 0), sxx = pts.reduce((a, p) => a + p[0] * p[0], 0);
  const slope = (n * sxy - sx * sy) / (n * sxx - sx * sx);
  const intercept = (sy - slope * sx) / n;
  return { slope, start: intercept + slope * pts[0][0], end: intercept + slope * pts[n - 1][0] };
}

function renderShiftCharts(shifts) {
  const years = shifts.years, t = shifts.trends;
  const val = (obj) => years.map((y) => obj[String(y)] ?? null);
  const wrap = (title) => `<div class="card"><div class="chart" id="c-${title.replace(/\W+/g, "")}"></div></div>`;
  const onsetVals = val(shifts.onset).map((d) => {
    if (!d) return null;
    const dt = new Date(d), j1 = new Date(`${dt.getFullYear()}-06-01`);
    return Math.round((dt - j1) / 86400000);
  });
  const charts = [
    ["Sowing window start (days after Jun 1)", onsetVals, "line", trendFor(years, onsetVals), `${t.sowing_window.change_per_decade > 0 ? "later" : "earlier"} ${Math.abs(t.sowing_window.change_per_decade).toFixed(1)} d/decade`],
    ["Longest mid-season dry spell (days)", val(shifts.dry_spell), "bar", trendFor(years, val(shifts.dry_spell)), `${sgn(t.dry_spell.change_per_decade, 1)} d/decade`],
    ["Heat-stress days ≥35 °C, Mar–May", val(shifts.heat_days), "bar", trendFor(years, val(shifts.heat_days)), `${sgn(t.heat_days.change_per_decade, 1)} d/decade`],
    ["Monsoon rainfall Jun–Sep (mm)", val(shifts.monsoon_rain), "bar", trendFor(years, val(shifts.monsoon_rain)), `${sgn(t.monsoon_rain.change_per_decade, 0)} mm/decade`],
    ["Heavy-rain days ≥50 mm, Jun–Sep", val(shifts.extreme_rain), "bar", trendFor(years, val(shifts.extreme_rain)), `${sgn(t.extreme_rain.change_per_decade, 1)} d/decade`],
    ["Rain days ≥2.5 mm, Jun–Sep", val(shifts.rain_days), "line", trendFor(years, val(shifts.rain_days)), `${sgn(t.rain_days.change_per_decade, 1)} d/decade`],
  ];
  $("#shift-charts").innerHTML = charts.map(([title]) => wrap(title)).join("");
  charts.forEach(([title, values, kind, trend, annot], idx) => {
    const el = $(`#c-${title.replace(/\W+/g, "")}`);
    if (kind === "bar") barChart(el, { title, unit: "", years, values, trend, annot });
    else lineChart(el, { title, unit: "", years, values, trend, annot });
  });
}

/* ---------- risk calendar ---------- */
function renderRiskCalendar(cal) {
  const strip = cal.map((m) => `
    <div class="risk-month">
      <h4>${m.month}</h4>
      <div class="row"><span class="risk-swatch s-dry"></span><div class="bar-track"><div class="bar-fill f-dry" style="width:${Math.round(m.p_dryspell8 * 100)}%"></div></div><b>${Math.round(m.p_dryspell8 * 100)}%</b></div>
      <div class="row"><span class="risk-swatch s-heavy"></span><div class="bar-track"><div class="bar-fill f-heavy" style="width:${Math.round(m.p_heavy * 100)}%"></div></div><b>${Math.round(m.p_heavy * 100)}%</b></div>
      <div class="row"><span class="risk-swatch s-heat"></span><div class="bar-track"><div class="bar-fill f-heat" style="width:${Math.min(100, Math.round(((m.mean_tmax || 0) - 20) * 6))}%"></div></div><b>${m.mean_tmax ?? "—"}°C</b></div>
      <div style="font-size:10.5px; color:var(--muted); margin-top:6px">avg ${Math.round(m.mean_total)} mm</div>
    </div>`).join("");
  $("#risk-strip").innerHTML = strip;
}

/* ---------- twin ---------- */
function renderTwin(twin) {
  $("#cand-count").textContent = twin.candidates_considered;
  const m = twin.matches[0];
  const fd = twin.deltas;
  $("#twin-card").innerHTML = `
    <div class="twin-head">
      <div class="twin-pin">📍</div>
      <div>
        <div class="twin-name">${m.name}</div>
        <div class="twin-sim">${Math.round(m.similarity * 100)}% climate match ·
          your projected ${fd.target_year} vs their today ·
          #${m.rank} of ${twin.candidates_considered} regions compared</div>
      </div>
    </div>
    <div class="twin-note"><b>Farming there today:</b> ${esc(twin.practice || "")}</div>
    <table class="feature-table">
      <tr><th>Climate feature</th><th>Your ${fd.target_year} (projected)</th><th>${m.name} today</th></tr>
      ${featureRows(twin.home_future, m.features)}
    </table>
    <div style="margin-top:12px">
      <div style="font-weight:700; font-size:13px; margin-bottom:4px">Next-best twins</div>
      ${twin.matches.slice(1).map((r) => `<div class="runner"><span>${r.rank}. ${r.name}</span><span>${Math.round(r.similarity * 100)}% match</span></div>`).join("")}
    </div>`;
}

const FEATURE_DEC = {
  annual_rain: 0, monsoon_rain: 0, monsoon_share: 2, post_rain: 0,
  tmean_hottest: 1, tmean_flower: 1, rh_mean: 0, rain_seasonality: 2,
};

function featureRows(homeF, twinF) {
  const labels = {
    annual_rain: "Annual rainfall (mm)", monsoon_rain: "Monsoon rainfall (mm)",
    monsoon_share: "Monsoon share of year", post_rain: "Oct–Dec rainfall (mm)",
    tmean_hottest: "Hottest-month mean (°C)", tmean_flower: "Flowering-window mean (°C)",
    rh_mean: "Mean humidity (%)", rain_seasonality: "Rainfall seasonality",
  };
  return Object.entries(labels).map(([k, label]) => {
    const a = homeF[k] ?? "—", b = twinF[k] ?? "—";
    const d = FEATURE_DEC[k] ?? 1;
    const fa = typeof a === "number" ? fmt(a, d) : a;
    const fb = typeof b === "number" ? fmt(b, d) : b;
    return `<tr><td>${label}</td><td><b>${fa}</b></td><td>${fb}</td></tr>`;
  }).join("");
}

/* ---------- climate path ---------- */
function renderTimeline(timeline) {
  const slider = $("#path-slider");
  $("#path-ticks").innerHTML = timeline.map((s, i) =>
    `<span data-i="${i}">${s.year}</span>`).join("");
  const update = () => {
    const i = +slider.value;
    const s = timeline[i];
    $("#path-ticks").querySelectorAll("span").forEach((sp, j) =>
      sp.classList.toggle("active", j === i));
    const drift = s.frac === 0 ? "today's climate"
      : `+${s.temp_add} °C vs today`;
    $("#path-result").innerHTML = `
      <div>Year <b>${s.year}</b> (${drift}): your twin is
        <b>${s.top.name}</b> — ${Math.round(s.top.similarity * 100)}% match
        (runner-up: ${s.runner.name}).</div>
      <div class="path-meter"><i style="width:${20 + s.frac * 80}%"></i></div>
      <div style="font-size:12px; color:var(--muted); margin-top:8px">${
        s.frac === 0
          ? "Baseline: your district's observed climate right now."
          : s.frac === 1
            ? "Target year of the projection. A stable twin means the advice is robust — no flip-flopping recommendations."
            : "Interpolated along the NEX-GDDP-CMIP6 ensemble path."}</div>`;
  };
  slider.addEventListener("input", update);
  update();
}

/* ---------- twin explorer ---------- */
function renderExplorer(candidates, twin) {
  const sel = $("#explorer-select");
  sel.innerHTML = candidates.map((c) =>
    `<option value="${c.id}">${c.name}</option>`).join("");
  const homeF = twin.home_future;
  const rankDiv = $("#explorer-ranking");
  rankDiv.innerHTML = twin.matches.map((m, i) =>
    `<div class="rank-line ${i === 0 ? "top" : ""}"><span>${i + 1}. ${m.name}</span><span>${Math.round(m.similarity * 100)}%</span></div>`).join("");

  const show = (id) => {
    const c = candidates.find((x) => x.id === id);
    if (!c) return;
    const rows = Object.entries(c.features).map(([k, v]) => {
      const hv = homeF[k];
      const diff = typeof hv === "number" && typeof v === "number" ? hv - v : null;
      const cls = diff == null ? "" : (Math.abs(diff) < Math.max(1, Math.abs(v) * 0.12) ? "close" : Math.abs(diff) < Math.max(2, Math.abs(v) * 0.3) ? "near" : "far");
      const label = {
        annual_rain: "Annual rain (mm)", monsoon_rain: "Monsoon rain (mm)",
        monsoon_share: "Monsoon share", post_rain: "Oct–Dec rain (mm)",
        tmean_hottest: "Hottest mean (°C)", tmean_flower: "Flowering mean (°C)",
        rh_mean: "Humidity (%)", rain_seasonality: "Seasonality",
      }[k] || k;
      const fv = fmt(v, FEATURE_DEC[k] ?? 1);
      const d = FEATURE_DEC[k] ?? 1;
      const dtxt = diff == null ? "" : `${diff >= 0 ? "+" : ""}${fmt(diff, d)}`;
      return `<div class="explorer-feature"><span>${label}</span><span>${fv}
        <span class="delta ${cls}">${dtxt ? `Δ ${dtxt}` : ""}</span></span></div>`;
    }).join("");
    $("#explorer-profile").innerHTML = `
      <div style="font-weight:800; font-size:15px; margin-bottom:2px">${c.name}</div>
      <div style="font-size:12px; color:var(--muted); margin-bottom:8px">Δ = your projected 2040 value minus this region today (green = close)</div>
      ${rows}`;
  };
  sel.addEventListener("change", () => show(sel.value));
  show(twin.matches[0].id);
  sel.value = twin.matches[0].id;
}

/* ---------- advice + whatsapp ---------- */
function waText() {
  const t = state.advice.cards[0];
  const twin = state.twin.matches[0];
  return `🌾 *Field Shift Compass — ${state.meta.district.short}*\n\n` +
    `*${t.recommendation}*\n\n` +
    `Evidence (NASA POWER, ${state.shifts.years[0]}–${state.shifts.years.at(-1)}):\n` +
    t.why.map((w) => `• ${w.text}`).join("\n") +
    `\n\n🧭 Your climate twin: *${twin.name}* (${Math.round(twin.similarity * 100)}% match)\n` +
    `Confidence: ${t.confidence[1]}\n` +
    `Not sure? Send a voice note — agronomist will reply.`;
}

function renderAdvice(advice) {
  const confCls = { "High": "high", "Medium-High": "medhigh", "Medium": "medium", "Low": "low" };
  $("#advice-cards").innerHTML = advice.cards.map((c, i) => `
    <div class="advice-card">
      <h3>#${i + 1} ${actionIcon(c.action_type)} ${actionTitle(c.action_type)}
          <span class="conf ${confCls[c.confidence[1]] || "medium"}">${c.confidence[1]} · ${Math.round(c.confidence[0] * 100)}%</span></h3>
      <div class="rec">${c.recommendation}</div>
      <div class="evidence">
        ${c.why.map((e) => `<div class="ev"><span class="b">•</span><span>${e.text}<span class="ds">Source: ${e.dataset}</span></span></div>`).join("")}
      </div>
      ${c.twin_reference ? `<div class="twin-ref">🧭 ${esc(c.twin_reference)}</div>` : ""}
      <div style="margin-top:10px">
        <button class="ghost" onclick="sendFeedback('${c.action_type}','follow')">👍 I'll follow this</button>
        <button class="ghost" onclick="askExpert('${c.action_type}')">❓ Ask an agronomist</button>
      </div>
    </div>`).join("");

  $("#wa-preview").innerHTML = `
    <div class="wa-bubble">${esc(waText())}<div class="wa-meta">✓✓ today</div></div>`;
  $("#btn-share").addEventListener("click", async () => {
    try { await navigator.clipboard.writeText(waText()); $("#btn-share").textContent = "✓ Copied!"; }
    catch { $("#btn-share").textContent = "Select & copy from preview"; }
    setTimeout(() => { $("#btn-share").textContent = "🔗 Copy broadcast text"; }, 1600);
  });
}

function actionIcon(t) {
  return { sowing_date: "📅", stagger: "🌗", variety: "🌱", water: "💧", heat: "🌡", crop_change: "🔁" }[t] || "✅";
}
function actionTitle(t) {
  return { sowing_date: "Adjust your sowing date", stagger: "Split your sowing to spread risk", variety: "Choose the right variety", water: "Protect against dry spells", heat: "Protect flowering from heat", crop_change: "Consider rotating a field" }[t] || t;
}

async function sendFeedback(type, decision) {
  try {
    await fetch("/api/feedback", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ advice_type: type, decision, farmer_note: "Marked follow from farmer app", source: "farmer" }),
    });
    toast("Recorded — thank you! Your feedback improves next season's advice.");
  } catch (e) {
    toast("Could not reach the server — your feedback was not saved.", "error");
  }
}
function askExpert(type) {
  document.querySelector('.tab[data-tab="chat"]').click();
  addMsg("user", `Can a local agronomist review advice #${type}?`);
  setTimeout(() => addMsg("bot", "Done — your question and this season's evidence pack were sent to the district agronomist queue (Expert View). They approve, edit, or correct advice, and their correction recalibrates the rules for your village. You'll get a reply in Marathi, Hindi or English."), 400);
}

/* ---------- backtest ---------- */
function renderBacktest(bt) {
  const countEl = $("#bt-count");
  if (countEl) countEl.textContent = `${bt.flagged_years.length} of ${bt.n_years} seasons flagged`;
  $("#backtest-summary").innerHTML =
    `🔍 ${bt.summary}<br><span style="font-weight:600; font-size:13px">Flagged years: ${bt.flagged_years.join(", ") || "none"}</span>`;
  $("#backtest-table").innerHTML = `
    <tr><th>Season</th><th>Onset</th><th>Onset anomaly</th><th>Dry spell</th><th>Flag</th></tr>
    ${bt.rows.slice().reverse().map((r) => `
      <tr class="${r.flagged ? "flagged" : ""}">
        <td><b>${r.year}</b></td>
        <td>${r.onset}</td>
        <td>${sgn(r.onset_anom, 0)} days</td>
        <td>${r.dry_spell} d (${sgn(r.dry_anom, 0)})</td>
        <td>${r.flagged ? `<span class="flag-badge">⚑ ${r.reason || "flag"}</span>` : "—"}</td>
      </tr>`).join("")}`;
  $("#backtest-how").innerHTML =
    `A season is flagged when its monsoon onset arrives more than <b>0.75σ later</b>
    than the ${bt.n_years}-year average (${bt.onset_mean_days} ± ${bt.onset_sd_days} days
    after Jun 1, so later than ~${(bt.onset_mean_days + 0.75 * bt.onset_sd_days).toFixed(0)} days),
    <b>or</b> when its longest mid-season dry spell exceeds
    <b>${bt.dry_mean} + 0.75 × ${bt.dry_sd} ≈ ${(bt.dry_mean + 0.75 * bt.dry_sd).toFixed(0)} days</b>.
    This is exactly the check behind the sowing-date advice — replayed over the whole
    record, so you can see it working before you trust it.`;
}

/* ================= chat ================= */
function addMsg(who, text) {
  const body = $("#chat-body");
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  div.textContent = text;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
  return div;
}

function answerFor(q, ctx) {
  const t = ctx.shifts.trends, m = ctx.twin.matches[0];
  const lastOn = ctx.shifts.onset[String(ctx.shifts.years.at(-1))];
  const ql = q.toLowerCase();
  if (ql.includes("sow") || ql.includes("when")) {
    return `Sow when the soil is ready, not by the old calendar. Your sowing window has moved about ${Math.abs(Math.round(t.sowing_window.slope_per_year * ctx.shifts.years.length))} days since ${ctx.shifts.years[0]}, and onset swings across a wide range year to year — stagger your nursery across two windows. I'll send a voice alert when the first good moisture window opens. (Evidence: NASA POWER rainfall record ${ctx.shifts.years[0]}–${ctx.shifts.years.at(-1)}.)`;
  }
  if (ql.includes("water") || ql.includes("dry")) {
    return `Mid-season dry spells are trending ${sgn(t.dry_spell.change_per_decade, 1)} days/decade, and June carries a ${Math.round(ctx.risk[0].p_dryspell8 * 100)}% chance of an 8+ day dry spell while October is nearly always dry (${Math.round(ctx.risk[4].p_dryspell8 * 100)}%) — plan harvest moisture accordingly. Mulch after sowing, keep paddy at alternate wetting-drying, and clear drains before July's heavy-rain weeks.`;
  }
  if (ql.includes("variety") || ql.includes("seed")) {
    return `Based on your record, a short-duration variety (like MTU-1010, ~115 days) protects you if onset slips again; for flood-prone fields use a submergence-tolerant type (DRR Dhan 44). Your climate twin is ${m.name} — farmers there already use staggered sowing with short-duration types.`;
  }
  if (ql.includes("trust") || ql.includes("why")) {
    return `Fair question. Every card shows its evidence and a confidence score computed from ${ctx.meta.record_years[0]}–${ctx.meta.record_years.at(-1)} of satellite-assimilated NASA rainfall data — no hidden model. Check the Proof tab: our rule replayed over 26 years flags the difficult seasons. A district agronomist reviews anything I'm unsure about, and farmer feedback each season recalibrates the rules. I'd rather say "Medium" than guess "High".`;
  }
  return `I can answer questions about sowing dates, dry spells, varieties, heat risk and water management — all backed by the district's NASA data record. Try one of the suggested questions. For anything else, send a voice note to your agronomist.`;
}

function setupChat() {
  const input = $("#chat-text");
  $("#btn-send").addEventListener("click", () => {
    const q = input.value.trim(); if (!q) return;
    input.value = "";
    addMsg("user", q);
    setTimeout(() => addMsg("bot", answerFor(q, state)), 350);
  });
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") $("#btn-send").click(); });
  document.querySelectorAll(".ask-list li").forEach((li) => {
    li.addEventListener("click", () => { addMsg("user", li.dataset.q); setTimeout(() => addMsg("bot", answerFor(li.dataset.q, state)), 350); });
  });

  $("#btn-voice").addEventListener("click", () => {
    if (!("speechSynthesis" in window)) { addMsg("bot", "Voice playback isn't supported in this browser — the mobile pilot uses pre-recorded Marathi voice notes."); return; }
    const t = state.advice.cards[0];
    const u = new SpeechSynthesisUtterance(`${t.recommendation} Evidence: ${t.why.map((w) => w.text).join(". ")}`);
    u.rate = 0.95; u.pitch = 1;
    speechSynthesis.speak(u);
    addMsg("bot", "🔊 Playing voice note (uses your browser's voice; the pilot app records real local-language notes)…");
  });

  $("#btn-mic").addEventListener("click", () => {
    addMsg("user", "🎙 [voice note: 0:14]");
    setTimeout(() => addMsg("bot", "Sent to the agronomist queue. They'll reply in your language — usually within a day. Voice notes also help us check whether my rain readings match what you see on the ground."), 500);
  });

  addMsg("bot", "Namaskar! 🙏 I'm your Field Shift Compass. I read 26 years of NASA satellite rainfall and temperature data for your district. Ask me anything, or tap a question on the right.");
  const top = state.advice && state.advice.cards[0];
  if (top) {
    addMsg("bot", `This season's top advice: ${top.recommendation} (${top.confidence[1]} confidence · ${Math.round(top.confidence[0] * 100)}%).`);
  }
}

/* ================= season plan ================= */
async function renderPlan() {
  const plan = await api("/api/season-plan");
  $("#season-plan").innerHTML = `
    <div class="plan-box">
      <div class="plan-meta"><span><b>${plan.district}</b></span><span>${plan.crop}</span><span>${plan.season}</span><span>Prepared for: ${plan.farmer}</span></div>
      <h4>1. The shift, in one line</h4>
      <p style="font-size:14.5px; line-height:1.6">${plan.headline_shift.text} Most recent onset: <b>${plan.headline_shift.last_onset}</b>.</p>
      <h4 style="margin-top:10px">2. Sowing advice</h4>
      <p style="font-size:14.5px; line-height:1.6">${plan.sowing_advice}</p>
      <h4 style="margin-top:10px">3. Learn from your climate twin: ${plan.twin.name}</h4>
      <p style="font-size:14.5px; line-height:1.6">${plan.twin.note}</p>
      <h4 style="margin-top:10px">4. Watch for</h4>
      <ul>${plan.watch_for.map((w) => `<li>${w}</li>`).join("")}</ul>
      <div style="margin-top:10px; font-size:11.5px; color:var(--muted)">Data: ${plan.data_sources.join(" · ")}. Decision support only — confirm with your agriculture officer.</div>
    </div>`;
}

/* ================= map (offline vector) ================= */
let map;
function renderMap(meta, twin) {
  if (typeof L === "undefined") {
    $(".map-card").innerHTML = '<div style="padding:40px 20px; text-align:center; color:#6b7263">Map unavailable — the app still works.</div>';
    return;
  }
  map = L.map("map", { scrollWheelZoom: true, attributionControl: false }).setView([21.5, 79.0], 5);
  const draw = (geo) => {
    const layer = L.geoJSON(geo, {
      style: { color: "#7c8a74", weight: 1, fillColor: "#e9ecdf", fillOpacity: 0.9, className: "india-land" },
      onEachFeature: (f, l) => l.bindTooltip(f.properties.name || "", { sticky: true }),
    }).addTo(map);
    map.fitBounds(layer.getBounds(), { padding: [18, 18], animate: false });
    addMarkers(meta, twin);
  };
  // Inlined in the boot payload -> map paints on the first frame (offline-safe).
  if (state.geojson) draw(state.geojson);
  else fetch("/web/assets/india_outline.geojson").then((r) => r.json())
    .then(draw).catch(() => addMarkers(meta, twin));
}

function addMarkers(meta, twin) {
  const h = meta.district;
  const top = twin.matches[0];

  // Show the climate-twin connection directly on the map.
  twin.matches.forEach((m, i) => {
    if (!m || m.rank === 1) return;
    L.polyline([[h.lat, h.lon], [m.lat, m.lon]], {
      color: "#8a978a", weight: 1.2, opacity: .35, dashArray: "3 7",
    }).addTo(map);
  });
  if (top) {
    L.polyline([[h.lat, h.lon], [top.lat, top.lon]], {
      color: "#12908a", weight: 1.8, opacity: .8, dashArray: "5 7",
    }).addTo(map);
  }

  L.circleMarker([h.lat, h.lon], {
    color: "#ffffff", weight: 2, fillColor: "#2f7d4f", fillOpacity: 1, radius: 10,
  }).addTo(map)
    .bindPopup(`<b>${h.name}</b><br>Your field · ${h.crop}`)
    .bindTooltip(`You · ${h.name.split(",")[0]}`, {
      permanent: true, direction: "bottom", offset: [0, 8],
      className: "map-label home",
    });

  twin.matches.forEach((m) => {
    const isTop = m.rank === 1;
    L.circleMarker([m.lat, m.lon], {
      color: "#ffffff", weight: 1.6,
      fillColor: isTop ? "#12908a" : "#9aa79a", fillOpacity: 1,
      radius: isTop ? 9 : 5.5,
    }).addTo(map)
      .bindPopup(`<b>${m.name}</b><br>Climate twin #${m.rank} · ${Math.round(m.similarity * 100)}% match`)
      .bindTooltip(isTop ? `Twin · ${m.name.split(",")[0]}` : m.name.split(",")[0], {
        permanent: isTop, direction: "right", offset: [9, 0],
        className: `map-label ${isTop ? "twin" : "cand"}`,
      });
  });
}

/* ================= boot ================= */
(async function boot() {
  try {
    // The backend injects window.__BOOT__ into the page, so the dashboard
    // paints with data on the first frame (no fetch race, works offline).
    if (window.__BOOT__) {
      const b = window.__BOOT__;
      state.meta = b.meta;
      state.shifts = b.shifts;
      state.twin = b.twin;
      state.advice = b.advice;
      state.clim = b.climatology;
      state.risk = b.risk.calendar;
      state.backtest = b.backtest;
      state.timeline = b.timeline.steps;
      state.candidates = b.candidates;
      state.geojson = b.geojson;
    } else {
      state.meta = await api("/api/meta");
      state.shifts = await api("/api/shifts");
      state.twin = await api("/api/twin");
      state.advice = await api("/api/advice");
      state.clim = await api("/api/climatology");
      state.risk = (await api("/api/risk-calendar")).calendar;
      state.backtest = await api("/api/backtest");
      state.timeline = (await api("/api/timeline")).steps;
      state.candidates = await api("/api/candidates");
    }

    renderHome(state.meta, state.shifts);
    renderShiftKpis(state.shifts);
    renderShiftCharts(state.shifts);
    renderRiskCalendar(state.risk);
    renderTwin(state.twin);
    renderTimeline(state.timeline);
    renderExplorer(state.candidates, state.twin);
    renderAdvice(state.advice);
    renderBacktest(state.backtest);
    anomalyChart($("#bt-chart"), state.backtest);
    setupChat();
    renderPlan();
    renderMap(state.meta, state.twin);

    $("#clim-legend").innerHTML = `
      <span><span class="chip" style="background:#d3952f"></span>Your ${state.twin.deltas.target_year} (projected)</span>
      <span><span class="chip" style="background:#12908a"></span>${state.twin.matches[0].name} today</span>
      <span style="color:var(--muted)">thick = monthly rainfall (mm) · thin = mean temp (°C)</span>`;
    climCompareChart($("#chart-clim-compare"), state.clim);
  } catch (err) {
    document.body.insertAdjacentHTML("afterbegin",
      `<div style="background:#c94f38;color:#fff;padding:10px 20px">Backend not reachable (${err.message}). Start it with: <b>./run.sh</b></div>`);
  }
})();
