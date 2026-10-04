/**
 * KELVRA Device Lab — Foundational Application Shell Client
 * Adheres strictly to KELVRA Bench Design Contract & reference.html
 * Zero Emoji Prohibition Enforced: Authentic Vector SVGs & Flat Dots Only
 */

class DeviceLabApp {
  constructor() {
    this.currentRoute = 'overview';
    this.pendingConfirmCallback = null;
    this.devices = [];
    this.viewLayout = 'grid';

    // Studio & Stream State (Phase 10)
    this.activeStudioDevice = null;
    this.streamWs = null;
    this.streamState = 'IDLE';
    this.heldLeaseToken = null;
    this.leaseHeartbeatTimer = null;
    this.pollDiagTimer = null;
    this.touchStartData = null;
    this.canvasCtx = null;

    // AVD Hub State (Phase 11)
    this.avds = [];
    this.avdPollTimer = null;

    this.initDOMElements();
    this.bindEvents();
    this.initRouting();
    this.loadSettings();
    this.checkHealth();
    this.loadDevices();
    this.loadSessions();
  }

  initDOMElements() {
    this.sidebar = document.getElementById('app-sidebar');
    this.btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
    this.navLinks = document.querySelectorAll('.sidebar-nav-link');
    this.pageViews = document.querySelectorAll('.page-view');
    this.toastContainer = document.getElementById('toast-container');

    // Modals
    this.modalBackdrop = document.getElementById('modal-backdrop');
    this.modalTitle = document.getElementById('modal-title');
    this.modalBody = document.getElementById('modal-body');
    this.modalBtnClose = document.getElementById('modal-btn-close');
    this.modalBtnCancel = document.getElementById('modal-btn-cancel');
    this.modalBtnConfirm = document.getElementById('modal-btn-confirm');

    // Topbar & Actions
    this.btnGlobalRefresh = document.getElementById('btn-global-refresh');
    this.btnAbout = document.getElementById('btn-about');
    this.serviceStatusDot = document.getElementById('service-status-dot');
    this.serviceStatusText = document.getElementById('service-status-text');
    this.btnScanDevicesPage = document.getElementById('btn-scan-devices-page');

    // Overview metrics
    this.overviewDeviceCount = document.getElementById('overview-device-count');
    this.navBadgeDevices = document.getElementById('nav-badge-devices');

    // Phase 8 Inventory Elements
    this.devicesListContainer = document.getElementById('devices-list-container');
    this.deviceSearchInput = document.getElementById('device-search-input');
    this.filterPlatform = document.getElementById('filter-platform');
    this.filterState = document.getElementById('filter-state');
    this.btnViewGrid = document.getElementById('btn-view-grid');
    this.btnViewTable = document.getElementById('btn-view-table');
    this.btnDevicesRefresh = document.getElementById('btn-devices-refresh');

    // Stats Bar Elements
    this.statTotalDevices = document.getElementById('stat-total-devices');
    this.statOnlineDevices = document.getElementById('stat-online-devices');
    this.statConnectedDevices = document.getElementById('stat-connected-devices');
    this.statUnauthorizedDevices = document.getElementById('stat-unauthorized-devices');

    // Phase 10 Studio & Remote Control Elements
    this.devicesInventoryPanel = document.getElementById('devices-inventory-panel');
    this.devicesStudioPanel = document.getElementById('devices-studio-panel');
    this.btnStudioBack = document.getElementById('btn-studio-back');
    this.studioDeviceName = document.getElementById('studio-device-name');
    this.studioDeviceSerial = document.getElementById('studio-device-serial');
    this.studioHudRes = document.getElementById('studio-hud-res');
    this.studioHudFps = document.getElementById('studio-hud-fps');
    this.studioLeaseBadge = document.getElementById('studio-lease-badge');
    this.btnStudioLeaseToggle = document.getElementById('btn-studio-lease-toggle');
    this.btnStudioStreamToggle = document.getElementById('btn-studio-stream-toggle');
    this.studioQualitySelect = document.getElementById('studio-quality-select');
    this.studioFpsSelect = document.getElementById('studio-fps-select');
    this.studioStreamStatusDot = document.getElementById('studio-stream-status-dot');
    this.studioStreamStatusText = document.getElementById('studio-stream-status-text');
    this.btnStudioFullscreen = document.getElementById('btn-studio-fullscreen');
    this.studioViewport = document.getElementById('studio-viewport');
    this.studioScreenCanvas = document.getElementById('studio-screen-canvas');
    this.studioOverlay = document.getElementById('studio-overlay');
    this.studioOverlayTitle = document.getElementById('studio-overlay-title');
    this.studioOverlayDesc = document.getElementById('studio-overlay-desc');

    // Hardware Navigation Buttons
    this.btnHwBack = document.getElementById('btn-hw-back');
    this.btnHwHome = document.getElementById('btn-hw-home');
    this.btnHwRecents = document.getElementById('btn-hw-recents');
    this.btnHwPower = document.getElementById('btn-hw-power');
    this.btnHwVolDown = document.getElementById('btn-hw-vol-down');
    this.btnHwVolUp = document.getElementById('btn-hw-vol-up');

    // Text injection
    this.studioTextInput = document.getElementById('studio-text-input');
    this.btnStudioSendText = document.getElementById('btn-studio-send-text');

    // Diagnostics & Sessions
    this.diagFps = document.getElementById('diag-fps');
    this.diagFrames = document.getElementById('diag-frames');
    this.diagDropped = document.getElementById('diag-dropped');
    this.diagBytes = document.getElementById('diag-bytes');
    this.diagStartup = document.getElementById('diag-startup');
    this.diagViewers = document.getElementById('diag-viewers');
    this.diagLeaseIndicator = document.getElementById('diag-lease-indicator');
    this.diagLeaseHolder = document.getElementById('diag-lease-holder');
    this.diagLeaseExpires = document.getElementById('diag-lease-expires');
    this.sessionsLeaseRows = document.getElementById('sessions-lease-rows');
    this.overviewSessionCount = document.getElementById('overview-session-count');

    // Phase 11 AVD Hub Elements
    this.avdEnvSdkPath = document.getElementById('avd-env-sdk-path');
    this.avdEnvEmuDot = document.getElementById('avd-env-emu-dot');
    this.avdEnvEmuStatus = document.getElementById('avd-env-emu-status');
    this.avdEnvAvdmDot = document.getElementById('avd-env-avdm-dot');
    this.avdEnvAvdmStatus = document.getElementById('avd-env-avdm-status');
    this.avdEnvSysimgCount = document.getElementById('avd-env-sysimg-count');
    this.avdEnvGuidance = document.getElementById('avd-env-guidance');
    this.avdEnvGuidanceText = document.getElementById('avd-env-guidance-text');

    this.btnRefreshAvds = document.getElementById('btn-refresh-avds');
    this.btnOpenCreateAvd = document.getElementById('btn-open-create-avd');
    this.avdSearchInput = document.getElementById('avd-search-input');
    this.avdBadgeCount = document.getElementById('avd-badge-count');
    this.avdListContainer = document.getElementById('avd-list-container');

    this.modalCreateAvd = document.getElementById('modal-create-avd');
    this.modalCreateAvdClose = document.getElementById('modal-create-avd-close');
    this.modalCreateAvdCancel = document.getElementById('modal-create-avd-cancel');
    this.formCreateAvd = document.getElementById('form-create-avd');
    this.createAvdName = document.getElementById('create-avd-name');
    this.createAvdPackage = document.getElementById('create-avd-package');
    this.createAvdProfile = document.getElementById('create-avd-profile');
    this.createAvdRam = document.getElementById('create-avd-ram');
    this.createAvdSdcard = document.getElementById('create-avd-sdcard');

    // Phase 13 Studio Controls
    this.btnStudioScreenshot = document.getElementById('btn-studio-screenshot');
    this.btnStudioRecordToggle = document.getElementById('btn-studio-record-toggle');
    this.btnStudioOpenLogs = document.getElementById('btn-studio-open-logs');
    this.isStudioRecording = false;
    this.recordingTimerInterval = null;
    this.recordingSeconds = 0;

    // Phase 13 Automation Elements
    this.btnOpenCreateWorkflow = document.getElementById('btn-open-create-workflow');
    this.autoActiveCard = document.getElementById('auto-active-card');
    this.autoActiveDot = document.getElementById('auto-active-dot');
    this.autoActiveTitle = document.getElementById('auto-active-title');
    this.autoActiveBadge = document.getElementById('auto-active-badge');
    this.autoActiveTimer = document.getElementById('auto-active-timer');
    this.btnCancelExecution = document.getElementById('btn-cancel-execution');
    this.autoProgressFill = document.getElementById('auto-progress-fill');
    this.autoActiveSteps = document.getElementById('auto-active-steps');
    this.autoTargetDevice = document.getElementById('auto-target-device');
    this.btnTemplateSmoke = document.getElementById('btn-template-smoke');
    this.btnTemplateApp = document.getElementById('btn-template-app');
    this.btnTemplateGesture = document.getElementById('btn-template-gesture');
    this.autoWorkflowJson = document.getElementById('auto-workflow-json');
    this.btnValidateWorkflow = document.getElementById('btn-validate-workflow');
    this.btnRunWorkflow = document.getElementById('btn-run-workflow');
    this.btnRefreshHistory = document.getElementById('btn-refresh-history');
    this.autoHistoryRows = document.getElementById('auto-history-rows');
    this.activeExecutionId = null;
    this.activeExecutionPollTimer = null;
    this.activeExecutionStartTime = null;

    // Phase 13 Modal Create Workflow
    this.modalCreateWorkflow = document.getElementById('modal-create-workflow');
    this.modalCreateWorkflowClose = document.getElementById('modal-create-workflow-close');
    this.modalCreateWorkflowCancel = document.getElementById('modal-create-workflow-cancel');
    this.formCreateWorkflow = document.getElementById('form-create-workflow');
    this.workflowNameInput = document.getElementById('workflow-name-input');
    this.workflowTargetDeviceInput = document.getElementById('workflow-target-device-input');
    this.workflowStepsJsonInput = document.getElementById('workflow-steps-json-input');

    // Phase 13 Logcat Elements
    this.btnLogExportTxt = document.getElementById('btn-log-export-txt');
    this.btnLogExportJson = document.getElementById('btn-log-export-json');
    this.btnLogClear = document.getElementById('btn-log-clear');
    this.btnLogStreamToggle = document.getElementById('btn-log-stream-toggle');
    this.logToggleLabel = document.getElementById('log-toggle-label');
    this.logDeviceSelect = document.getElementById('log-device-select');
    this.logLevelFilter = document.getElementById('log-level-filter');
    this.logTagFilter = document.getElementById('log-tag-filter');
    this.logSearchFilter = document.getElementById('log-search-filter');
    this.logAutoscrollToggle = document.getElementById('log-autoscroll-toggle');
    this.logcatTerminal = document.getElementById('logcat-terminal');
    this.isLogPolling = false;
    this.logPollTimer = null;
    this.currentLogDevice = null;

    // Phase 13 Deep Diagnostics Elements
    this.diagDeepDeviceSelect = document.getElementById('diag-deep-device-select');
    this.btnRefreshDeepDiag = document.getElementById('btn-refresh-deep-diag');
    this.deepDiagStateDot = document.getElementById('deep-diag-state-dot');
    this.deepDiagStateMetric = document.getElementById('deep-diag-state-metric');
    this.deepDiagProviderMeta = document.getElementById('deep-diag-provider-meta');
    this.deepDiagStreamDot = document.getElementById('deep-diag-stream-dot');
    this.deepDiagStreamFps = document.getElementById('deep-diag-stream-fps');
    this.deepDiagStreamMeta = document.getElementById('deep-diag-stream-meta');
    this.deepDiagLeaseMetric = document.getElementById('deep-diag-lease-metric');
    this.deepDiagLeaseMeta = document.getElementById('deep-diag-lease-meta');
    this.deepDiagBatteryMetric = document.getElementById('deep-diag-battery-metric');
    this.deepDiagScreenMeta = document.getElementById('deep-diag-screen-meta');
    this.deepDiagErrorRows = document.getElementById('deep-diag-error-rows');

    if (this.studioScreenCanvas) {
      this.canvasCtx = this.studioScreenCanvas.getContext('2d');
    }
  }

