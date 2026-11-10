import { BrowserWindow, WebContentsView } from 'electron';

export interface TabView {
  tabId: string;
  view: WebContentsView;
  url: string;
  title: string;
  isAudioPlaying: boolean;
  isMuted: boolean;
  canGoBack: boolean;
  canGoForward: boolean;
  lastActive: number;
}

export class ViewManager {
  private window: BrowserWindow;
  private views = new Map<string, TabView>();
  private activeTabId: string | null = null;
  private secondaryTabId: string | null = null;
  private isSplit = false;
  private splitOrientation: 'horizontal' | 'vertical' = 'horizontal';

  private sidebarWidth = 260;
  private sidebarVisible = true;

  constructor(window: BrowserWindow) {
    this.window = window;

    this.window.on('resize', () => {
      this.updateLayoutBounds();
    });
  }

  public setSidebarGeometry(width: number, visible: boolean): void {
    this.sidebarWidth = width;
    this.sidebarVisible = visible;
    this.updateLayoutBounds();
  }

  public getOrCreateView(tabId: string, url: string): TabView {
    let entry = this.views.get(tabId);
    if (!entry) {
      const view = new WebContentsView();
      const resolvedUrl = this.resolveUrl(url);

      view.webContents.loadURL(resolvedUrl);

      entry = {
        tabId,
        view,
        url: resolvedUrl,
        title: 'New Tab',
        isAudioPlaying: false,
        isMuted: false,
        canGoBack: false,
        canGoForward: false,
        lastActive: Date.now(),
      };

      view.webContents.on('did-navigate', (_event, uri) => {
        if (entry) {
          entry.url = uri;
          const nav = view.webContents.navigationHistory;
          entry.canGoBack = nav ? nav.canGoBack() : view.webContents.canGoBack();
          entry.canGoForward = nav ? nav.canGoForward() : view.webContents.canGoForward();
          this.window.webContents.send('tab-nav-updated', {
            tabId,
            url: uri,
            canGoBack: entry.canGoBack,
            canGoForward: entry.canGoForward,
          });
        }
      });

      view.webContents.on('page-title-updated', (_event, title) => {
        if (entry) {
          entry.title = title;
          this.window.webContents.send('tab-title-updated', { tabId, title });
        }
      });

      view.webContents.on('page-favicon-updated', (_event, favicons) => {
        if (favicons && favicons.length > 0) {
          this.window.webContents.send('tab-favicon-updated', { tabId, favicon: favicons[0] });
        }
      });

      view.webContents.on('media-started-playing', () => {
        if (entry) {
          entry.isAudioPlaying = true;
          this.window.webContents.send('tab-audio-updated', { tabId, isPlaying: true });
        }
      });

      view.webContents.on('media-paused', () => {
        if (entry) {
          entry.isAudioPlaying = false;
          this.window.webContents.send('tab-audio-updated', { tabId, isPlaying: false });
        }
      });

      this.views.set(tabId, entry);
    }
    return entry;
  }

