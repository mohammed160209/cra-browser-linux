import { SidebarDocument, Space, SidebarItem, DropAction } from './types';
import { DragDropManager } from './dnd';

declare const window: Window & { craAPI: any };

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

  private isSidebarVisible = true;
  private sidebarWidth = 280;

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

    this.dndManager = new DragDropManager(this.handleDropAction.bind(this));

    this.setupResizer();
    this.setupControls();
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

  public createNewTab(url = 'https://duckduckgo.com', title = 'New Tab'): void {
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

    // Also check inside folders
    for (const item of Object.values(this.doc.items)) {
      if (item.children) {
        item.children = item.children.filter((id) => id !== tabId);
      }
    }

    delete this.doc.items[tabId];
    window.craAPI.closeTab(tabId);

    // If active tab was closed, select next available tab
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

  private createFolderElement(folder: SidebarItem): HTMLElement {
    const container = document.createElement('div');
    container.className = 'folder-container';
    container.setAttribute('data-folder-id', folder.id);

    const folderRow = document.createElement('div');
    folderRow.className = 'folder-row';
    folderRow.innerHTML = `
      <svg class="folder-chevron expanded" viewBox="0 0 24 24"><path fill="currentColor" d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>
      <span class="folder-title">${this.escapeHtml(folder.title)}</span>
      <span class="folder-count">${folder.children?.length || 0}</span>
    `;

    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'folder-children';
    childrenContainer.setAttribute('data-container-id', folder.id);

    (folder.children || []).forEach((childId) => {
      const childItem = this.doc.items[childId];
      if (childItem) {
        childrenContainer.appendChild(this.createTabElement(childItem, true));
      }
    });

    folderRow.addEventListener('click', () => {
      const chevron = folderRow.querySelector('.folder-chevron');
      const isExpanded = chevron?.classList.toggle('expanded');
      childrenContainer.style.display = isExpanded ? 'flex' : 'none';
    });

    this.dndManager.registerFolderDrop(folderRow, folder.id);

    container.appendChild(folderRow);
    container.appendChild(childrenContainer);
    return container;
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
        // Select first available tab in this space
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
        // Maybe it's a folder
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

  private removeFromContainers(tabId: string): void {
    for (const key of Object.keys(this.doc.containers)) {
      this.doc.containers[key] = this.doc.containers[key].filter((id) => id !== tabId);
    }
    for (const item of Object.values(this.doc.items)) {
      if (item.children) {
        item.children = item.children.filter((id) => id !== tabId);
      }
    }
  }

  private setupResizer(): void {
    let isResizing = false;
    let startX = 0;
    let startW = 280;

    this.resizerElement.addEventListener('mousedown', (e) => {
      isResizing = true;
      startX = e.clientX;
      startW = this.sidebarWidth;
      this.resizerElement.classList.add('resizing');
      document.body.style.cursor = 'col-resize';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      const newWidth = Math.min(Math.max(startW + (e.clientX - startX), 200), 460);
      this.sidebarWidth = newWidth;
      this.sidebarElement.style.setProperty('--sidebar-width', `${newWidth}px`);
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
