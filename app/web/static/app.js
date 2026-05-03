const MAX_POINTS = 120;
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
  if (element.dataset.boolean === "true") return value ? "aktiv" : "inaktiv";
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
          label: "Istwert",
          data: [],
          borderColor: "#2563eb",
          backgroundColor: "#2563eb22",
          tension: 0.25,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: "Sollwert",
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
  charts.grid = makeChart("gridChart", "Netzleistung", "#0f766e");
  charts.output = makeChart("outputChart", "Ausgangsleistung", "#2563eb");
  charts.pv = makeChart("pvChart", "PV-Leistung", "#ca8a04");
  charts.soc = makeChart("socChart", "Batterie-SOC", "#16a34a", "%");
  charts.target = makeTargetChart();
  charts.deviation = makeChart("deviationChart", "Abweichung", "#be123c");
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

socket.addEventListener("message", (event) => {
  const payload = JSON.parse(event.data);
  updateFields(payload);
  updateCharts(payload);
});

socket.addEventListener("close", () => {
  document.querySelectorAll("[data-field='device_status']").forEach((element) => {
    element.textContent = "offline";
  });
});

setupCharts();

