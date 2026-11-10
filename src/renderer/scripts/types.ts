export interface SpaceTheme {
  primaryHex: string;
  secondaryHex: string;
  gradientAngle: number;
  isDark: boolean;
}

export interface Space {
  id: string;
  title: string;
  emoji: string;
  theme: SpaceTheme;
  todayContainerId: string;
  pinnedContainerId: string;
  favoritesContainerId: string;
}

export interface TabData {
  url: string;
  originalURL: string;
  timeLastActive: number;
  isAudioPlaying?: boolean;
  isMuted?: boolean;
  favicon?: string;
  sessionStateB64?: string;
}

export interface SidebarItem {
  id: string;
  spaceId: string;
  itemType: 'tab' | 'folder';
  title: string;
  customTitle?: string;
  savedURL?: string;
  children?: string[];
  tabData?: TabData;
}

export interface SidebarDocument {
  spaces: Space[];
  spaceOrder: string[];
  containers: Record<string, string[]>;
  items: Record<string, SidebarItem>;
}

export interface Settings {
  search_engine: string;
  adblock_enabled: boolean;
  auto_archive_threshold_hours: number;
  tab_sleep_enabled: boolean;
  tab_sleep_threshold_minutes: number;
  sidebar_width: number;
  hardware_acceleration: boolean;
  https_only: boolean;
  new_tabs_at_top: boolean;
  folder_previews: boolean;
  block_cookie_banners: boolean;
}

export type DropAction =
  | { type: 'reorder'; containerId: string; targetIndex: number }
  | { type: 'split'; targetTabId: string; leading: boolean }
  | { type: 'into-folder'; folderId: string }
  | { type: 'reorder-favorite'; targetIndex: number };
