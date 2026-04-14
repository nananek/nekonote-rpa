/**
 * Auto-update via electron-updater.
 *
 * Polls GitHub Releases for newer versions and downloads them in the
 * background. When ready, prompts the user to restart.
 *
 * This is the mechanism by which bundled Chromium (via Playwright) gets
 * security updates — each nekonote release re-bundles the latest Chromium,
 * and users receive the new version automatically.
 */

import { app, BrowserWindow, dialog, ipcMain } from 'electron'
import { autoUpdater } from 'electron-updater'
import { existsSync } from 'fs'
import { dirname, join } from 'path'

let checking = false

/** Detect portable/zip extraction by checking for the uninstaller. */
function isPortableInstall(): boolean {
  try {
    // NSIS installer creates an uninstall.exe next to the app
    const appDir = dirname(app.getPath('exe'))
    return !existsSync(join(appDir, 'Uninstall Nekonote.exe'))
  } catch {
    return false
  }
}

export function setupAutoUpdate(): void {
  // No auto-updates during development
  if (!app.isPackaged) return

  // No auto-updates in portable/zip mode (no installer to run)
  if (isPortableInstall()) {
    console.log('Portable mode detected — skipping auto-update.')
    return
  }

  autoUpdater.autoDownload = true
  autoUpdater.autoInstallOnAppQuit = true
  autoUpdater.allowPrerelease = false

  autoUpdater.on('checking-for-update', () => {
    broadcast('update:checking')
  })

  autoUpdater.on('update-available', (info) => {
    broadcast('update:available', {
      version: info.version,
      releaseDate: info.releaseDate,
    })
  })

  autoUpdater.on('update-not-available', () => {
    broadcast('update:none')
  })

  autoUpdater.on('download-progress', (progress) => {
    broadcast('update:progress', {
      percent: Math.round(progress.percent),
      bytesPerSecond: progress.bytesPerSecond,
      transferred: progress.transferred,
      total: progress.total,
    })
  })

  autoUpdater.on('update-downloaded', (info) => {
    broadcast('update:downloaded', { version: info.version })

    // Prompt user to restart
    dialog
      .showMessageBox({
        type: 'info',
        title: 'アップデート準備完了',
        message: `nekonote ${info.version} のダウンロードが完了しました。`,
        detail: '今すぐ再起動してインストールしますか？\n（後で再起動しても自動インストールされます）',
        buttons: ['今すぐ再起動', '後で'],
        defaultId: 0,
        cancelId: 1,
      })
      .then((result) => {
        if (result.response === 0) {
          autoUpdater.quitAndInstall()
        }
      })
  })

  autoUpdater.on('error', (err) => {
    broadcast('update:error', { message: String(err) })
  })

  // IPC: manual check
  ipcMain.handle('update:check', async () => {
    if (checking) return { checking: true }
    checking = true
    try {
      return await autoUpdater.checkForUpdates()
    } finally {
      checking = false
    }
  })

  // IPC: manual download (if autoDownload is off)
  ipcMain.handle('update:download', async () => {
    return autoUpdater.downloadUpdate()
  })

  // IPC: install now
  ipcMain.on('update:install', () => {
    autoUpdater.quitAndInstall()
  })

  // Check for updates 5 seconds after app start, then every 4 hours
  setTimeout(() => {
    autoUpdater.checkForUpdates().catch(() => { /* ignore */ })
  }, 5000)

  setInterval(() => {
    autoUpdater.checkForUpdates().catch(() => { /* ignore */ })
  }, 4 * 60 * 60 * 1000)
}

function broadcast(channel: string, payload?: unknown): void {
  for (const win of BrowserWindow.getAllWindows()) {
    win.webContents.send(channel, payload)
  }
}
