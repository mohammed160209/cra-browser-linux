import { contextBridge, ipcRenderer } from 'electron';

export interface CraAPI {
  getSidebar: () => Promise<any>;
  saveSidebar: (doc: any) => Promise<boolean>;
  getSettings: () => Promise<any>;
  saveSettings: (settings: any) => Promise<boolean>;
  getArchive: () => Promise<any>;
  clearArchive: () => Promise<boolean>;
  showTab: (tabId: string, url?: string) => Promise<boolean>;
  navigateTab: (url: string) => Promise<boolean>;
  closeTab: (tabId: string) => Promise<boolean>;
  splitTab: (secondaryTabId: string, orientation?: 'horizontal' | 'vertical') => Promise<boolean>;
  unsplit: () => Promise<boolean>;
  toggleSplitOrientation: () => Promise<boolean>;
  updateSidebarGeometry: (width: number, visible: boolean) => Promise<boolean>;
  goBack: () => Promise<void>;
  goForward: () => Promise<void>;
  reload: () => Promise<void>;
  zoomIn: () => Promise<void>;
  zoomOut: () => Promise<void>;
  zoomReset: () => Promise<void>;
  toggleMute: (tabId: string) => Promise<boolean>;
  toggleDevTools: () => Promise<void>;
  openExternal: (url: string) => Promise<void>;
  setContentVisible: (visible: boolean) => Promise<boolean>;
  onTabNavUpdated: (callback: (data: { tabId: string; url: string; canGoBack: boolean; canGoForward: boolean }) => void) => void;
  onTabTitleUpdated: (callback: (data: { tabId: string; title: string }) => void) => void;
  onTabFaviconUpdated: (callback: (data: { tabId: string; favicon: string }) => void) => void;
  onTabAudioUpdated: (callback: (data: { tabId: string; isPlaying: boolean }) => void) => void;
}

const api: CraAPI = {
  getSidebar: () => ipcRenderer.invoke('get-sidebar'),
  saveSidebar: (doc) => ipcRenderer.invoke('save-sidebar', doc),
  getSettings: () => ipcRenderer.invoke('get-settings'),
  saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
  getArchive: () => ipcRenderer.invoke('get-archive'),
  clearArchive: () => ipcRenderer.invoke('clear-archive'),
  showTab: (tabId, url) => ipcRenderer.invoke('show-tab', tabId, url),
  navigateTab: (url) => ipcRenderer.invoke('navigate-tab', url),
  closeTab: (tabId) => ipcRenderer.invoke('close-tab', tabId),
  splitTab: (secId, orient) => ipcRenderer.invoke('split-tab', secId, orient),
  unsplit: () => ipcRenderer.invoke('unsplit'),
  toggleSplitOrientation: () => ipcRenderer.invoke('toggle-split-orientation'),
  updateSidebarGeometry: (width, visible) => ipcRenderer.invoke('update-sidebar-geometry', width, visible),
  goBack: () => ipcRenderer.invoke('go-back'),
  goForward: () => ipcRenderer.invoke('go-forward'),
  reload: () => ipcRenderer.invoke('reload'),
  zoomIn: () => ipcRenderer.invoke('zoom-in'),
  zoomOut: () => ipcRenderer.invoke('zoom-out'),
  zoomReset: () => ipcRenderer.invoke('zoom-reset'),
  toggleMute: (tabId) => ipcRenderer.invoke('toggle-mute', tabId),
  toggleDevTools: () => ipcRenderer.invoke('toggle-devtools'),
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  setContentVisible: (visible) => ipcRenderer.invoke('set-content-visible', visible),
  onTabNavUpdated: (cb) => ipcRenderer.on('tab-nav-updated', (_e, data) => cb(data)),
  onTabTitleUpdated: (cb) => ipcRenderer.on('tab-title-updated', (_e, data) => cb(data)),
  onTabFaviconUpdated: (cb) => ipcRenderer.on('tab-favicon-updated', (_e, data) => cb(data)),
  onTabAudioUpdated: (cb) => ipcRenderer.on('tab-audio-updated', (_e, data) => cb(data)),
};

contextBridge.exposeInMainWorld('craAPI', api);
