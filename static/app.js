// ── State ────────────────────────────────────────────────────────────────────
let currentChart = "yoy_overlay";
let selectedYears = ALL_YEARS.map(Number);

const CHART_META = {
  yoy_overlay:      { num:"1", label:"Day-of-year overlay",       desc:"All years overlaid on a single day-of-year axis to reveal seasonal patterns", part:1 },
  monthly_avg:      { num:"2", label:"Monthly averages",          desc:"Average price per month grouped by year — spot seasonal highs and lows", part:1 },
  heatmap:          { num:"3", label:"Month × Year heatmap",      desc:"Average price colour-coded by month and year for quick pattern scanning", part:1 },
  dow:              { num:"4", label:"Day-of-week pattern",       desc:"Average price for each day of the week — weekend vs weekday dynamics", part:1 },
  outlier_timeline: { num:"5", label:"Timeline with outliers",    desc:"Full price timeline with confirmed outliers highlighted in red", part:2 },
  zscore:           { num:"6", label:"Z-score over time",         desc:"Global z-score per day — points above the dashed line are anomalous", part:2 },
  histogram:        { num:"7", label:"Price distribution",        desc:"Distribution of prices with IQR fences marking the outlier boundaries", part:2 },
  boxplot:          { num:"8", label:"Box-plots by year",         desc:"Box-and-whisker summary per year — outliers appear as individual dots", part:2 },
  forecast:         { num:"9", label:"Feb 2022 forecast",         desc:"Historical prices + extrapolated Feb 2022 forecast using trend + seasonal index", part:3 },
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
