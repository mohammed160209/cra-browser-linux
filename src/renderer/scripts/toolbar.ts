declare const window: Window & { craAPI: any };

export class ToolbarController {
  private backBtn: HTMLButtonElement;
  private forwardBtn: HTMLButtonElement;
  private reloadBtn: HTMLButtonElement;
  private urlPill: HTMLElement;
  private urlText: HTMLElement;
  private muteBtn: HTMLElement;
  private splitBtn: HTMLElement;
  private unsplitBtn: HTMLElement;

  // Window Controls
  private winMinimizeBtn: HTMLElement;
  private winMaximizeBtn: HTMLElement;
  private winCloseBtn: HTMLElement;
  private iconMaximize: HTMLElement;
  private iconRestore: HTMLElement;

  // Split Divider Handle (1:1 macOS Cra SplitDraggerHandleView)
  private splitHandle: HTMLElement;
  private isSplitActive = false;
  private splitOrientation: 'horizontal' | 'vertical' = 'horizontal';
  private splitRatio = 0.5;

  private onOpenCommandBarCallback: () => void;

  constructor(onOpenCommandBar: () => void) {
    this.onOpenCommandBarCallback = onOpenCommandBar;

    this.backBtn = document.getElementById('btn-history-back') as HTMLButtonElement;
    this.forwardBtn = document.getElementById('btn-history-forward') as HTMLButtonElement;
    this.reloadBtn = document.getElementById('btn-reload') as HTMLButtonElement;
    this.urlPill = document.getElementById('url-pill')!;
    this.urlText = document.getElementById('url-text')!;
    this.muteBtn = document.getElementById('btn-toggle-mute')!;
    this.splitBtn = document.getElementById('btn-toggle-split')!;
    this.unsplitBtn = document.getElementById('btn-unsplit')!;

    this.winMinimizeBtn = document.getElementById('btn-win-minimize')!;
    this.winMaximizeBtn = document.getElementById('btn-win-maximize')!;
    this.winCloseBtn = document.getElementById('btn-win-close')!;
    this.iconMaximize = this.winMaximizeBtn?.querySelector('.icon-maximize') as HTMLElement;
    this.iconRestore = this.winMaximizeBtn?.querySelector('.icon-restore') as HTMLElement;

    this.splitHandle = document.getElementById('split-divider-handle')!;

    this.setupListeners();
    this.setupWindowControls();
    this.setupSplitDividerHandle();
  }

  public updateNavigationState(canGoBack: boolean, canGoForward: boolean, url: string): void {
    this.backBtn.disabled = !canGoBack;
    this.forwardBtn.disabled = !canGoForward;
    this.displayUrl(url);
  }

  public displayUrl(url: string): void {
    if (!url || url === 'about:blank') {
      this.urlText.textContent = 'Search or Enter URL…';
      return;
    }
    try {
      const parsed = new URL(url);
      this.urlText.textContent = parsed.hostname.replace(/^www\./, '') + (parsed.pathname !== '/' ? parsed.pathname : '');
    } catch {
      this.urlText.textContent = url;
    }
  }

  public setAudioState(isPlaying: boolean, isMuted: boolean): void {
    if (isPlaying) {
      this.muteBtn.style.display = 'inline-flex';
      this.muteBtn.title = isMuted ? 'Unmute Tab' : 'Mute Tab';
      this.muteBtn.style.color = isMuted ? 'var(--text-tertiary)' : 'var(--space-accent)';
    } else {
      this.muteBtn.style.display = 'none';
    }
  }

  public setSplitActive(active: boolean, orientation: 'horizontal' | 'vertical' = 'horizontal'): void {
    this.isSplitActive = active;
    this.splitOrientation = orientation;
    this.unsplitBtn.style.display = active ? 'inline-flex' : 'none';

    if (active) {
      this.splitHandle.style.display = 'flex';
      this.splitHandle.classList.toggle('vertical', orientation === 'vertical');
      this.updateSplitHandlePosition();
    } else {
      this.splitHandle.style.display = 'none';
    }
  }

