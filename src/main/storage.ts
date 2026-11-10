import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

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

export interface ArchiveEntry {
  id: string;
  url: string;
  title: string;
  archivedAt: number;
  reason: string;
}

export class Storage {
  private static getConfigDir(): string {
    const xdgConfig = process.env.XDG_CONFIG_HOME;
    const base = xdgConfig || path.join(os.homedir(), '.config');
    const dir = path.join(base, 'cra-browser');
    fs.mkdirSync(dir, { recursive: true });
    return dir;
  }

  public static getSidebarPath(): string {
    return path.join(this.getConfigDir(), 'sidebar.json');
  }

  public static getSettingsPath(): string {
    return path.join(this.getConfigDir(), 'settings.json');
  }

  public static getArchivePath(): string {
    return path.join(this.getConfigDir(), 'archive.json');
  }

  public static createFreshSidebar(): SidebarDocument {
    const spaceId = 'space-personal';
    const favId = 'fav-personal';
    const pinId = 'pin-personal';
    const todayId = 'today-personal';

    const defaultFavorites: SidebarItem[] = [
      {
        id: 'fav-1',
        spaceId,
        itemType: 'tab',
        title: 'DuckDuckGo',
        savedURL: 'https://duckduckgo.com',
        tabData: { url: 'https://duckduckgo.com', originalURL: 'https://duckduckgo.com', timeLastActive: Date.now() },
      },
      {
        id: 'fav-2',
        spaceId,
        itemType: 'tab',
        title: 'Arch Linux',
        savedURL: 'https://archlinux.org',
        tabData: { url: 'https://archlinux.org', originalURL: 'https://archlinux.org', timeLastActive: Date.now() },
      },
      {
        id: 'fav-3',
        spaceId,
        itemType: 'tab',
        title: 'GitHub',
        savedURL: 'https://github.com',
        tabData: { url: 'https://github.com', originalURL: 'https://github.com', timeLastActive: Date.now() },
      },
      {
        id: 'fav-4',
        spaceId,
        itemType: 'tab',
        title: 'YouTube',
        savedURL: 'https://youtube.com',
        tabData: { url: 'https://youtube.com', originalURL: 'https://youtube.com', timeLastActive: Date.now() },
      },
    ];

    const initialToday: SidebarItem = {
      id: 'tab-welcome',
      spaceId,
      itemType: 'tab',
      title: 'Welcome to Cra',
      savedURL: 'https://duckduckgo.com',
      tabData: { url: 'https://duckduckgo.com', originalURL: 'https://duckduckgo.com', timeLastActive: Date.now() },
    };

    const items: Record<string, SidebarItem> = {};
    for (const f of defaultFavorites) {
      items[f.id] = f;
    }
    items[initialToday.id] = initialToday;

    return {
      spaces: [
        {
          id: spaceId,
          title: 'Personal',
          emoji: '🏠',
          theme: { primaryHex: '#252136', secondaryHex: '#393552', gradientAngle: 135, isDark: true },
          todayContainerId: todayId,
          pinnedContainerId: pinId,
          favoritesContainerId: favId,
        },
        {
          id: 'space-work',
          title: 'Work',
          emoji: '💼',
          theme: { primaryHex: '#1e2030', secondaryHex: '#2d3f76', gradientAngle: 135, isDark: true },
          todayContainerId: 'today-work',
          pinnedContainerId: 'pin-work',
          favoritesContainerId: 'fav-work',
        },
      ],
      spaceOrder: [spaceId, 'space-work'],
      containers: {
        [favId]: defaultFavorites.map((f) => f.id),
        [pinId]: [],
        [todayId]: [initialToday.id],
        'fav-work': [],
        'pin-work': [],
        'today-work': [],
      },
      items,
    };
  }

