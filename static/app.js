/**
 * KELVRA Device Lab — Control Console Client
 * High-performance WebSocket streaming, input injection, and telemetry monitoring
 * Adheres strictly to Zero Emoji Rule
 */

class DeviceLabConsole {
  constructor() {
    this.activeDevice = null;
    this.devices = [];
    this.screenWs = null;
    this.logcatWs = null;
    this.telemetryInterval = null;
    this.fleetInterval = null;
    this.isStreaming = true;
    this.autoScrollLogs = true;

    // Gesture tracking state
    this.dragStart = null;

    this.initDOMElements();
    this.bindEvents();
    this.startFleetScanner();
  }

  initDOMElements() {
    this.deviceListEl = document.getElementById('device-list');
    this.deviceCountBadge = document.getElementById('device-count-badge');
    this.btnRefresh = document.getElementById('btn-refresh-devices');

    // Stage elements
    this.activeTitleEl = document.getElementById('active-device-title');
    this.activeSpecsEl = document.getElementById('active-device-specs');
    this.canvas = document.getElementById('device-canvas');
    this.ctx = this.canvas.getContext('2d');
    this.canvasOverlay = document.getElementById('canvas-overlay');
    this.btnToggleStream = document.getElementById('btn-toggle-stream');
    this.streamLabel = document.getElementById('stream-label');

    // Input elements
    this.typeInput = document.getElementById('type-input');
    this.btnSendText = document.getElementById('btn-send-text');

    // Telemetry elements
    this.metricCpu = document.getElementById('metric-cpu');
    this.barCpu = document.getElementById('bar-cpu');
    this.metricRam = document.getElementById('metric-ram');
    this.barRam = document.getElementById('bar-ram');
    this.metricBattery = document.getElementById('metric-battery');
    this.metricTemp = document.getElementById('metric-temp');
    this.metricStorage = document.getElementById('metric-storage');
    this.barStorage = document.getElementById('bar-storage');

    // Action elements
    this.packageInput = document.getElementById('app-package-input');
    this.btnLaunchApp = document.getElementById('btn-launch-app');
    this.btnStopApp = document.getElementById('btn-stop-app');
    this.btnRunSmoke = document.getElementById('btn-run-smoke');
    this.testReportCard = document.getElementById('test-report-card');
    this.testStatusPill = document.getElementById('test-status-pill');
    this.testIdLabel = document.getElementById('test-id-label');
    this.testStepsList = document.getElementById('test-steps-list');

    // Logcat elements
    this.logcatViewport = document.getElementById('logcat-viewport');
    this.logCountBadge = document.getElementById('log-count');
    this.logLevelFilter = document.getElementById('log-level-filter');
    this.logSearchInput = document.getElementById('log-search-input');
    this.btnAutoScroll = document.getElementById('btn-autoscroll');
    this.btnClearLogs = document.getElementById('btn-clear-logs');
    this.totalLogsCount = 0;
  }

