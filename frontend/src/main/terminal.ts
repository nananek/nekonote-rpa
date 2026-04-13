/**
 * Terminal PTY management for the embedded Claude Code terminal.
 *
 * Always launches Claude Code (not a generic shell).
 * Includes Auto-Y: automatically approves Claude Code permission prompts.
 */

import { ipcMain, BrowserWindow, app } from 'electron'
import { join, resolve } from 'path'
import * as pty from 'node-pty'
import * as os from 'os'
import { existsSync, mkdirSync, writeFileSync, copyFileSync } from 'fs'

let ptyProcess: pty.IPty | null = null

/** Create a temp workspace with CLAUDE.md and .mcp.json so Claude Code picks them up. */
function ensureWorkspace(): string {
  const tmpBase = join(os.tmpdir(), 'nekonote-workspace')
  if (!existsSync(tmpBase)) mkdirSync(tmpBase, { recursive: true })

  // Find engine path (bundled backend)
  const resourcesPath = join(app.getAppPath(), '..', 'engine')
  const enginePython = existsSync(join(resourcesPath, 'nekonote-engine.exe'))
    ? join(resourcesPath, 'nekonote-engine.exe')
    : 'python'

  // Write CLAUDE.md from bundled app or generate minimal one
  const claudeMdSrc = join(app.getAppPath(), '..', '..', 'CLAUDE.md')
  const claudeMdDst = join(tmpBase, 'CLAUDE.md')
  if (existsSync(claudeMdSrc)) {
    copyFileSync(claudeMdSrc, claudeMdDst)
  } else {
    // Generate from embedded content
    writeFileSync(claudeMdDst, CLAUDE_MD_CONTENT, 'utf-8')
  }

  // Write .mcp.json pointing to the backend
  const mcpDir = join(tmpBase, '.claude')
  if (!existsSync(mcpDir)) mkdirSync(mcpDir, { recursive: true })

  const mcpJson = {
    mcpServers: {
      nekonote: {
        type: 'stdio',
        command: enginePython === 'python' ? 'python' : enginePython,
        args: enginePython === 'python' ? ['-m', 'nekonote.mcp_server'] : ['--mcp'],
        env: { PYTHONDONTWRITEBYTECODE: '1' }
      }
    }
  }
  writeFileSync(join(tmpBase, '.mcp.json'), JSON.stringify(mcpJson, null, 2), 'utf-8')

  return tmpBase
}

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

    // Set up temp workspace with CLAUDE.md and .mcp.json for Claude Code
    const cwd = ensureWorkspace()

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

// Embedded CLAUDE.md — full API reference so Claude Code knows everything at startup
const CLAUDE_MD_CONTENT = `# nekonote

Windows RPA toolkit. Use MCP tools to edit the open scenario.

## MCP tools (use these first!)
- get_current_flow() / update_flow(flow_json) / add_block(type, label, params) / remove_block(id) / update_block_params(id, params)
- inspect_windows(filter) / inspect_ui_tree(title, depth, xpath) / inspect_browser() / inspect_screenshot(output)
- run_script(script_path) / check_script(script_path) / list_actions()

## Block types
browser.open, browser.navigate, browser.click, browser.type, browser.getText, browser.wait, browser.screenshot, browser.close
desktop.click, desktop.type, desktop.hotkey, desktop.screenshot, desktop.findImage
control.if, control.loop, control.forEach, control.tryCatch, control.wait
data.setVariable, data.log, data.comment, subflow.call

## hotkey format: comma-separated keys
{"keys": "ctrl,a"}, {"keys": "win,r"}, {"keys": "enter"}

## Python API (from nekonote import browser, desktop, ...)
All sync, no async needed. 21 modules: ai, browser, config, db, desktop, dialog, excel, file, gsheets, history, http, log, mail, ocr, pdf, recorder, retry, scheduler, teams, text, window.

## Key functions
browser: open/navigate/click/type/get_text/wait/screenshot/execute_js/get_table/close
desktop: click(x,y)/type(text)/hotkey(*keys)/press(key)/screenshot/find_image/click_element(title,xpath)
window: find(title)/launch(exe)/activate/maximize/close
file: copy/move/delete/read_text/write_text/list_files/zip/unzip
excel: read/write/read_csv/write_csv/read_cell/write_cell
http: get/post/put/patch/delete/download -> Response (.json()/.text())
db: connect(driver,database) -> conn.query(sql)/execute(sql)/close()
text: replace/split/join/trim/regex_match/regex_replace/now()/today()/add_time()
dialog: show_message/confirm/input/select/open_file/save_file
mail: send(to,subject,body)/receive(imap_server,username,password)
log: info/warning/error/debug
`
