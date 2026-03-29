// ── State ────────────────────────────────────────────────────────────────────
let currentChart = "yoy_overlay";
let selectedYears = ALL_YEARS.map(Number);

const CHART_META = {
  yoy_overlay:      { num:"1", label:"Day-of-year overlay",       desc:"Each year's daily prices plotted on the same 1–365 axis so you can directly compare how prices moved through the year across different years — peaks and dips at the same day line up for easy comparison.", part:1 },
  monthly_avg:      { num:"2", label:"Monthly averages",          desc:"Average price for each month grouped by year shown as bars side by side. Taller bars mean higher average prices that month — useful for spotting which months are consistently expensive or cheap.", part:1 },
  heatmap:          { num:"3", label:"Month × Year heatmap",      desc:"A grid where each cell is a month–year combination, colour-coded from cool (cheap) to warm (expensive). Darker red cells are the most expensive month–year combinations at a glance.", part:1 },
  dow:              { num:"4", label:"Day-of-week pattern",       desc:"Average price for each day of the week (Mon–Sun) shown as lines per year. Peaks indicate which days hotels are most expensive — helps identify weekend vs weekday pricing patterns.", part:1 },
  outlier_timeline: { num:"5", label:"Timeline with outliers",    desc:"Daily prices plotted over time — normal days shown as a blue line, confirmed outlier days shown as red dots. A red dot means that day's price was flagged as abnormal by at least 2 of the 3 detection methods.", part:2 },
  zscore:           { num:"6", label:"Z-score over time",         desc:"How far each day's price deviates from the overall mean, measured in standard deviations. The dashed red line is the 2.5 threshold — any point above it is statistically unusual and marked as an outlier.", part:2 },
  histogram:        { num:"7", label:"Price distribution",        desc:"Frequency distribution of all prices split into normal (blue) and outlier (red) bars. The two dashed orange lines are the IQR fences — prices outside these boundaries are considered outliers by the IQR method.", part:2 },
  boxplot:          { num:"8", label:"Box-plots by year",         desc:"Yearly price spread shown as box-and-whisker plots. The box covers the middle 50% of prices, the line inside is the median, and dots outside the whiskers are individual outlier days for that year.", part:2 },
  forecast:         { num:"9", label:"Feb 2022 forecast",         desc:"Predicts daily hotel prices for February 2022 by combining two signals: a long-term price trend (rising or falling each year) and a seasonal index (how prices typically move day-by-day through the year). The orange line is the forecast, the shaded band is a ±$8 uncertainty range.", part:3 },
};

const OUTLIER_CHARTS = new Set(["outlier_timeline","zscore","histogram","boxplot"]);

// ── Year dropdown ─────────────────────────────────────────────────────────────

function updateTriggerLabel() {
  const label = document.getElementById("yearTriggerLabel");
  const all   = ALL_YEARS.map(Number);
  if (selectedYears.length === 0) { label.textContent = "None selected"; return; }
  if (selectedYears.length === all.length) { label.textContent = "All years"; return; }
  const sorted = [...selectedYears].sort((a, b) => a - b);
  label.textContent = sorted.length <= 3
    ? sorted.join(", ")
    : sorted.slice(0, 3).join(", ") + ` + ${sorted.length - 3} more`;
}

function updateCheckboxDisabledState() {
  document.querySelectorAll(".year-checkbox").forEach(cb => {
    const yr = Number(cb.dataset.year);
    cb.disabled = selectedYears.length === 1 && selectedYears.includes(yr);
  });
}

function toggleYearDropdown(event) {
  event.stopPropagation();
  const trigger  = document.getElementById("yearTrigger");
  const dropdown = document.getElementById("yearDropdown");
  if (dropdown.classList.contains("open")) {
    closeYearDropdown();
  } else {
    trigger.classList.add("open");
    dropdown.classList.add("open");
    const search = document.getElementById("yearSearch");
    search.value = "";
    filterYearOptions("");
    search.focus();
  }
}

function closeYearDropdown() {
  document.getElementById("yearTrigger").classList.remove("open");
  document.getElementById("yearDropdown").classList.remove("open");
}

function handleYearCheckbox(cb) {
  const yr = Number(cb.dataset.year);
  if (cb.checked) {
    if (!selectedYears.includes(yr)) { selectedYears.push(yr); selectedYears.sort((a,b) => a-b); }
  } else {
    if (selectedYears.length === 1) { cb.checked = true; return; }
    selectedYears = selectedYears.filter(y => y !== yr);
  }
  cb.closest(".year-option").classList.toggle("deselected", !cb.checked);
  updateCheckboxDisabledState();
  updateTriggerLabel();
  refresh();
}

