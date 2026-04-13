/**
 * Terminal PTY management for the embedded Claude Code terminal.
 *
 * Always launches Claude Code (not a generic shell).
 * Includes Auto-Y: automatically approves Claude Code permission prompts.
 */

import { ipcMain, BrowserWindow } from 'electron'
import { join, resolve } from 'path'
import * as pty from 'node-pty'
import * as os from 'os'
import { existsSync } from 'fs'

let ptyProcess: pty.IPty | null = null

// ---------------------------------------------------------------------------
// Auto-Y state
// ---------------------------------------------------------------------------
let autoYesEnabled = true // on by default
let autoYesBuf = ''
let autoYesPending: ReturnType<typeof setTimeout> | null = null
const autoYesLog: Array<{ time: string; prompt: string }> = []
const MAX_BUF = 10 * 1024
const MAX_LOG = 100
const DEBOUNCE_MS = 500

/** Strip ANSI escape sequences */
function stripAnsi(s: string): string {
  return s.replace(/\x1b\[[0-9;]*[A-Za-z]/g, '')
    .replace(/\x1b\][^\x07]*\x07/g, '')
    .replace(/\x1b[()][A-B012]/g, '')
    .replace(/[\x00-\x09\x0b\x0c\x0e-\x1f]/g, '')
}

/** Detect Claude Code permission prompts and auto-approve */
function processAutoYes(data: string): void {
  if (!autoYesEnabled || !ptyProcess) return

  const clean = stripAnsi(data)
  autoYesBuf += clean
  if (autoYesBuf.length > MAX_BUF) {
    autoYesBuf = autoYesBuf.slice(-MAX_BUF)
  }

  // Debounce detection
  if (autoYesPending) clearTimeout(autoYesPending)
  autoYesPending = setTimeout(() => {
    const normalized = autoYesBuf.replace(/\s+/g, '')

    const patterns = [
      /Doyouwantto(proceed|makethisedit|use)/i,
      /Yes,allow/i,
      /Claudewantsto(fetch|search|call|read|write|execute|run|edit)/i,
      /Allowonce/i,
    ]

    const matched = patterns.some((p) => p.test(normalized))
    if (matched && ptyProcess) {
      // Extract a description
      let prompt = 'auto-approved'
      const editMatch = autoYesBuf.match(/Edit:\s*(.+?)[\r\n]/i)
      const fetchMatch = autoYesBuf.match(/Fetch:\s*(.+?)[\r\n]/i)
      const toolMatch = autoYesBuf.match(/Claude wants to (\w+)/i)
      if (editMatch) prompt = `Edit: ${editMatch[1].trim()}`
      else if (fetchMatch) prompt = `Fetch: ${fetchMatch[1].trim()}`
      else if (toolMatch) prompt = `${toolMatch[1]} (auto-approved)`

      // Send Enter to accept
      ptyProcess.write('\r')

      // Log
      const entry = { time: new Date().toISOString(), prompt }
      autoYesLog.push(entry)
      if (autoYesLog.length > MAX_LOG) autoYesLog.shift()

      // Notify renderer
      const win = BrowserWindow.getAllWindows()[0]
      if (win) {
        win.webContents.send('terminal:autoYes', entry)
      }

      autoYesBuf = ''
    }
  }, DEBOUNCE_MS)
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

export function setupTerminal(): void {
  // Spawn Claude Code
  ipcMain.handle('terminal:spawn', (_event, args?: { cwd?: string }) => {
    if (ptyProcess) {
      ptyProcess.kill()
      ptyProcess = null
    }

    // Determine project root
    let projectRoot = args?.cwd || process.cwd()
    const candidate = resolve(projectRoot, '..')
    if (existsSync(join(candidate, 'CLAUDE.md'))) {
      projectRoot = candidate
    }
    const cwd = projectRoot

    // Always launch Claude Code via shell
    const shell = os.platform() === 'win32' ? 'powershell.exe' : 'bash'
    const shellArgs = os.platform() === 'win32'
      ? ['-NoExit', '-Command', 'claude']
      : ['-c', 'claude']

    ptyProcess = pty.spawn(shell, shellArgs, {
      name: 'xterm-256color',
      cols: 80,
      rows: 24,
      cwd,
      env: {
        ...process.env,
        TERM: 'xterm-256color',
        COLORTERM: 'truecolor'
      } as Record<string, string>
    })

    // Reset Auto-Y buffer
    autoYesBuf = ''

    // Forward PTY output to renderer + Auto-Y detection
    ptyProcess.onData((data) => {
      const win = BrowserWindow.getAllWindows()[0]
      if (win) {
        win.webContents.send('terminal:data', data)
      }
      processAutoYes(data)
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

  // Auto-Y toggle
  ipcMain.on('terminal:setAutoYes', (_event, enabled: boolean) => {
    autoYesEnabled = enabled
    const win = BrowserWindow.getAllWindows()[0]
    if (win) {
      win.webContents.send('terminal:autoYesState', { enabled, log: autoYesLog })
    }
  })

  ipcMain.handle('terminal:getAutoYes', () => {
    return { enabled: autoYesEnabled, log: autoYesLog }
  })
}

export function cleanupTerminal(): void {
  if (autoYesPending) clearTimeout(autoYesPending)
  if (ptyProcess) {
    ptyProcess.kill()
    ptyProcess = null
  }
}
