/**
 * Terminal PTY management for the embedded terminal.
 *
 * Spawns a shell (or `claude` directly) via node-pty and bridges
 * stdin/stdout with the renderer process over IPC.
 */

import { ipcMain, BrowserWindow } from 'electron'
import * as pty from 'node-pty'
import * as os from 'os'

let ptyProcess: pty.IPty | null = null

/**
 * Set up IPC handlers for terminal communication.
 * Call once from the main process during app init.
 */
export function setupTerminal(): void {
  // Spawn PTY
  ipcMain.handle('terminal:spawn', (_event, args?: { cmd?: string; cwd?: string }) => {
    if (ptyProcess) {
      ptyProcess.kill()
      ptyProcess = null
    }

    const shell = args?.cmd || (os.platform() === 'win32' ? 'powershell.exe' : 'bash')
    const cwd = args?.cwd || process.cwd()

    ptyProcess = pty.spawn(shell, [], {
      name: 'xterm-color',
      cols: 120,
      rows: 30,
      cwd,
      env: { ...process.env } as Record<string, string>
    })

    // Forward PTY output to renderer
    ptyProcess.onData((data) => {
      const win = BrowserWindow.getAllWindows()[0]
      if (win) {
        win.webContents.send('terminal:data', data)
      }
    })

    ptyProcess.onExit(({ exitCode }) => {
      const win = BrowserWindow.getAllWindows()[0]
      if (win) {
        win.webContents.send('terminal:exit', exitCode)
      }
      ptyProcess = null
    })

    return true
  })

  // Receive input from renderer
  ipcMain.on('terminal:input', (_event, data: string) => {
    if (ptyProcess) {
      ptyProcess.write(data)
    }
  })

  // Resize
  ipcMain.on('terminal:resize', (_event, cols: number, rows: number) => {
    if (ptyProcess) {
      ptyProcess.resize(cols, rows)
    }
  })

  // Kill
  ipcMain.handle('terminal:kill', () => {
    if (ptyProcess) {
      ptyProcess.kill()
      ptyProcess = null
    }
    return true
  })
}

/**
 * Kill the PTY process if it's still running.
 * Call during app shutdown.
 */
export function cleanupTerminal(): void {
  if (ptyProcess) {
    ptyProcess.kill()
    ptyProcess = null
  }
}