function selectAllYears() {
  selectedYears = ALL_YEARS.map(Number);
  document.querySelectorAll(".year-checkbox").forEach(cb => {
    cb.checked = true;
    cb.closest(".year-option").classList.remove("deselected");
  });
  updateCheckboxDisabledState();
  updateTriggerLabel();
  refresh();
}

function deselectAllYears() {
  const first = ALL_YEARS.map(Number)[0];
  selectedYears = [first];
  document.querySelectorAll(".year-checkbox").forEach(cb => {
    const yr = Number(cb.dataset.year);
    cb.checked = yr === first;
    cb.closest(".year-option").classList.toggle("deselected", yr !== first);
  });
  updateCheckboxDisabledState();
  updateTriggerLabel();
  refresh();
}

function filterYearOptions(query) {
  const q = query.trim().toLowerCase();
  document.querySelectorAll(".year-option").forEach(row => {
    row.classList.toggle("hidden", q !== "" && !row.dataset.year.includes(q));
  });
}

document.addEventListener("click", function(e) {
  const wrap = document.querySelector(".year-select-wrap");
  if (wrap && !wrap.contains(e.target)) closeYearDropdown();
});

// ── Accordion sections ────────────────────────────────────────────────────────
function toggleSection(titleEl) {
  const body = titleEl.nextElementSibling;
  const collapsed = body.classList.toggle("collapsed");
  titleEl.classList.toggle("collapsed", collapsed);
}

// ── Chart selection ───────────────────────────────────────────────────────────
function selectChart(btn) {
  document.querySelectorAll(".chart-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  currentChart = btn.dataset.chart;
  const meta = CHART_META[currentChart];
  document.getElementById("chart-num").textContent   = meta.num;
  document.getElementById("chart-label").textContent = meta.label;
  document.getElementById("chart-desc").textContent  = meta.desc;
  document.getElementById("outlier-table-card").style.display = OUTLIER_CHARTS.has(currentChart) ? "block" : "none";
  document.getElementById("forecast-strip").style.display     = currentChart === "forecast" ? "block" : "none";
  loadChart();
  loadOutlierTable();
}

// ── API calls ─────────────────────────────────────────────────────────────────
function yearsParam() { return selectedYears.join(","); }

async function loadStats() {
  try {
    const res  = await fetch(`/api/stats?years=${yearsParam()}`);
    const data = await res.json();
    document.getElementById("m-days").textContent = data.total_days.toLocaleString();
    document.getElementById("m-avg").textContent  = "$" + data.avg_price;
    document.getElementById("m-min").textContent  = "$" + data.min_price;
    document.getElementById("m-max").textContent  = "$" + data.max_price;
    document.getElementById("m-out").textContent  = data.outlier_count;
  } catch(e) { console.error(e); }
}

async function loadOutlierTable() {
  if (!OUTLIER_CHARTS.has(currentChart)) return;
  try {
    const res  = await fetch(`/api/outliers?years=${yearsParam()}`);
    const rows = await res.json();
    const tbody = document.getElementById("outlier-tbody");
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td>${r.date}</td>
        <td>$${r.price}</td>
        <td>${r.zscore}</td>
        <td><span class="badge ${r.flag_z  ? 'badge-yes':'badge-no'}">${r.flag_z  ? 'YES':'no'}</span></td>
        <td><span class="badge ${r.flag_iq ? 'badge-yes':'badge-no'}">${r.flag_iq ? 'YES':'no'}</span></td>
        <td><span class="badge ${r.flag_yr ? 'badge-yes':'badge-no'}">${r.flag_yr ? 'YES':'no'}</span></td>
      </tr>`).join("");
  } catch(e) { console.error(e); }
}

async function loadChart() {
  const loader = document.getElementById("loader");
  loader.classList.add("show");
  try {
    const res  = await fetch(`/api/chart/${currentChart}?years=${yearsParam()}`);
    const fig  = await res.json();
    Plotly.react("plotly-chart", fig.data, fig.layout, {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ["autoScale2d","lasso2d","select2d"],
      displaylogo: false,
    });

    if (currentChart === "forecast") {
      const title = fig.layout?.title?.text || fig.layout?.title || "";
      const match = title.match(/slope:\s*([+-]?[\d.]+)/);
      document.getElementById("slope-val").textContent = match ? match[1] + " USD" : "—";
    }
  } catch(e) {
    document.getElementById("plotly-chart").innerHTML =
      `<div class="empty"><div class="empty-icon">⚠</div>Failed to load chart.</div>`;
    console.error(e);
  } finally {
    loader.classList.remove("show");
  }
}

function refresh() {
  loadStats();
  loadChart();
  loadOutlierTable();
}

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener("load", () => {
  updateTriggerLabel();
  updateCheckboxDisabledState();
  refresh();
});
window.addEventListener("resize", () => Plotly.Plots.resize("plotly-chart"));