  private setupListeners(): void {
    this.backBtn.addEventListener('click', () => {
      window.craAPI.goBack();
    });

    this.forwardBtn.addEventListener('click', () => {
      window.craAPI.goForward();
    });

    this.reloadBtn.addEventListener('click', () => {
      window.craAPI.reload();
    });

    this.urlPill.addEventListener('click', () => {
      this.onOpenCommandBarCallback();
    });

    document.getElementById('placeholder-search-trigger')?.addEventListener('click', () => {
      this.onOpenCommandBarCallback();
    });

    this.splitBtn.addEventListener('click', () => {
      this.splitOrientation = this.splitOrientation === 'horizontal' ? 'vertical' : 'horizontal';
      this.splitHandle.classList.toggle('vertical', this.splitOrientation === 'vertical');
      window.craAPI.toggleSplitOrientation();
      this.updateSplitHandlePosition();
    });

    this.unsplitBtn.addEventListener('click', () => {
      window.craAPI.unsplit();
      this.setSplitActive(false);
    });
  }

  private setupWindowControls(): void {
    this.winMinimizeBtn?.addEventListener('click', () => {
      window.craAPI.minimizeWindow();
    });

    this.winMaximizeBtn?.addEventListener('click', async () => {
      const isMax = await window.craAPI.maximizeWindow();
      this.updateMaximizeState(isMax);
    });

    this.winCloseBtn?.addEventListener('click', () => {
      window.craAPI.closeWindow();
    });

    window.craAPI.onWindowStateChanged((isMaximized: boolean) => {
      this.updateMaximizeState(isMaximized);
    });
  }

  private updateMaximizeState(isMax: boolean): void {
    if (this.iconMaximize && this.iconRestore) {
      this.iconMaximize.style.display = isMax ? 'none' : 'inline-block';
      this.iconRestore.style.display = isMax ? 'inline-block' : 'none';
      this.winMaximizeBtn.title = isMax ? 'Restore' : 'Maximize';
    }
  }

  // 1:1 macOS Cra SplitDraggerHandleView interactive dragging & double-click reset
  private setupSplitDividerHandle(): void {
    let isDragging = false;
    let containerRect: DOMRect;

    this.splitHandle.addEventListener('mousedown', (e) => {
      if (e.detail === 2) {
        // Double-click resets to equal widths (50/50)
        this.splitRatio = 0.5;
        window.craAPI.setSplitRatio(0.5);
        this.updateSplitHandlePosition();
        return;
      }

      isDragging = true;
      this.splitHandle.classList.add('dragging');
      const paneCard = document.getElementById('pane-card')!;
      containerRect = paneCard.getBoundingClientRect();
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging || !containerRect) return;

      if (this.splitOrientation === 'horizontal') {
        const x = e.clientX - containerRect.left;
        const ratio = Math.max(0.15, Math.min(0.85, x / containerRect.width));
        this.splitRatio = ratio;
        window.craAPI.setSplitRatio(ratio);
        this.updateSplitHandlePosition();
      } else {
        const y = e.clientY - containerRect.top;
        const ratio = Math.max(0.15, Math.min(0.85, y / containerRect.height));
        this.splitRatio = ratio;
        window.craAPI.setSplitRatio(ratio);
        this.updateSplitHandlePosition();
      }
    });

    window.addEventListener('mouseup', () => {
      if (isDragging) {
        isDragging = false;
        this.splitHandle.classList.remove('dragging');
      }
    });

    window.addEventListener('resize', () => {
      if (this.isSplitActive) {
        this.updateSplitHandlePosition();
      }
    });
  }

  private updateSplitHandlePosition(): void {
    const paneCard = document.getElementById('pane-card');
    if (!paneCard || !this.isSplitActive) return;

    const width = paneCard.clientWidth;
    const height = paneCard.clientHeight;
    const toolbarHeight = document.body.classList.contains('compact-topbar') ? 0 : 44;

    if (this.splitOrientation === 'horizontal') {
      const x = Math.floor(width * this.splitRatio) - 3;
      this.splitHandle.style.left = `${x}px`;
      this.splitHandle.style.top = `${toolbarHeight}px`;
      this.splitHandle.style.width = '6px';
      this.splitHandle.style.height = `${height - toolbarHeight}px`;
    } else {
      const y = toolbarHeight + Math.floor((height - toolbarHeight) * this.splitRatio) - 3;
      this.splitHandle.style.left = '0px';
      this.splitHandle.style.top = `${y}px`;
      this.splitHandle.style.width = `${width}px`;
      this.splitHandle.style.height = '6px';
    }
  }
}
