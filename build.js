const esbuild = require('esbuild');
const fs = require('fs');
const path = require('path');

async function build() {
  fs.mkdirSync('dist/renderer', { recursive: true });

  // 1. Build Main Process
  await esbuild.build({
    entryPoints: ['src/main/index.ts'],
    outfile: 'dist/main.js',
    bundle: true,
    platform: 'node',
    target: 'node20',
    format: 'cjs',
    external: ['electron'],
    sourcemap: true,
  });

  // 2. Build Preload Script
  await esbuild.build({
    entryPoints: ['src/preload/index.ts'],
    outfile: 'dist/preload.js',
    bundle: true,
    platform: 'node',
    target: 'node20',
    format: 'cjs',
    external: ['electron'],
    sourcemap: true,
  });

  // 3. Build Renderer Script
  await esbuild.build({
    entryPoints: ['src/renderer/scripts/app.ts'],
    outfile: 'dist/renderer/app.js',
    bundle: true,
    platform: 'browser',
    target: 'chrome120',
    sourcemap: true,
  });

  // 4. Copy static assets (index.html, styles)
  if (fs.existsSync('src/renderer/index.html')) {
    fs.copyFileSync('src/renderer/index.html', 'dist/renderer/index.html');
  }
  if (fs.existsSync('src/renderer/styles')) {
    fs.cpSync('src/renderer/styles', 'dist/renderer/styles', { recursive: true });
  }

  console.log('Build completed successfully.');
}

build().catch((err) => {
  console.error(err);
  process.exit(1);
});
