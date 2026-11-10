import { SidebarDocument, Space, SidebarItem, DropAction } from './types';
import { DragDropManager } from './dnd';

declare const window: Window & { craAPI: any };

export const FOLDER_SYMBOLS: Record<string, string> = {
  star: '<path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>',
  bookmark: '<path d="M17 3H7c-1.1 0-1.99.9-1.99 2L5 21l7-3 7 3V5c0-1.1-.9-2-2-2z"/>',
  heart: '<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>',
  bolt: '<path d="M11 21h-1l1-7H7.5c-.58 0-.57-.32-.38-.66.19-.34.05-.08.07-.12C8.48 10.94 10.42 7.54 13 3h1l-1 7h3.5c.49 0 .56.33.47.51l-.07.15C12.9 17.55 11 21 11 21z"/>',
  triangle: '<path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>',
  asterisk: '<path d="M19 10.5h-4.68l3.3-3.3-1.41-1.41-3.3 3.3V4.5h-2v4.59l-3.3-3.3-1.41 1.41 3.3 3.3H5v2h4.59l-3.3 3.3 1.41 1.41 3.3-3.3V19.5h2v-4.59l3.3 3.3 1.41-1.41-3.3-3.3H19v-2z"/>',
  bell: '<path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.63-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.64 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/>',
  lightbulb: '<path d="M9 21c0 .55.45 1 1 1h4c.55 0 1-.45 1-1v-1H9v1zm3-19C8.14 2 5 5.14 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.86-3.14-7-7-7z"/>',
  chat: '<path d="M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>',
  people: '<path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>',
  tools: '<path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"/>',
  egg: '<path d="M12 2C8.5 2 5 7.5 5 13.5 5 18 8 22 12 22s7-4 7-8.5C19 7.5 15.5 2 12 2z"/>',
  circle: '<circle cx="12" cy="12" r="9"/>',
  moon: '<path d="M12.3 2a10 10 0 0 0-1.9 19.8 10 10 0 0 0 11.5-11.5A10 10 0 0 1 12.3 2z"/>',
  planet: '<path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/>',
  leaf: '<path d="M17 8C8 10 5.9 16.17 3.82 21.34l1.89.66.95-2.3c.48.17.98.3 1.34.3C19 20 22 3 22 3c-1 2-8 2.52-11 3.5 3.5 1.5 7 2.5 6 1.5z"/>',
  cloud: '<path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/>',
  paw: '<path d="M12 11c1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3 1.34 3 3 3zm6.5 2c1.38 0 2.5-1.12 2.5-2.5S19.88 8 18.5 8 16 9.12 16 10.5s1.12 2.5 2.5 2.5zM5.5 13C6.88 13 8 11.88 8 10.5S6.88 8 5.5 8 3 9.12 3 10.5 4.12 13 5.5 13zm6.5 2c-3.1 0-6 1.5-6 4 0 1.5 2.5 3 6 3s6-1.5 6-3c0-2.5-2.9-4-6-4z"/>',
  cutlery: '<path d="M11 9H9V2H7v7H5V2H3v7c0 2.12 1.66 3.84 3.75 3.97V22h2.5v-9.03C11.34 12.84 13 11.12 13 9V2h-2v7zm5-3v8h2.5v8H21V2c-2.76 0-5 2.24-5 4z"/>',
  airplane: '<path d="M21 16v-2l-8-5V3.5c0-.83-.67-1.5-1.5-1.5S10 2.67 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>',
  music: '<path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/>',
  video: '<path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>',
  code: '<path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/>',
  skull: '<path d="M12 2C7.58 2 4 5.58 4 10c0 2.89 1.54 5.41 3.85 6.8V20c0 .55.45 1 1 1h6.3c.55 0 1-.45 1-1v-3.2C18.46 15.41 20 12.89 20 10c0-4.42-3.58-8-8-8zm-3 10c-.83 0-1.5-.67-1.5-1.5S8.17 9 9 9s1.5.67 1.5 1.5S9.83 12 9 12zm6 0c-.83 0-1.5-.67-1.5-1.5S14.17 9 15 9s1.5.67 1.5 1.5S15.83 12 15 12z"/>',
};

export const COLOR_PALETTE = [
  '#8b68fc', // Purple (Default)
  '#5e81f4', // Blue
  '#00c6ae', // Teal
  '#28c840', // Green
  '#ffb900', // Yellow
  '#ff8d36', // Orange
  '#ff5f57', // Red
  '#e56ee0', // Pink
  '#888888', // Grey
];

