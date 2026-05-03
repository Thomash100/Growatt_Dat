const MAX_POINTS = 120;
const i18n = window.GLG_I18N || { labels: {}, values: {} };
const socketProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const socket = new WebSocket(`${socketProtocol}//${window.location.host}/ws/live`);
const charts = {};

function readPath(source, path) {
  return path.split(".").reduce((value, key) => {
    if (value === null || value === undefined) return undefined;
    return value[key];
  }, source);
}

function formatValue(value, element) {
  if (value === null || value === undefined || value === "") return "-";
  if (element.dataset.valueMap && i18n.values[element.dataset.valueMap]) {
    return i18n.values[element.dataset.valueMap][value] || value;
  }
  if (element.dataset.boolean === "true") return value ? i18n.labels.active || "active" : i18n.labels.inactive || "inactive";
  if (element.dataset.date === "true") return new Date(value).toLocaleString();
  return `${value}${element.dataset.unit || ""}`;
}

function updateFields(payload) {
  document.querySelectorAll("[data-field]").forEach((element) => {
    const value = readPath(payload, element.dataset.field);
    element.textContent = formatValue(value, element);
  });
}

function makeChart(canvasId, label, color, unit = "W") {
  const canvas = document.getElementById(canvasId);
  if (!canvas || !window.Chart) return null;
  return new Chart(canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label,
        data: [],
        borderColor: color,
        backgroundColor: `${color}22`,
        tension: 0.25,
        pointRadius: 0,
        borderWidth: 2
      }]
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { maxTicksLimit: 6 } },
        y: { title: { display: true, text: unit } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

function makeTargetChart() {
  const canvas = document.getElementById("targetChart");
  if (!canvas || !window.Chart) return null;
  return new Chart(canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: i18n.labels.actual || "Actual",
          data: [],
          borderColor: "#2563eb",
          backgroundColor: "#2563eb22",
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: i18n.labels.target || "Target",
          data: [],
          borderColor: "#c2410c",
          backgroundColor: "#c2410c22",
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2
        }
      ]
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { maxTicksLimit: 6 } },
        y: { title: { display: true, text: "W" } }
      }
    }
  });
}

function setupCharts() {
  if (!document.getElementById("liveCharts")) return;
  charts.grid = makeChart("gridChart", i18n.labels.gridPower || "Grid power", "#0f766e");
  charts.output = makeChart("outputChart", i18n.labels.outputPower || "Output power", "#2563eb");
  charts.pv = makeChart("pvChart", i18n.labels.pvPower || "PV power", "#ca8a04");
  charts.soc = makeChart("socChart", i18n.labels.batterySoc || "Battery SOC", "#16a34a", "%");
  charts.target = makeTargetChart();
  charts.deviation = makeChart("deviationChart", i18n.labels.deviation || "Deviation", "#be123c");
}

function pushPoint(chart, label, values) {
  if (!chart) return;
  chart.data.labels.push(label);
  chart.data.datasets.forEach((dataset, index) => dataset.data.push(values[index]));
  if (chart.data.labels.length > MAX_POINTS) {
    chart.data.labels.shift();
    chart.data.datasets.forEach((dataset) => dataset.data.shift());
  }
  chart.update("none");
}

function updateCharts(payload) {
  if (!document.getElementById("liveCharts")) return;
  const measurements = payload.measurements;
  const control = payload.control;
  const settings = payload.settings;
  if (!measurements || !control || !settings) return;
  const label = new Date(measurements.timestamp).toLocaleTimeString();
  pushPoint(charts.grid, label, [measurements.grid_power_w]);
  pushPoint(charts.output, label, [measurements.output_power_w]);
  pushPoint(charts.pv, label, [measurements.pv_power_w]);
  pushPoint(charts.soc, label, [measurements.battery_soc]);
  pushPoint(charts.target, label, [measurements.output_power_w, control.target_output_power_w]);
  pushPoint(charts.deviation, label, [measurements.grid_power_w - settings.target_grid_power_w]);
}

function setupReleaseNotice() {
  const modal = document.getElementById("releaseModal");
  if (!modal) return;
  const version = modal.dataset.releaseVersion || "unknown";
  const storageKey = `growattLocalGateway.releaseSeen.${version}`;
  let alreadySeen = false;
  try {
    alreadySeen = window.localStorage.getItem(storageKey) === "true";
  } catch (error) {
    alreadySeen = false;
  }
  if (!alreadySeen) {
    modal.hidden = false;
  }

  function closeModal() {
    modal.hidden = true;
    try {
      window.localStorage.setItem(storageKey, "true");
    } catch (error) {
      return;
    }
  }

  modal.querySelectorAll("[data-release-close]").forEach((element) => {
    element.addEventListener("click", closeModal);
  });

  modal.addEventListener("click", (event) => {
    if (event.target === modal) closeModal();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) closeModal();
  });
}

function setupUpdateIndicator() {
  const indicator = document.getElementById("updateIndicator");
  if (!indicator || !window.fetch) return;
  fetch("/api/update/check")
    .then((response) => {
      if (!response.ok) throw new Error("update check failed");
      return response.json();
    })
    .then((payload) => {
      if (payload.update_available) {
        indicator.hidden = false;
      }
    })
    .catch(() => {
      indicator.hidden = true;
    });
}

socket.addEventListener("message", (event) => {
  const payload = JSON.parse(event.data);
  updateFields(payload);
  updateCharts(payload);
});

socket.addEventListener("close", () => {
  document.querySelectorAll("[data-field='device_status']").forEach((element) => {
    element.textContent = i18n.labels.offline || "offline";
  });
});

setupCharts();
setupReleaseNotice();
setupUpdateIndicator();