  bindEvents() {
    this.btnRefresh.addEventListener('click', () => this.fetchFleet());

    // Canvas click & gesture interaction
    this.canvas.addEventListener('mousedown', (e) => {
      this.dragStart = this.getCanvasCoords(e);
    });

    this.canvas.addEventListener('mouseup', (e) => {
      if (!this.activeDevice || !this.dragStart) return;
      const dragEnd = this.getCanvasCoords(e);
      const dx = dragEnd.x - this.dragStart.x;
      const dy = dragEnd.y - this.dragStart.y;
      const dist = Math.hypot(dx, dy);

      if (dist < 10) {
        // Tap
        this.injectTap(this.dragStart.realX, this.dragStart.realY);
      } else {
        // Swipe
        this.injectSwipe(this.dragStart.realX, this.dragStart.realY, dragEnd.realX, dragEnd.realY);
      }
      this.dragStart = null;
    });

    // Hardware buttons
    document.querySelectorAll('.key-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const key = btn.dataset.key;
        if (key && this.activeDevice) {
          this.injectKey(key);
        }
      });
    });

    // Typing injection
    this.btnSendText.addEventListener('click', () => this.sendTypedText());
    this.typeInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        this.sendTypedText();
      }
    });

    // App actions
    this.btnLaunchApp.addEventListener('click', () => this.launchApp());
    this.btnStopApp.addEventListener('click', () => this.stopApp());
    this.btnRunSmoke.addEventListener('click', () => this.runSmokeTest());

    // Stream toggle
    this.btnToggleStream.addEventListener('click', () => {
      this.isStreaming = !this.isStreaming;
      this.streamLabel.textContent = this.isStreaming ? 'Pause Stream' : 'Resume Stream';
    });

    // Logcat controls
    this.btnClearLogs.addEventListener('click', () => {
      this.logcatViewport.innerHTML = '';
      this.totalLogsCount = 0;
      this.logCountBadge.textContent = '0 lines';
    });

    this.btnAutoScroll.addEventListener('click', () => {
      this.autoScrollLogs = !this.autoScrollLogs;
      this.btnAutoScroll.classList.toggle('active', this.autoScrollLogs);
    });

    this.logLevelFilter.addEventListener('change', () => this.filterLogs());
    this.logSearchInput.addEventListener('input', () => this.filterLogs());
  }

  getCanvasCoords(event) {
    const rect = this.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    const scaleX = (this.activeDevice ? this.activeDevice.screen_width : 1080) / this.canvas.width;
    const scaleY = (this.activeDevice ? this.activeDevice.screen_height : 2400) / this.canvas.height;

    return {
      x,
      y,
      realX: Math.round(x * scaleX),
      realY: Math.round(y * scaleY)
    };
  }

  startFleetScanner() {
    this.fetchFleet();
    this.fleetInterval = setInterval(() => this.fetchFleet(), 5000);
  }

  async fetchFleet() {
    try {
      const res = await fetch('/api/devices');
      if (res.ok) {
        this.devices = await res.json();
        this.renderDeviceList();
      }
    } catch (err) {
      console.warn('Fleet scan failed:', err);
    }
  }

  renderDeviceList() {
    this.deviceCountBadge.textContent = this.devices.length;

    if (this.devices.length === 0) {
      this.deviceListEl.innerHTML = `
        <div class="empty-state">
          <p>No Android devices detected on ADB bus.</p>
        </div>
      `;
      return;
    }

    this.deviceListEl.innerHTML = '';
    this.devices.forEach(dev => {
      const isSelected = this.activeDevice && this.activeDevice.serial === dev.serial;
      const card = document.createElement('div');
      card.className = `device-card ${isSelected ? 'active' : ''}`;
      card.innerHTML = `
        <div class="device-card-header">
          <span class="device-card-name">${dev.market_name || dev.model}</span>
          <span class="device-status-pill ${dev.status.toLowerCase()}">${dev.status}</span>
        </div>
        <div class="device-card-details">
          <span>Android ${dev.android_version} (API ${dev.sdk_level})</span>
          <span>${dev.battery_level}%</span>
        </div>
        <div class="device-card-details">
          <span>${dev.serial}</span>
          <span>${dev.paired ? 'PAIRED' : 'UNPAIRED'}</span>
        </div>
      `;
      card.addEventListener('click', () => this.selectDevice(dev));
      this.deviceListEl.appendChild(card);
    });

    // Auto-select first device if none selected
    if (!this.activeDevice && this.devices.length > 0) {
      this.selectDevice(this.devices[0]);
    }
  }

  selectDevice(device) {
    this.activeDevice = device;
    this.renderDeviceList();

    this.activeTitleEl.textContent = `${device.market_name || device.model}`;
    this.activeSpecsEl.textContent = `${device.screen_width}x${device.screen_height} | API ${device.sdk_level} | ${device.abi}`;
    this.canvasOverlay.classList.add('hidden');

    // Resize canvas aspect ratio
    const aspect = device.screen_width / device.screen_height;
    const maxH = 580;
    this.canvas.height = maxH;
    this.canvas.width = Math.round(maxH * aspect);

    this.connectScreenStream(device.serial);
    this.connectLogcatStream(device.serial);
    this.startTelemetryLoop(device.serial);
  }

  connectScreenStream(serial) {
    if (this.screenWs) {
      this.screenWs.close();
    }

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${location.host}/ws/devices/${serial}/screen`;
    this.screenWs = new WebSocket(url);

    this.screenWs.onmessage = (event) => {
      if (!this.isStreaming) return;
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'frame' && msg.data) {
          const img = new Image();
          img.onload = () => {
            this.ctx.drawImage(img, 0, 0, this.canvas.width, this.canvas.height);
          };
          img.src = `data:image/jpeg;base64,${msg.data}`;
        }
      } catch (err) {
        console.error('Frame decode error:', err);
      }
    };
  }

  connectLogcatStream(serial) {
    if (this.logcatWs) {
      this.logcatWs.close();
    }

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${proto}//${location.host}/ws/devices/${serial}/logcat`;
    this.logcatWs = new WebSocket(url);

    this.logcatWs.onmessage = (event) => {
      try {
        const entry = JSON.parse(event.data);
        this.appendLogEntry(entry);
      } catch (err) {
        console.error('Logcat parse error:', err);
      }
    };
  }

  appendLogEntry(entry) {
    this.totalLogsCount++;
    this.logCountBadge.textContent = `${this.totalLogsCount} lines`;

    const row = document.createElement('div');
    row.className = 'log-line';
    row.dataset.level = entry.level || 'I';
    row.dataset.tag = (entry.tag || '').toLowerCase();
    row.dataset.msg = (entry.message || '').toLowerCase();

    row.innerHTML = `
      <span class="log-time">${entry.timestamp || ''}</span>
      <span class="log-level ${entry.level}">${entry.level}</span>
      <span class="log-tag">${entry.tag}:</span>
      <span class="log-msg">${escapeHtml(entry.message)}</span>
    `;

    this.logcatViewport.appendChild(row);

    if (this.autoScrollLogs) {
      this.logcatViewport.scrollTop = this.logcatViewport.scrollHeight;
    }
  }

  filterLogs() {
    const minLevel = this.logLevelFilter.value;
    const filterText = this.logSearchInput.value.toLowerCase().trim();
    const levelsOrder = ['V', 'D', 'I', 'W', 'E', 'F'];

    const rows = this.logcatViewport.querySelectorAll('.log-line');
    rows.forEach(r => {
      const lvl = r.dataset.level;
      const tag = r.dataset.tag;
      const msg = r.dataset.msg;

      let levelMatch = true;
      if (minLevel !== 'ALL') {
        const currentIdx = levelsOrder.indexOf(lvl);
        const reqIdx = levelsOrder.indexOf(minLevel);
        levelMatch = currentIdx >= reqIdx;
      }

      let textMatch = true;
      if (filterText) {
        textMatch = tag.includes(filterText) || msg.includes(filterText);
      }

      r.style.display = (levelMatch && textMatch) ? 'flex' : 'none';
    });
  }

  startTelemetryLoop(serial) {
    if (this.telemetryInterval) {
      clearInterval(this.telemetryInterval);
    }

    const poll = async () => {
      if (!this.activeDevice) return;
      try {
        const res = await fetch(`/api/devices/${serial}/telemetry`);
        if (res.ok) {
          const t = await res.json();
          this.metricCpu.textContent = `${t.cpu_usage_percent.toFixed(1)} %`;
          this.barCpu.style.width = `${Math.min(100, t.cpu_usage_percent)}%`;

          this.metricRam.textContent = `${t.ram_used_mb} MB`;
          const ramPct = t.ram_total_mb > 0 ? (t.ram_used_mb / t.ram_total_mb) * 100 : 0;
          this.barRam.style.width = `${Math.min(100, ramPct)}%`;

          this.metricBattery.textContent = `${t.battery_level} %`;
          this.metricTemp.textContent = `${t.battery_temp_c.toFixed(1)} °C`;

          this.metricStorage.textContent = `${t.storage_used_gb} / ${t.storage_total_gb} GB`;
          const storPct = t.storage_total_gb > 0 ? (t.storage_used_gb / t.storage_total_gb) * 100 : 0;
          this.barStorage.style.width = `${Math.min(100, storPct)}%`;
        }
      } catch (err) {
        console.debug('Telemetry error:', err);
      }
    };

    poll();
    this.telemetryInterval = setInterval(poll, 4000);
  }

  async injectTap(x, y) {
    if (!this.activeDevice) return;
    try {
      await fetch(`/api/devices/${this.activeDevice.serial}/input/tap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x, y })
      });
    } catch (err) {
      console.warn('Tap failed:', err);
    }
  }

  async injectSwipe(x1, y1, x2, y2) {
    if (!this.activeDevice) return;
    try {
      await fetch(`/api/devices/${this.activeDevice.serial}/input/swipe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ x1, y1, x2, y2, duration_ms: 300 })
      });
    } catch (err) {
      console.warn('Swipe failed:', err);
    }
  }

  async injectKey(key) {
    if (!this.activeDevice) return;
    try {
      await fetch(`/api/devices/${this.activeDevice.serial}/input/key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key })
      });
    } catch (err) {
      console.warn('Key injection failed:', err);
    }
  }

  async sendTypedText() {
    const text = this.typeInput.value;
    if (!text || !this.activeDevice) return;
    try {
      await fetch(`/api/devices/${this.activeDevice.serial}/input/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      this.typeInput.value = '';
    } catch (err) {
      console.warn('Text injection failed:', err);
    }
  }

  async launchApp() {
    const pkg = this.packageInput.value.trim();
    if (!pkg || !this.activeDevice) return;
    try {
      await fetch(`/api/devices/${this.activeDevice.serial}/apps/launch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package: pkg })
      });
    } catch (err) {
      console.warn('Launch app failed:', err);
    }
  }

  async stopApp() {
    const pkg = this.packageInput.value.trim();
    if (!pkg || !this.activeDevice) return;
    try {
      await fetch(`/api/devices/${this.activeDevice.serial}/apps/stop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package: pkg })
      });
    } catch (err) {
      console.warn('Stop app failed:', err);
    }
  }

  async runSmokeTest() {
    const pkg = this.packageInput.value.trim();
    if (!pkg || !this.activeDevice) return;

    this.btnRunSmoke.disabled = true;
    this.btnRunSmoke.textContent = 'Running Smoke Test...';

    try {
      const res = await fetch(`/api/devices/${this.activeDevice.serial}/tests/smoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ package: pkg })
      });

      if (res.ok) {
        const report = await res.json();
        this.renderTestReport(report);
      }
    } catch (err) {
      console.error('Smoke test error:', err);
    } finally {
      this.btnRunSmoke.disabled = false;
      this.btnRunSmoke.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="5 3 19 12 5 21 5 3"></polygon>
        </svg>
        Execute Smoke Test
      `;
    }
  }

  renderTestReport(report) {
    this.testReportCard.classList.remove('hidden');
    this.testIdLabel.textContent = report.test_id;
    this.testStatusPill.textContent = report.overall_status;
    this.testStatusPill.className = `pill ${report.overall_status}`;

    this.testStepsList.innerHTML = '';
    report.steps.forEach(step => {
      const item = document.createElement('li');
      item.className = 'step-item';
      item.innerHTML = `
        <span>${escapeHtml(step.step_name)}</span>
        <span class="pill ${step.status}">${step.status} (${step.duration_ms}ms)</span>
      `;
      this.testStepsList.appendChild(item);
    });
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

document.addEventListener('DOMContentLoaded', () => {
  window.deviceLab = new DeviceLabConsole();
});
