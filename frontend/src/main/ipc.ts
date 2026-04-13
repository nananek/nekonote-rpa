import { ipcMain, dialog, BrowserWindow, app } from 'electron'
import { readFile, writeFile, watch } from 'fs/promises'
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs'
import { join } from 'path'

/** Path to the shared flow file that MCP server can read/write */
function getSharedFlowPath(): string {
  const dir = join(app.getPath('userData'), 'shared')
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true })
  return join(dir, 'current_flow.json')
}

let fileWatchAbort: AbortController | null = null

export function setupIpc(): void {
  // Expose shared flow path to renderer
  ipcMain.handle('flow:getSharedPath', () => getSharedFlowPath())

  // Sync flow to shared file (called by renderer whenever flow changes)
  ipcMain.on('flow:syncToFile', (_event, flowJson: string) => {
    try {
      writeFileSync(getSharedFlowPath(), flowJson, 'utf-8')
    } catch {
      // ignore write errors
    }
  })

  // Watch shared flow file for external changes (from MCP)
  ipcMain.handle('flow:startWatching', async () => {
    if (fileWatchAbort) fileWatchAbort.abort()
    fileWatchAbort = new AbortController()
    const flowPath = getSharedFlowPath()

    try {
      const watcher = watch(flowPath, { signal: fileWatchAbort.signal })
      ;(async () => {
        try {
          for await (const event of watcher) {
            if (event.eventType === 'change') {
              try {
                const content = readFileSync(flowPath, 'utf-8')
                const win = BrowserWindow.getAllWindows()[0]
                if (win) {
                  win.webContents.send('flow:externalUpdate', content)
                }
              } catch {
                // file may be mid-write
              }
            }
          }
        } catch {
          // watcher aborted or errored
        }
      })()
    } catch {
      // watch setup failed
    }
    return true
  })

  ipcMain.handle('flow:stopWatching', () => {
    if (fileWatchAbort) {
      fileWatchAbort.abort()
      fileWatchAbort = null
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
