const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const path = require('path');
const esbuild = require('esbuild');

// Compile storage module for unit testing
const result = esbuild.buildSync({
  entryPoints: ['src/main/storage.ts'],
  write: false,
  format: 'cjs',
  target: 'node20',
});

const moduleCode = result.outputFiles[0].text;
const storageModule = { exports: {} };
const fn = new Function('module', 'exports', 'require', '__dirname', moduleCode);
fn(storageModule, storageModule.exports, require, __dirname);
const { Storage } = storageModule.exports;

test('Storage module initializes and normalizes sidebar', () => {
  assert.ok(Storage, 'Storage class is exported');

  const fresh = Storage.createFreshSidebar();
  assert.ok(Array.isArray(fresh.spaces), 'Spaces is an array');
  assert.ok(fresh.spaces.length >= 2, 'Default spaces created (Personal, Work)');
  assert.ok(fresh.containers[fresh.spaces[0].todayContainerId], 'Today container exists');
  assert.ok(fresh.containers[fresh.spaces[0].favoritesContainerId], 'Favorites container exists');

  // Test legacy normalization with folder attributes
  const legacyDoc = {
    spaces: [{ id: 'sp-1', title: 'Personal', todayContainerId: 'tod-1' }],
    items: [
      { id: 'tod-1', itemType: 'container', containerKind: 'today', spaceID: 'sp-1', children: ['tab-1'] },
      { id: 'tab-1', itemType: 'tab', spaceID: 'sp-1', title: 'Test Tab', tabData: { url: 'https://example.com' } },
      { id: 'folder-1', itemType: 'folder', spaceID: 'sp-1', title: 'Code Folder', folderSymbol: 'code', folderColor: '#5e81f4', children: ['tab-1'] }
    ]
  };
  const normalized = Storage.normalizeSidebar(legacyDoc);
  assert.equal(normalized.spaces[0].id, 'sp-1');
  assert.deepEqual(normalized.containers['tod-1'], ['tab-1']);
  assert.equal(normalized.items['tab-1'].title, 'Test Tab');
  assert.equal(normalized.items['tab-1'].tabData.url, 'https://example.com');
  assert.equal(normalized.items['folder-1'].title, 'Code Folder');
  assert.equal(normalized.items['folder-1'].folderSymbol, 'code');
  assert.equal(normalized.items['folder-1'].folderColor, '#5e81f4');
});

test('Settings load and save defaults correctly', () => {
  const settings = Storage.loadSettings();
  assert.ok(settings.search_engine, 'Search engine is defined');
  assert.equal(typeof settings.adblock_enabled, 'boolean');
  assert.equal(typeof settings.tab_sleep_enabled, 'boolean');
  assert.equal(typeof settings.sidebar_width, 'number');
  assert.equal(settings.top_bar_mode, 'toolbar');
  assert.equal(settings.window_controls_position, 'right');
});

test('Distribution files are properly generated', () => {
  assert.ok(fs.existsSync('dist/main.js'), 'dist/main.js exists');
  assert.ok(fs.existsSync('dist/preload.js'), 'dist/preload.js exists');
  assert.ok(fs.existsSync('dist/renderer/index.html'), 'dist/renderer/index.html exists');
  assert.ok(fs.existsSync('dist/renderer/app.js'), 'dist/renderer/app.js exists');
  assert.ok(fs.existsSync('dist/renderer/styles/main.css'), 'dist/renderer/styles/main.css exists');
  assert.ok(fs.existsSync('dist/renderer/styles/sidebar.css'), 'dist/renderer/styles/sidebar.css exists');
  assert.ok(fs.existsSync('dist/renderer/styles/tabs.css'), 'dist/renderer/styles/tabs.css exists');
  assert.ok(fs.existsSync('dist/renderer/styles/toolbar.css'), 'dist/renderer/styles/toolbar.css exists');
  assert.ok(fs.existsSync('dist/renderer/styles/settings.css'), 'dist/renderer/styles/settings.css exists');
  assert.ok(fs.existsSync('dist/renderer/styles/command-bar.css'), 'dist/renderer/styles/command-bar.css exists');
});
