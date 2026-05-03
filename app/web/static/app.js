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

function setupIntegrationScan() {
  const form = document.getElementById("integrationScanForm");
  const cidrInput = document.getElementById("integrationScanCidr");
  const statusBox = document.getElementById("integrationScanStatus");
  const resultsBody = document.getElementById("integrationResults");
  if (!form || !cidrInput || !statusBox || !resultsBody) return;

  function setStatus(message, important = false) {
    statusBox.textContent = message;
    statusBox.hidden = false;
    statusBox.classList.toggle("important", important);
  }

  function clearResults(message) {
    resultsBody.replaceChildren();
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 7;
    cell.textContent = message;
    row.appendChild(cell);
    resultsBody.appendChild(row);
  }

  function addCell(row, value) {
    const cell = document.createElement("td");
    cell.textContent = value || "-";
    row.appendChild(cell);
    return cell;
  }

  async function applyCandidate(candidate, button) {
    button.disabled = true;
    const response = await fetch("/api/integrations/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        integration_type: candidate.integration_type,
        base_url: candidate.base_url,
        generation: candidate.generation || "auto",
        meter_power_sign: "normal"
      })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || response.statusText);
    }
    setStatus(i18n.labels.integrationApplied || "Integration applied.");
  }

  function renderCandidates(candidates) {
    resultsBody.replaceChildren();
    if (!candidates.length) {
      clearResults(i18n.labels.scanNoResults || "No matching integrations found.");
      return;
    }
    candidates.forEach((candidate) => {
      const row = document.createElement("tr");
      addCell(row, candidate.ip_address);
      addCell(row, candidate.integration_type);
      addCell(row, candidate.name);
      addCell(row, candidate.model);
      addCell(row, candidate.generation);
      const statusText = candidate.duplicate_of
        ? `${i18n.labels.duplicateIntegration || "Duplicate of"} ${candidate.duplicate_of}`
        : (candidate.supported ? (i18n.labels.meterCandidate || "Grid meter") : candidate.status);
      addCell(row, statusText);
      const actionCell = document.createElement("td");
      if (candidate.duplicate_of) {
        actionCell.textContent = `${i18n.labels.duplicateIntegration || "Duplicate of"} ${candidate.duplicate_of}`;
      } else if (candidate.supported) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "small-button";
        button.textContent = i18n.labels.applyIntegration || "Apply";
        button.addEventListener("click", async () => {
          try {
            await applyCandidate(candidate, button);
          } catch (error) {
            button.disabled = false;
            setStatus(`${i18n.labels.scanFailed || "Failed"}: ${error.message}`, true);
          }
        });
        actionCell.appendChild(button);
      } else {
        actionCell.textContent = i18n.labels.unsupportedIntegration || "Not supported yet";
      }
      row.appendChild(actionCell);
      resultsBody.appendChild(row);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const cidr = cidrInput.value.trim();
    setStatus(i18n.labels.scanRunning || "Scan running...");
    clearResults(i18n.labels.scanRunning || "Scan running...");
    try {
      const response = await fetch(`/api/integrations/scan?cidr=${encodeURIComponent(cidr)}`);
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || response.statusText);
      }
      const payload = await response.json();
      setStatus(
        `${payload.scanned_hosts} ${i18n.labels.hostsScanned || "hosts scanned"}, ` +
        `${payload.candidates.length} ${i18n.labels.candidatesFound || "candidate(s)"}`
      );
      renderCandidates(payload.candidates);
    } catch (error) {
      clearResults(i18n.labels.scanNoResults || "No matching integrations found.");
      setStatus(`${i18n.labels.scanFailed || "Scan failed"}: ${error.message}`, true);
    }
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
setupIntegrationScan();