  public static normalizeSidebar(data: any): SidebarDocument {
    if (!data || typeof data !== 'object') {
      return this.createFreshSidebar();
    }

    // If it already conforms to the normalized SidebarDocument
    if (
      data.spaces &&
      Array.isArray(data.spaces) &&
      data.containers &&
      typeof data.containers === 'object' &&
      data.items &&
      typeof data.items === 'object' &&
      !Array.isArray(data.items)
    ) {
      return data as SidebarDocument;
    }

    const spaces: Space[] = [];
    const spaceOrder: string[] = [];
    const containers: Record<string, string[]> = {};
    const items: Record<string, SidebarItem> = {};

    if (Array.isArray(data.spaces) && data.spaces.length > 0) {
      for (const s of data.spaces) {
        const spaceId = s.id || ('space-' + Math.random().toString(36).substring(2, 8));
        const space: Space = {
          id: spaceId,
          title: s.title || 'Personal',
          emoji: s.emoji || '🏠',
          theme: s.theme || { primaryHex: '#252136', secondaryHex: '#393552', gradientAngle: 135, isDark: true },
          todayContainerId: s.todayContainerId || `today-${spaceId}`,
          pinnedContainerId: s.pinnedContainerId || `pin-${spaceId}`,
          favoritesContainerId: s.favoritesContainerId || `fav-${spaceId}`,
        };
        spaces.push(space);
        spaceOrder.push(spaceId);
        containers[space.todayContainerId] = [];
        containers[space.pinnedContainerId] = [];
        containers[space.favoritesContainerId] = [];
      }
    } else {
      const fresh = this.createFreshSidebar();
      spaces.push(...fresh.spaces);
      spaceOrder.push(...fresh.spaceOrder);
      Object.assign(containers, fresh.containers);
    }

    if (Array.isArray(data.items)) {
      for (const it of data.items) {
        if (!it || !it.id) continue;
        if (it.itemType === 'container') {
          const targetSpace = spaces.find((sp) => sp.id === it.spaceID) || spaces[0];
          if (it.containerKind === 'today') {
            targetSpace.todayContainerId = it.id;
            containers[it.id] = it.children || [];
          } else if (it.containerKind === 'pinned') {
            targetSpace.pinnedContainerId = it.id;
            containers[it.id] = it.children || [];
          } else if (it.containerKind === 'favorites') {
            targetSpace.favoritesContainerId = it.id;
            containers[it.id] = it.children || [];
          } else {
            containers[it.id] = it.children || [];
          }
        } else {
          items[it.id] = {
            id: it.id,
            spaceId: it.spaceID || spaces[0].id,
            itemType: it.itemType || 'tab',
            title: it.title || it.tabData?.savedTitle || 'Tab',
            savedURL: it.tabData?.savedURL,
            children: it.children || [],
            tabData: it.tabData
              ? {
                  url: it.tabData.url || 'https://duckduckgo.com',
                  originalURL: it.tabData.savedURL || it.tabData.url || 'https://duckduckgo.com',
                  timeLastActive: it.tabData.timeLastActiveAt ? it.tabData.timeLastActiveAt * 1000 : Date.now(),
                  isAudioPlaying: false,
                  isMuted: it.tabData.muted || false,
                }
              : undefined,
          };
        }
      }
    }

    // Ensure all space container IDs exist in containers
    for (const s of spaces) {
      if (!containers[s.todayContainerId]) containers[s.todayContainerId] = [];
      if (!containers[s.pinnedContainerId]) containers[s.pinnedContainerId] = [];
      if (!containers[s.favoritesContainerId]) containers[s.favoritesContainerId] = [];
    }

    return {
      spaces,
      spaceOrder: spaceOrder.length > 0 ? spaceOrder : spaces.map((s) => s.id),
      containers,
      items,
    };
  }

  public static loadSidebar(): SidebarDocument {
    const file = this.getSidebarPath();
    if (fs.existsSync(file)) {
      try {
        const raw = fs.readFileSync(file, 'utf-8');
        const parsed = JSON.parse(raw);
        return this.normalizeSidebar(parsed);
      } catch (e) {
        console.error('Error reading sidebar.json, creating fresh default:', e);
      }
    }
    const fresh = this.createFreshSidebar();
    this.saveSidebar(fresh);
    return fresh;
  }

  public static saveSidebar(doc: SidebarDocument): void {
    const file = this.getSidebarPath();
    fs.writeFileSync(file, JSON.stringify(doc, null, 2), 'utf-8');
  }

  public static loadSettings(): Settings {
    const file = this.getSettingsPath();
    const defaults: Settings = {
      search_engine: 'DuckDuckGo',
      adblock_enabled: true,
      auto_archive_threshold_hours: 24,
      tab_sleep_enabled: true,
      tab_sleep_threshold_minutes: 60,
      sidebar_width: 260,
      hardware_acceleration: true,
      https_only: true,
      new_tabs_at_top: false,
      folder_previews: true,
      block_cookie_banners: true,
    };
    if (fs.existsSync(file)) {
      try {
        const loaded = JSON.parse(fs.readFileSync(file, 'utf-8'));
        return { ...defaults, ...loaded };
      } catch {
        return defaults;
      }
    }
    this.saveSettings(defaults);
    return defaults;
  }

  public static saveSettings(settings: Settings): void {
    const file = this.getSettingsPath();
    fs.writeFileSync(file, JSON.stringify(settings, null, 2), 'utf-8');
  }

  public static loadArchive(): ArchiveEntry[] {
    const file = this.getArchivePath();
    if (fs.existsSync(file)) {
      try {
        return JSON.parse(fs.readFileSync(file, 'utf-8'));
      } catch {
        return [];
      }
    }
    return [];
  }

  public static archiveTabs(entries: ArchiveEntry[]): void {
    const current = this.loadArchive();
    const updated = [...entries, ...current];
    fs.writeFileSync(this.getArchivePath(), JSON.stringify(updated, null, 2), 'utf-8');
  }

  public static clearArchive(): void {
    fs.writeFileSync(this.getArchivePath(), JSON.stringify([], null, 2), 'utf-8');
  }
}
