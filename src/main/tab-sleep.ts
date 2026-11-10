import { ViewManager } from './view-manager';
import { Storage } from './storage';

export class TabSleepService {
  private viewManager: ViewManager;
  private intervalId: NodeJS.Timeout | null = null;

  constructor(viewManager: ViewManager) {
    this.viewManager = viewManager;
  }

  public start(): void {
    if (this.intervalId) return;
    this.intervalId = setInterval(() => {
      this.evaluateSleep();
    }, 60 * 1000); // Check every minute
  }

  public stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  public evaluateSleep(): void {
    const settings = Storage.loadSettings();
    if (!settings.tab_sleep_enabled) return;

    const thresholdMs = settings.tab_sleep_threshold_minutes * 60 * 1000;
    if (thresholdMs <= 0) return;

    // ViewManager maintains active view timestamps.
    // Idle tabs exceeding threshold can be frozen or discarded to save RAM.
  }
}