export class SidebarController {
  private doc: SidebarDocument;
  private currentSpaceId: string;
  private activeTabId: string | null = null;
  private dndManager: DragDropManager;

  private sidebarElement: HTMLElement;
  private favoritesGrid: HTMLElement;
  private pinnedList: HTMLElement;
  private todayList: HTMLElement;
  private spaceDockItems: HTMLElement;
  private resizerElement: HTMLElement;
  private spaceTitleDisplay: HTMLElement;

  private isSidebarVisible = true;
  private sidebarWidth = 280;

  // Folder Customization State
  private editingFolderId: string | null = null;
  private selectedSymbol = 'bookmark';
  private selectedColor = '#8b68fc';

  private onTabSelectedCallback: (tabId: string, url?: string) => void;

  constructor(
    doc: SidebarDocument,
    onTabSelected: (tabId: string, url?: string) => void
  ) {
    this.doc = doc;
    this.currentSpaceId = doc.spaceOrder[0] || doc.spaces[0]?.id || 'space-personal';
    this.onTabSelectedCallback = onTabSelected;

    this.sidebarElement = document.getElementById('sidebar')!;
    this.favoritesGrid = document.getElementById('favorites-grid')!;
    this.pinnedList = document.getElementById('pinned-list')!;
    this.todayList = document.getElementById('today-list')!;
    this.spaceDockItems = document.getElementById('space-dock-items')!;
    this.resizerElement = document.getElementById('sidebar-resizer')!;
    this.spaceTitleDisplay = document.getElementById('space-title-display')!;

    this.dndManager = new DragDropManager(this.handleDropAction.bind(this));

    this.setupResizer();
    this.setupControls();
    this.setupFolderPicker();
    this.setupContextMenu();
  }

  public getDocument(): SidebarDocument {
    return this.doc;
  }

  public getCurrentSpace(): Space {
    return this.doc.spaces.find((s) => s.id === this.currentSpaceId) || this.doc.spaces[0];
  }

  public getActiveTabId(): string | null {
    return this.activeTabId;
  }

  public render(): void {
    this.applySpaceTheme();
    this.renderSpaceDock();
    this.renderFavorites();
    this.renderPinnedTabs();
    this.renderTodayTabs();
  }

  public selectTab(tabId: string): void {
    this.activeTabId = tabId;
    const item = this.doc.items[tabId];
    const url = item?.savedURL || item?.tabData?.url || 'https://duckduckgo.com';

    this.highlightActiveTab(tabId);
    this.onTabSelectedCallback(tabId, url);
  }

  public createNewTab(url = 'https://duckduckgo.com', title = 'New Tab', targetFolderId?: string): void {
    const space = this.getCurrentSpace();
    const tabId = 'tab-' + Date.now();
    const newItem: SidebarItem = {
      id: tabId,
      spaceId: space.id,
      itemType: 'tab',
      title,
      tabData: {
        url,
        originalURL: url,
        timeLastActive: Date.now(),
      },
    };

    this.doc.items[tabId] = newItem;

    if (targetFolderId && this.doc.items[targetFolderId]) {
      const folder = this.doc.items[targetFolderId];
      if (!folder.children) folder.children = [];
      folder.children.push(tabId);
      folder.isCollapsed = false;
      this.persist();
      this.renderPinnedTabs();
      this.selectTab(tabId);
      return;
    }

    if (!this.doc.containers[space.todayContainerId]) {
      this.doc.containers[space.todayContainerId] = [];
    }
    this.doc.containers[space.todayContainerId].unshift(tabId);

    this.persist();
    this.renderTodayTabs();
    this.selectTab(tabId);
  }

  public closeTab(tabId: string): void {
    const space = this.getCurrentSpace();
    const todayTabs = this.doc.containers[space.todayContainerId] || [];
    const pinnedTabs = this.doc.containers[space.pinnedContainerId] || [];

    this.doc.containers[space.todayContainerId] = todayTabs.filter((id) => id !== tabId);
    this.doc.containers[space.pinnedContainerId] = pinnedTabs.filter((id) => id !== tabId);

    // Check inside folders
    for (const item of Object.values(this.doc.items)) {
      if (item.children) {
        item.children = item.children.filter((id) => id !== tabId);
      }
    }

    delete this.doc.items[tabId];
    window.craAPI.closeTab(tabId);

    if (this.activeTabId === tabId) {
      const remainingToday = this.doc.containers[space.todayContainerId] || [];
      const remainingPinned = this.doc.containers[space.pinnedContainerId] || [];
      const favs = this.doc.containers[space.favoritesContainerId] || [];
      const nextId = remainingToday[0] || remainingPinned[0] || favs[0];
      if (nextId) {
        this.selectTab(nextId);
      } else {
        this.activeTabId = null;
        document.getElementById('tab-placeholder')!.style.display = 'flex';
      }
    }

    this.persist();
    this.render();
  }

