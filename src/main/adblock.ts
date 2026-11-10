import * as fs from 'fs';
import * as path from 'path';
import { session } from 'electron';

export class AdblockService {
  private static blockedDomains = new Set<string>();
  private static isInitialized = false;

  public static initialize(): void {
    if (this.isInitialized) return;

    const blocklistPath = path.join(__dirname, '../data/blocklist/domains.txt');
    const altPath = path.join(process.cwd(), 'data/blocklist/domains.txt');
    const finalPath = fs.existsSync(blocklistPath) ? blocklistPath : altPath;

    if (fs.existsSync(finalPath)) {
      try {
        const content = fs.readFileSync(finalPath, 'utf-8');
        const lines = content.split('\n');
        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed && !trimmed.startsWith('#')) {
            this.blockedDomains.add(trimmed.toLowerCase());
          }
        }
        console.log(`[AdblockService] Loaded ${this.blockedDomains.size} blocked domains.`);
      } catch (e) {
        console.error('[AdblockService] Failed to load blocklist:', e);
      }
    }

    session.defaultSession.webRequest.onBeforeRequest((details, callback) => {
      try {
        const parsed = new URL(details.url);
        const hostname = parsed.hostname.toLowerCase();

        // Check if hostname or parent domain is in blocked list
        const parts = hostname.split('.');
        for (let i = 0; i < parts.length - 1; i++) {
          const check = parts.slice(i).join('.');
          if (this.blockedDomains.has(check)) {
            callback({ cancel: true });
            return;
          }
        }
      } catch {
        // invalid URL
      }
      callback({ cancel: false });
    });

    this.isInitialized = true;
  }
}
