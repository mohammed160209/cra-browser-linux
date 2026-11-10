import { DropAction } from './types';

export class DragDropManager {
  private draggedItemId: string | null = null;
  private draggedItemType: 'tab' | 'favorite' | 'folder' | null = null;
  private onDropCallback: (action: DropAction, draggedId: string) => void;
  private activeIndicatorLine: HTMLElement | null = null;

  constructor(onDrop: (action: DropAction, draggedId: string) => void) {
    this.onDropCallback = onDrop;
    this.activeIndicatorLine = document.createElement('div');
    this.activeIndicatorLine.className = 'drop-indicator-line';
  }

  public registerDraggableTab(element: HTMLElement, tabId: string): void {
    element.draggable = true;

    element.addEventListener('dragstart', (e) => {
      this.draggedItemId = tabId;
      this.draggedItemType = 'tab';
      element.classList.add('dragging');
      if (e.dataTransfer) {
        e.dataTransfer.setData('text/plain', tabId);
        e.dataTransfer.effectAllowed = 'move';
      }
    });

    element.addEventListener('dragend', () => {
      this.draggedItemId = null;
      this.draggedItemType = null;
      element.classList.remove('dragging');
      this.cleanupIndicators();
    });

    element.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!this.draggedItemId || this.draggedItemId === tabId) return;

      const rect = element.getBoundingClientRect();
      const relY = e.clientY - rect.top;
      const height = rect.height;

      // In the middle zone (between 25% and 75% height), check for split combination!
      if (relY > height * 0.25 && relY < height * 0.75) {
        this.removeIndicatorLine();
        const relX = e.clientX - rect.left;
        const isLeft = relX < rect.width / 2;
        element.classList.remove('drag-over-split-left', 'drag-over-split-right');
        element.classList.add(isLeft ? 'drag-over-split-left' : 'drag-over-split-right');
      } else {
        element.classList.remove('drag-over-split-left', 'drag-over-split-right');
        // Show insertion line above or below
        const insertBefore = relY <= height / 2;
        if (insertBefore) {
          element.parentNode?.insertBefore(this.activeIndicatorLine!, element);
        } else {
          element.parentNode?.insertBefore(this.activeIndicatorLine!, element.nextSibling);
        }
      }
    });

    element.addEventListener('dragleave', (e) => {
      if (!element.contains(e.relatedTarget as Node)) {
        element.classList.remove('drag-over-split-left', 'drag-over-split-right');
      }
    });

    element.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const draggedId = this.draggedItemId;
      if (!draggedId || draggedId === tabId) {
        this.cleanupIndicators();
        return;
      }

      // Check if dropped as split
      if (element.classList.contains('drag-over-split-left')) {
        this.cleanupIndicators();
        this.onDropCallback({ type: 'split', targetTabId: tabId, leading: true }, draggedId);
        return;
      }
      if (element.classList.contains('drag-over-split-right')) {
        this.cleanupIndicators();
        this.onDropCallback({ type: 'split', targetTabId: tabId, leading: false }, draggedId);
        return;
      }

      // Otherwise reorder relative to parent container
      const container = element.parentElement;
      const containerId = container?.getAttribute('data-container-id') || 'today';
      const children = Array.from(container?.children || []).filter((c) => c !== this.activeIndicatorLine);
      const targetIndex = children.indexOf(element);

      const rect = element.getBoundingClientRect();
      const insertAfter = (e.clientY - rect.top) > (rect.height / 2);
      const finalIndex = insertAfter ? targetIndex + 1 : targetIndex;

      this.cleanupIndicators();
      this.onDropCallback({ type: 'reorder', containerId, targetIndex: finalIndex }, draggedId);
    });
  }

  public registerFolderDrop(element: HTMLElement, folderId: string): void {
    element.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!this.draggedItemId || this.draggedItemId === folderId) return;
      element.classList.add('drag-over-folder');
    });

    element.addEventListener('dragleave', (e) => {
      if (!element.contains(e.relatedTarget as Node)) {
        element.classList.remove('drag-over-folder');
      }
    });

    element.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const draggedId = this.draggedItemId;
      element.classList.remove('drag-over-folder');
      if (draggedId && draggedId !== folderId) {
        this.onDropCallback({ type: 'into-folder', folderId }, draggedId);
      }
    });
  }

  public registerFavoriteTile(element: HTMLElement, favId: string, index: number): void {
    element.draggable = true;

    element.addEventListener('dragstart', (e) => {
      this.draggedItemId = favId;
      this.draggedItemType = 'favorite';
      element.classList.add('dragging');
      if (e.dataTransfer) {
        e.dataTransfer.setData('text/plain', favId);
        e.dataTransfer.effectAllowed = 'move';
      }
    });

    element.addEventListener('dragend', () => {
      this.draggedItemId = null;
      this.draggedItemType = null;
      element.classList.remove('dragging');
    });

    element.addEventListener('dragover', (e) => {
      e.preventDefault();
    });

    element.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      const draggedId = this.draggedItemId;
      if (draggedId && draggedId !== favId) {
        this.onDropCallback({ type: 'reorder-favorite', targetIndex: index }, draggedId);
      }
    });
  }

  private removeIndicatorLine(): void {
    if (this.activeIndicatorLine && this.activeIndicatorLine.parentNode) {
      this.activeIndicatorLine.parentNode.removeChild(this.activeIndicatorLine);
    }
  }

  private cleanupIndicators(): void {
    this.removeIndicatorLine();
    document.querySelectorAll('.drag-over-split-left, .drag-over-split-right, .drag-over-folder').forEach((el) => {
      el.classList.remove('drag-over-split-left', 'drag-over-split-right', 'drag-over-folder');
    });
  }
}