  bindEvents() {
    // Sidebar toggle
    if (this.btnToggleSidebar) {
      this.btnToggleSidebar.addEventListener('click', () => {
        this.toggleSidebar();
      });
    }

    // Modal controls
    if (this.modalBtnClose) {
      this.modalBtnClose.addEventListener('click', () => this.closeModal());
    }
    if (this.modalBtnCancel) {
      this.modalBtnCancel.addEventListener('click', () => this.closeModal());
    }
    if (this.modalBtnConfirm) {
      this.modalBtnConfirm.addEventListener('click', () => {
        if (this.pendingConfirmCallback) {
          this.pendingConfirmCallback();
        }
        this.closeModal();
      });
    }
    if (this.modalBackdrop) {
      this.modalBackdrop.addEventListener('click', (e) => {
        if (e.target === this.modalBackdrop) {
          this.closeModal();
        }
      });
    }

    // Topbar actions
    if (this.btnGlobalRefresh) {
      this.btnGlobalRefresh.addEventListener('click', () => {
        this.scanFleet();
      });
    }

    if (this.btnScanDevicesPage) {
      this.btnScanDevicesPage.addEventListener('click', () => {
        this.scanFleet();
      });
    }

    if (this.btnDevicesRefresh) {
      this.btnDevicesRefresh.addEventListener('click', () => {
        this.scanFleet();
      });
    }

    if (this.btnAbout) {
      this.btnAbout.addEventListener('click', () => {
        this.showAboutDialog();
      });
    }

    // Filters and search
    if (this.deviceSearchInput) {
      this.deviceSearchInput.addEventListener('input', () => {
        this.renderDevices();
      });
    }

    if (this.filterPlatform) {
      this.filterPlatform.addEventListener('change', () => {
        this.renderDevices();
      });
    }

    if (this.filterState) {
      this.filterState.addEventListener('change', () => {
        this.renderDevices();
      });
    }

    // Layout toggle
    if (this.btnViewGrid) {
      this.btnViewGrid.addEventListener('click', () => {
        this.viewLayout = 'grid';
        this.btnViewGrid.classList.add('active');
        if (this.btnViewTable) this.btnViewTable.classList.remove('active');
        this.renderDevices();
      });
    }

    if (this.btnViewTable) {
      this.btnViewTable.addEventListener('click', () => {
        this.viewLayout = 'table';
        this.btnViewTable.classList.add('active');
        if (this.btnViewGrid) this.btnViewGrid.classList.remove('active');
        this.renderDevices();
      });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        this.closeModal();
      }
    });

    // Studio Controls
    if (this.btnStudioBack) {
      this.btnStudioBack.addEventListener('click', () => this.closeDeviceStudio());
    }
    if (this.btnStudioStreamToggle) {
      this.btnStudioStreamToggle.addEventListener('click', () => this.toggleStream());
    }
    if (this.btnStudioLeaseToggle) {
      this.btnStudioLeaseToggle.addEventListener('click', () => this.toggleLease());
    }
    if (this.btnStudioFullscreen) {
      this.btnStudioFullscreen.addEventListener('click', () => this.toggleFullscreen());
    }

    // Hardware Navigation Keys
    if (this.btnHwBack) this.btnHwBack.addEventListener('click', () => this.sendKey('BACK'));
    if (this.btnHwHome) this.btnHwHome.addEventListener('click', () => this.sendKey('HOME'));
    if (this.btnHwRecents) this.btnHwRecents.addEventListener('click', () => this.sendKey('APP_SWITCH'));
    if (this.btnHwPower) this.btnHwPower.addEventListener('click', () => this.sendKey('POWER'));
    if (this.btnHwVolDown) this.btnHwVolDown.addEventListener('click', () => this.sendKey('VOLUME_DOWN'));
    if (this.btnHwVolUp) this.btnHwVolUp.addEventListener('click', () => this.sendKey('VOLUME_UP'));

    // Text injection
    if (this.btnStudioSendText) {
      this.btnStudioSendText.addEventListener('click', () => this.sendText());
    }
    if (this.studioTextInput) {
      this.studioTextInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          this.sendText();
        }
      });
    }

    // AVD Hub Events (Phase 11)
    if (this.btnRefreshAvds) {
      this.btnRefreshAvds.addEventListener('click', () => {
        this.loadAvdEnvironment();
        this.loadAvds();
      });
    }

    if (this.btnOpenCreateAvd) {
      this.btnOpenCreateAvd.addEventListener('click', () => {
        this.openCreateAvdModal();
      });
    }

    if (this.modalCreateAvdClose) {
      this.modalCreateAvdClose.addEventListener('click', () => {
        this.closeCreateAvdModal();
      });
    }

    if (this.modalCreateAvdCancel) {
      this.modalCreateAvdCancel.addEventListener('click', () => {
        this.closeCreateAvdModal();
      });
    }

    if (this.modalCreateAvd) {
      this.modalCreateAvd.addEventListener('click', (e) => {
        if (e.target === this.modalCreateAvd) {
          this.closeCreateAvdModal();
        }
      });
    }

    if (this.avdSearchInput) {
      this.avdSearchInput.addEventListener('input', () => {
        this.renderAvds();
      });
    }

    // Phase 13 Studio Screenshot & Recording
    if (this.btnStudioScreenshot) {
      this.btnStudioScreenshot.addEventListener('click', () => this.takeStudioScreenshot());
    }
    if (this.btnStudioRecordToggle) {
      this.btnStudioRecordToggle.addEventListener('click', () => this.toggleStudioRecording());
    }
    if (this.btnStudioOpenLogs) {
      this.btnStudioOpenLogs.addEventListener('click', () => this.openStudioDeviceLogs());
    }

    // Phase 13 Automation Events
    if (this.btnOpenCreateWorkflow) {
      this.btnOpenCreateWorkflow.addEventListener('click', () => this.openCreateWorkflowModal());
    }
    if (this.modalCreateWorkflowClose) {
      this.modalCreateWorkflowClose.addEventListener('click', () => this.closeCreateWorkflowModal());
    }
    if (this.modalCreateWorkflowCancel) {
      this.modalCreateWorkflowCancel.addEventListener('click', () => this.closeCreateWorkflowModal());
    }
    if (this.btnTemplateSmoke) {
      this.btnTemplateSmoke.addEventListener('click', () => this.setWorkflowTemplate('smoke'));
    }
    if (this.btnTemplateApp) {
      this.btnTemplateApp.addEventListener('click', () => this.setWorkflowTemplate('app'));
    }
    if (this.btnTemplateGesture) {
      this.btnTemplateGesture.addEventListener('click', () => this.setWorkflowTemplate('gesture'));
    }
    if (this.btnValidateWorkflow) {
      this.btnValidateWorkflow.addEventListener('click', () => this.validateWorkflowJSON());
    }
    if (this.btnRunWorkflow) {
      this.btnRunWorkflow.addEventListener('click', () => this.runAutomationWorkflow());
    }
    if (this.btnCancelExecution) {
      this.btnCancelExecution.addEventListener('click', () => this.cancelActiveExecution());
    }
    if (this.btnRefreshHistory) {
      this.btnRefreshHistory.addEventListener('click', () => this.loadExecutionHistory());
    }

    // Phase 13 Logcat Events
    if (this.logDeviceSelect) {
      this.logDeviceSelect.addEventListener('change', () => this.handleLogDeviceChange());
    }
    if (this.logLevelFilter) {
      this.logLevelFilter.addEventListener('change', () => this.pollLogcat());
    }
    if (this.logTagFilter) {
      this.logTagFilter.addEventListener('input', () => this.debounceLogPoll());
    }
    if (this.logSearchFilter) {
      this.logSearchFilter.addEventListener('input', () => this.debounceLogPoll());
    }
    if (this.btnLogClear) {
      this.btnLogClear.addEventListener('click', () => this.clearDeviceLogs());
    }
    if (this.btnLogStreamToggle) {
      this.btnLogStreamToggle.addEventListener('click', () => this.toggleLogStream());
    }
    if (this.btnLogExportTxt) {
      this.btnLogExportTxt.addEventListener('click', () => this.exportDeviceLogs('txt'));
    }
    if (this.btnLogExportJson) {
      this.btnLogExportJson.addEventListener('click', () => this.exportDeviceLogs('json'));
    }

    // Phase 13 Deep Diagnostics Events
    if (this.btnRefreshDeepDiag) {
      this.btnRefreshDeepDiag.addEventListener('click', () => this.fetchDeepDiagnostics());
    }
    if (this.diagDeepDeviceSelect) {
      this.diagDeepDeviceSelect.addEventListener('change', () => this.fetchDeepDiagnostics());
    }

    // Canvas Pointer Interactivity
    this.initCanvasPointerEvents();

    // Window resize observer
    window.addEventListener('resize', () => {
      this.handleResize();
    });
  }

  initRouting() {
    window.addEventListener('hashchange', () => {
      this.handleHashChange();
    });

    // Handle initial route
    this.handleHashChange();
  }

  handleHashChange() {
    const rawHash = window.location.hash.replace(/^#\/?/, '').trim();
    const route = rawHash || 'overview';
    this.navigateTo(route);
  }

  navigateTo(route) {
    const validRoutes = ['overview', 'devices', 'virtual', 'sessions', 'automation', 'diagnostics', 'settings'];
    const targetRoute = validRoutes.includes(route) ? route : 'overview';

    this.currentRoute = targetRoute;

    // Update active navigation link
    this.navLinks.forEach(link => {
      const linkRoute = link.getAttribute('data-route');
      if (linkRoute === targetRoute) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('active');
        link.removeAttribute('aria-current');
      }
    });

    // Update active page view
    this.pageViews.forEach(view => {
      if (view.id === `view-${targetRoute}`) {
        view.classList.add('active');
      } else {
        view.classList.remove('active');
      }
    });

    // Route specific actions
    if (targetRoute === 'devices') {
      this.loadDevices();
    } else if (targetRoute === 'virtual') {
      this.loadAvdEnvironment();
      this.loadAvds();
    } else if (targetRoute === 'sessions' || targetRoute === 'overview') {
      this.loadSessions();
    } else if (targetRoute === 'automation') {
      this.initAutomationRoute();
    } else if (targetRoute === 'diagnostics') {
      this.initDiagnosticsRoute();
    }

    // Scroll to top of main container
    const mainContainer = document.querySelector('.page-container');
    if (mainContainer) {
      mainContainer.scrollTop = 0;
    }
  }

  toggleSidebar() {
    const isCollapsed = this.sidebar.classList.toggle('collapsed');
    localStorage.setItem('kelvra_sidebar_collapsed', isCollapsed ? '1' : '0');
  }

  handleResize() {
    if (window.innerWidth < 1024) {
      this.sidebar.classList.add('collapsed');
    } else {
      const saved = localStorage.getItem('kelvra_sidebar_collapsed');
      if (saved === '1') {
        this.sidebar.classList.add('collapsed');
      } else {
        this.sidebar.classList.remove('collapsed');
      }
    }
  }

  async checkHealth() {
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        this.serviceStatusDot.className = 'status-dot complete pulse';
        this.serviceStatusText.textContent = `PORT :${data.port || 8098} ACTIVE`;
      } else {
        this.serviceStatusDot.className = 'status-dot blocked';
        this.serviceStatusText.textContent = 'SERVICE DEGRADED';
      }
    } catch {
      this.serviceStatusDot.className = 'status-dot error';
      this.serviceStatusText.textContent = 'PORT :8098 OFFLINE';
    }

    await this.fetchRegistryStats();
  }

  async fetchRegistryStats() {
    try {
      const res = await fetch('/api/registry/stats');
      if (res.ok) {
        const stats = await res.json();
        const total = stats.total || 0;
        const online = stats.online || 0;
        const connected = stats.connected || 0;
        const unauthorized = stats.unauthorized || 0;

        if (this.overviewDeviceCount) this.overviewDeviceCount.textContent = total;
        if (this.navBadgeDevices) this.navBadgeDevices.textContent = total;

        if (this.statTotalDevices) this.statTotalDevices.textContent = total;
        if (this.statOnlineDevices) this.statOnlineDevices.textContent = online;
        if (this.statConnectedDevices) this.statConnectedDevices.textContent = connected;
        if (this.statUnauthorizedDevices) this.statUnauthorizedDevices.textContent = unauthorized;
      }
    } catch {
      // Ignore background stats poll errors
    }
  }

  async loadDevices() {
    try {
      const res = await fetch('/api/devices');
      if (res.ok) {
        this.devices = await res.json();
        this.renderDevices();
        this.fetchRegistryStats();
      }
    } catch {
      this.showToast('Unable to load device fleet from server.', 'error', 3000);
    }
  }

  async scanFleet() {
    this.showToast('Scanning platform tools for attached devices...', 'info', 2000);
    try {
      const res = await fetch('/api/devices');
      if (res.ok) {
        this.devices = await res.json();
        const count = this.devices.length;
        this.renderDevices();
        this.fetchRegistryStats();
        this.showToast(`Fleet scan complete: ${count} device(s) found.`, 'success', 3000);
      } else {
        this.showToast('Fleet scan query failed. Check ADB daemon.', 'warning', 4000);
      }
    } catch {
      this.showToast('Unable to reach Device Lab API server.', 'error', 4000);
    }
  }

  getFilteredDevices() {
    const search = this.deviceSearchInput ? this.deviceSearchInput.value.toLowerCase().trim() : '';
    const platform = this.filterPlatform ? this.filterPlatform.value : '';
    const state = this.filterState ? this.filterState.value : '';

    return this.devices.filter(dev => {
      if (search) {
        const matchSerial = dev.serial.toLowerCase().includes(search);
        const matchModel = (dev.model || '').toLowerCase().includes(search);
        const matchMfr = (dev.manufacturer || '').toLowerCase().includes(search);
        const matchDisplay = (dev.display_name || '').toLowerCase().includes(search);
        if (!matchSerial && !matchModel && !matchMfr && !matchDisplay) {
          return false;
        }
      }

      if (platform && dev.platform !== platform) {
        return false;
      }

      if (state && dev.state !== state) {
        return false;
      }

      return true;
    });
  }

  renderDevices() {
    if (!this.devicesListContainer) return;

    const filtered = this.getFilteredDevices();

    if (filtered.length === 0) {
      this.devicesListContainer.innerHTML = `
        <div class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
            <line x1="12" y1="18" x2="12.01" y2="18"></line>
          </svg>
          <h2 class="empty-title">No Mobile Devices Discovered</h2>
          <p class="empty-description">
            Connect a physical Android device via USB with USB Debugging enabled, or boot a local virtual emulator.
          </p>
          <button id="btn-scan-devices-page-inner" class="btn primary" type="button">
            <span>Scan for Attached Devices</span>
          </button>
        </div>
      `;
      const btnInner = document.getElementById('btn-scan-devices-page-inner');
      if (btnInner) {
        btnInner.addEventListener('click', () => this.scanFleet());
      }
      return;
    }

    if (this.viewLayout === 'table') {
      this.renderTableView(filtered);
    } else {
      this.renderGridView(filtered);
    }

    this.bindDeviceActionButtons();
  }

  renderGridView(devices) {
    let html = '<div class="device-inventory-grid">';

    devices.forEach(dev => {
      const isOnline = dev.state === 'available' || dev.state === 'connected';
      const isConnected = dev.state === 'connected';
      const isUnauthorized = dev.state === 'unauthorized';
      const isBusy = dev.state === 'busy';

      let dotClass = 'error';
      let stateLabel = dev.state.toUpperCase();

      if (isOnline) {
        dotClass = isConnected ? 'complete pulse' : 'complete';
      } else if (isUnauthorized || isBusy) {
        dotClass = 'blocked';
      }

      const isApple = dev.platform === 'apple_physical' || dev.platform === 'apple_virtual';
      const platformLabel = dev.platform === 'apple_physical' ? 'Apple Physical' : (
        dev.platform === 'android_virtual' ? 'Android Virtual' : 'Android Physical'
      );
      const transportLabel = (dev.transport || 'usb').toUpperCase();
      const osSdkLabel = isApple
        ? `${this.escapeHtml(dev.os_name || 'iOS')} ${this.escapeHtml(dev.os_version || 'Unknown')}`
        : `${this.escapeHtml(dev.os_name || 'Android')} ${this.escapeHtml(dev.os_version || 'Unknown')} (API ${dev.sdk_level || 0})`;

      html += `
        <div class="device-inventory-card" data-device-id="${dev.id}">
          <div class="device-card-header">
            <div class="device-title-wrap">
              <span class="device-card-title">${this.escapeHtml(dev.display_name || dev.model || (isApple ? 'Apple Device' : 'Android Device'))}</span>
              <span class="device-card-subtitle">${this.escapeHtml(dev.manufacturer || (isApple ? 'Apple' : 'Unknown Manufacturer'))}</span>
            </div>
            <div class="status-indicator">
              <span class="status-dot ${dotClass}"></span>
              <span style="font-family: var(--font-mono); font-size: 11px;">${stateLabel}</span>
            </div>
          </div>

          <div class="device-badges-row">
            <span class="badge ${isApple ? 'accent' : ''}">${platformLabel}</span>
            <span class="badge">${transportLabel}</span>
            ${dev.battery_level !== undefined ? `<span class="badge" style="font-family: var(--font-mono);">Battery: ${dev.battery_level}%</span>` : ''}
          </div>

          <table class="device-specs-table">
            <tbody>
              <tr>
                <td class="spec-key">${isApple ? 'UDID' : 'Serial'}</td>
                <td class="spec-val">
                  <span class="device-serial-pill">
                    <span>${this.escapeHtml(dev.serial)}</span>
                    <button class="device-copy-btn" data-copy="${this.escapeHtml(dev.serial)}" title="Copy Serial" aria-label="Copy Serial">
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                      </svg>
                    </button>
                  </span>
                </td>
              </tr>
              <tr>
                <td class="spec-key">${isApple ? 'Operating System' : 'OS / SDK'}</td>
                <td class="spec-val">${osSdkLabel}</td>
              </tr>
              <tr>
                <td class="spec-key">Architecture</td>
                <td class="spec-val">${this.escapeHtml(dev.abi || (isApple ? 'arm64' : 'arm64-v8a'))}</td>
              </tr>
            </tbody>
          </table>

          ${isUnauthorized ? `
            <div class="device-unauthorized-alert">
              <svg class="alert-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <div class="alert-text">
                ${isApple ? (
                  dev.error && dev.error.recovery_hint
                    ? `<strong>Trust Required:</strong> ${this.escapeHtml(dev.error.recovery_hint)}`
                    : '<strong>Device Trust Required:</strong> Unlock your iPhone/iPad and tap <em>Trust This Computer</em> on the screen.'
                ) : '<strong>Unauthorized Device:</strong> Unlock your device screen and tap <em>Allow USB debugging</em> to authorize this workstation.'}
              </div>
            </div>
          ` : ''}

          <div class="device-card-footer">
            <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-tertiary);">ID: ${this.escapeHtml(dev.id)}</span>
            <div class="device-actions">
              <button class="btn sm btn-refresh-device" data-id="${this.escapeHtml(dev.id)}" title="Refresh Metadata" aria-label="Refresh Metadata" type="button">
                <span>Refresh</span>
              </button>
              ${isOnline ? `
                <button class="btn sm accent btn-open-studio" data-id="${this.escapeHtml(dev.id)}" type="button">
                  <span>${isApple ? 'Inspect Device' : 'View Screen'}</span>
                </button>
              ` : ''}
              ${isConnected ? `
                <button class="btn sm btn-disconnect" data-id="${this.escapeHtml(dev.id)}" type="button">
                  <span>Disconnect</span>
                </button>
              ` : (dev.state === 'available' ? `
                <button class="btn sm primary btn-connect" data-id="${this.escapeHtml(dev.id)}" type="button">
                  <span>Connect</span>
                </button>
              ` : `
                <button class="btn sm" disabled type="button">
                  <span>${isUnauthorized ? (isApple ? 'Trust Required' : 'Unauthorized') : 'Unavailable'}</span>
                </button>
              `)}
            </div>
          </div>
        </div>
      `;
    });

    html += '</div>';
    this.devicesListContainer.innerHTML = html;
  }

  renderTableView(devices) {
    let html = `
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Device Model</th>
              <th>Serial</th>
              <th>Platform / Transport</th>
              <th>OS / ABI</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
    `;

    devices.forEach(dev => {
      const isOnline = dev.state === 'available' || dev.state === 'connected';
      const isConnected = dev.state === 'connected';
      const isUnauthorized = dev.state === 'unauthorized';
      const isApple = dev.platform === 'apple_physical' || dev.platform === 'apple_virtual';
      const platformLabel = dev.platform === 'apple_physical' ? 'Apple Physical' : (
        dev.platform === 'android_virtual' ? 'Android Virtual' : 'Android Physical'
      );
      const osSdkLabel = isApple
        ? `${this.escapeHtml(dev.os_name || 'iOS')} ${this.escapeHtml(dev.os_version || 'Unknown')}`
        : `${this.escapeHtml(dev.os_name || 'Android')} ${this.escapeHtml(dev.os_version || 'Unknown')} (${this.escapeHtml(dev.abi || 'arm64-v8a')})`;

      let dotClass = 'error';
      if (isOnline) {
        dotClass = isConnected ? 'complete pulse' : 'complete';
      } else if (isUnauthorized) {
        dotClass = 'blocked';
      }

      html += `
        <tr>
          <td>
            <div class="status-indicator">
              <span class="status-dot ${dotClass}"></span>
              <span style="font-family: var(--font-mono); font-size: 11px;">${dev.state.toUpperCase()}</span>
            </div>
          </td>
          <td>
            <strong>${this.escapeHtml(dev.display_name || dev.model || (isApple ? 'Apple Device' : 'Unknown'))}</strong>
            <div style="font-size: 11px; color: var(--text-tertiary);">${this.escapeHtml(dev.manufacturer || (isApple ? 'Apple' : 'Unknown'))}</div>
          </td>
          <td class="tabular-nums">
            <span class="device-serial-pill">
              <span>${this.escapeHtml(dev.serial)}</span>
              <button class="device-copy-btn" data-copy="${this.escapeHtml(dev.serial)}" title="Copy Serial" aria-label="Copy Serial">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
              </button>
            </span>
          </td>
          <td>
            <span class="badge ${isApple ? 'accent' : ''}">${platformLabel}</span>
            <span class="badge">${(dev.transport || 'usb').toUpperCase()}</span>
          </td>
          <td style="font-family: var(--font-mono); font-size: 12px;">
            ${osSdkLabel}
          </td>
          <td>
            <div style="display: flex; gap: var(--space-2);">
              ${isOnline ? `
                <button class="btn sm accent btn-open-studio" data-id="${this.escapeHtml(dev.id)}" type="button">
                  <span>${isApple ? 'Inspect Device' : 'View Screen'}</span>
                </button>
              ` : ''}
              ${isConnected ? `
                <button class="btn sm btn-disconnect" data-id="${this.escapeHtml(dev.id)}" type="button">
                  <span>Disconnect</span>
                </button>
              ` : (dev.state === 'available' ? `
                <button class="btn sm primary btn-connect" data-id="${this.escapeHtml(dev.id)}" type="button">
                  <span>Connect</span>
                </button>
              ` : `
                <button class="btn sm" disabled type="button">
                  <span>${isUnauthorized ? (isApple ? 'Trust Required' : 'Unauthorized') : 'Unavailable'}</span>
                </button>
              `)}
            </div>
          </td>
        </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>
    `;

    this.devicesListContainer.innerHTML = html;
  }

  bindDeviceActionButtons() {
    // Studio open buttons
    const studioBtns = this.devicesListContainer.querySelectorAll('.btn-open-studio');
    studioBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.getAttribute('data-id');
        if (id) {
          this.openDeviceStudio(id);
        }
      });
    });
    // Copy buttons
    const copyBtns = this.devicesListContainer.querySelectorAll('.device-copy-btn');
    copyBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const text = btn.getAttribute('data-copy');
        if (text) {
          navigator.clipboard.writeText(text).then(() => {
            this.showToast(`Serial copied: ${text}`, 'info', 2000);
          });
        }
      });
    });

    // Connect buttons
    const connectBtns = this.devicesListContainer.querySelectorAll('.btn-connect');
    connectBtns.forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        if (id) {
          await this.connectDevice(id);
        }
      });
    });

    // Refresh buttons
    const refreshBtns = this.devicesListContainer.querySelectorAll('.btn-refresh-device');
    refreshBtns.forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.getAttribute('data-id');
        if (id) {
          await this.refreshDevice(id);
        }
      });
    });

    // Disconnect buttons
    const disconnectBtns = this.devicesListContainer.querySelectorAll('.btn-disconnect');
    disconnectBtns.forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        if (id) {
          await this.disconnectDevice(id);
        }
      });
    });
  }

  async refreshDevice(deviceId) {
    this.showToast(`Refreshing metadata for ${deviceId}...`, 'info', 2000);
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/refresh`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        this.showToast(`Device ${data.serial || deviceId} refreshed.`, 'success', 2500);
        await this.loadDevices();
      } else {
        const err = await res.json().catch(() => ({}));
        this.showToast(`Refresh failed: ${err.detail || 'Error'}`, 'error', 4000);
      }
    } catch {
      this.showToast('Network error while refreshing device.', 'error', 3000);
    }
  }

  async connectDevice(deviceId) {
    this.showToast(`Connecting to device ${deviceId}...`, 'info', 2000);
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/connect`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        this.showToast(`Device ${data.serial || deviceId} connected successfully.`, 'success', 3000);
        await this.loadDevices();
      } else {
        const err = await res.json().catch(() => ({}));
        this.showToast(`Connection failed: ${err.detail || 'Unable to connect'}`, 'error', 4000);
      }
    } catch {
      this.showToast('Network error while connecting to device.', 'error', 3000);
    }
  }

  async disconnectDevice(deviceId) {
    this.showToast(`Disconnecting session for ${deviceId}...`, 'info', 2000);
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/disconnect`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        this.showToast(`Device ${data.serial || deviceId} disconnected.`, 'info', 3000);
        await this.loadDevices();
      } else {
        const err = await res.json().catch(() => ({}));
        this.showToast(`Disconnect failed: ${err.detail || 'Error'}`, 'error', 4000);
      }
    } catch {
      this.showToast('Network error while disconnecting device.', 'error', 3000);
    }
  }

  // ==========================================================================
  // Phase 10: Device Viewer Studio & Remote Control
  // ==========================================================================

  async openDeviceStudio(deviceId) {
    let dev = this.devices.find(d => d.id === deviceId || d.serial === deviceId);
    if (!dev) {
      try {
        const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}`);
        if (res.ok) dev = await res.json();
      } catch {}
    }
    if (!dev) {
      this.showToast(`Device ${deviceId} not found.`, 'error', 3000);
      return;
    }

    this.activeStudioDevice = dev;

    const isApple = dev.platform === 'apple_physical' || dev.platform === 'apple_virtual';

    if (this.devicesInventoryPanel) this.devicesInventoryPanel.style.display = 'none';
    if (this.devicesStudioPanel) this.devicesStudioPanel.style.display = 'flex';

    if (this.studioDeviceName) {
      this.studioDeviceName.textContent = dev.display_name || dev.model || (isApple ? 'Apple Device' : 'Android Device');
    }
    if (this.studioDeviceSerial) {
      this.studioDeviceSerial.textContent = dev.serial;
    }

    const [w, h] = this.getDeviceDimensions();
    if (this.studioHudRes) {
      this.studioHudRes.textContent = `${w}x${h}`;
    }
    if (this.studioScreenCanvas) {
      this.studioScreenCanvas.width = w > 0 ? w : 720;
      this.studioScreenCanvas.height = h > 0 ? h : 1600;
    }

    if (isApple) {
      if (this.btnStudioStreamToggle) this.btnStudioStreamToggle.disabled = true;
      if (this.btnStudioLeaseToggle) this.btnStudioLeaseToggle.disabled = true;
      this.updateStreamUIState(
        'INSPECTION_MODE',
        'Physical Apple iOS/iPadOS device inspection active. Live screen streaming and remote touch injection are not supported on Windows host environments. Hardware metadata and lockdown trust verification are active.',
        'Apple Device Inspection Mode'
      );
      return;
    }

    if (this.btnStudioStreamToggle) this.btnStudioStreamToggle.disabled = false;
    if (this.btnStudioLeaseToggle) this.btnStudioLeaseToggle.disabled = false;

    this.updateStreamUIState('IDLE', 'Click "Start Stream" to negotiate visual teleoperation session.', 'Stream Idle');
    await this.checkCurrentLease();
    await this.startStream();
  }

  async closeDeviceStudio() {
    await this.stopStream();
    if (this.btnStudioStreamToggle) this.btnStudioStreamToggle.disabled = false;
    if (this.btnStudioLeaseToggle) this.btnStudioLeaseToggle.disabled = false;
    if (this.heldLeaseToken) {
      await this.releaseLease(false);
    }
    if (this.pollDiagTimer) {
      clearInterval(this.pollDiagTimer);
      this.pollDiagTimer = null;
    }
    if (this.leaseHeartbeatTimer) {
      clearInterval(this.leaseHeartbeatTimer);
      this.leaseHeartbeatTimer = null;
    }

    this.activeStudioDevice = null;
    if (this.devicesStudioPanel) this.devicesStudioPanel.style.display = 'none';
    if (this.devicesInventoryPanel) this.devicesInventoryPanel.style.display = 'block';

    await this.loadDevices();
  }

  getDeviceDimensions() {
    if (!this.activeStudioDevice) return [720, 1600];
    const dev = this.activeStudioDevice;
    if (dev.screen_width && dev.screen_height) {
      return [dev.screen_width, dev.screen_height];
    }
    if (dev.metadata && dev.metadata.display_resolution) {
      const parts = String(dev.metadata.display_resolution).toLowerCase().split('x');
      if (parts.length === 2) {
        const parsedW = parseInt(parts[0], 10);
        const parsedH = parseInt(parts[1], 10);
        if (!isNaN(parsedW) && !isNaN(parsedH) && parsedW > 0 && parsedH > 0) {
          return [parsedW, parsedH];
        }
      }
    }
    return [1080, 2400];
  }

  updateStreamUIState(state, infoText, titleText) {
    this.streamState = state;
    if (this.studioStreamStatusText) {
      this.studioStreamStatusText.textContent = state;
    }

    let dotClass = 'idle';
    if (state === 'STREAMING') dotClass = 'complete pulse';
    else if (state === 'STARTING' || state === 'PREPARING') dotClass = 'working';
    else if (state === 'FAILED' || state === 'ERROR') dotClass = 'error';

    if (this.studioStreamStatusDot) {
      this.studioStreamStatusDot.className = `status-dot ${dotClass}`;
    }

    if (this.btnStudioStreamToggle) {
      const span = this.btnStudioStreamToggle.querySelector('span');
      if (span) {
        span.textContent = (state === 'STREAMING' || state === 'STARTING') ? 'Stop Stream' : 'Start Stream';
      }
      this.btnStudioStreamToggle.className = (state === 'STREAMING' || state === 'STARTING') ? 'btn sm' : 'btn sm primary';
    }

    if (this.studioOverlay) {
      if (state === 'STREAMING') {
        this.studioOverlay.classList.add('hidden');
      } else {
        this.studioOverlay.classList.remove('hidden');
        if (titleText && this.studioOverlayTitle) this.studioOverlayTitle.textContent = titleText;
        if (infoText && this.studioOverlayDesc) this.studioOverlayDesc.textContent = infoText;
      }
    }

    if (state !== 'STREAMING' && this.studioHudFps) {
      this.studioHudFps.textContent = '0.0 FPS';
    }
  }

  async toggleStream() {
    if (this.streamState === 'STREAMING' || this.streamState === 'STARTING') {
      await this.stopStream();
    } else {
      await this.startStream();
    }
  }

  async startStream() {
    if (!this.activeStudioDevice) return;
    const dev = this.activeStudioDevice;
    const qualityVal = this.studioQualitySelect ? parseInt(this.studioQualitySelect.value, 10) : 720;
    const fpsVal = this.studioFpsSelect ? parseInt(this.studioFpsSelect.value, 10) : 30;

    this.updateStreamUIState('STARTING', 'Connecting WebSocket and starting capture pipe...', 'Negotiating Stream');

    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(dev.serial)}/stream/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          max_width: qualityVal || 720,
          max_fps: fpsVal || 30
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        this.updateStreamUIState('FAILED', err.detail || 'Failed to start screen stream.', 'Stream Failed');
        this.showToast(`Stream negotiation error: ${err.detail || 'Service unavailable'}`, 'error', 4000);
        return;
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/devices/${encodeURIComponent(dev.serial)}/stream`;

      if (this.streamWs) {
        try { this.streamWs.close(); } catch {}
        this.streamWs = null;
      }

      this.streamWs = new WebSocket(wsUrl);

      this.streamWs.onopen = () => {
        this.updateStreamUIState('STREAMING');
        this.showToast(`Screen stream active (${qualityVal}p @ ${fpsVal}fps).`, 'success', 2500);
      };

      this.streamWs.onmessage = (event) => {
        if (typeof event.data === 'string') {
          try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'frame') {
              this.renderFrame(msg.data, msg.fps);
            } else if (msg.type === 'state') {
              if (msg.state === 'Stopped') {
                this.updateStreamUIState('STOPPED', 'Stream stopped by server.', 'Stream Stopped');
              }
            } else if (msg.type === 'error') {
              this.updateStreamUIState('ERROR', msg.message || 'Stream error encountered.', 'Stream Error');
              this.showToast(`Stream error: ${msg.message || msg.code}`, 'error', 4000);
            }
          } catch (e) {
            // Non-JSON frame
          }
        } else if (event.data instanceof Blob) {
          const url = URL.createObjectURL(event.data);
          const img = new Image();
          img.onload = () => {
            if (this.canvasCtx && this.studioScreenCanvas) {
              this.canvasCtx.drawImage(img, 0, 0, this.studioScreenCanvas.width, this.studioScreenCanvas.height);
            }
            URL.revokeObjectURL(url);
          };
          img.src = url;
        }
      };

      this.streamWs.onerror = () => {
        this.updateStreamUIState('ERROR', 'WebSocket connection encountered a network error.', 'Stream Connection Error');
      };

      this.streamWs.onclose = () => {
        if (this.streamState === 'STREAMING') {
          this.updateStreamUIState('STOPPED', 'Stream connection closed.', 'Stream Closed');
        }
      };

      if (!this.pollDiagTimer) {
        this.pollDiagTimer = setInterval(() => this.pollDiagnostics(), 2000);
      }
    } catch {
      this.updateStreamUIState('FAILED', 'Unable to initiate stream connection.', 'Connection Failed');
      this.showToast('Network error while starting stream.', 'error', 3000);
    }
  }

  renderFrame(base64Data, fps) {
    if (!this.canvasCtx || !this.studioScreenCanvas) return;
    const img = new Image();
    img.onload = () => {
      if (this.canvasCtx && this.studioScreenCanvas) {
        this.canvasCtx.drawImage(img, 0, 0, this.studioScreenCanvas.width, this.studioScreenCanvas.height);
      }
    };
    img.src = 'data:image/jpeg;base64,' + base64Data;

    if (fps !== undefined && this.studioHudFps) {
      this.studioHudFps.textContent = `${Number(fps).toFixed(1)} FPS`;
    }
    if (fps !== undefined && this.diagFps) {
      this.diagFps.textContent = Number(fps).toFixed(1);
    }
  }

  async stopStream() {
    if (this.streamWs) {
      try { this.streamWs.close(); } catch {}
      this.streamWs = null;
    }

    if (this.pollDiagTimer) {
      clearInterval(this.pollDiagTimer);
      this.pollDiagTimer = null;
    }

    if (this.activeStudioDevice) {
      try {
        await fetch(`/api/devices/${encodeURIComponent(this.activeStudioDevice.serial)}/stream/stop`, {
          method: 'POST'
        });
      } catch {}
    }

    this.updateStreamUIState('STOPPED', 'Screen stream stopped. Click "Start Stream" to resume.', 'Stream Paused');
  }

  async toggleLease() {
    if (this.heldLeaseToken) {
      await this.releaseLease(true);
    } else {
      await this.acquireLease();
    }
  }

  async acquireLease() {
    if (!this.activeStudioDevice) return;
    const dev = this.activeStudioDevice;
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(dev.serial)}/lease`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operator_id: 'operator-web-ui',
          role: 'admin',
          ttl_seconds: 300
        })
      });

      if (res.ok) {
        const data = await res.json();
        this.heldLeaseToken = data.session_token;
        this.updateLeaseUI(true, 'operator-web-ui', data.expires_in_seconds || 300);
        this.showToast('Exclusive operator lease acquired. Remote input unlocked.', 'success', 3000);

        if (!this.leaseHeartbeatTimer) {
          this.leaseHeartbeatTimer = setInterval(() => this.renewLease(), 20000);
        }
        await this.loadSessions();
      } else if (res.status === 409) {
        const err = await res.json().catch(() => ({}));
        const holder = (err.detail && err.detail.held_by) ? err.detail.held_by : 'another session';
        this.showToast(`Device already leased exclusively by ${holder}.`, 'warning', 4000);
        await this.checkCurrentLease();
      } else if (res.status === 403) {
        this.showToast('Device is unauthorized. Cannot acquire input lease.', 'error', 4000);
      } else {
        const err = await res.json().catch(() => ({}));
        this.showToast(`Failed to acquire lease: ${err.detail || 'Error'}`, 'error', 4000);
      }
    } catch {
      this.showToast('Network error while requesting operator lease.', 'error', 3000);
    }
  }

  async renewLease() {
    if (!this.activeStudioDevice || !this.heldLeaseToken) return;
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(this.activeStudioDevice.serial)}/lease/renew`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_token: this.heldLeaseToken,
          extension_seconds: 300
        })
      });
      if (res.ok) {
        const data = await res.json();
        this.updateLeaseUI(true, 'operator-web-ui', data.expires_in_seconds || 300);
      } else {
        this.heldLeaseToken = null;
        if (this.leaseHeartbeatTimer) {
          clearInterval(this.leaseHeartbeatTimer);
          this.leaseHeartbeatTimer = null;
        }
        this.updateLeaseUI(false);
        this.showToast('Operator lease expired or revoked.', 'warning', 3000);
      }
    } catch {
      // Lease renewal network hiccup
    }
  }

  async releaseLease(notify = true) {
    if (!this.activeStudioDevice) return;
    const token = this.heldLeaseToken;
    this.heldLeaseToken = null;

    if (this.leaseHeartbeatTimer) {
      clearInterval(this.leaseHeartbeatTimer);
      this.leaseHeartbeatTimer = null;
    }

    try {
      await fetch(`/api/devices/${encodeURIComponent(this.activeStudioDevice.serial)}/lease${token ? `?session_token=${encodeURIComponent(token)}` : ''}`, {
        method: 'DELETE'
      });
    } catch {}

    this.updateLeaseUI(false);
    if (notify) {
      this.showToast('Operator lease released. Returning to read-only viewer mode.', 'info', 2500);
    }
    await this.loadSessions();
  }

  async checkCurrentLease() {
    if (!this.activeStudioDevice) return;
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(this.activeStudioDevice.serial)}/lease`);
      if (res.ok) {
        const data = await res.json();
        if (data.active && data.lease) {
          const isOurs = (data.lease.session_token && data.lease.session_token === this.heldLeaseToken);
          this.updateLeaseUI(isOurs, data.lease.client_id, data.lease.expires_in_seconds);
        } else {
          this.updateLeaseUI(false);
        }
      }
    } catch {}
  }

  updateLeaseUI(isHeldByUs, holderName = '', expiresIn = 0) {
    if (this.studioLeaseBadge) {
      if (isHeldByUs) {
        this.studioLeaseBadge.textContent = 'Exclusive Operator';
        this.studioLeaseBadge.className = 'badge accent';
      } else if (holderName) {
        this.studioLeaseBadge.textContent = `Locked (${holderName})`;
        this.studioLeaseBadge.className = 'badge';
      } else {
        this.studioLeaseBadge.textContent = 'Read-Only Viewer';
        this.studioLeaseBadge.className = 'badge';
      }
    }

    if (this.btnStudioLeaseToggle) {
      const span = this.btnStudioLeaseToggle.querySelector('span');
      if (span) {
        span.textContent = isHeldByUs ? 'Release Lease' : 'Acquire Operator Lease';
      }
      this.btnStudioLeaseToggle.className = isHeldByUs ? 'btn sm' : 'btn sm primary';
    }

    if (this.diagLeaseIndicator) {
      this.diagLeaseIndicator.className = isHeldByUs ? 'status-dot complete' : (holderName ? 'status-dot blocked' : 'status-dot idle');
    }
    if (this.diagLeaseHolder) {
      this.diagLeaseHolder.textContent = holderName || 'None';
    }
    if (this.diagLeaseExpires) {
      this.diagLeaseExpires.textContent = expiresIn > 0 ? `${Math.round(expiresIn)}s` : '--';
    }
  }

  initCanvasPointerEvents() {
    if (!this.studioScreenCanvas) return;

    const onPointerDown = (e) => {
      const coords = this.getCanvasTouchCoords(e);
      if (!coords) return;
      this.touchStartData = {
        ...coords,
        time: Date.now()
      };
    };

    const onPointerUp = async (e) => {
      if (!this.touchStartData) return;
      const endCoords = this.getCanvasTouchCoords(e);
      const start = this.touchStartData;
      this.touchStartData = null;

      if (!endCoords) return;

      const dx = endCoords.x - start.x;
      const dy = endCoords.y - start.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const dt = Date.now() - start.time;

      this.showTouchRipple(endCoords.viewportX, endCoords.viewportY);

      if (!this.heldLeaseToken) {
        this.showToast('Acquire an Operator Lease to inject touch inputs.', 'warning', 2500);
        return;
      }

      if (!this.activeStudioDevice) return;
      const dev = this.activeStudioDevice;

      try {
        if (dist < 12 && dt < 450) {
          // Tap
          await fetch(`/api/devices/${encodeURIComponent(dev.serial)}/input/tap`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              x: start.x,
              y: start.y,
              session_token: this.heldLeaseToken
            })
          });
        } else if (dist >= 12) {
          // Swipe
          await fetch(`/api/devices/${encodeURIComponent(dev.serial)}/input/swipe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              x1: start.x,
              y1: start.y,
              x2: endCoords.x,
              y2: endCoords.y,
              duration_ms: Math.min(Math.max(dt, 100), 1000),
              session_token: this.heldLeaseToken
            })
          });
        } else if (dist < 12 && dt >= 450) {
          // Long press simulated via swipe in place
          await fetch(`/api/devices/${encodeURIComponent(dev.serial)}/input/swipe`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              x1: start.x,
              y1: start.y,
              x2: start.x,
              y2: start.y,
              duration_ms: Math.min(dt, 1000),
              session_token: this.heldLeaseToken
            })
          });
        }
      } catch {
        this.showToast('Failed to dispatch touch input.', 'error', 2000);
      }
    };

    this.studioScreenCanvas.addEventListener('mousedown', onPointerDown);
    this.studioScreenCanvas.addEventListener('mouseup', onPointerUp);

    this.studioScreenCanvas.addEventListener('touchstart', onPointerDown, { passive: true });
    this.studioScreenCanvas.addEventListener('touchend', onPointerUp, { passive: true });
  }

  getCanvasTouchCoords(e) {
    if (!this.studioScreenCanvas) return null;
    const rect = this.studioScreenCanvas.getBoundingClientRect();
    let clientX = e.clientX;
    let clientY = e.clientY;
    if (clientX === undefined && e.changedTouches && e.changedTouches.length > 0) {
      clientX = e.changedTouches[0].clientX;
      clientY = e.changedTouches[0].clientY;
    }
    if (clientX === undefined || clientY === undefined) return null;

    const relX = clientX - rect.left;
    const relY = clientY - rect.top;

    const [nativeW, nativeH] = this.getDeviceDimensions();
    const scaleX = nativeW / rect.width;
    const scaleY = nativeH / rect.height;

    const devX = Math.round(relX * scaleX);
    const devY = Math.round(relY * scaleY);

    return {
      x: Math.max(0, Math.min(nativeW - 1, devX)),
      y: Math.max(0, Math.min(nativeH - 1, devY)),
      viewportX: relX,
      viewportY: relY
    };
  }

  showTouchRipple(viewportX, viewportY) {
    if (!this.studioViewport) return;
    const ripple = document.createElement('div');
    ripple.className = 'touch-ripple';
    ripple.style.width = '24px';
    ripple.style.height = '24px';
    ripple.style.marginLeft = '-12px';
    ripple.style.marginTop = '-12px';
    ripple.style.left = `${viewportX}px`;
    ripple.style.top = `${viewportY}px`;
    this.studioViewport.appendChild(ripple);
    setTimeout(() => {
      if (ripple.parentNode) ripple.parentNode.removeChild(ripple);
    }, 320);
  }

  async sendKey(keyName) {
    if (!this.activeStudioDevice) return;
    if (!this.heldLeaseToken) {
      this.showToast('Acquire an Operator Lease to inject hardware keys.', 'warning', 2500);
      return;
    }
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(this.activeStudioDevice.serial)}/input/key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          key: keyName,
          session_token: this.heldLeaseToken
        })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        this.showToast(`Hardware key error: ${err.detail || 'Failed'}`, 'error', 3000);
      }
    } catch {
      this.showToast('Network error while dispatching key event.', 'error', 2500);
    }
  }

  async sendText() {
    if (!this.activeStudioDevice || !this.studioTextInput) return;
    const textVal = this.studioTextInput.value;
    if (!textVal) return;

    if (!this.heldLeaseToken) {
      this.showToast('Acquire an Operator Lease to inject text.', 'warning', 2500);
      return;
    }

    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(this.activeStudioDevice.serial)}/input/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textVal,
          session_token: this.heldLeaseToken
        })
      });
      if (res.ok) {
        this.studioTextInput.value = '';
        this.showToast('Text injected into focused device field.', 'info', 1800);
      } else {
        const err = await res.json().catch(() => ({}));
        this.showToast(`Text injection error: ${err.detail || 'Failed'}`, 'error', 3000);
      }
    } catch {
      this.showToast('Network error while injecting text.', 'error', 2500);
    }
  }

  toggleFullscreen() {
    if (!this.studioViewport) return;
    if (!document.fullscreenElement) {
      this.studioViewport.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  async pollDiagnostics() {
    if (!this.activeStudioDevice) return;
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(this.activeStudioDevice.serial)}/stream/status`);
      if (res.ok) {
        const data = await res.json();
        if (this.diagFps && data.fps !== undefined) this.diagFps.textContent = Number(data.fps).toFixed(1);
        if (this.diagFrames && data.total_frames !== undefined) this.diagFrames.textContent = data.total_frames;
        if (this.diagDropped && data.dropped_frames !== undefined) this.diagDropped.textContent = data.dropped_frames;
        if (this.diagBytes && data.bytes_sent !== undefined) {
          const kb = (data.bytes_sent / 1024).toFixed(1);
          this.diagBytes.textContent = `${kb} KB`;
        }
        if (this.diagStartup && data.startup_duration_ms !== undefined) {
          this.diagStartup.textContent = `${Number(data.startup_duration_ms).toFixed(0)} ms`;
        }
        if (this.diagViewers && data.active_viewers !== undefined) this.diagViewers.textContent = data.active_viewers;
      }
    } catch {}
  }

  async loadSessions() {
    try {
      const res = await fetch('/api/sessions');
      if (!res.ok) return;
      const sessions = await res.json();

      if (this.overviewSessionCount) {
        this.overviewSessionCount.textContent = sessions.length;
      }

      if (!this.sessionsLeaseRows) return;

      if (!sessions || sessions.length === 0) {
        this.sessionsLeaseRows.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-tertiary); padding: var(--space-6);">
              No active operator leases held. Devices are available for reservation.
            </td>
          </tr>
        `;
        return;
      }

      let html = '';
      sessions.forEach(s => {
        const exp = Math.max(0, Math.round(s.expires_in_seconds || 0));
        const dtStr = s.created_at ? new Date(s.created_at * 1000).toLocaleTimeString() : '--';
        html += `
          <tr>
            <td class="tabular-nums mono" style="font-size: 12px; font-weight: 600;">${this.escapeHtml(s.device_id)}</td>
            <td>
              <span class="status-indicator">
                <span class="status-dot complete pulse"></span>
                <span>${this.escapeHtml(s.client_id || 'operator')}</span>
              </span>
            </td>
            <td><span class="badge accent">${this.escapeHtml(s.role || 'operator')}</span></td>
            <td class="tabular-nums mono" style="font-size: 12px;">${dtStr}</td>
            <td class="tabular-nums mono" style="font-size: 12px;">${exp}s</td>
            <td>
              <button class="btn sm btn-revoke-session" data-device-id="${this.escapeHtml(s.device_id)}" type="button">
                <span>Revoke</span>
              </button>
            </td>
          </tr>
        `;
      });
      this.sessionsLeaseRows.innerHTML = html;

      const revokeBtns = this.sessionsLeaseRows.querySelectorAll('.btn-revoke-session');
      revokeBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
          const devId = btn.getAttribute('data-device-id');
          if (devId) {
            await this.revokeSession(devId);
          }
        });
      });
    } catch {}
  }

  async revokeSession(deviceId) {
    this.showToast(`Revoking lease for ${deviceId}...`, 'info', 2000);
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(deviceId)}/lease?force=true`, {
        method: 'DELETE'
      });
      if (res.ok) {
        this.showToast(`Lease on ${deviceId} successfully revoked.`, 'success', 2500);
        await this.loadSessions();
        if (this.activeStudioDevice && (this.activeStudioDevice.id === deviceId || this.activeStudioDevice.serial === deviceId)) {
          this.heldLeaseToken = null;
          await this.checkCurrentLease();
        }
      } else {
        const err = await res.json().catch(() => ({}));
        this.showToast(`Revocation error: ${err.detail || 'Failed'}`, 'error', 3000);
      }
    } catch {
      this.showToast('Network error while revoking lease.', 'error', 3000);
    }
  }

  loadSettings() {
    const savedPath = localStorage.getItem('kelvra_adb_path');
    const savedTier = localStorage.getItem('kelvra_streaming_tier');
    const savedTimeout = localStorage.getItem('kelvra_lease_timeout');

    const inputPath = document.getElementById('setting-adb-path');
    if (inputPath && savedPath) {
      inputPath.value = savedPath;
    }

    if (savedTier) {
      const radio = document.querySelector(`input[name="streaming-tier"][value="${savedTier}"]`);
      if (radio) radio.checked = true;
    }

    const inputTimeout = document.getElementById('setting-lease-timeout');
    if (inputTimeout && savedTimeout) {
      inputTimeout.value = savedTimeout;
    }
  }

  async saveSettings() {
    const inputPath = document.getElementById('setting-adb-path');
    const selectedTier = document.querySelector('input[name="streaming-tier"]:checked');
    const inputTimeout = document.getElementById('setting-lease-timeout');

    let adbPathVal = '';
    if (inputPath) {
      adbPathVal = inputPath.value.trim();
      localStorage.setItem('kelvra_adb_path', adbPathVal);
    }
    if (selectedTier) {
      localStorage.setItem('kelvra_streaming_tier', selectedTier.value);
    }
    if (inputTimeout) {
      localStorage.setItem('kelvra_lease_timeout', inputTimeout.value);
    }

    if (adbPathVal) {
      try {
        const res = await fetch('/api/providers/android/configure', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ adb_path: adbPathVal })
        });
        if (res.ok) {
          const data = await res.json();
          this.showToast(`ADB configured: ${data.version || 'Ready'}`, 'success', 3000);
          this.loadDevices();
          return;
        } else {
          const err = await res.json().catch(() => ({}));
          this.showToast(`ADB configuration error: ${err.detail || 'Invalid executable'}`, 'error', 4000);
          return;
        }
      } catch {
        this.showToast('Failed to contact provider configuration API.', 'warning', 3000);
      }
    }

    this.showToast('Device Lab settings saved successfully.', 'success', 3000);
  }

  showToast(message, type = 'info', duration = 3000) {
    if (!this.toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'status');

    const dot = document.createElement('span');
    dot.className = `status-dot ${type === 'success' ? 'complete' : type === 'error' ? 'error' : type === 'warning' ? 'blocked' : 'working'}`;
    toast.appendChild(dot);

    const text = document.createElement('span');
    text.textContent = message;
    toast.appendChild(text);

    this.toastContainer.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, duration);
  }

  showConfirm(title, message, onConfirm) {
    if (!this.modalBackdrop) return;
    this.modalTitle.textContent = title;
    this.modalBody.textContent = message;
    this.pendingConfirmCallback = onConfirm;
    this.modalBackdrop.classList.add('open');
  }

  closeModal() {
    if (this.modalBackdrop) {
      this.modalBackdrop.classList.remove('open');
    }
    this.pendingConfirmCallback = null;
  }

  // ==========================================================================
  // Phase 11: Android Virtual Device (AVD Hub) Controller
  // ==========================================================================

  async loadAvdEnvironment() {
    try {
      const res = await fetch('/api/avd/environment');
      if (res.ok) {
        const data = await res.json();
        if (this.avdEnvSdkPath) {
          this.avdEnvSdkPath.textContent = data.sdk_root || 'None Detected';
          this.avdEnvSdkPath.title = data.sdk_root || '';
        }
        if (this.avdEnvEmuDot && this.avdEnvEmuStatus) {
          if (data.emulator_available) {
            this.avdEnvEmuDot.className = 'status-dot complete';
            this.avdEnvEmuStatus.textContent = 'Installed';
          } else {
            this.avdEnvEmuDot.className = 'status-dot error';
            this.avdEnvEmuStatus.textContent = 'Missing';
          }
        }
        if (this.avdEnvAvdmDot && this.avdEnvAvdmStatus) {
          if (data.avdmanager_available) {
            this.avdEnvAvdmDot.className = 'status-dot complete';
            this.avdEnvAvdmStatus.textContent = 'Available';
          } else {
            this.avdEnvAvdmDot.className = 'status-dot idle';
            this.avdEnvAvdmStatus.textContent = 'Not Found';
          }
        }
        if (this.avdEnvSysimgCount) {
          const count = data.system_images ? data.system_images.length : 0;
          this.avdEnvSysimgCount.textContent = `${count} Available`;
        }

        // Host setup guidance
        if (this.avdEnvGuidance && this.avdEnvGuidanceText) {
          if (data.guidance && data.guidance.length > 0) {
            let html = '<ul style="margin: 0; padding-left: var(--space-4); line-height: 1.6;">';
            data.guidance.forEach(item => {
              html += `<li>${this.escapeHtml(item)}</li>`;
            });
            html += '</ul>';
            this.avdEnvGuidanceText.innerHTML = html;
            this.avdEnvGuidance.style.display = 'block';
          } else {
            this.avdEnvGuidance.style.display = 'none';
          }
        }
      }
    } catch (err) {
      console.warn('Failed to load AVD environment status:', err);
    }
  }

  async loadAvds() {
    try {
      const res = await fetch('/api/avd/list');
      if (res.ok) {
        this.avds = await res.json();
        if (this.avdBadgeCount) {
          this.avdBadgeCount.textContent = `${this.avds.length} Virtual Device${this.avds.length === 1 ? '' : 's'}`;
        }
        this.renderAvds();

        // Check if any AVD is booting or launching to schedule poll
        const hasTransitioning = this.avds.some(avd => avd.status === 'LAUNCHING' || avd.status === 'BOOTING');
        if (hasTransitioning) {
          if (this.avdPollTimer) clearTimeout(this.avdPollTimer);
          this.avdPollTimer = setTimeout(() => this.pollAvdStatuses(), 2500);
        }
      }
    } catch (err) {
      console.error('Failed to load AVD list:', err);
      if (this.avdListContainer) {
        this.avdListContainer.innerHTML = `
          <div class="empty-state">
            <h2 class="empty-title">Error Loading Virtual Devices</h2>
            <p class="empty-description">Could not connect to AVD management endpoint.</p>
          </div>
        `;
      }
    }
  }

  async pollAvdStatuses() {
    if (this.currentRoute !== 'virtual') return;
    await this.loadAvds();
  }

  renderAvds() {
    if (!this.avdListContainer) return;

    const query = this.avdSearchInput ? this.avdSearchInput.value.toLowerCase().trim() : '';
    const filtered = this.avds.filter(avd => {
      if (!query) return true;
      const name = (avd.name || '').toLowerCase();
      const profile = (avd.device_profile || '').toLowerCase();
      const abi = (avd.abi || '').toLowerCase();
      const target = (avd.target || '').toLowerCase();
      return name.includes(query) || profile.includes(query) || abi.includes(query) || target.includes(query);
    });

    if (filtered.length === 0) {
      this.avdListContainer.innerHTML = `
        <div class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
          <h2 class="empty-title">${query ? 'No Matching Virtual Devices' : 'No Virtual Devices Configured'}</h2>
          <p class="empty-description">
            ${query ? 'Try modifying your search term.' : 'Create an Android Virtual Device using the button above or inspect local SDK images.'}
          </p>
          ${!query ? `
            <button class="btn primary" type="button" onclick="window.deviceLabApp.openCreateAvdModal()">
              <span>Create Virtual Device</span>
            </button>
          ` : ''}
        </div>
      `;
      return;
    }

    let html = '';
    filtered.forEach(avd => {
      let statusClass = 'idle';
      let cardClass = '';
      const st = avd.status || 'STOPPED';

      if (st === 'RUNNING') {
        statusClass = 'complete pulse';
        cardClass = 'running';
      } else if (st === 'BOOTING' || st === 'LAUNCHING') {
        statusClass = 'working pulse';
        cardClass = 'booting';
      } else if (st === 'ERROR') {
        statusClass = 'error';
        cardClass = 'error';
      }

      html += `
        <div class="avd-card ${cardClass}" data-avd-name="${this.escapeHtml(avd.name)}">
          <div class="avd-card-header">
            <div class="avd-card-title-wrap">
              <span class="avd-card-name">${this.escapeHtml(avd.name)}</span>
              <span class="avd-card-target">${this.escapeHtml(avd.target || 'Android')} (${this.escapeHtml(avd.abi || 'x86_64')})</span>
            </div>
            <div class="status-indicator">
              <span class="status-dot ${statusClass}"></span>
              <span style="font-family: var(--font-mono); font-size: 11px;">${this.escapeHtml(st)}</span>
            </div>
          </div>

          ${(st === 'BOOTING' || st === 'LAUNCHING') ? `
            <div class="avd-boot-progress">
              <div class="avd-boot-progress-bar"></div>
            </div>
          ` : ''}

          <div class="avd-card-specs">
            <div class="avd-spec-item">
              <span class="avd-spec-k">Profile</span>
              <span class="avd-spec-v">${this.escapeHtml(avd.device_profile || 'Default Handset')}</span>
            </div>
            <div class="avd-spec-item">
              <span class="avd-spec-k">API Level</span>
              <span class="avd-spec-v tabular-nums">${avd.api_level ? `API ${avd.api_level}` : 'Unknown'}</span>
            </div>
            <div class="avd-spec-item">
              <span class="avd-spec-k">RAM</span>
              <span class="avd-spec-v tabular-nums">${avd.ram_size_mb || 2048} MB</span>
            </div>
            <div class="avd-spec-item">
              <span class="avd-spec-k">Port / Serial</span>
              <span class="avd-spec-v mono">${avd.serial ? this.escapeHtml(avd.serial) : '--'}</span>
            </div>
          </div>

          <div class="avd-card-actions">
            ${st === 'STOPPED' || st === 'ERROR' ? `
              <button class="btn sm primary btn-launch-avd" type="button" data-name="${this.escapeHtml(avd.name)}">
                <span>Launch</span>
              </button>
              <button class="btn sm btn-delete-avd" type="button" data-name="${this.escapeHtml(avd.name)}" title="Delete Virtual Device">
                <span>Delete</span>
              </button>
            ` : ''}

            ${st === 'BOOTING' || st === 'LAUNCHING' ? `
              <button class="btn sm" type="button" disabled>
                <span>Booting...</span>
              </button>
              <button class="btn sm btn-stop-avd" type="button" data-name="${this.escapeHtml(avd.name)}">
                <span>Stop</span>
              </button>
            ` : ''}

            ${st === 'RUNNING' ? `
              <button class="btn sm primary btn-studio-avd" type="button" data-device-id="${this.escapeHtml(avd.device_id || '')}">
                <span>View Screen</span>
              </button>
              <button class="btn sm btn-stop-avd" type="button" data-name="${this.escapeHtml(avd.name)}">
                <span>Stop</span>
              </button>
            ` : ''}
          </div>
        </div>
      `;
    });

    this.avdListContainer.innerHTML = html;
    this.bindAvdCardActions();
  }

  bindAvdCardActions() {
    if (!this.avdListContainer) return;

    const launchBtns = this.avdListContainer.querySelectorAll('.btn-launch-avd');
    launchBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const name = btn.getAttribute('data-name');
        if (name) this.launchAvd(name);
      });
    });

    const stopBtns = this.avdListContainer.querySelectorAll('.btn-stop-avd');
    stopBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const name = btn.getAttribute('data-name');
        if (name) this.stopAvd(name);
      });
    });

    const deleteBtns = this.avdListContainer.querySelectorAll('.btn-delete-avd');
    deleteBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const name = btn.getAttribute('data-name');
        if (name) this.confirmDeleteAvd(name);
      });
    });

    const studioBtns = this.avdListContainer.querySelectorAll('.btn-studio-avd');
    studioBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const deviceId = btn.getAttribute('data-device-id');
        if (deviceId) {
          this.openAvdInStudio(deviceId);
        }
      });
    });
  }

  async launchAvd(name) {
    try {
      this.showToast(`Launching virtual device ${name}...`, 'info', 3000);
      const res = await fetch(`/api/avd/${encodeURIComponent(name)}/launch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ headless: false, cold_boot: false })
      });
      if (res.ok) {
        const data = await res.json();
        this.showToast(`AVD ${name} is booting on port ${data.port || 5554}`, 'success', 4000);
        await this.loadAvds();
      } else {
        const err = await res.json();
        this.showToast(err.detail || `Failed to launch AVD ${name}`, 'error', 5000);
      }
    } catch (err) {
      console.error('Launch AVD error:', err);
      this.showToast(`Connection error launching AVD ${name}`, 'error', 4000);
    }
  }

  async stopAvd(name) {
    try {
      this.showToast(`Stopping virtual device ${name}...`, 'info', 3000);
      const res = await fetch(`/api/avd/${encodeURIComponent(name)}/stop`, {
        method: 'POST'
      });
      if (res.ok) {
        this.showToast(`Virtual device ${name} stopped`, 'success', 3000);
        await this.loadAvds();
      } else {
        const err = await res.json();
        this.showToast(err.detail || `Failed to stop AVD ${name}`, 'error', 4000);
      }
    } catch (err) {
      console.error('Stop AVD error:', err);
      this.showToast(`Connection error stopping AVD ${name}`, 'error', 4000);
    }
  }

  openCreateAvdModal() {
    if (this.modalCreateAvd) {
      if (this.createAvdName) this.createAvdName.value = '';
      if (this.createAvdPackage) this.createAvdPackage.value = '';
      if (this.createAvdProfile) this.createAvdProfile.value = 'pixel_7';
      if (this.createAvdRam) this.createAvdRam.value = '2048';
      if (this.createAvdSdcard) this.createAvdSdcard.value = '512';
      this.modalCreateAvd.style.display = 'flex';
      this.modalCreateAvd.classList.add('open');
    }
  }

  closeCreateAvdModal() {
    if (this.modalCreateAvd) {
      this.modalCreateAvd.style.display = 'none';
      this.modalCreateAvd.classList.remove('open');
    }
  }

  async submitCreateAvd() {
    const name = this.createAvdName ? this.createAvdName.value.trim() : '';
    const pkg = this.createAvdPackage ? this.createAvdPackage.value.trim() : '';
    const profile = this.createAvdProfile ? this.createAvdProfile.value.trim() : '';
    const ram = this.createAvdRam ? parseInt(this.createAvdRam.value, 10) : 2048;
    const sdcard = this.createAvdSdcard ? parseInt(this.createAvdSdcard.value, 10) : 512;

    if (!name || !pkg) {
      this.showToast('Please fill in required fields (Name and System Image Package)', 'error', 3000);
      return;
    }

    try {
      this.showToast(`Creating virtual device ${name}...`, 'info', 3000);
      const res = await fetch('/api/avd/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          package: pkg,
          device_profile: profile || null,
          ram_size_mb: ram,
          sdcard_size_mb: sdcard
        })
      });

      if (res.ok) {
        this.showToast(`Virtual device ${name} created successfully`, 'success', 4000);
        this.closeCreateAvdModal();
        await this.loadAvds();
      } else {
        const err = await res.json();
        this.showToast(err.detail || `Failed to create virtual device ${name}`, 'error', 5000);
      }
    } catch (err) {
      console.error('Create AVD error:', err);
      this.showToast(`Connection error creating virtual device ${name}`, 'error', 4000);
    }
  }

  confirmDeleteAvd(name) {
    this.showConfirm(
      'Delete Virtual Device',
      `Are you sure you want to permanently delete virtual device "${name}"? This removes its configuration and virtual disk files.`,
      async () => {
        try {
          this.showToast(`Deleting virtual device ${name}...`, 'info', 3000);
          const res = await fetch(`/api/avd/${encodeURIComponent(name)}?confirm=true`, {
            method: 'DELETE'
          });
          if (res.ok) {
            this.showToast(`Virtual device ${name} deleted`, 'success', 3000);
            await this.loadAvds();
          } else {
            const err = await res.json();
            this.showToast(err.detail || `Failed to delete virtual device ${name}`, 'error', 4000);
          }
        } catch (err) {
          console.error('Delete AVD error:', err);
          this.showToast(`Connection error deleting virtual device ${name}`, 'error', 4000);
        }
      }
    );
  }

  openAvdInStudio(deviceId) {
    if (!deviceId) return;
    this.navigateTo('devices');
    setTimeout(() => {
      this.openDeviceStudio(deviceId);
    }, 200);
  }

  // ============================================================================
  // Phase 13: Studio Screenshot & Screen Recording
  // ============================================================================

  async takeStudioScreenshot() {
    if (!this.activeStudioDevice) {
      this.showToast('No active device in studio', 'warn', 3000);
      return;
    }
    const serial = this.activeStudioDevice.serial || this.activeStudioDevice.id;
    try {
      this.showToast('Capturing device screenshot...', 'info', 2000);
      const res = await fetch(`/api/devices/${encodeURIComponent(serial)}/screenshot?format=jpeg&quality=85`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        this.showToast(`Screenshot captured: ${data.name} (${Math.round(data.file_size_bytes / 1024)} KB)`, 'success', 4000);
        if (data.download_url) {
          const a = document.createElement('a');
          a.href = data.download_url;
          a.download = data.name;
          document.body.appendChild(a);
          a.click();
          a.remove();
        }
      } else {
        const err = await res.json();
        this.showToast(err.detail || 'Failed to capture screenshot', 'error', 4000);
      }
    } catch (err) {
      console.error('Screenshot capture error:', err);
      this.showToast('Network error capturing screenshot', 'error', 4000);
    }
  }

  async toggleStudioRecording() {
    if (!this.activeStudioDevice) {
      this.showToast('No active device in studio', 'warn', 3000);
      return;
    }
    const serial = this.activeStudioDevice.serial || this.activeStudioDevice.id;

    if (this.isStudioRecording) {
      // Stop recording
      try {
        this.showToast('Stopping and finalizing recording...', 'info', 2000);
        const res = await fetch(`/api/recordings/${encodeURIComponent(serial)}/stop`, {
          method: 'POST'
        });
        if (res.ok) {
          const data = await res.json();
          this.stopRecordingUI();
          this.showToast(`Recording saved: ${data.name || 'session.mp4'} (${Math.round(data.file_size_bytes / 1024)} KB)`, 'success', 5000);
          if (data.download_url) {
            const a = document.createElement('a');
            a.href = data.download_url;
            a.download = data.name || 'session.mp4';
            document.body.appendChild(a);
            a.click();
            a.remove();
          }
        } else {
          const err = await res.json();
          this.showToast(err.detail || 'Failed to stop recording', 'error', 4000);
        }
      } catch (err) {
        console.error('Stop recording error:', err);
        this.showToast('Network error stopping recording', 'error', 4000);
      }
    } else {
      // Start recording
      try {
        this.showToast('Starting screen recording...', 'info', 2000);
        const res = await fetch(`/api/recordings/${encodeURIComponent(serial)}/start`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ max_duration_seconds: 180, bit_rate_mbps: 4 })
        });
        if (res.ok) {
          this.startRecordingUI();
          this.showToast('Screen recording in progress (max 3 min)', 'success', 3000);
        } else {
          const err = await res.json();
          this.showToast(err.detail || 'Failed to start recording', 'error', 4000);
        }
      } catch (err) {
        console.error('Start recording error:', err);
        this.showToast('Network error starting recording', 'error', 4000);
      }
    }
  }

  startRecordingUI() {
    this.isStudioRecording = true;
    this.recordingSeconds = 0;
    const dot = document.getElementById('studio-record-dot');
    const text = document.getElementById('studio-record-text');
    const timer = document.getElementById('studio-record-timer');
    if (dot) dot.classList.add('recording-pulse');
    if (text) text.textContent = 'Stop';
    if (timer) {
      timer.style.display = 'inline';
      timer.textContent = '00:00';
    }
    clearInterval(this.recordingTimerInterval);
    this.recordingTimerInterval = setInterval(() => {
      this.recordingSeconds++;
      const mins = String(Math.floor(this.recordingSeconds / 60)).padStart(2, '0');
      const secs = String(this.recordingSeconds % 60).padStart(2, '0');
      if (timer) timer.textContent = `${mins}:${secs}`;
    }, 1000);
  }

  stopRecordingUI() {
    this.isStudioRecording = false;
    clearInterval(this.recordingTimerInterval);
    const dot = document.getElementById('studio-record-dot');
    const text = document.getElementById('studio-record-text');
    const timer = document.getElementById('studio-record-timer');
    if (dot) dot.classList.remove('recording-pulse');
    if (text) text.textContent = 'Record';
    if (timer) {
      timer.style.display = 'none';
      timer.textContent = '00:00';
    }
  }

  openStudioDeviceLogs() {
    if (!this.activeStudioDevice) return;
    const serial = this.activeStudioDevice.serial || this.activeStudioDevice.id;
    this.navigateTo('diagnostics');
    setTimeout(() => {
      if (this.logDeviceSelect) {
        this.logDeviceSelect.value = serial;
        this.handleLogDeviceChange();
      }
    }, 200);
  }

  // ============================================================================
  // Phase 13: Automation & Workflow Suite
  // ============================================================================

  initAutomationRoute() {
    this.populateDeviceSelectors();
    if (this.autoWorkflowJson && !this.autoWorkflowJson.value.trim()) {
      this.setWorkflowTemplate('smoke');
    }
    this.loadExecutionHistory();
  }

  populateDeviceSelectors() {
    const devices = this.devices || [];
    const onlineDevices = devices.filter(d => d.state === 'available' || d.state === 'busy');

    // 1. Auto target device
    if (this.autoTargetDevice) {
      const prevVal = this.autoTargetDevice.value;
      this.autoTargetDevice.innerHTML = '<option value="">Select target device...</option>';
      onlineDevices.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id || d.serial;
        opt.textContent = `${d.display_name || d.model || d.serial} (${d.platform})`;
        this.autoTargetDevice.appendChild(opt);
      });
      if (prevVal && this.autoTargetDevice.querySelector(`option[value="${prevVal}"]`)) {
        this.autoTargetDevice.value = prevVal;
      } else if (onlineDevices.length > 0) {
        this.autoTargetDevice.value = onlineDevices[0].id || onlineDevices[0].serial;
      }
    }

    // 2. Modal target device
    if (this.workflowTargetDeviceInput) {
      this.workflowTargetDeviceInput.innerHTML = '<option value="">Select target device...</option>';
      onlineDevices.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id || d.serial;
        opt.textContent = `${d.display_name || d.model || d.serial} (${d.platform})`;
        this.workflowTargetDeviceInput.appendChild(opt);
      });
    }

    // 3. Log target device
    if (this.logDeviceSelect) {
      const prevVal = this.logDeviceSelect.value;
      this.logDeviceSelect.innerHTML = '<option value="">Select target device...</option>';
      devices.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.serial || d.id;
        opt.textContent = `${d.display_name || d.model || d.serial} (${d.platform})`;
        this.logDeviceSelect.appendChild(opt);
      });
      if (prevVal && this.logDeviceSelect.querySelector(`option[value="${prevVal}"]`)) {
        this.logDeviceSelect.value = prevVal;
      } else if (onlineDevices.length > 0) {
        this.logDeviceSelect.value = onlineDevices[0].serial || onlineDevices[0].id;
      }
    }

    // 4. Deep diag target device
    if (this.diagDeepDeviceSelect) {
      const prevVal = this.diagDeepDeviceSelect.value;
      this.diagDeepDeviceSelect.innerHTML = '<option value="">Select target device...</option>';
      devices.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.serial || d.id;
        opt.textContent = `${d.display_name || d.model || d.serial} (${d.platform})`;
        this.diagDeepDeviceSelect.appendChild(opt);
      });
      if (prevVal && this.diagDeepDeviceSelect.querySelector(`option[value="${prevVal}"]`)) {
        this.diagDeepDeviceSelect.value = prevVal;
      } else if (onlineDevices.length > 0) {
        this.diagDeepDeviceSelect.value = onlineDevices[0].serial || onlineDevices[0].id;
      }
    }
  }

  setWorkflowTemplate(type) {
    if (!this.autoWorkflowJson) return;
    let template = {};
    if (type === 'smoke') {
      template = {
        name: "SmokeVerification",
        steps: [
          { step_name: "Wake & Home Key", action: "KEY", key: "HOME" },
          { step_name: "Pause 300ms", action: "WAIT", duration_ms: 300 },
          { step_name: "Capture Screen", action: "SCREENSHOT" },
          { step_name: "Assert Device Online", action: "ASSERT_STATE", expected_state: "available" }
        ]
      };
    } else if (type === 'app') {
      template = {
        name: "SettingsLifecycle",
        steps: [
          { step_name: "Launch Settings", action: "LAUNCH_APP", package: "com.android.settings" },
          { step_name: "Wait UI Settle", action: "WAIT", duration_ms: 1000 },
          { step_name: "Capture Settings Screen", action: "SCREENSHOT" },
          { step_name: "Stop Settings", action: "STOP_APP", package: "com.android.settings" },
          { step_name: "Return Home", action: "KEY", key: "HOME" }
        ]
      };
    } else if (type === 'gesture') {
      template = {
        name: "GestureNavigation",
        steps: [
          { step_name: "Press Home", action: "KEY", key: "HOME" },
          { step_name: "Swipe Up App Drawer", action: "SWIPE", x1: 500, y1: 1600, x2: 500, y2: 400, duration_ms: 300 },
          { step_name: "Wait Animation", action: "WAIT", duration_ms: 600 },
          { step_name: "Capture Drawer View", action: "SCREENSHOT" },
          { step_name: "Return Home", action: "KEY", key: "HOME" }
        ]
      };
    }
    this.autoWorkflowJson.value = JSON.stringify(template, null, 2);
  }

  validateWorkflowJSON() {
    if (!this.autoWorkflowJson) return;
    try {
      const parsed = JSON.parse(this.autoWorkflowJson.value);
      if (!parsed.steps || !Array.isArray(parsed.steps) || parsed.steps.length === 0) {
        this.showToast('Workflow JSON must contain a non-empty "steps" array', 'warn', 4000);
        return false;
      }
      this.showToast(`Valid JSON: ${parsed.name || 'Unnamed'} with ${parsed.steps.length} steps`, 'success', 3000);
      return true;
    } catch (err) {
      this.showToast(`JSON Syntax Error: ${err.message}`, 'error', 4000);
      return false;
    }
  }

  async runAutomationWorkflow() {
    const targetDev = this.autoTargetDevice ? this.autoTargetDevice.value : '';
    if (!targetDev) {
      this.showToast('Please select a target device for the workflow', 'warn', 3000);
      return;
    }
    if (!this.validateWorkflowJSON()) return;

    try {
      const parsed = JSON.parse(this.autoWorkflowJson.value);
      parsed.target_device = targetDev;

      this.showToast(`Launching workflow: ${parsed.name || 'Custom'}...`, 'info', 2000);
      const res = await fetch('/api/automation/execute-inline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target_device: targetDev, workflow: parsed })
      });

      if (res.ok) {
        const report = await res.json();
        this.showToast(`Execution started: ${report.execution_id}`, 'success', 3000);
        this.startExecutionMonitoring(report);
      } else {
        const err = await res.json();
        this.showToast(err.detail || 'Execution failed to start', 'error', 4000);
      }
    } catch (err) {
      console.error('Run workflow error:', err);
      this.showToast('Network error launching workflow execution', 'error', 4000);
    }
  }

  startExecutionMonitoring(initialReport) {
    this.activeExecutionId = initialReport.execution_id;
    this.activeExecutionStartTime = Date.now();

    if (this.autoActiveCard) this.autoActiveCard.style.display = 'block';
    if (this.autoActiveTitle) this.autoActiveTitle.textContent = `Running: ${initialReport.workflow_name || initialReport.execution_id}`;
    if (this.autoActiveBadge) {
      this.autoActiveBadge.className = 'badge accent';
      this.autoActiveBadge.textContent = 'RUNNING';
    }
    if (this.autoActiveDot) this.autoActiveDot.className = 'status-dot working';
    if (this.autoProgressFill) this.autoProgressFill.style.width = '20%';

    clearInterval(this.activeExecutionPollTimer);
    this.activeExecutionPollTimer = setInterval(async () => {
      if (!this.activeExecutionId) return;

      const elapsed = ((Date.now() - this.activeExecutionStartTime) / 1000).toFixed(1);
      if (this.autoActiveTimer) this.autoActiveTimer.textContent = `${elapsed}s`;

      try {
        const res = await fetch(`/api/automation/executions/${encodeURIComponent(this.activeExecutionId)}`);
        if (res.ok) {
          const report = await res.json();
          this.renderActiveExecutionSteps(report);

          if (report.status !== 'RUNNING') {
            clearInterval(this.activeExecutionPollTimer);
            this.finishExecutionMonitoring(report);
          }
        }
      } catch (err) {
        console.warn('Execution poll error:', err);
      }
    }, 600);
  }

  renderActiveExecutionSteps(report) {
    if (!this.autoActiveSteps) return;
    const steps = report.step_results || [];
    const totalSteps = steps.length;
    const passedCount = steps.filter(s => s.status === 'PASSED').length;
    const percent = totalSteps > 0 ? Math.round((passedCount / totalSteps) * 100) : 50;

    if (this.autoProgressFill) {
      this.autoProgressFill.style.width = `${Math.max(10, percent)}%`;
    }

    this.autoActiveSteps.innerHTML = steps.map((s, idx) => {
      let statusClass = 'auto-step-item';
      let dotClass = 'status-dot idle';
      if (s.status === 'PASSED') {
        statusClass += ' passed';
        dotClass = 'status-dot complete';
      } else if (s.status === 'FAILED') {
        statusClass += ' failed';
        dotClass = 'status-dot error';
      } else if (s.status === 'RUNNING') {
        statusClass += ' running';
        dotClass = 'status-dot working';
      }

      return `
        <div class="${statusClass}">
          <div style="display: flex; align-items: center; gap: var(--space-2);">
            <span class="${dotClass}"></span>
            <span class="mono" style="font-size: 11px; color: var(--text-tertiary);">#${idx + 1}</span>
            <span style="font-weight: 500;">${this.escapeHtml(s.step_name || s.action)}</span>
          </div>
          <div style="display: flex; align-items: center; gap: var(--space-3);">
            <span class="mono tabular-nums" style="font-size: 11px; color: var(--text-tertiary);">${s.duration_ms ? s.duration_ms + 'ms' : '--'}</span>
            <span class="badge" style="font-size: 10px;">${s.status}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  finishExecutionMonitoring(report) {
    if (this.autoActiveBadge) {
      this.autoActiveBadge.textContent = report.status;
      if (report.status === 'COMPLETED') {
        this.autoActiveBadge.className = 'badge complete';
        if (this.autoActiveDot) this.autoActiveDot.className = 'status-dot complete';
        if (this.autoProgressFill) this.autoProgressFill.style.width = '100%';
        this.showToast(`Workflow execution completed successfully (${report.duration_ms}ms)`, 'success', 4000);
      } else if (report.status === 'FAILED') {
        this.autoActiveBadge.className = 'badge error';
        if (this.autoActiveDot) this.autoActiveDot.className = 'status-dot error';
        this.showToast(`Workflow execution failed: ${report.error_details || 'Unknown error'}`, 'error', 5000);
      } else if (report.status === 'CANCELLED') {
        this.autoActiveBadge.className = 'badge';
        if (this.autoActiveDot) this.autoActiveDot.className = 'status-dot idle';
        this.showToast('Workflow execution cancelled by operator', 'warn', 4000);
      }
    }
    this.loadExecutionHistory();
  }

  async cancelActiveExecution() {
    if (!this.activeExecutionId) return;
    try {
      this.showToast(`Aborting execution ${this.activeExecutionId}...`, 'info', 2000);
      const res = await fetch(`/api/automation/executions/${encodeURIComponent(this.activeExecutionId)}/cancel`, {
        method: 'POST'
      });
      if (res.ok) {
        this.showToast('Execution abort requested', 'warn', 3000);
      }
    } catch (err) {
      console.error('Cancel execution error:', err);
    }
  }

  async loadExecutionHistory() {
    if (!this.autoHistoryRows) return;
    try {
      const res = await fetch('/api/automation/executions');
      if (res.ok) {
        const list = await res.json();
        if (list.length === 0) {
          this.autoHistoryRows.innerHTML = `
            <tr>
              <td colspan="7" style="text-align: center; color: var(--text-tertiary); padding: var(--space-6);">
                No executions recorded in this session.
              </td>
            </tr>
          `;
          return;
        }

        this.autoHistoryRows.innerHTML = list.map(item => {
          let statusBadge = '<span class="badge">PENDING</span>';
          if (item.status === 'COMPLETED') statusBadge = '<span class="badge complete">COMPLETED</span>';
          else if (item.status === 'FAILED') statusBadge = '<span class="badge error">FAILED</span>';
          else if (item.status === 'RUNNING') statusBadge = '<span class="badge accent">RUNNING</span>';
          else if (item.status === 'CANCELLED') statusBadge = '<span class="badge">CANCELLED</span>';

          const timeStr = item.completed_at ? item.completed_at.replace('T', ' ').substring(0, 19) : (item.started_at ? item.started_at.replace('T', ' ').substring(0, 19) : '--');

          return `
            <tr>
              <td class="mono" style="font-size: 11px;">${this.escapeHtml(item.execution_id)}</td>
              <td style="font-weight: 500;">${this.escapeHtml(item.workflow_name || '--')}</td>
              <td class="mono" style="font-size: 12px;">${this.escapeHtml(item.target_device)}</td>
              <td>${statusBadge}</td>
              <td class="tabular-nums mono" style="font-size: 12px;">${item.duration_ms ? item.duration_ms + ' ms' : '--'}</td>
              <td class="tabular-nums" style="font-size: 12px; color: var(--text-tertiary);">${timeStr}</td>
              <td>
                <button class="btn sm" type="button" onclick="window.deviceLabApp.inspectExecutionReport('${this.escapeHtml(item.execution_id)}')">
                  <span>Report</span>
                </button>
              </td>
            </tr>
          `;
        }).join('');
      }
    } catch (err) {
      console.warn('Load history error:', err);
    }
  }

  async inspectExecutionReport(executionId) {
    try {
      const res = await fetch(`/api/automation/executions/${encodeURIComponent(executionId)}`);
      if (res.ok) {
        const report = await res.json();
        const jsonFormatted = JSON.stringify(report, null, 2);
        this.showConfirm(
          `Execution Report: ${executionId}`,
          `<pre style="background: #121211; padding: var(--space-3); border-radius: var(--radius-sm); font-family: var(--font-mono); font-size: 11px; max-height: 340px; overflow-y: auto; color: var(--text-primary);">${this.escapeHtml(jsonFormatted)}</pre>`,
          () => {}
        );
      }
    } catch (err) {
      this.showToast('Failed to fetch execution report', 'error');
    }
  }

  openCreateWorkflowModal() {
    this.populateDeviceSelectors();
    if (this.modalCreateWorkflow) {
      this.modalCreateWorkflow.style.display = 'flex';
      if (this.workflowStepsJsonInput && !this.workflowStepsJsonInput.value.trim()) {
        this.workflowStepsJsonInput.value = JSON.stringify([
          { step_name: "Return Home", action: "KEY", key: "HOME" },
          { step_name: "Screenshot Check", action: "SCREENSHOT" }
        ], null, 2);
      }
    }
  }

  closeCreateWorkflowModal() {
    if (this.modalCreateWorkflow) {
      this.modalCreateWorkflow.style.display = 'none';
    }
  }

  async submitCreateWorkflow() {
    const name = this.workflowNameInput ? this.workflowNameInput.value.trim() : '';
    const targetDev = this.workflowTargetDeviceInput ? this.workflowTargetDeviceInput.value : '';
    const stepsText = this.workflowStepsJsonInput ? this.workflowStepsJsonInput.value.trim() : '';

    if (!name || !targetDev || !stepsText) {
      this.showToast('All fields are required', 'warn', 3000);
      return;
    }

    try {
      const steps = JSON.parse(stepsText);
      const payload = {
        name: name,
        target_device: targetDev,
        steps: steps
      };

      const res = await fetch('/api/automation/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const created = await res.json();
        this.closeCreateWorkflowModal();
        this.showToast(`Workflow "${created.name}" registered (${created.workflow_id})`, 'success', 4000);
      } else {
        const err = await res.json();
        this.showToast(err.detail || 'Failed to create workflow', 'error', 4000);
      }
    } catch (err) {
      this.showToast(`Invalid JSON steps: ${err.message}`, 'error', 4000);
    }
  }

  // ============================================================================
  // Phase 13: Live Logcat Console & Diagnostics
  // ============================================================================

  initDiagnosticsRoute() {
    this.populateDeviceSelectors();
    this.handleLogDeviceChange();
    this.fetchDeepDiagnostics();
  }

  handleLogDeviceChange() {
    const dev = this.logDeviceSelect ? this.logDeviceSelect.value : '';
    this.currentLogDevice = dev;
    if (this.logcatTerminal) {
      this.logcatTerminal.innerHTML = dev ?
        `<div style="color: var(--text-tertiary); font-style: italic;">Connecting to logcat stream on ${this.escapeHtml(dev)}...</div>` :
        `<div style="color: var(--text-tertiary); font-style: italic;">Select an attached device to stream live sanitized logcat output...</div>`;
    }
    if (dev) {
      this.pollLogcat();
      this.startLogPolling();
    } else {
      this.stopLogPolling();
    }
  }

  startLogPolling() {
    this.isLogPolling = true;
    if (this.logToggleLabel) this.logToggleLabel.textContent = 'Pause';
    clearInterval(this.logPollTimer);
    this.logPollTimer = setInterval(() => {
      if (this.isLogPolling && this.currentLogDevice) {
        this.pollLogcat();
      }
    }, 1500);
  }

  stopLogPolling() {
    this.isLogPolling = false;
    if (this.logToggleLabel) this.logToggleLabel.textContent = 'Resume';
    clearInterval(this.logPollTimer);
  }

  toggleLogStream() {
    if (this.isLogPolling) {
      this.stopLogPolling();
      this.showToast('Log stream paused', 'info', 2000);
    } else {
      this.startLogPolling();
      this.showToast('Log stream resumed', 'info', 2000);
    }
  }

  debounceLogPoll() {
    clearTimeout(this._logDebounceTimer);
    this._logDebounceTimer = setTimeout(() => {
      this.pollLogcat();
    }, 350);
  }

  async pollLogcat() {
    if (!this.currentLogDevice || !this.logcatTerminal) return;
    const level = this.logLevelFilter ? this.logLevelFilter.value : 'ALL';
    const tag = this.logTagFilter ? this.logTagFilter.value.trim() : '';
    const search = this.logSearchFilter ? this.logSearchFilter.value.trim() : '';

    const params = new URLSearchParams();
    if (level && level !== 'ALL') params.set('level', level);
    if (tag) params.set('tag', tag);
    if (search) params.set('search', search);
    params.set('limit', '250');

    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(this.currentLogDevice)}/logs?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        const entries = data.entries || [];
        if (entries.length === 0) {
          this.logcatTerminal.innerHTML = `<div style="color: var(--text-tertiary); font-style: italic;">No matching logs found for current filters. Buffer: ${data.total_entries || 0} items.</div>`;
          return;
        }

        const linesHtml = entries.map(e => {
          const lvl = (e.level || 'I').toUpperCase();
          const lvlClass = `log-${lvl.toLowerCase()}`;
          return `
            <div class="log-entry ${lvlClass}">
              <span class="log-time">${this.escapeHtml(e.timestamp.substring(11, 23))}</span>
              <span class="log-level">[${lvl}]</span>
              <span class="log-tag">${this.escapeHtml(e.tag || 'System')}:</span>
              <span class="log-msg">${this.escapeHtml(e.message)}</span>
            </div>
          `;
        }).join('');

        this.logcatTerminal.innerHTML = linesHtml;

        if (this.logAutoscrollToggle && this.logAutoscrollToggle.checked) {
          this.logcatTerminal.scrollTop = this.logcatTerminal.scrollHeight;
        }
      }
    } catch (err) {
      console.warn('Poll logcat error:', err);
    }
  }

  async clearDeviceLogs() {
    if (!this.currentLogDevice) return;
    try {
      const res = await fetch(`/api/devices/${encodeURIComponent(this.currentLogDevice)}/logs`, {
        method: 'DELETE'
      });
      if (res.ok) {
        if (this.logcatTerminal) {
          this.logcatTerminal.innerHTML = '<div style="color: var(--text-tertiary); font-style: italic;">Log buffer cleared.</div>';
        }
        this.showToast('Log buffer cleared', 'info', 2000);
      }
    } catch (err) {
      this.showToast('Failed to clear logs', 'error');
    }
  }

  async exportDeviceLogs(format) {
    if (!this.currentLogDevice) {
      this.showToast('Please select a device to export logs from', 'warn');
      return;
    }
    const level = this.logLevelFilter ? this.logLevelFilter.value : 'ALL';
    const tag = this.logTagFilter ? this.logTagFilter.value.trim() : '';
    const search = this.logSearchFilter ? this.logSearchFilter.value.trim() : '';

    const params = new URLSearchParams();
    params.set('format', format);
    if (level && level !== 'ALL') params.set('level', level);
    if (tag) params.set('tag', tag);
    if (search) params.set('search', search);

    try {
      this.showToast(`Exporting logs as ${format.toUpperCase()}...`, 'info', 2000);
      const res = await fetch(`/api/devices/${encodeURIComponent(this.currentLogDevice)}/logs/export?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        this.showToast(`Log export ready: ${data.name} (${Math.round(data.file_size_bytes / 1024)} KB)`, 'success', 4000);
        if (data.download_url) {
          const a = document.createElement('a');
          a.href = data.download_url;
          a.download = data.name;
          document.body.appendChild(a);
          a.click();
          a.remove();
        }
      } else {
        const err = await res.json();
        this.showToast(err.detail || 'Export failed', 'error');
      }
    } catch (err) {
      console.error('Export logs error:', err);
      this.showToast('Network error exporting logs', 'error');
    }
  }

  async fetchDeepDiagnostics() {
    const dev = this.diagDeepDeviceSelect ? this.diagDeepDeviceSelect.value : '';
    if (!dev) return;

    try {
      const res = await fetch(`/api/diagnostics/devices/${encodeURIComponent(dev)}`);
      if (res.ok) {
        const report = await res.json();
        if (this.deepDiagStateMetric) this.deepDiagStateMetric.textContent = report.state.toUpperCase();
        if (this.deepDiagStateDot) {
          this.deepDiagStateDot.className = report.state === 'available' ? 'status-dot complete' : (report.state === 'busy' ? 'status-dot working' : 'status-dot idle');
        }
        if (this.deepDiagProviderMeta) this.deepDiagProviderMeta.textContent = `Provider: ${report.provider_id} (${report.platform})`;

        if (this.deepDiagStreamFps) this.deepDiagStreamFps.textContent = `${report.stream.fps.toFixed(1)} FPS`;
        if (this.deepDiagStreamDot) {
          this.deepDiagStreamDot.className = report.stream.is_streaming ? 'status-dot working' : 'status-dot idle';
        }
        if (this.deepDiagStreamMeta) this.deepDiagStreamMeta.textContent = `${report.stream.frames_sent} frames / ${Math.round(report.stream.bytes_transferred / 1024)} KB`;

        if (this.deepDiagLeaseMetric) {
          this.deepDiagLeaseMetric.textContent = report.lease.has_lease ? report.lease.lease_holder : 'Available';
        }
        if (this.deepDiagLeaseMeta) {
          this.deepDiagLeaseMeta.textContent = report.automation_busy ? 'Automation lock engaged' : (report.lease.has_lease ? `${report.lease.expires_in_seconds}s timeout remaining` : 'No single-writer lock held');
        }

        if (this.deepDiagBatteryMetric) {
          this.deepDiagBatteryMetric.textContent = report.battery_level !== null ? `${report.battery_level}%` : '--';
        }
        if (this.deepDiagScreenMeta) {
          this.deepDiagScreenMeta.textContent = (report.screen_width && report.screen_height) ? `${report.screen_width}x${report.screen_height}` : 'Dimensions: Default';
        }

        // Render errors
        if (this.deepDiagErrorRows) {
          const errors = report.recent_errors || [];
          if (errors.length === 0) {
            this.deepDiagErrorRows.innerHTML = `
              <tr>
                <td colspan="3" style="text-align: center; color: var(--text-tertiary); padding: var(--space-4);">
                  No error events recorded for this device.
                </td>
              </tr>
            `;
          } else {
            this.deepDiagErrorRows.innerHTML = errors.map(e => `
              <tr>
                <td class="tabular-nums" style="font-size: 11px; font-family: var(--font-mono); color: var(--text-tertiary);">${this.escapeHtml(e.timestamp || '--')}</td>
                <td><span class="badge error" style="font-size: 10px;">${this.escapeHtml(e.code || 'ERROR')}</span></td>
                <td style="font-size: 12px; color: var(--text-secondary);">${this.escapeHtml(e.message || '')}</td>
              </tr>
            `).join('');
          }
        }
      }
    } catch (err) {
      console.warn('Fetch deep diagnostics error:', err);
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
  window.deviceLabApp = new DeviceLabApp();
});