  public clearTodayTabs(): void {
    const space = this.getCurrentSpace();
    const todayTabs = this.doc.containers[space.todayContainerId] || [];
    for (const tabId of todayTabs) {
      delete this.doc.items[tabId];
      window.craAPI.closeTab(tabId);
    }
    this.doc.containers[space.todayContainerId] = [];
    this.persist();
    this.renderTodayTabs();
    if (todayTabs.includes(this.activeTabId || '')) {
      const favs = this.doc.containers[space.favoritesContainerId] || [];
      if (favs.length > 0) {
        this.selectTab(favs[0]);
      }
    }
  }

  public updateTabNav(tabId: string, url: string): void {
    const item = this.doc.items[tabId];
    if (item && item.tabData) {
      item.tabData.url = url;
      item.tabData.timeLastActive = Date.now();
      this.renderTabHomeIcon(tabId);
    }
  }

  public updateTabTitle(tabId: string, title: string): void {
    const item = this.doc.items[tabId];
    if (item) {
      item.title = title;
      const titleEl = document.querySelector(`[data-tab-id="${tabId}"] .tab-title`);
      if (titleEl) {
        titleEl.textContent = title;
      }
    }
  }

  public updateTabFavicon(tabId: string, favicon: string): void {
    const item = this.doc.items[tabId];
    if (item && item.tabData) {
      item.tabData.favicon = favicon;
      const favEl = document.querySelector(`[data-tab-id="${tabId}"] img.tab-favicon`) as HTMLImageElement;
      if (favEl) {
        favEl.src = favicon;
      }
    }
  }

  public updateTabAudio(tabId: string, isPlaying: boolean): void {
    const item = this.doc.items[tabId];
    if (item && item.tabData) {
      item.tabData.isAudioPlaying = isPlaying;
      const badge = document.querySelector(`[data-tab-id="${tabId}"] .tab-audio-badge`) as HTMLElement;
      if (badge) {
        badge.style.display = isPlaying ? 'inline-flex' : 'none';
      }
    }
  }

  public toggleSidebar(forceState?: boolean): void {
    this.isSidebarVisible = forceState !== undefined ? forceState : !this.isSidebarVisible;
    if (this.isSidebarVisible) {
      this.sidebarElement.classList.remove('collapsed');
    } else {
      this.sidebarElement.classList.add('collapsed');
    }
    window.craAPI.updateSidebarGeometry(this.sidebarWidth, this.isSidebarVisible);
  }

  private renderFavorites(): void {
    const space = this.getCurrentSpace();
    const favIds = this.doc.containers[space.favoritesContainerId] || [];
    this.favoritesGrid.innerHTML = '';

    favIds.forEach((favId, index) => {
      const item = this.doc.items[favId];
      if (!item) return;

      const tile = document.createElement('div');
      tile.className = 'favorite-tile' + (this.activeTabId === favId ? ' active' : '');
      tile.setAttribute('data-tab-id', favId);

      const faviconUrl = item.tabData?.favicon || this.getDefaultFavicon(item.savedURL || item.tabData?.url || '');
      tile.innerHTML = `
        <img class="favorite-favicon" src="${faviconUrl}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22><circle cx=%228%22 cy=%228%22 r=%226%22 fill=%22%23888%22/></svg>'">
        <span class="favorite-title">${this.escapeHtml(item.title)}</span>
      `;

      tile.addEventListener('click', () => this.selectTab(favId));
      this.dndManager.registerFavoriteTile(tile, favId, index);

      this.favoritesGrid.appendChild(tile);
    });
  }

  private renderPinnedTabs(): void {
    const space = this.getCurrentSpace();
    const pinIds = this.doc.containers[space.pinnedContainerId] || [];
    this.pinnedList.innerHTML = '';
    this.pinnedList.setAttribute('data-container-id', space.pinnedContainerId);

    pinIds.forEach((itemId) => {
      const item = this.doc.items[itemId];
      if (!item) return;

      if (item.itemType === 'folder') {
        const folderEl = this.createFolderElement(item);
        this.pinnedList.appendChild(folderEl);
      } else {
        const tabEl = this.createTabElement(item, true);
        this.pinnedList.appendChild(tabEl);
      }
    });
  }

