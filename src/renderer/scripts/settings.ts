import { Settings } from './types';

declare const window: Window & { craAPI: any };

export class SettingsController {
  private overlay: HTMLElement;
  private currentPaneTitle: HTMLElement;
  private contentContainer: HTMLElement;
  private settings: Settings;
  private activePane = 'general';
  private isOpen = false;

  constructor(initialSettings: Settings) {
    this.settings = initialSettings;
    this.overlay = document.getElementById('settings-overlay')!;
    this.currentPaneTitle = document.getElementById('settings-current-pane-title')!;
    this.contentContainer = document.getElementById('settings-pane-content')!;

    this.setupListeners();
  }

  public open(pane = 'general'): void {
    this.isOpen = true;
    this.activePane = pane;
    this.overlay.classList.add('open');

    // Hide native Chromium view while settings is open
    window.craAPI.setContentVisible(false);

    this.updateActiveNav();
    this.renderPane();
  }

  public close(): void {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.overlay.classList.remove('open');

    // Restore native Chromium view
    window.craAPI.setContentVisible(true);
  }

  public isSettingsOpen(): boolean {
    return this.isOpen;
  }

  private setupListeners(): void {
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.close();
      }
    });

    document.getElementById('btn-close-settings')?.addEventListener('click', () => {
      this.close();
    });

    document.querySelectorAll('.settings-nav-item').forEach((item) => {
      item.addEventListener('click', () => {
        const pane = item.getAttribute('data-pane') || 'general';
        this.activePane = pane;
        this.updateActiveNav();
        this.renderPane();
      });
    });

    window.addEventListener('keydown', (e) => {
      if (this.isOpen && e.key === 'Escape') {
        this.close();
      }
    });
  }

  private updateActiveNav(): void {
    document.querySelectorAll('.settings-nav-item').forEach((item) => {
      if (item.getAttribute('data-pane') === this.activePane) {
        item.classList.add('active');
        this.currentPaneTitle.textContent = item.querySelector('span:last-child')?.textContent || 'Settings';
      } else {
        item.classList.remove('active');
      }
    });
  }

  private renderPane(): void {
    this.contentContainer.innerHTML = '';
    switch (this.activePane) {
      case 'general':
        this.renderGeneralPane();
        break;
      case 'tabs':
        this.renderTabsPane();
        break;
      case 'privacy':
        this.renderPrivacyPane();
        break;
      case 'shortcuts':
        this.renderShortcutsPane();
        break;
      case 'performance':
        this.renderPerformancePane();
        break;
      case 'advanced':
        this.renderAdvancedPane();
        break;
    }
  }

  private renderGeneralPane(): void {
    this.contentContainer.innerHTML = `
      <div>
        <h4 class="settings-section-header">System Integration</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Default Browser</span>
              <span class="mac-row-desc">Make Cra the system default web browser</span>
            </div>
            <button class="mac-btn primary" id="btn-set-default-browser">Set as Default</button>
          </div>
          <div class="mac-card-divider"></div>
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Search Engine</span>
              <span class="mac-row-desc">Default engine used for omnibox queries</span>
            </div>
            <select class="mac-select" id="select-search-engine">
              <option value="DuckDuckGo" ${this.settings.search_engine === 'DuckDuckGo' ? 'selected' : ''}>DuckDuckGo</option>
              <option value="Google" ${this.settings.search_engine === 'Google' ? 'selected' : ''}>Google</option>
              <option value="Brave" ${this.settings.search_engine === 'Brave' ? 'selected' : ''}>Brave</option>
              <option value="Bing" ${this.settings.search_engine === 'Bing' ? 'selected' : ''}>Bing</option>
            </select>
          </div>
        </div>
        <p class="settings-footnote">Cra works best when set as your primary web browser.</p>
      </div>

      <div>
        <h4 class="settings-section-header">Appearance</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Folder Previews</span>
              <span class="mac-row-desc">Show tab count badges and tooltips on folder hover</span>
            </div>
            <label class="mac-switch">
              <input type="checkbox" id="chk-folder-previews" ${this.settings.folder_previews ? 'checked' : ''}>
              <span class="mac-switch-slider"></span>
            </label>
          </div>
        </div>
      </div>
    `;

    document.getElementById('select-search-engine')?.addEventListener('change', (e) => {
      this.settings.search_engine = (e.target as HTMLSelectElement).value;
      this.persist();
    });

    document.getElementById('chk-folder-previews')?.addEventListener('change', (e) => {
      this.settings.folder_previews = (e.target as HTMLInputElement).checked;
      this.persist();
    });
  }

  private renderTabsPane(): void {
    this.contentContainer.innerHTML = `
      <div>
        <h4 class="settings-section-header">Tab Organization</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Add New Tabs to Top</span>
              <span class="mac-row-desc">Open newly created tabs at the top of the Today list</span>
            </div>
            <label class="mac-switch">
              <input type="checkbox" id="chk-new-tabs-top" ${this.settings.new_tabs_at_top ? 'checked' : ''}>
              <span class="mac-switch-slider"></span>
            </label>
          </div>
          <div class="mac-card-divider"></div>
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Auto-Archive Inactive Tabs</span>
              <span class="mac-row-desc">Automatically archive tabs after period of inactivity</span>
            </div>
            <select class="mac-select" id="select-auto-archive">
              <option value="12" ${this.settings.auto_archive_threshold_hours === 12 ? 'selected' : ''}>12 Hours</option>
              <option value="24" ${this.settings.auto_archive_threshold_hours === 24 ? 'selected' : ''}>24 Hours</option>
              <option value="168" ${this.settings.auto_archive_threshold_hours === 168 ? 'selected' : ''}>7 Days</option>
              <option value="720" ${this.settings.auto_archive_threshold_hours === 720 ? 'selected' : ''}>30 Days</option>
            </select>
          </div>
        </div>
      </div>

      <div>
        <h4 class="settings-section-header">Memory & Sleeping</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Tab Sleep Policy</span>
              <span class="mac-row-desc">Put inactive background tabs to sleep to conserve memory</span>
            </div>
            <label class="mac-switch">
              <input type="checkbox" id="chk-tab-sleep" ${this.settings.tab_sleep_enabled ? 'checked' : ''}>
              <span class="mac-switch-slider"></span>
            </label>
          </div>
          <div class="mac-card-divider"></div>
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Sleep Threshold</span>
              <span class="mac-row-desc">Time before an inactive background tab sleeps</span>
            </div>
            <select class="mac-select" id="select-sleep-threshold">
              <option value="30" ${this.settings.tab_sleep_threshold_minutes === 30 ? 'selected' : ''}>30 Minutes</option>
              <option value="60" ${this.settings.tab_sleep_threshold_minutes === 60 ? 'selected' : ''}>1 Hour</option>
              <option value="120" ${this.settings.tab_sleep_threshold_minutes === 120 ? 'selected' : ''}>2 Hours</option>
              <option value="240" ${this.settings.tab_sleep_threshold_minutes === 240 ? 'selected' : ''}>4 Hours</option>
            </select>
          </div>
        </div>
      </div>
    `;

    document.getElementById('chk-new-tabs-top')?.addEventListener('change', (e) => {
      this.settings.new_tabs_at_top = (e.target as HTMLInputElement).checked;
      this.persist();
    });

    document.getElementById('select-auto-archive')?.addEventListener('change', (e) => {
      this.settings.auto_archive_threshold_hours = parseInt((e.target as HTMLSelectElement).value, 10);
      this.persist();
    });

    document.getElementById('chk-tab-sleep')?.addEventListener('change', (e) => {
      this.settings.tab_sleep_enabled = (e.target as HTMLInputElement).checked;
      this.persist();
    });

    document.getElementById('select-sleep-threshold')?.addEventListener('change', (e) => {
      this.settings.tab_sleep_threshold_minutes = parseInt((e.target as HTMLSelectElement).value, 10);
      this.persist();
    });
  }

  private renderPrivacyPane(): void {
    this.contentContainer.innerHTML = `
      <div>
        <h4 class="settings-section-header">Content Blocking</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Built-in Ad & Tracker Blocker</span>
              <span class="mac-row-desc">Block ads, telemetry, and tracking networks</span>
            </div>
            <label class="mac-switch">
              <input type="checkbox" id="chk-adblock" ${this.settings.adblock_enabled ? 'checked' : ''}>
              <span class="mac-switch-slider"></span>
            </label>
          </div>
          <div class="mac-card-divider"></div>
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Block Cookie Banners</span>
              <span class="mac-row-desc">Automatically hide intrusive GDPR cookie prompts</span>
            </div>
            <label class="mac-switch">
              <input type="checkbox" id="chk-cookie-banners" ${this.settings.block_cookie_banners ? 'checked' : ''}>
              <span class="mac-switch-slider"></span>
            </label>
          </div>
          <div class="mac-card-divider"></div>
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>HTTPS-Only Mode</span>
              <span class="mac-row-desc">Automatically upgrade all web connections to HTTPS</span>
            </div>
            <label class="mac-switch">
              <input type="checkbox" id="chk-https-only" ${this.settings.https_only ? 'checked' : ''}>
              <span class="mac-switch-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div>
        <h4 class="settings-section-header">Browsing Data</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Clear Inactive Tab Archive</span>
              <span class="mac-row-desc">Remove all stored archived tab sessions</span>
            </div>
            <button class="mac-btn" id="btn-clear-archive-data">Clear Archive</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('chk-adblock')?.addEventListener('change', (e) => {
      this.settings.adblock_enabled = (e.target as HTMLInputElement).checked;
      this.persist();
    });

    document.getElementById('chk-cookie-banners')?.addEventListener('change', (e) => {
      this.settings.block_cookie_banners = (e.target as HTMLInputElement).checked;
      this.persist();
    });

    document.getElementById('chk-https-only')?.addEventListener('change', (e) => {
      this.settings.https_only = (e.target as HTMLInputElement).checked;
      this.persist();
    });

    document.getElementById('btn-clear-archive-data')?.addEventListener('click', async () => {
      await window.craAPI.clearArchive();
      alert('Tab archive successfully cleared.');
    });
  }

  private renderShortcutsPane(): void {
    const shortcuts = [
      { action: 'New Tab / Command Bar', shortcut: 'Ctrl + T' },
      { action: 'Edit URL / Search', shortcut: 'Ctrl + L' },
      { action: 'Close Active Tab', shortcut: 'Ctrl + W' },
      { action: 'Toggle Sidebar', shortcut: 'Ctrl + S' },
      { action: 'Open Settings', shortcut: 'Ctrl + ,' },
      { action: 'Clear Today Tabs', shortcut: 'Shift + Ctrl + K' },
      { action: 'Reload Tab', shortcut: 'Ctrl + R / F5' },
      { action: 'Back History', shortcut: 'Alt + Left' },
      { action: 'Forward History', shortcut: 'Alt + Right' },
      { action: 'Zoom In / Out / Reset', shortcut: 'Ctrl + / - / 0' },
      { action: 'Toggle Developer Tools', shortcut: 'Ctrl + Shift + I' },
    ];

    this.contentContainer.innerHTML = `
      <div>
        <h4 class="settings-section-header">Keyboard Shortcuts</h4>
        <div class="mac-card">
          ${shortcuts
            .map(
              (item, idx) => `
            <div class="mac-card-row">
              <span class="mac-row-label">${item.action}</span>
              <span class="keycap">${item.shortcut}</span>
            </div>
            ${idx < shortcuts.length - 1 ? '<div class="mac-card-divider"></div>' : ''}
          `
            )
            .join('')}
        </div>
      </div>
    `;
  }

  private renderPerformancePane(): void {
    this.contentContainer.innerHTML = `
      <div>
        <h4 class="settings-section-header">Graphics & Performance</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Hardware Acceleration</span>
              <span class="mac-row-desc">Use GPU hardware acceleration when available</span>
            </div>
            <label class="mac-switch">
              <input type="checkbox" id="chk-hw-accel" ${this.settings.hardware_acceleration ? 'checked' : ''}>
              <span class="mac-switch-slider"></span>
            </label>
          </div>
        </div>
      </div>
    `;

    document.getElementById('chk-hw-accel')?.addEventListener('change', (e) => {
      this.settings.hardware_acceleration = (e.target as HTMLInputElement).checked;
      this.persist();
    });
  }

  private renderAdvancedPane(): void {
    this.contentContainer.innerHTML = `
      <div>
        <h4 class="settings-section-header">Advanced Configuration</h4>
        <div class="mac-card">
          <div class="mac-card-row">
            <div class="mac-row-label">
              <span>Reset All Settings</span>
              <span class="mac-row-desc">Restore Cra browser configuration to default values</span>
            </div>
            <button class="mac-btn" id="btn-reset-defaults">Restore Defaults</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('btn-reset-defaults')?.addEventListener('click', () => {
      if (confirm('Are you sure you want to restore default settings?')) {
        this.settings = {
          search_engine: 'DuckDuckGo',
          adblock_enabled: true,
          auto_archive_threshold_hours: 24,
          tab_sleep_enabled: true,
          tab_sleep_threshold_minutes: 60,
          sidebar_width: 280,
          hardware_acceleration: true,
          https_only: true,
          new_tabs_at_top: false,
          folder_previews: true,
          block_cookie_banners: true,
        };
        this.persist();
        this.renderPane();
      }
    });
  }

  private persist(): void {
    window.craAPI.saveSettings(this.settings);
  }
}
