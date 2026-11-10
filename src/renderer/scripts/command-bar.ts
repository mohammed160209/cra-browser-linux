import { SidebarDocument } from './types';

declare const window: Window & { craAPI: any };

interface Suggestion {
  id: string;
  title: string;
  subtitle: string;
  iconSvg: string;
  action: () => void;
}

export class CommandBarController {
  private overlay: HTMLElement;
  private card: HTMLElement;
  private input: HTMLInputElement;
  private scopeBadge: HTMLElement;
  private suggestionsList: HTMLElement;

  private isOpen = false;
  private selectedIndex = 0;
  private suggestions: Suggestion[] = [];
  private getSidebarDoc: () => SidebarDocument;
  private onSelectTab: (tabId: string) => void;
  private onOpenSettings: () => void;

  constructor(
    getSidebarDoc: () => SidebarDocument,
    onSelectTab: (tabId: string) => void,
    onOpenSettings: () => void
  ) {
    this.getSidebarDoc = getSidebarDoc;
    this.onSelectTab = onSelectTab;
    this.onOpenSettings = onOpenSettings;

    this.overlay = document.getElementById('command-bar-overlay')!;
    this.card = document.getElementById('command-bar-card')!;
    this.input = document.getElementById('command-input') as HTMLInputElement;
    this.scopeBadge = document.getElementById('command-scope-badge')!;
    this.suggestionsList = document.getElementById('command-suggestions-list')!;

    this.setupListeners();
  }

  public open(prefill = ''): void {
    this.isOpen = true;
    this.overlay.classList.add('open');
    this.input.value = prefill;
    this.selectedIndex = 0;
    this.scopeBadge.classList.remove('visible');

    // Hide native Chromium view while modal is open for crystal-clear glassmorphism
    window.craAPI.setContentVisible(false);

    setTimeout(() => {
      this.input.focus();
      this.input.select();
      this.updateSuggestions();
    }, 50);
  }

  public close(): void {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.overlay.classList.remove('open');
    this.input.blur();

    // Restore native Chromium view
    window.craAPI.setContentVisible(true);
  }

  public isBarOpen(): boolean {
    return this.isOpen;
  }

  private setupListeners(): void {
    this.overlay.addEventListener('click', (e) => {
      if (e.target === this.overlay) {
        this.close();
      }
    });

    this.input.addEventListener('input', () => {
      this.selectedIndex = 0;
      this.updateSuggestions();
    });

    this.input.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        this.close();
      } else if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.moveSelection(1);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.moveSelection(-1);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        this.commit();
      } else if (e.key === 'Tab') {
        e.preventDefault();
        this.toggleScope();
      }
    });
  }

  private toggleScope(): void {
    const isVisible = this.scopeBadge.classList.toggle('visible');
    this.scopeBadge.textContent = isVisible ? 'ACTIONS' : '';
    this.updateSuggestions();
  }

  private moveSelection(delta: number): void {
    if (this.suggestions.length === 0) return;
    const count = this.suggestions.length;
    this.selectedIndex = (this.selectedIndex + delta + count) % count;
    this.renderSuggestions();

    const selectedEl = this.suggestionsList.children[this.selectedIndex] as HTMLElement;
    if (selectedEl) {
      selectedEl.scrollIntoView({ block: 'nearest' });
    }
  }

  private commit(): void {
    if (this.suggestions.length > 0 && this.suggestions[this.selectedIndex]) {
      const selected = this.suggestions[this.selectedIndex];
      this.close();
      selected.action();
    } else {
      const query = this.input.value.trim();
      if (query) {
        this.close();
        window.craAPI.navigateTab(query);
      }
    }
  }

  private updateSuggestions(): void {
    const query = this.input.value.trim().toLowerCase();
    const isActionScope = this.scopeBadge.classList.contains('visible');
    const doc = this.getSidebarDoc();
    const list: Suggestion[] = [];

    const searchIcon = '<svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>';
    const tabIcon = '<svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/></svg>';
    const actionIcon = '<svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>';

    // Top Row: Search or Navigate
    if (query) {
      const isUrl = query.includes('.') && !query.includes(' ');
      list.push({
        id: 'primary-action',
        title: isUrl ? `Navigate to https://${query}` : `Search DuckDuckGo for "${query}"`,
        subtitle: isUrl ? 'Open URL' : 'Web Search',
        iconSvg: searchIcon,
        action: () => window.craAPI.navigateTab(query),
      });
    }

    // Matching Open Tabs
    if (!isActionScope) {
      for (const item of Object.values(doc.items)) {
        if (item.itemType === 'tab') {
          const title = item.title.toLowerCase();
          const url = (item.tabData?.url || item.savedURL || '').toLowerCase();
          if (!query || title.includes(query) || url.includes(query)) {
            list.push({
              id: `tab-${item.id}`,
              title: item.title,
              subtitle: item.tabData?.url || item.savedURL || 'Open Tab',
              iconSvg: tabIcon,
              action: () => this.onSelectTab(item.id),
            });
          }
        }
      }
    }

    // Built-in Actions
    const actions: Suggestion[] = [
      {
        id: 'action-settings',
        title: 'Open Settings',
        subtitle: 'Browser Preferences (Ctrl+,)',
        iconSvg: actionIcon,
        action: () => this.onOpenSettings(),
      },
      {
        id: 'action-devtools',
        title: 'Toggle Developer Tools',
        subtitle: 'Inspect DOM and Console (Ctrl+Shift+I)',
        iconSvg: actionIcon,
        action: () => window.craAPI.toggleDevTools(),
      },
      {
        id: 'action-split',
        title: 'Toggle Split View Orientation',
        subtitle: 'Switch horizontal / vertical split',
        iconSvg: actionIcon,
        action: () => window.craAPI.toggleSplitOrientation(),
      },
      {
        id: 'action-clear-archive',
        title: 'Clear Tabs Archive',
        subtitle: 'Remove all archived sessions',
        iconSvg: actionIcon,
        action: () => window.craAPI.clearArchive(),
      },
    ];

    for (const act of actions) {
      if (!query || act.title.toLowerCase().includes(query)) {
        list.push(act);
      }
    }

    this.suggestions = list.slice(0, 10);
    this.renderSuggestions();
  }

  private renderSuggestions(): void {
    this.suggestionsList.innerHTML = '';
    this.suggestions.forEach((item, index) => {
      const row = document.createElement('div');
      row.className = 'suggestion-item' + (this.selectedIndex === index ? ' selected' : '');
      row.innerHTML = `
        <div class="suggestion-icon">${item.iconSvg}</div>
        <div class="suggestion-content">
          <span class="suggestion-title">${this.escapeHtml(item.title)}</span>
          <span class="suggestion-subtitle">${this.escapeHtml(item.subtitle)}</span>
        </div>
      `;

      row.addEventListener('click', () => {
        this.close();
        item.action();
      });

      this.suggestionsList.appendChild(row);
    });
  }

  private escapeHtml(str: string): string {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}
