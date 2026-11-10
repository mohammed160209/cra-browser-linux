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

    this.setupListeners();
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
      window.craAPI.toggleSplitOrientation();
    });

    this.unsplitBtn.addEventListener('click', () => {
      window.craAPI.unsplit();
      this.unsplitBtn.style.display = 'none';
    });
  }
}
