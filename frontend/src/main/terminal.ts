/**
 * Terminal PTY management for the embedded terminal.
 *
 * Spawns a shell (or `claude` directly) via node-pty and bridges
 * stdin/stdout with the renderer process over IPC.
 */

import { ipcMain, BrowserWindow, app } from 'electron'
import { join, resolve } from 'path'
import * as pty from 'node-pty'
import * as os from 'os'
import { existsSync } from 'fs'

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

    const defaultShell = os.platform() === 'win32' ? 'powershell.exe' : 'bash'

    // Determine project root: prefer parent of frontend/ (dev) or app resources (prod)
    let projectRoot = args?.cwd || process.cwd()
    // In dev, cwd is frontend/; go up to project root where CLAUDE.md and .claude/ live
    const candidate = resolve(projectRoot, '..')
    if (existsSync(join(candidate, 'CLAUDE.md'))) {
      projectRoot = candidate
    } else if (existsSync(join(projectRoot, 'CLAUDE.md'))) {
      // Already at project root
    }
    const cwd = projectRoot

    let shell: string
    let shellArgs: string[]

    if (args?.cmd && args.cmd !== defaultShell) {
      // Launch a specific command via the default shell
      if (os.platform() === 'win32') {
        shell = 'powershell.exe'
        shellArgs = ['-NoExit', '-Command', args.cmd]
      } else {
        shell = 'bash'
        shellArgs = ['-c', args.cmd]
      }
    } else {
      shell = defaultShell
      shellArgs = []
    }

    const cols = args?.cols || 80
    const rows = args?.rows || 24

    ptyProcess = pty.spawn(shell, shellArgs, {
      name: 'xterm-256color',
      cols,
      rows,
      cwd,
      env: {
        ...process.env,
        TERM: 'xterm-256color',
        COLORTERM: 'truecolor'
      } as Record<string, string>
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
