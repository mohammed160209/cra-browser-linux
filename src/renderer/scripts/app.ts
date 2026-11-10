import { SidebarController } from './sidebar';
import { ToolbarController } from './toolbar';
import { CommandBarController } from './command-bar';
import { SettingsController } from './settings';

declare const window: Window & { craAPI: any };

async function bootstrap() {
  const sidebarDoc = await window.craAPI.getSidebar();
  const settings = await window.craAPI.getSettings();

  // 1. Initialize Controllers
  let sidebarCtrl: SidebarController;
  let toolbarCtrl: ToolbarController;
  let commandBarCtrl: CommandBarController;
  let settingsCtrl: SettingsController;

  const handleTabSelected = (tabId: string, url?: string) => {
    window.craAPI.showTab(tabId, url);
    if (url) {
      toolbarCtrl.displayUrl(url);
    }
  };

  sidebarCtrl = new SidebarController(sidebarDoc, handleTabSelected);
  toolbarCtrl = new ToolbarController(() => {
    const activeTab = sidebarCtrl.getActiveTabId();
    const item = activeTab ? sidebarDoc.items[activeTab] : null;
    const currentUrl = item?.tabData?.url || item?.savedURL || '';
    commandBarCtrl.open(currentUrl);
  });

  settingsCtrl = new SettingsController(settings);
  commandBarCtrl = new CommandBarController(
    () => sidebarCtrl.getDocument(),
    (tabId) => sidebarCtrl.selectTab(tabId),
    () => settingsCtrl.open('general')
  );

  // 2. Initial Render
  sidebarCtrl.render();

  // Select initial tab
  const space = sidebarCtrl.getCurrentSpace();
  const initialToday = sidebarDoc.containers[space.todayContainerId] || [];
  const initialFavs = sidebarDoc.containers[space.favoritesContainerId] || [];
  const initialTabId = initialToday[0] || initialFavs[0];
  if (initialTabId) {
    sidebarCtrl.selectTab(initialTabId);
  }

  // 3. Setup Window Controls
  document.getElementById('btn-close-app')?.addEventListener('click', () => {
    window.close();
  });

  document.getElementById('btn-open-settings')?.addEventListener('click', () => {
    settingsCtrl.open('general');
  });

  // 4. Register IPC Event Listeners from Main Process
  window.craAPI.onTabNavUpdated((data: { tabId: string; url: string; canGoBack: boolean; canGoForward: boolean }) => {
    sidebarCtrl.updateTabNav(data.tabId, data.url);
    if (sidebarCtrl.getActiveTabId() === data.tabId) {
      toolbarCtrl.updateNavigationState(data.canGoBack, data.canGoForward, data.url);
    }
  });

  window.craAPI.onTabTitleUpdated((data: { tabId: string; title: string }) => {
    sidebarCtrl.updateTabTitle(data.tabId, data.title);
  });

  window.craAPI.onTabFaviconUpdated((data: { tabId: string; favicon: string }) => {
    sidebarCtrl.updateTabFavicon(data.tabId, data.favicon);
  });

  window.craAPI.onTabAudioUpdated((data: { tabId: string; isPlaying: boolean }) => {
    sidebarCtrl.updateTabAudio(data.tabId, data.isPlaying);
    if (sidebarCtrl.getActiveTabId() === data.tabId) {
      toolbarCtrl.setAudioState(data.isPlaying, false);
    }
  });

  // 5. Global Keyboard Shortcuts
  window.addEventListener('keydown', (e) => {
    const isCtrl = e.ctrlKey || e.metaKey;

    // Ctrl + T : Command Bar (New Tab)
    if (isCtrl && !e.shiftKey && e.key.toLowerCase() === 't') {
      e.preventDefault();
      commandBarCtrl.open();
      return;
    }

    // Ctrl + L : Edit URL
    if (isCtrl && !e.shiftKey && e.key.toLowerCase() === 'l') {
      e.preventDefault();
      const activeTab = sidebarCtrl.getActiveTabId();
      const item = activeTab ? sidebarDoc.items[activeTab] : null;
      const currentUrl = item?.tabData?.url || item?.savedURL || '';
      commandBarCtrl.open(currentUrl);
      return;
    }

    // Ctrl + W : Close Tab
    if (isCtrl && !e.shiftKey && e.key.toLowerCase() === 'w') {
      e.preventDefault();
      const activeTab = sidebarCtrl.getActiveTabId();
      if (activeTab) {
        sidebarCtrl.closeTab(activeTab);
      }
      return;
    }

    // Ctrl + S : Toggle Sidebar
    if (isCtrl && !e.shiftKey && e.key.toLowerCase() === 's') {
      e.preventDefault();
      sidebarCtrl.toggleSidebar();
      return;
    }

    // Ctrl + , : Settings
    if (isCtrl && e.key === ',') {
      e.preventDefault();
      settingsCtrl.open('general');
      return;
    }

    // Shift + Ctrl + K : Clear Today Tabs
    if (isCtrl && e.shiftKey && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      sidebarCtrl.clearTodayTabs();
      return;
    }

    // Ctrl + R or F5 : Reload
    if ((isCtrl && e.key.toLowerCase() === 'r') || e.key === 'F5') {
      e.preventDefault();
      window.craAPI.reload();
      return;
    }

    // Alt + Left : Go Back
    if (e.altKey && e.key === 'ArrowLeft') {
      e.preventDefault();
      window.craAPI.goBack();
      return;
    }

    // Alt + Right : Go Forward
    if (e.altKey && e.key === 'ArrowRight') {
      e.preventDefault();
      window.craAPI.goForward();
      return;
    }

    // Zoom Controls
    if (isCtrl && (e.key === '=' || e.key === '+')) {
      e.preventDefault();
      window.craAPI.zoomIn();
      return;
    }
    if (isCtrl && (e.key === '-' || e.key === '_')) {
      e.preventDefault();
      window.craAPI.zoomOut();
      return;
    }
    if (isCtrl && e.key === '0') {
      e.preventDefault();
      window.craAPI.zoomReset();
      return;
    }

    // Ctrl + Shift + I : DevTools
    if (isCtrl && e.shiftKey && e.key.toLowerCase() === 'i') {
      e.preventDefault();
      window.craAPI.toggleDevTools();
      return;
    }
  });
}

window.addEventListener('DOMContentLoaded', () => {
  bootstrap().catch((err) => {
    console.error('Failed to initialize Cra Browser UI shell:', err);
  });
});
