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
  indicator.hidden = true;
  indicator.setAttribute("aria-hidden", "true");
  fetch("/api/update/check", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error("update check failed");
      return response.json();
    })
    .then((payload) => {
      const hasUpdate = Boolean(payload.update_available);
      indicator.hidden = !hasUpdate;
      indicator.setAttribute("aria-hidden", hasUpdate ? "false" : "true");
    })
    .catch(() => {
      indicator.hidden = true;
      indicator.setAttribute("aria-hidden", "true");
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

  async function addCandidateAsShelly(candidate, button) {
    button.disabled = true;
    const suggested = (candidate.suggested_settings && candidate.suggested_settings.shelly_device) || {};
    const response = await fetch("/api/shelly-devices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: suggested.name || candidate.name || candidate.ip_address,
        base_url: suggested.base_url || candidate.base_url,
        generation: suggested.generation || candidate.generation || "auto",
        model: suggested.model || candidate.model || "",
        role: suggested.role || "pv",
        power_sign: suggested.power_sign || "normal",
        unique_id: suggested.unique_id || candidate.unique_id || "",
        enabled: true
      })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || response.statusText);
    }
    setStatus(i18n.labels.shellyDeviceAdded || "Shelly device added.");
    if (window.loadShellyDevices) {
      window.loadShellyDevices();
    }
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
      } else {
        const actions = document.createElement("div");
        actions.className = "action-stack";
        if (candidate.supported) {
          const gridButton = document.createElement("button");
          gridButton.type = "button";
          gridButton.className = "small-button";
          gridButton.textContent = i18n.labels.applyIntegration || "Apply";
          gridButton.addEventListener("click", async () => {
            try {
              await applyCandidate(candidate, gridButton);
            } catch (error) {
              gridButton.disabled = false;
              setStatus(`${i18n.labels.scanFailed || "Failed"}: ${error.message}`, true);
            }
          });
          actions.appendChild(gridButton);
        }
        if ((candidate.integration_type || "").startsWith("shelly")) {
          const shellyButton = document.createElement("button");
          shellyButton.type = "button";
          shellyButton.className = "small-button secondary-button";
          shellyButton.textContent = i18n.labels.addShellyDevice || "Add Shelly";
          shellyButton.addEventListener("click", async () => {
            try {
              await addCandidateAsShelly(candidate, shellyButton);
            } catch (error) {
              shellyButton.disabled = false;
              setStatus(`${i18n.labels.scanFailed || "Failed"}: ${error.message}`, true);
            }
          });
          actions.appendChild(shellyButton);
        }
        if (!actions.children.length) {
          actionCell.textContent = i18n.labels.unsupportedIntegration || "Not supported yet";
        } else {
          actionCell.appendChild(actions);
        }
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

function setupShellyDevices() {
  const form = document.getElementById("shellyDeviceForm");
  const rows = document.getElementById("shellyDeviceRows");
  const statusBox = document.getElementById("shellyDeviceStatus");
  if (!form || !rows || !statusBox) return;

  function setStatus(message, important = false) {
    statusBox.textContent = message;
    statusBox.hidden = false;
    statusBox.classList.toggle("important", important);
  }

  function option(label, value, selected) {
    const element = document.createElement("option");
    element.value = value;
    element.textContent = label;
    element.selected = value === selected;
    return element;
  }

  function addCell(row, child) {
    const cell = document.createElement("td");
    if (child instanceof Node) {
      cell.appendChild(child);
    } else {
      cell.textContent = child || "-";
    }
    row.appendChild(cell);
    return cell;
  }

  function makeInput(value) {
    const input = document.createElement("input");
    input.type = "text";
    input.value = value || "";
    return input;
  }

  function makeRoleSelect(value) {
    const select = document.createElement("select");
    select.appendChild(option(i18n.labels.shellyRolePv || "PV", "pv", value));
    select.appendChild(option(i18n.labels.shellyRoleLoad || "Load", "load", value));
    select.appendChild(option(i18n.labels.shellyRoleBattery || "Battery", "battery", value));
    select.appendChild(option(i18n.labels.shellyRoleOther || "Other", "other", value));
    return select;
  }

  function makeSignSelect(value) {
    const select = document.createElement("select");
    select.appendChild(option(i18n.labels.powerSignNormal || "Normal", "normal", value));
    select.appendChild(option(i18n.labels.powerSignInverted || "Inverted", "inverted", value));
    return select;
  }

  function makeGenerationSelect(value) {
    const select = document.createElement("select");
    select.appendChild(option(i18n.labels.shellyGenerationAuto || "Automatic", "auto", value));
    select.appendChild(option(i18n.labels.shellyGenerationGen1 || "Gen1", "gen1", value));
    select.appendChild(option(i18n.labels.shellyGenerationGen2 || "Gen2", "gen2", value));
    return select;
  }

  function powerText(reading) {
    if (!reading || reading.power_w === null || reading.power_w === undefined) return "-";
    return `${reading.power_w} W`;
  }

  function statusText(device) {
    const reading = device.reading;
    if (!device.enabled) return i18n.labels.inactive || "inactive";
    if (!reading) return "-";
    if (reading.error_status) return reading.error_status;
    return reading.status || "-";
  }

  function renderDevices(payload) {
    const devices = payload.devices || [];
    rows.replaceChildren();
    if (!devices.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 8;
      cell.textContent = i18n.labels.noShellyDevices || "No Shelly devices configured.";
      row.appendChild(cell);
      rows.appendChild(row);
      return;
    }
    devices.forEach((device) => {
      const row = document.createElement("tr");
      const nameInput = makeInput(device.name);
      const roleSelect = makeRoleSelect(device.role);
      const generationSelect = makeGenerationSelect(device.generation);
      const signSelect = makeSignSelect(device.power_sign);
      const timeoutInput = document.createElement("input");
      timeoutInput.type = "number";
      timeoutInput.min = "0.2";
      timeoutInput.step = "0.1";
      timeoutInput.value = device.timeout_seconds || 3;
      const enabledInput = document.createElement("input");
      enabledInput.type = "checkbox";
      enabledInput.checked = Boolean(device.enabled);

      const parameterBox = document.createElement("div");
      parameterBox.className = "inline-control-grid";
      parameterBox.appendChild(generationSelect);
      parameterBox.appendChild(signSelect);
      parameterBox.appendChild(timeoutInput);
      const enabledLabel = document.createElement("label");
      enabledLabel.className = "inline-checkbox";
      enabledLabel.appendChild(enabledInput);
      enabledLabel.appendChild(document.createTextNode(i18n.labels.active || "active"));
      parameterBox.appendChild(enabledLabel);

      const actionBox = document.createElement("div");
      actionBox.className = "action-stack";
      const saveButton = document.createElement("button");
      saveButton.type = "button";
      saveButton.className = "small-button";
      saveButton.textContent = i18n.labels.save || "Save";
      saveButton.addEventListener("click", async () => {
        saveButton.disabled = true;
        try {
          const response = await fetch(`/api/shelly-devices/${encodeURIComponent(device.id)}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: nameInput.value,
              base_url: device.base_url,
              generation: generationSelect.value,
              model: device.model || "",
              role: roleSelect.value,
              power_sign: signSelect.value,
              timeout_seconds: timeoutInput.value,
              enabled: enabledInput.checked
            })
          });
          if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || response.statusText);
          }
          setStatus(i18n.labels.shellyDeviceSaved || "Shelly device saved.");
          await loadDevices();
        } catch (error) {
          setStatus(`${i18n.labels.scanFailed || "Failed"}: ${error.message}`, true);
        } finally {
          saveButton.disabled = false;
        }
      });
      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "small-button danger-button";
      deleteButton.textContent = i18n.labels.remove || "Remove";
      deleteButton.addEventListener("click", async () => {
        deleteButton.disabled = true;
        try {
          const response = await fetch(`/api/shelly-devices/${encodeURIComponent(device.id)}`, { method: "DELETE" });
          if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || response.statusText);
          }
          setStatus(i18n.labels.shellyDeviceRemoved || "Shelly device removed.");
          await loadDevices();
        } catch (error) {
          setStatus(`${i18n.labels.scanFailed || "Failed"}: ${error.message}`, true);
        } finally {
          deleteButton.disabled = false;
        }
      });
      actionBox.appendChild(saveButton);
      actionBox.appendChild(deleteButton);

      addCell(row, nameInput);
      addCell(row, roleSelect);
      addCell(row, device.base_url);
      addCell(row, device.model || device.generation);
      addCell(row, powerText(device.reading));
      addCell(row, statusText(device));
      addCell(row, parameterBox);
      addCell(row, actionBox);
      rows.appendChild(row);
    });
  }

  async function loadDevices() {
    const response = await fetch("/api/shelly-devices");
    if (!response.ok) return;
    renderDevices(await response.json());
  }

  window.loadShellyDevices = loadDevices;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    payload.enabled = formData.get("enabled") === "true";
    try {
      const response = await fetch("/api/shelly-devices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || response.statusText);
      }
      form.reset();
      form.elements.enabled.checked = true;
      form.elements.timeout_seconds.value = "3";
      setStatus(i18n.labels.shellyDeviceAdded || "Shelly device added.");
      await loadDevices();
    } catch (error) {
      setStatus(`${i18n.labels.scanFailed || "Failed"}: ${error.message}`, true);
    }
  });

  loadDevices();
  window.setInterval(loadDevices, 5000);
}

function setupWebUpdateInstall() {
  const form = document.getElementById("webUpdateForm");
  const tokenInput = document.getElementById("webUpdateToken");
  const statusBox = document.getElementById("webUpdateStatus");
  const logBox = document.getElementById("webUpdateLog");
  if (!form || !statusBox || !logBox) return;

  function setWebUpdateStatus(message, important = false) {
    statusBox.textContent = message;
    statusBox.hidden = false;
    statusBox.classList.toggle("important", important);
  }

  function renderWebUpdateJob(job) {
    if (!job) return;
    logBox.hidden = false;
    logBox.textContent = job.steps.map((step) => {
      const header = `[${step.name}] ${step.command} -> ${step.returncode ?? ""}`;
      return `${header}\n${step.output || step.error_status || ""}`.trim();
    }).join("\n\n");
    if (job.status === "succeeded") {
      setWebUpdateStatus(i18n.labels.webUpdateSucceeded || "Web update completed.");
    } else if (job.status === "failed") {
      setWebUpdateStatus(`${i18n.labels.webUpdateFailed || "Web update failed"}: ${job.error_status || ""}`, true);
    } else {
      setWebUpdateStatus(i18n.labels.webUpdateRunning || "Web update running...");
    }
  }

  async function pollWebUpdateStatus() {
    const response = await fetch("/api/update/install/status");
    if (!response.ok) return;
    const payload = await response.json();
    renderWebUpdateJob(payload.job);
    if (payload.running) {
      window.setTimeout(pollWebUpdateStatus, 2500);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const token = tokenInput ? tokenInput.value : "";
    if (tokenInput) tokenInput.value = "";
    setWebUpdateStatus(i18n.labels.webUpdateRunning || "Web update running...");
    logBox.hidden = true;
    logBox.textContent = "";
    try {
      const response = await fetch("/api/update/install", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token })
      });
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || response.statusText);
      }
      const payload = await response.json();
      renderWebUpdateJob(payload.job);
      window.setTimeout(pollWebUpdateStatus, 2500);
    } catch (error) {
      setWebUpdateStatus(`${i18n.labels.webUpdateFailed || "Web update failed"}: ${error.message}`, true);
    }
  });

  pollWebUpdateStatus();
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
setupShellyDevices();
setupWebUpdateInstall();
