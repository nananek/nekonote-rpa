import { ipcMain, dialog, BrowserWindow, app, screen } from 'electron'
import { readFile, writeFile } from 'fs/promises'
import { existsSync, mkdirSync, writeFileSync, readFileSync, statSync } from 'fs'
import { join } from 'path'

let recordBarWindow: BrowserWindow | null = null

/** Show a small always-on-top floating bar during recording. */
function showRecordBar(): void {
  if (recordBarWindow && !recordBarWindow.isDestroyed()) {
    recordBarWindow.show()
    return
  }

  const display = screen.getPrimaryDisplay()
  const { width } = display.workAreaSize
  const barWidth = 320
  const barHeight = 56

  recordBarWindow = new BrowserWindow({
    width: barWidth,
    height: barHeight,
    x: Math.floor((width - barWidth) / 2),
    y: 20,
    frame: false,
    alwaysOnTop: true,
    transparent: false,
    resizable: false,
    skipTaskbar: true,
    focusable: true,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
  })

  recordBarWindow.setAlwaysOnTop(true, 'screen-saver')

  const html = `
    <!DOCTYPE html><html><head><meta charset="UTF-8"><style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      body {
        font-family: 'Segoe UI', sans-serif;
        background: #0f0f23;
        color: #e2e8f0;
        height: 100vh;
        display: flex;
        align-items: center;
        padding: 0 12px;
        gap: 8px;
        border: 2px solid #a855f7;
        -webkit-app-region: drag;
      }
      .dot {
        width: 10px; height: 10px; border-radius: 50%;
        background: #ef4444;
        animation: pulse 1s infinite;
      }
      .dot.paused { background: #f59e0b; animation: none; }
      @keyframes pulse { 50% { opacity: 0.3; } }
      .label { font-size: 12px; font-weight: 600; flex: 1; }
      button {
        -webkit-app-region: no-drag;
        padding: 4px 10px;
        font-size: 11px;
        background: #1e293b;
        color: #e2e8f0;
        border: 1px solid #334155;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 600;
      }
      button.stop { background: #ef4444; color: #fff; border: none; }
      button:hover { background: #334155; }
      button.stop:hover { background: #dc2626; }
    </style></head><body>
      <div class="dot" id="dot"></div>
      <span class="label" id="label">記録中</span>
      <button id="pause">‖</button>
      <button id="stop" class="stop">■ 完了</button>
      <script>
        const { ipcRenderer } = require('electron');
        let paused = false;
        document.getElementById('pause').onclick = () => {
          paused = !paused;
          ipcRenderer.send('recordbar:action', paused ? 'pause' : 'resume');
          document.getElementById('dot').classList.toggle('paused', paused);
          document.getElementById('label').textContent = paused ? '一時停止中' : '記録中';
          document.getElementById('pause').textContent = paused ? '▶' : '‖';
        };
        document.getElementById('stop').onclick = () => {
          ipcRenderer.send('recordbar:action', 'stop');
        };
      </script>
    </body></html>
  `
  recordBarWindow.loadURL('data:text/html;charset=utf-8,' + encodeURIComponent(html))

  recordBarWindow.on('closed', () => {
    recordBarWindow = null
  })
}

function hideRecordBar(): void {
  if (recordBarWindow && !recordBarWindow.isDestroyed()) {
    recordBarWindow.close()
  }
  recordBarWindow = null
}

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
  // Record bar
  ipcMain.on('recordbar:show', () => showRecordBar())
  ipcMain.on('recordbar:hide', () => hideRecordBar())
  ipcMain.on('recordbar:action', (_e, action: string) => {
    // Forward to main window's renderer
    const mainWin = BrowserWindow.getAllWindows().find((w) => w !== recordBarWindow)
    if (mainWin) {
      mainWin.webContents.send('recordbar:action', action)
    }
  })

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
