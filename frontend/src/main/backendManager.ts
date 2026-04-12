import { ChildProcess, spawn } from 'child_process'
import { join } from 'path'
import { existsSync } from 'fs'
import { app } from 'electron'
import { is } from '@electron-toolkit/utils'

const BACKEND_PORT = 18080
const HEALTH_URL = `http://127.0.0.1:${BACKEND_PORT}/api/health`

export class BackendManager {
  private process: ChildProcess | null = null

  async start(): Promise<void> {
    // Check if backend is already running (remote mode)
    if (await this.isHealthy()) {
      console.log('Backend already running on port', BACKEND_PORT)
      return
    }

    const { command, args, cwd } = this.getBackendCommand()
    console.log(`Starting backend: ${command} ${args.join(' ')}`)

    this.process = spawn(command, args, {
      cwd,
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true
    })

    this.process.stdout?.on('data', (data: Buffer) => {
      console.log('[backend]', data.toString().trim())
    })

    this.process.stderr?.on('data', (data: Buffer) => {
      console.error('[backend]', data.toString().trim())
    })

    this.process.on('exit', (code) => {
      console.log('Backend process exited with code', code)
      this.process = null
    })

    // Wait for backend to be ready
    await this.waitForHealth(20000)
  }

  stop(): void {
    if (this.process) {
      console.log('Stopping backend...')
      this.process.kill()
      this.process = null
    }
  }

  private getBackendCommand(): { command: string; args: string[]; cwd?: string } {
    if (is.dev) {
      // Development: use python -m
      return {
        command: 'python',
        args: ['-m', 'nekonote.main', '--port', String(BACKEND_PORT)],
        cwd: undefined
      }
    }

    // Production: look for bundled engine executable
    const resourcesPath = join(app.getAppPath(), '..', 'engine')
    const engineExe = join(resourcesPath, 'nekonote-engine.exe')

    if (existsSync(engineExe)) {
      return {
        command: engineExe,
        args: ['--port', String(BACKEND_PORT)],
        cwd: resourcesPath
      }
    }

    // Fallback: try python -m (if user has Python installed)
    console.warn('Bundled engine not found, falling back to python -m')
    return {
      command: 'python',
      args: ['-m', 'nekonote.main', '--port', String(BACKEND_PORT)],
      cwd: undefined
    }
  }

  private async isHealthy(): Promise<boolean> {
    try {
      const res = await fetch(HEALTH_URL)
      return res.ok
    } catch {
      return false
    }
  }

  private async waitForHealth(timeoutMs: number): Promise<void> {
    const start = Date.now()
    while (Date.now() - start < timeoutMs) {
      if (await this.isHealthy()) {
        console.log('Backend is ready')
        return
      }
      await new Promise((r) => setTimeout(r, 500))
    }
    console.warn('Backend health check timed out')
  }
}