  public showTab(tabId: string): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const current = this.views.get(this.activeTabId)!;
      try {
        this.window.contentView.removeChildView(current.view);
      } catch {}
    }

    if (this.secondaryTabId && this.views.has(this.secondaryTabId)) {
      const sec = this.views.get(this.secondaryTabId)!;
      try {
        this.window.contentView.removeChildView(sec.view);
      } catch {}
    }

    this.activeTabId = tabId;
    const current = this.getOrCreateView(tabId, 'https://duckduckgo.com');
    current.lastActive = Date.now();

    this.window.contentView.addChildView(current.view);

    if (this.isSplit && this.secondaryTabId) {
      const sec = this.getOrCreateView(this.secondaryTabId, 'https://duckduckgo.com');
      this.window.contentView.addChildView(sec.view);
    }

    this.updateLayoutBounds();
  }

  public splitWithTab(secondaryTabId: string, orientation: 'horizontal' | 'vertical' = 'horizontal'): void {
    this.secondaryTabId = secondaryTabId;
    this.isSplit = true;
    this.splitOrientation = orientation;

    const sec = this.getOrCreateView(secondaryTabId, 'https://duckduckgo.com');
    this.window.contentView.addChildView(sec.view);
    this.updateLayoutBounds();
  }

  public unsplit(): void {
    if (this.secondaryTabId && this.views.has(this.secondaryTabId)) {
      const sec = this.views.get(this.secondaryTabId)!;
      try {
        this.window.contentView.removeChildView(sec.view);
      } catch {}
    }
    this.secondaryTabId = null;
    this.isSplit = false;
    this.updateLayoutBounds();
  }

  public toggleSplitOrientation(): void {
    this.splitOrientation = this.splitOrientation === 'horizontal' ? 'vertical' : 'horizontal';
    this.updateLayoutBounds();
  }

  public navigateActiveTab(url: string): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      const target = this.resolveUrl(url);
      entry.view.webContents.loadURL(target);
    }
  }

  public goBack(): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      const nav = entry.view.webContents.navigationHistory;
      if (nav ? nav.canGoBack() : entry.view.webContents.canGoBack()) {
        if (nav) nav.goBack(); else entry.view.webContents.goBack();
      }
    }
  }

  public goForward(): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      const nav = entry.view.webContents.navigationHistory;
      if (nav ? nav.canGoForward() : entry.view.webContents.canGoForward()) {
        if (nav) nav.goForward(); else entry.view.webContents.goForward();
      }
    }
  }

  public reload(): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      entry.view.webContents.reload();
    }
  }

  public toggleMute(tabId: string): boolean {
    const entry = this.views.get(tabId);
    if (entry) {
      const next = !entry.isMuted;
      entry.isMuted = next;
      entry.view.webContents.setAudioMuted(next);
      return next;
    }
    return false;
  }

  public zoomIn(): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      const level = entry.view.webContents.getZoomLevel();
      entry.view.webContents.setZoomLevel(Math.min(level + 0.5, 5.0));
    }
  }

  public zoomOut(): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      const level = entry.view.webContents.getZoomLevel();
      entry.view.webContents.setZoomLevel(Math.max(level - 0.5, -3.0));
    }
  }

  public zoomReset(): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      entry.view.webContents.setZoomLevel(0);
    }
  }

  public toggleDevTools(): void {
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const entry = this.views.get(this.activeTabId)!;
      entry.view.webContents.toggleDevTools();
    }
  }

  public closeTab(tabId: string): void {
    const entry = this.views.get(tabId);
    if (entry) {
      try {
        this.window.contentView.removeChildView(entry.view);
      } catch {}
      this.views.delete(tabId);
    }
    if (this.secondaryTabId === tabId) {
      this.unsplit();
    }
  }

  private isContentVisible = true;

  public setContentVisible(visible: boolean): void {
    this.isContentVisible = visible;
    if (this.activeTabId && this.views.has(this.activeTabId)) {
      const primary = this.views.get(this.activeTabId)!;
      try {
        primary.view.setVisible(visible);
      } catch {
        if (!visible) {
          try { this.window.contentView.removeChildView(primary.view); } catch {}
        } else {
          try { this.window.contentView.addChildView(primary.view); } catch {}
        }
      }
    }
    if (this.secondaryTabId && this.views.has(this.secondaryTabId)) {
      const sec = this.views.get(this.secondaryTabId)!;
      try {
        sec.view.setVisible(visible);
      } catch {
        if (!visible) {
          try { this.window.contentView.removeChildView(sec.view); } catch {}
        } else {
          try { this.window.contentView.addChildView(sec.view); } catch {}
        }
      }
    }
    if (visible) {
      this.updateLayoutBounds();
    }
  }

  public getActiveView(): TabView | null {
    if (this.activeTabId) {
      return this.views.get(this.activeTabId) || null;
    }
    return null;
  }

  private updateLayoutBounds(): void {
    if (!this.isContentVisible) return;
    const [winWidth, winHeight] = this.window.getSize();
    const xOffset = this.sidebarVisible ? this.sidebarWidth : 0;
    const inset = 6;
    const topBarHeight = 44;
    const contentWidth = Math.max(winWidth - xOffset - (inset * 2), 100);
    const contentHeight = Math.max(winHeight - topBarHeight - (inset * 2), 100);
    const startX = xOffset + inset;
    const startY = topBarHeight + inset;

    if (!this.activeTabId || !this.views.has(this.activeTabId)) return;
    const primary = this.views.get(this.activeTabId)!;

    if (!this.isSplit || !this.secondaryTabId || !this.views.has(this.secondaryTabId)) {
      primary.view.setBounds({
        x: startX,
        y: startY,
        width: contentWidth,
        height: contentHeight,
      });
    } else {
      const secondary = this.views.get(this.secondaryTabId)!;
      const splitGap = 4;
      if (this.splitOrientation === 'horizontal') {
        const halfWidth = Math.floor((contentWidth - splitGap) / 2);
        primary.view.setBounds({
          x: startX,
          y: startY,
          width: halfWidth,
          height: contentHeight,
        });
        secondary.view.setBounds({
          x: startX + halfWidth + splitGap,
          y: startY,
          width: contentWidth - halfWidth - splitGap,
          height: contentHeight,
        });
      } else {
        const halfHeight = Math.floor((contentHeight - splitGap) / 2);
        primary.view.setBounds({
          x: startX,
          y: startY,
          width: contentWidth,
          height: halfHeight,
        });
        secondary.view.setBounds({
          x: startX,
          y: startY + halfHeight + splitGap,
          width: contentWidth,
          height: contentHeight - halfHeight - splitGap,
        });
      }
    }
  }

  private resolveUrl(input: string): string {
    const trimmed = input.trim();
    if (!trimmed) return 'https://duckduckgo.com';
    if (trimmed.startsWith('about:') || trimmed.startsWith('file://')) return trimmed;
    if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed;
    if (trimmed.includes('.') && !trimmed.includes(' ')) return `https://${trimmed}`;
    return `https://duckduckgo.com/?q=${encodeURIComponent(trimmed)}`;
  }
}
