import { ChildProcess, spawn } from 'child_process'
import { join } from 'path'
import { existsSync } from 'fs'
import { app, ipcMain, BrowserWindow } from 'electron'
import { is } from '@electron-toolkit/utils'
import * as readline from 'readline'

export class BackendManager {
  private process: ChildProcess | null = null
  private rl: readline.Interface | null = null

  async start(): Promise<void> {
    const { command, args, cwd } = this.getBackendCommand()
    console.log(`Starting backend (stdio): ${command} ${args.join(' ')}`)

    this.process = spawn(command, args, {
      cwd,
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true
    })

    // Read JSON lines from stdout
    this.rl = readline.createInterface({ input: this.process.stdout! })
    this.rl.on('line', (line: string) => {
      try {
        const event = JSON.parse(line)
        // Forward to all renderer windows
        for (const win of BrowserWindow.getAllWindows()) {
          win.webContents.send('backend:event', event)
        }
      } catch {
        console.log('[backend stdout]', line)
      }
    })

    this.process.stderr?.on('data', (data: Buffer) => {
      console.error('[backend]', data.toString().trim())
    })

    this.process.on('exit', (code) => {
      console.log('Backend process exited with code', code)
      this.process = null
      this.rl = null
    })

    // Set up IPC: renderer -> backend
    ipcMain.on('backend:send', (_event, msg: unknown) => {
      this.send(msg)
    })

    // Wait for "ready" message
    await this.waitForReady(15000)
  }

  stop(): void {
    if (this.process) {
      console.log('Stopping backend...')
      this.process.kill()
      this.process = null
      this.rl = null
    }
    ipcMain.removeAllListeners('backend:send')
  }

  send(msg: unknown): void {
    if (this.process?.stdin?.writable) {
      this.process.stdin.write(JSON.stringify(msg) + '\n')
    }
  }

  private getBackendCommand(): { command: string; args: string[]; cwd?: string } {
    if (is.dev) {
      return {
        command: 'python',
        args: ['-m', 'nekonote.main', '--stdio']
      }
    }

    const resourcesPath = join(app.getAppPath(), '..', 'engine')
    const engineExe = join(resourcesPath, 'nekonote-engine.exe')

    if (existsSync(engineExe)) {
      return {
        command: engineExe,
        args: ['--stdio'],
        cwd: resourcesPath
      }
    }

    console.warn('Bundled engine not found, falling back to python')
    return {
      command: 'python',
      args: ['-m', 'nekonote.main', '--stdio']
    }
  }

  private waitForReady(timeoutMs: number): Promise<void> {
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        console.warn('Backend ready timeout, continuing anyway')
        resolve()
      }, timeoutMs)

      const handler = (line: string): void => {
        try {
          const msg = JSON.parse(line)
          if (msg.type === 'ready') {
            clearTimeout(timeout)
            console.log('Backend is ready (stdio)')
            // Remove this one-time listener, the main rl listener handles the rest
            resolve()
          }
        } catch {
          // ignore
        }
      }

      // Listen on the already-created readline
      // The main rl.on('line') handler also fires, forwarding "ready" to renderer is fine
      if (this.rl) {
        this.rl.once('line', handler)
      } else {
        clearTimeout(timeout)
        resolve()
      }
    })
  }
}
