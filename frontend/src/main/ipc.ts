import { ipcMain, dialog, BrowserWindow, app } from 'electron'
import { readFile, writeFile } from 'fs/promises'
import { existsSync, mkdirSync, writeFileSync, readFileSync, statSync } from 'fs'
import { join } from 'path'

/** Path to the shared flow file that MCP server can read/write */
function getSharedFlowPath(): string {
  const dir = join(app.getPath('userData'), 'shared')
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  return join(dir, 'current_flow.json')
}

let pollInterval: ReturnType<typeof setInterval> | null = null
let lastMtime = 0
let lastContent = ''

export function setupIpc(): void {
  // Expose shared flow path to renderer
  ipcMain.handle('flow:getSharedPath', () => getSharedFlowPath())

  // Sync flow to shared file (called by renderer whenever flow changes)
  ipcMain.on('flow:syncToFile', (_event, flowJson: string) => {
    try {
      writeFileSync(getSharedFlowPath(), flowJson, 'utf-8')
      // Update tracking so we don't treat our own write as an external change
      lastContent = flowJson
      try { lastMtime = statSync(getSharedFlowPath()).mtimeMs } catch { /* */ }
    } catch {
      // ignore write errors
    }
  })

  // Watch shared flow file for external changes (from MCP) — polling for Windows reliability
  ipcMain.handle('flow:startWatching', async () => {
    if (pollInterval) clearInterval(pollInterval)
    const flowPath = getSharedFlowPath()

    // Initialize baseline
    try {
      const stat = statSync(flowPath)
      lastMtime = stat.mtimeMs
      lastContent = readFileSync(flowPath, 'utf-8')
    } catch {
      lastMtime = 0
      lastContent = ''
    }

    pollInterval = setInterval(() => {
      try {
        const stat = statSync(flowPath)
        if (stat.mtimeMs !== lastMtime) {
          lastMtime = stat.mtimeMs
          const content = readFileSync(flowPath, 'utf-8')
          if (content !== lastContent) {
            lastContent = content
            const win = BrowserWindow.getAllWindows()[0]
            if (win) {
              win.webContents.send('flow:externalUpdate', content)
            }
          }
        }
      } catch {
        // file may not exist yet
      }
    }, 500) // poll every 500ms

    return true
  })

  ipcMain.handle('flow:stopWatching', () => {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
    return true
  })

  ipcMain.handle('dialog:openFile', async () => {
    const result = await dialog.showOpenDialog({
      filters: [{ name: 'Nekonote Flow', extensions: ['neko', 'json'] }],
      properties: ['openFile']
    })
    if (result.canceled || result.filePaths.length === 0) return null
    const filePath = result.filePaths[0]
    const content = await readFile(filePath, 'utf-8')
    return { filePath, content }
  })

  ipcMain.handle('dialog:saveFile', async (_event, content: string, currentPath?: string) => {
    let filePath = currentPath
    if (!filePath) {
      const result = await dialog.showSaveDialog({
        filters: [{ name: 'Nekonote Flow', extensions: ['neko'] }]
      })
      if (result.canceled || !result.filePath) return null
      filePath = result.filePath
    }
    await writeFile(filePath, content, 'utf-8')
    return filePath
  })
}
