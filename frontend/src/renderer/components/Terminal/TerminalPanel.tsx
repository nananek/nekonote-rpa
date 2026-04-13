import { useEffect, useRef, useState } from 'react'
import { Terminal } from 'xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import 'xterm/css/xterm.css'

declare global {
  interface Window {
    api: {
      terminalSpawn: (opts?: { cmd?: string; cwd?: string }) => Promise<boolean>
      terminalInput: (data: string) => void
      terminalResize: (cols: number, rows: number) => void
      terminalKill: () => Promise<boolean>
      onTerminalData: (cb: (data: string) => void) => () => void
      onTerminalExit: (cb: (code: number) => void) => () => void
    }
  }
}

export function TerminalPanel(): JSX.Element {
  const containerRef = useRef<HTMLDivElement>(null)
  const termRef = useRef<Terminal | null>(null)
  const fitRef = useRef<FitAddon | null>(null)
  const [started, setStarted] = useState(false)
  const [claudeMode, setClaudeMode] = useState(false)

  useEffect(() => {
    if (!containerRef.current || termRef.current) return

    const term = new Terminal({
      theme: {
        background: '#0f0f23',
        foreground: '#e2e8f0',
        cursor: '#60a5fa',
        selectionBackground: '#334155',
        black: '#0f0f23',
        red: '#ef4444',
        green: '#22c55e',
        yellow: '#eab308',
        blue: '#3b82f6',
        magenta: '#a855f7',
        cyan: '#06b6d4',
        white: '#e2e8f0'
      },
      fontFamily: '"Cascadia Code", "Consolas", monospace',
      fontSize: 13,
      lineHeight: 1.3,
      cursorBlink: true,
      cursorStyle: 'bar',
      scrollback: 5000
    })

    const fitAddon = new FitAddon()
    const webLinksAddon = new WebLinksAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(webLinksAddon)

    term.open(containerRef.current)
    fitAddon.fit()

    termRef.current = term
    fitRef.current = fitAddon

    // Forward keyboard input to PTY
    term.onData((data) => {
      window.api.terminalInput(data)
    })

    // Receive PTY output
    const unsubData = window.api.onTerminalData((data) => {
      term.write(data)
    })

    const unsubExit = window.api.onTerminalExit((_code) => {
      term.writeln('\r\n\x1b[90m[Process exited]\x1b[0m')
      setStarted(false)
    })

    // Resize handling
    const resizeObserver = new ResizeObserver(() => {
      fitAddon.fit()
      window.api.terminalResize(term.cols, term.rows)
    })
    resizeObserver.observe(containerRef.current)

    return () => {
      unsubData()
      unsubExit()
      resizeObserver.disconnect()
      term.dispose()
      termRef.current = null
    }
  }, [])

  const spawn = async (cmd?: string): Promise<void> => {
    await window.api.terminalSpawn(cmd ? { cmd } : undefined)
    setStarted(true)
    termRef.current?.focus()
    if (fitRef.current) {
      fitRef.current.fit()
      if (termRef.current) {
        window.api.terminalResize(termRef.current.cols, termRef.current.rows)
      }
    }
  }

  const launchClaude = async (): Promise<void> => {
    await window.api.terminalSpawn({ cmd: 'claude' })
    setStarted(true)
    setClaudeMode(true)
    termRef.current?.focus()
    if (fitRef.current) {
      fitRef.current.fit()
      if (termRef.current) {
        window.api.terminalResize(termRef.current.cols, termRef.current.rows)
      }
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#0f0f23'
      }}
    >
      {/* Toolbar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '4px 12px',
          borderBottom: '1px solid #1e293b',
          backgroundColor: '#0a0a1a',
          flexShrink: 0
        }}
      >
        <span style={{ fontSize: 12, color: '#94a3b8', marginRight: 'auto' }}>Terminal</span>

        {!started && (
          <>
            <button
              onClick={() => spawn()}
              style={{
                padding: '3px 10px',
                fontSize: 11,
                backgroundColor: '#1e293b',
                color: '#e2e8f0',
                border: '1px solid #334155',
                borderRadius: 4,
                cursor: 'pointer'
              }}
            >
              Shell
            </button>
            <button
              onClick={launchClaude}
              style={{
                padding: '3px 10px',
                fontSize: 11,
                backgroundColor: '#7c3aed',
                color: '#fff',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              Claude Code
            </button>
          </>
        )}

        {started && (
          <button
            onClick={async () => {
              await window.api.terminalKill()
              setStarted(false)
              setClaudeMode(false)
            }}
            style={{
              padding: '3px 10px',
              fontSize: 11,
              backgroundColor: '#dc2626',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer'
            }}
          >
            Kill
          </button>
        )}
      </div>

      {/* Terminal area */}
      <div ref={containerRef} style={{ flex: 1, padding: '4px 0 0 4px' }} />
    </div>
  )
}
