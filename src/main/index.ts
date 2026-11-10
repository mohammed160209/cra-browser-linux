import { app, BrowserWindow, ipcMain, shell, Menu } from 'electron';
import * as path from 'path';
import { Storage, SidebarDocument, Settings } from './storage';
import { ViewManager } from './view-manager';
import { AdblockService } from './adblock';
import { TabSleepService } from './tab-sleep';

declare const __dirname: string;
const currentDir = typeof __dirname !== 'undefined' ? __dirname : path.resolve('.');

let mainWindow: BrowserWindow | null = null;
let viewManager: ViewManager | null = null;
let tabSleepService: TabSleepService | null = null;

function createWindow() {
  Menu.setApplicationMenu(null);
  const settings = Storage.loadSettings();

  mainWindow = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 800,
    minHeight: 600,
    title: 'Cra Browser',
    frame: false,
    backgroundColor: '#1e1c26',
    webPreferences: {
      preload: path.join(currentDir, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.on('maximize', () => {
    mainWindow?.webContents.send('window-state-changed', true);
  });
  mainWindow.on('unmaximize', () => {
    mainWindow?.webContents.send('window-state-changed', false);
  });

  viewManager = new ViewManager(mainWindow);
  tabSleepService = new TabSleepService(viewManager);
  tabSleepService.start();

  AdblockService.initialize();

  // Load UI Shell
  const uiPath = path.join(currentDir, 'renderer/index.html');
  mainWindow.loadFile(uiPath);

  // Initialize initial tab from storage
  const sidebarDoc = Storage.loadSidebar();
  const currentSpace = sidebarDoc?.spaces?.[0];
  const initialTabs = (currentSpace && sidebarDoc?.containers?.[currentSpace.todayContainerId]) || [];
  const initialFavs = (currentSpace && sidebarDoc?.containers?.[currentSpace.favoritesContainerId]) || [];

  const firstTabId = initialTabs[0] || initialFavs[0] || 'tab-welcome';
  const firstItem = sidebarDoc?.items?.[firstTabId];
  const initialUrl = firstItem?.savedURL || firstItem?.tabData?.url || 'https://duckduckgo.com';

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
    if (viewManager) {
      viewManager.getOrCreateView(firstTabId, initialUrl);
      viewManager.showTab(firstTabId);
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
    viewManager = null;
  });
}

// App lifecycle
app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('certificate-error', (event, _webContents, _url, _error, _certificate, callback) => {
  event.preventDefault();
  callback(true);
});

// IPC Handlers
ipcMain.handle('get-sidebar', () => {
  return Storage.loadSidebar();
});

ipcMain.handle('save-sidebar', (_event, doc: SidebarDocument) => {
  Storage.saveSidebar(doc);
  return true;
});

ipcMain.handle('get-settings', () => {
  return Storage.loadSettings();
});

ipcMain.handle('save-settings', (_event, settings: Settings) => {
  Storage.saveSettings(settings);
  return true;
});

ipcMain.handle('get-archive', () => {
  return Storage.loadArchive();
});

ipcMain.handle('clear-archive', () => {
  Storage.clearArchive();
  return true;
});

ipcMain.handle('show-tab', (_event, tabId: string, url?: string) => {
  if (viewManager) {
    if (url) {
      viewManager.getOrCreateView(tabId, url);
    }
    viewManager.showTab(tabId);
  }
  return true;
});

ipcMain.handle('navigate-tab', (_event, url: string) => {
  if (viewManager) {
    viewManager.navigateActiveTab(url);
  }
  return true;
});

ipcMain.handle('close-tab', (_event, tabId: string) => {
  if (viewManager) {
    viewManager.closeTab(tabId);
  }
  return true;
});

ipcMain.handle('split-tab', (_event, secondaryTabId: string, orientation?: 'horizontal' | 'vertical') => {
  if (viewManager) {
    viewManager.splitWithTab(secondaryTabId, orientation || 'horizontal');
  }
  return true;
});

ipcMain.handle('unsplit', () => {
  if (viewManager) {
    viewManager.unsplit();
  }
  return true;
});

ipcMain.handle('toggle-split-orientation', () => {
  if (viewManager) {
    viewManager.toggleSplitOrientation();
  }
  return true;
});

ipcMain.handle('update-sidebar-geometry', (_event, width: number, visible: boolean) => {
  if (viewManager) {
    viewManager.setSidebarGeometry(width, visible);
  }
  return true;
});

ipcMain.handle('go-back', () => {
  viewManager?.goBack();
});

ipcMain.handle('go-forward', () => {
  viewManager?.goForward();
});

ipcMain.handle('reload', () => {
  viewManager?.reload();
});

ipcMain.handle('zoom-in', () => {
  viewManager?.zoomIn();
});

ipcMain.handle('zoom-out', () => {
  viewManager?.zoomOut();
});

ipcMain.handle('zoom-reset', () => {
  viewManager?.zoomReset();
});

ipcMain.handle('toggle-devtools', () => {
  viewManager?.toggleDevTools();
});

ipcMain.handle('toggle-mute', (_event, tabId: string) => {
  return viewManager?.toggleMute(tabId);
});

ipcMain.handle('open-external', (_event, url: string) => {
  shell.openExternal(url);
});

ipcMain.handle('set-content-visible', (_event, visible: boolean) => {
  viewManager?.setContentVisible(visible);
  return true;
});

ipcMain.handle('window-minimize', () => {
  mainWindow?.minimize();
  return true;
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
  return mainWindow?.isMaximized() || false;
});

ipcMain.handle('window-close', () => {
  mainWindow?.close();
  return true;
});

ipcMain.handle('window-is-maximized', () => {
  return mainWindow?.isMaximized() || false;
});

ipcMain.handle('set-split-ratio', (_event, ratio: number) => {
  viewManager?.setSplitRatio(ratio);
  return true;
});

ipcMain.handle('set-topbar-visible', (_event, visible: boolean) => {
  viewManager?.setTopBarVisible(visible);
  return true;
});