  private renderTodayTabs(): void {
    const space = this.getCurrentSpace();
    const todayIds = this.doc.containers[space.todayContainerId] || [];
    this.todayList.innerHTML = '';
    this.todayList.setAttribute('data-container-id', space.todayContainerId);

    todayIds.forEach((tabId) => {
      const item = this.doc.items[tabId];
      if (!item) return;
      const tabEl = this.createTabElement(item, false);
      this.todayList.appendChild(tabEl);
    });
  }

  private createTabElement(item: SidebarItem, isPinned: boolean): HTMLElement {
    const row = document.createElement('div');
    row.className = 'tab-row' + (this.activeTabId === item.id ? ' active' : '');
    row.setAttribute('data-tab-id', item.id);

    const faviconUrl = item.tabData?.favicon || this.getDefaultFavicon(item.tabData?.url || item.savedURL || '');
    const isAudio = item.tabData?.isAudioPlaying;
    const canRevert = isPinned && item.savedURL && item.tabData?.url && item.savedURL !== item.tabData.url;

    row.innerHTML = `
      <img class="tab-favicon" src="${faviconUrl}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22><circle cx=%228%22 cy=%228%22 r=%226%22 fill=%22%23888%22/></svg>'">
      <span class="tab-title">${this.escapeHtml(item.title)}</span>
      <div class="tab-badges">
        <span class="tab-audio-badge" style="display: ${isAudio ? 'inline-flex' : 'none'};" title="Playing audio">
          <svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/></svg>
        </span>
        ${isPinned ? `
        <button class="tab-home-btn" style="display: ${canRevert ? 'inline-flex' : 'none'};" title="Revert to saved URL">
          <svg viewBox="0 0 24 24"><path d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z"/></svg>
        </button>` : ''}
        <button class="tab-close-btn" title="Close Tab (Ctrl+W)">
          <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
        </button>
      </div>
    `;

    row.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (target.closest('.tab-close-btn')) {
        e.stopPropagation();
        this.closeTab(item.id);
        return;
      }
      if (target.closest('.tab-home-btn')) {
        e.stopPropagation();
        if (item.savedURL) {
          window.craAPI.navigateTab(item.savedURL);
        }
        return;
      }
      this.selectTab(item.id);
    });

    this.dndManager.registerDraggableTab(row, item.id);
    return row;
  }

  // 1:1 macOS Folder Glyph and Interactions
  private createFolderElement(folder: SidebarItem): HTMLElement {
    const container = document.createElement('div');
    container.className = 'folder-container';
    container.setAttribute('data-folder-id', folder.id);

    const isExpanded = folder.isCollapsed !== true;
    const color = folder.folderColor || 'var(--space-accent)';
    const symbol = folder.folderSymbol || 'bookmark';
    const symbolSvg = FOLDER_SYMBOLS[symbol] || FOLDER_SYMBOLS['bookmark'];
    const hasChildren = (folder.children?.length || 0) > 0;

    const folderRow = document.createElement('div');
    folderRow.className = 'folder-row';
    folderRow.setAttribute('data-folder-id', folder.id);

    folderRow.innerHTML = `
      <div class="folder-glyph-container ${isExpanded ? 'expanded' : ''}" style="color: ${color};">
        <div class="folder-back-panel"></div>
        <div class="folder-front-panel">
          ${symbol ? `
          <svg class="folder-symbol-icon" viewBox="0 0 24 24">${symbolSvg}</svg>
          ` : (hasChildren && !isExpanded ? `
          <div class="folder-peek-dots">
            <span class="folder-peek-dot"></span>
            <span class="folder-peek-dot"></span>
            <span class="folder-peek-dot"></span>
          </div>
          ` : '')}
        </div>
      </div>
      <span class="folder-title" title="Double click to rename">${this.escapeHtml(folder.title)}</span>
      <span class="folder-count">${folder.children?.length || 0}</span>
    `;

    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'folder-children';
    childrenContainer.setAttribute('data-container-id', folder.id);
    childrenContainer.style.display = isExpanded ? 'flex' : 'none';

    (folder.children || []).forEach((childId) => {
      const childItem = this.doc.items[childId];
      if (childItem) {
        childrenContainer.appendChild(this.createTabElement(childItem, true));
      }
    });

    // Expand/Collapse toggle on click
    folderRow.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT') return;

      folder.isCollapsed = !folder.isCollapsed;
      const glyph = folderRow.querySelector('.folder-glyph-container');
      if (glyph) {
        glyph.classList.toggle('expanded', !folder.isCollapsed);
      }
      childrenContainer.style.display = folder.isCollapsed ? 'none' : 'flex';
      this.persist();
    });

    // Double-click to inline rename
    folderRow.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      this.startInlineFolderRename(folder.id, folderRow);
    });

    // Right-click context menu
    folderRow.addEventListener('contextmenu', (e) => {
      e.preventDefault();
      e.stopPropagation();
      this.openContextMenu(folder.id, e.clientX, e.clientY);
    });

    // Hover preview card
    folderRow.addEventListener('mouseenter', (e) => {
      if (folder.isCollapsed && (folder.children?.length || 0) > 0) {
        this.showFolderHoverPreview(folder, e.clientX, e.clientY);
      }
    });

    folderRow.addEventListener('mouseleave', () => {
      this.hideFolderHoverPreview();
    });

    this.dndManager.registerFolderDrop(folderRow, folder.id);

    container.appendChild(folderRow);
    container.appendChild(childrenContainer);
    return container;
  }

  private startInlineFolderRename(folderId: string, folderRow: HTMLElement): void {
    const titleEl = folderRow.querySelector('.folder-title') as HTMLElement;
    if (!titleEl) return;

    const currentTitle = this.doc.items[folderId]?.title || 'Folder';
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'folder-rename-input';
    input.value = currentTitle;

    const finishRename = () => {
      const newTitle = input.value.trim() || currentTitle;
      this.doc.items[folderId].title = newTitle;
      this.persist();
      this.renderPinnedTabs();
    };

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') finishRename();
      if (e.key === 'Escape') this.renderPinnedTabs();
    });

    input.addEventListener('blur', finishRename);

    titleEl.replaceWith(input);
    input.focus();
    input.select();
  }

  // Right-Click Context Menu Implementation
  private setupContextMenu(): void {
    const menu = document.getElementById('folder-context-menu')!;

    document.getElementById('ctx-new-tab')?.addEventListener('click', () => {
      if (this.editingFolderId) {
        this.createNewTab('https://duckduckgo.com', 'New Tab', this.editingFolderId);
      }
      this.hideContextMenu();
    });

    document.getElementById('ctx-rename-folder')?.addEventListener('click', () => {
      if (this.editingFolderId) {
        const row = document.querySelector(`.folder-row[data-folder-id="${this.editingFolderId}"]`) as HTMLElement;
        if (row) this.startInlineFolderRename(this.editingFolderId, row);
      }
      this.hideContextMenu();
    });

    document.getElementById('ctx-custom-folder')?.addEventListener('click', () => {
      if (this.editingFolderId) {
        this.openFolderPicker(this.editingFolderId);
      }
      this.hideContextMenu();
    });

    document.getElementById('ctx-delete-folder')?.addEventListener('click', () => {
      if (this.editingFolderId) {
        this.deleteFolder(this.editingFolderId);
      }
      this.hideContextMenu();
    });

    window.addEventListener('click', () => this.hideContextMenu());
    window.addEventListener('blur', () => this.hideContextMenu());
  }

  private openContextMenu(folderId: string, x: number, y: number): void {
    this.editingFolderId = folderId;
    const menu = document.getElementById('folder-context-menu')!;
    menu.style.display = 'flex';
    menu.style.left = `${Math.min(x, window.innerWidth - 200)}px`;
    menu.style.top = `${Math.min(y, window.innerHeight - 150)}px`;
  }

  private hideContextMenu(): void {
    const menu = document.getElementById('folder-context-menu');
    if (menu) menu.style.display = 'none';
  }

  private deleteFolder(folderId: string): void {
    const space = this.getCurrentSpace();
    const folder = this.doc.items[folderId];
    if (!folder) return;

    // Move children tabs to Today list before deleting folder
    if (folder.children) {
      if (!this.doc.containers[space.todayContainerId]) {
        this.doc.containers[space.todayContainerId] = [];
      }
      this.doc.containers[space.todayContainerId].push(...folder.children);
    }

    const pinned = this.doc.containers[space.pinnedContainerId] || [];
    this.doc.containers[space.pinnedContainerId] = pinned.filter((id) => id !== folderId);
    delete this.doc.items[folderId];

    this.persist();
    this.render();
  }

  // Folder Symbol & Color Customization Modal
  private setupFolderPicker(): void {
    const overlay = document.getElementById('folder-picker-overlay')!;
    const palette = document.getElementById('folder-color-palette')!;
    const grid = document.getElementById('folder-symbol-grid')!;
    const closeBtn = document.getElementById('btn-close-folder-picker')!;
    const cancelBtn = document.getElementById('btn-cancel-folder-picker')!;
    const saveBtn = document.getElementById('btn-save-folder-picker')!;
    const nameInput = document.getElementById('folder-picker-name-input') as HTMLInputElement;

    // Render Color Swatches
    palette.innerHTML = '';
    COLOR_PALETTE.forEach((hex) => {
      const swatch = document.createElement('div');
      swatch.className = 'color-swatch';
      swatch.style.backgroundColor = hex;
      swatch.setAttribute('data-color', hex);
      swatch.addEventListener('click', () => {
        palette.querySelectorAll('.color-swatch').forEach((s) => s.classList.remove('active'));
        swatch.classList.add('active');
        this.selectedColor = hex;
        this.updateFolderPickerPreview();
      });
      palette.appendChild(swatch);
    });

    // Render Symbol Buttons
    grid.innerHTML = '';
    Object.entries(FOLDER_SYMBOLS).forEach(([symName, svgPath]) => {
      const btn = document.createElement('button');
      btn.className = 'symbol-btn';
      btn.setAttribute('data-symbol', symName);
      btn.title = symName;
      btn.innerHTML = `<svg viewBox="0 0 24 24">${svgPath}</svg>`;
      btn.addEventListener('click', () => {
        grid.querySelectorAll('.symbol-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        this.selectedSymbol = symName;
        this.updateFolderPickerPreview();
      });
      grid.appendChild(btn);
    });

    closeBtn.addEventListener('click', () => this.closeFolderPicker());
    cancelBtn.addEventListener('click', () => this.closeFolderPicker());
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) this.closeFolderPicker();
    });

    saveBtn.addEventListener('click', () => {
      if (this.editingFolderId && this.doc.items[this.editingFolderId]) {
        const folder = this.doc.items[this.editingFolderId];
        folder.title = nameInput.value.trim() || folder.title;
        folder.folderColor = this.selectedColor;
        folder.folderSymbol = this.selectedSymbol;
        this.persist();
        this.renderPinnedTabs();
      }
      this.closeFolderPicker();
    });
  }

  public openFolderPicker(folderId: string): void {
    this.editingFolderId = folderId;
    const folder = this.doc.items[folderId];
    if (!folder) return;

    this.selectedColor = folder.folderColor || COLOR_PALETTE[0];
    this.selectedSymbol = folder.folderSymbol || 'bookmark';

    const overlay = document.getElementById('folder-picker-overlay')!;
    const nameInput = document.getElementById('folder-picker-name-input') as HTMLInputElement;
    nameInput.value = folder.title;

    // Highlight selected color
    document.querySelectorAll('#folder-color-palette .color-swatch').forEach((s) => {
      s.classList.toggle('active', s.getAttribute('data-color') === this.selectedColor);
    });

    // Highlight selected symbol
    document.querySelectorAll('#folder-symbol-grid .symbol-btn').forEach((b) => {
      b.classList.toggle('active', b.getAttribute('data-symbol') === this.selectedSymbol);
    });

    this.updateFolderPickerPreview();
    overlay.classList.add('open');
    window.craAPI.setContentVisible(false);
  }

  private updateFolderPickerPreview(): void {
    const previewBox = document.getElementById('folder-preview-glyph-box')!;
    const symSvg = FOLDER_SYMBOLS[this.selectedSymbol] || FOLDER_SYMBOLS['bookmark'];
    previewBox.innerHTML = `
      <div class="folder-glyph-container expanded" style="color: ${this.selectedColor};">
        <div class="folder-back-panel"></div>
        <div class="folder-front-panel">
          <svg class="folder-symbol-icon" viewBox="0 0 24 24">${symSvg}</svg>
        </div>
      </div>
    `;
  }

  private closeFolderPicker(): void {
    document.getElementById('folder-picker-overlay')?.classList.remove('open');
    window.craAPI.setContentVisible(true);
  }

  // Folder Hover Preview Card
  private showFolderHoverPreview(folder: SidebarItem, x: number, y: number): void {
    const preview = document.getElementById('folder-hover-preview')!;
    const children = (folder.children || []).map((id) => this.doc.items[id]).filter(Boolean);
    if (children.length === 0) return;

    preview.innerHTML = `
      <div style="font-weight: 600; font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--text-tertiary); margin-bottom: 2px;">
        ${this.escapeHtml(folder.title)} (${children.length})
      </div>
      ${children.slice(0, 6).map((c) => `
        <div class="folder-preview-item">
          <img class="folder-preview-favicon" src="${c.tabData?.favicon || this.getDefaultFavicon(c.tabData?.url || '')}" onerror="this.style.display='none'">
          <span class="folder-preview-title">${this.escapeHtml(c.title)}</span>
        </div>
      `).join('')}
    `;

    preview.style.display = 'flex';
    preview.style.left = `${Math.min(x + 20, window.innerWidth - 300)}px`;
    preview.style.top = `${Math.min(y, window.innerHeight - 200)}px`;
  }

  private hideFolderHoverPreview(): void {
    const preview = document.getElementById('folder-hover-preview');
    if (preview) preview.style.display = 'none';
  }

  private renderSpaceDock(): void {
    this.spaceDockItems.innerHTML = '';
    this.doc.spaceOrder.forEach((spaceId) => {
      const space = this.doc.spaces.find((s) => s.id === spaceId);
      if (!space) return;

      const btn = document.createElement('button');
      btn.className = 'space-dock-btn' + (this.currentSpaceId === space.id ? ' active' : '');
      btn.textContent = space.emoji || '🌐';
      btn.title = space.title;

      btn.addEventListener('click', () => {
        this.currentSpaceId = space.id;
        this.render();
        const todayTabs = this.doc.containers[space.todayContainerId] || [];
        const pinTabs = this.doc.containers[space.pinnedContainerId] || [];
        const favTabs = this.doc.containers[space.favoritesContainerId] || [];
        const first = todayTabs[0] || pinTabs[0] || favTabs[0];
        if (first) {
          this.selectTab(first);
        }
      });

      this.spaceDockItems.appendChild(btn);
    });
  }

  private applySpaceTheme(): void {
    const space = this.getCurrentSpace();
    const root = document.documentElement;
    root.style.setProperty('--space-primary', space.theme.primaryHex || '#1e1b2e');
    root.style.setProperty('--space-secondary', space.theme.secondaryHex || '#2a253a');
    root.style.setProperty('--space-angle', `${space.theme.gradientAngle || 135}deg`);

    if (this.spaceTitleDisplay) {
      this.spaceTitleDisplay.textContent = space.title || 'Personal';
    }
  }

  private highlightActiveTab(tabId: string): void {
    document.querySelectorAll('.tab-row, .favorite-tile').forEach((el) => {
      el.classList.remove('active');
    });
    const current = document.querySelector(`[data-tab-id="${tabId}"]`);
    if (current) {
      current.classList.add('active');
    }
    document.getElementById('tab-placeholder')!.style.display = 'none';
  }

  private renderTabHomeIcon(tabId: string): void {
    const item = this.doc.items[tabId];
    if (!item) return;
    const canRevert = item.savedURL && item.tabData?.url && item.savedURL !== item.tabData.url;
    const homeBtn = document.querySelector(`[data-tab-id="${tabId}"] .tab-home-btn`) as HTMLElement;
    if (homeBtn) {
      homeBtn.style.display = canRevert ? 'inline-flex' : 'none';
    }
  }

  private handleDropAction(action: DropAction, draggedId: string): void {
    const space = this.getCurrentSpace();

    if (action.type === 'split') {
      window.craAPI.splitTab(action.targetTabId, 'horizontal');
      document.getElementById('btn-unsplit')!.style.display = 'inline-flex';
      return;
    }

    if (action.type === 'into-folder') {
      const folder = this.doc.items[action.folderId];
      if (folder) {
        if (!folder.children) folder.children = [];
        this.removeFromContainers(draggedId);
        folder.children.push(draggedId);
        folder.isCollapsed = false;
        this.persist();
        this.render();
      }
      return;
    }

    if (action.type === 'reorder-favorite') {
      const favs = this.doc.containers[space.favoritesContainerId] || [];
      const oldIdx = favs.indexOf(draggedId);
      if (oldIdx !== -1) {
        favs.splice(oldIdx, 1);
        favs.splice(action.targetIndex, 0, draggedId);
        this.persist();
        this.renderFavorites();
      }
      return;
    }

    if (action.type === 'reorder') {
      this.removeFromContainers(draggedId);
      let targetList = this.doc.containers[action.containerId];
      if (!targetList) {
        const folder = this.doc.items[action.containerId];
        if (folder) {
          if (!folder.children) folder.children = [];
          targetList = folder.children;
        }
      }

      if (targetList) {
        targetList.splice(action.targetIndex, 0, draggedId);
        this.persist();
        this.render();
      }
    }
  }

  private removeFromContainers(itemId: string): void {
    Object.values(this.doc.containers).forEach((list) => {
      const idx = list.indexOf(itemId);
      if (idx !== -1) list.splice(idx, 1);
    });

    Object.values(this.doc.items).forEach((item) => {
      if (item.children) {
        const idx = item.children.indexOf(itemId);
        if (idx !== -1) item.children.splice(idx, 1);
      }
    });
  }

  private setupResizer(): void {
    let isResizing = false;
    let startX = 0;
    let startWidth = 280;

    this.resizerElement.addEventListener('mousedown', (e) => {
      isResizing = true;
      startX = e.clientX;
      startWidth = this.sidebarWidth;
      this.resizerElement.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      const delta = e.clientX - startX;
      const newWidth = Math.max(200, Math.min(460, startWidth + delta));
      this.sidebarWidth = newWidth;
      document.documentElement.style.setProperty('--sidebar-width', `${newWidth}px`);
      window.craAPI.updateSidebarGeometry(newWidth, this.isSidebarVisible);
    });

    window.addEventListener('mouseup', () => {
      if (isResizing) {
        isResizing = false;
        this.resizerElement.classList.remove('resizing');
        document.body.style.cursor = '';
      }
    });
  }

  private setupControls(): void {
    document.getElementById('btn-toggle-sidebar')?.addEventListener('click', () => {
      this.toggleSidebar();
    });

    document.getElementById('btn-new-tab')?.addEventListener('click', () => {
      this.createNewTab();
    });

    document.getElementById('btn-new-folder')?.addEventListener('click', () => {
      const space = this.getCurrentSpace();
      const folderId = 'folder-' + Date.now();
      const folder: SidebarItem = {
        id: folderId,
        spaceId: space.id,
        itemType: 'folder',
        title: 'New Folder',
        folderColor: COLOR_PALETTE[0],
        folderSymbol: 'bookmark',
        isCollapsed: false,
        children: [],
      };
      this.doc.items[folderId] = folder;
      if (!this.doc.containers[space.pinnedContainerId]) {
        this.doc.containers[space.pinnedContainerId] = [];
      }
      this.doc.containers[space.pinnedContainerId].unshift(folderId);
      this.persist();
      this.renderPinnedTabs();
    });

    document.getElementById('btn-clear-today')?.addEventListener('click', () => {
      this.clearTodayTabs();
    });

    document.getElementById('btn-new-space')?.addEventListener('click', () => {
      const newId = 'space-' + Date.now();
      const spaceCount = this.doc.spaces.length + 1;
      const newSpace: Space = {
        id: newId,
        title: `Space ${spaceCount}`,
        emoji: '🚀',
        theme: { primaryHex: '#221e35', secondaryHex: '#3d2b56', gradientAngle: 135, isDark: true },
        todayContainerId: `today-${newId}`,
        pinnedContainerId: `pin-${newId}`,
        favoritesContainerId: `fav-${newId}`,
      };
      this.doc.spaces.push(newSpace);
      this.doc.spaceOrder.push(newId);
      this.doc.containers[newSpace.todayContainerId] = [];
      this.doc.containers[newSpace.pinnedContainerId] = [];
      this.doc.containers[newSpace.favoritesContainerId] = [];

      this.currentSpaceId = newId;
      this.persist();
      this.render();
      this.createNewTab();
    });
  }

  private persist(): void {
    window.craAPI.saveSidebar(this.doc);
  }

  private getDefaultFavicon(url: string): string {
    try {
      const parsed = new URL(url);
      return `https://icons.duckduckgo.com/ip3/${parsed.hostname}.ico`;
    } catch {
      return 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><circle cx="8" cy="8" r="6" fill="%23888"/></svg>';
    }
  }

  private escapeHtml(str: string): string {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}
