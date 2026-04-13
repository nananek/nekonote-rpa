import { useCallback, useEffect, useRef, useState } from 'react'
import { BlockEditor } from './components/BlockEditor/BlockEditor'
import { NodePalette } from './components/FlowEditor/NodePalette'
import { PropertiesPanel } from './components/PropertiesPanel/PropertiesPanel'
import { CodePanel } from './components/CodeEditor/CodePanel'
import { ExecutionPanel } from './components/ExecutionPanel/ExecutionPanel'
import { TerminalPanel } from './components/Terminal/TerminalPanel'
import { Toolbar } from './components/Toolbar/Toolbar'
import { wsClient } from './api/ws'
import { useExecutionStore } from './stores/executionStore'
import { useFlowStore } from './stores/flowStore'

export type ViewMode = 'visual' | 'code' | 'split'
type BottomTab = 'execution' | 'terminal'

export default function App(): JSX.Element {
  const handleEvent = useExecutionStore((s) => s.handleEvent)
  const selectedBlockId = useFlowStore((s) => s.selectedBlockId)
  const [viewMode, setViewMode] = useState<ViewMode>('visual')
  const [bottomTab, setBottomTab] = useState<BottomTab>('terminal')
  const [bottomHeight, setBottomHeight] = useState(320)
  const [isPopped, setIsPopped] = useState(false)
  const popupRef = useRef<Window | null>(null)
  const [popupContainer, setPopupContainer] = useState<HTMLDivElement | null>(null)
  const isDragging = useRef(false)

  const flow = useFlowStore((s) => s.flow)
  const setFlow = useFlowStore((s) => s.setFlow)

  useEffect(() => {
    wsClient.connect()
    const unsub = wsClient.subscribe(handleEvent)
    return () => {
      unsub()
      wsClient.disconnect()
    }
  }, [handleEvent])

  // Sync flow to shared file for MCP access
  const externalUpdateRef = useRef(false)
  useEffect(() => {
    if (externalUpdateRef.current) {
      externalUpdateRef.current = false
      return
    }
    try {
      ;(window as any).api.flowSyncToFile(JSON.stringify(flow, null, 2))
    } catch { /* ignore */ }
  }, [flow])

  // Watch for external flow changes (from MCP/Claude Code)
  useEffect(() => {
    ;(window as any).api.flowStartWatching()
    const unsub = (window as any).api.onFlowExternalUpdate((json: string) => {
      try {
        const updated = JSON.parse(json)
        // Only update if actually different
        if (JSON.stringify(updated) !== JSON.stringify(flow)) {
          externalUpdateRef.current = true
          setFlow(updated)
        }
      } catch { /* ignore bad json */ }
    })
    return () => {
      unsub()
      ;(window as any).api.flowStopWatching()
    }
  }, []) // intentionally empty deps - run once

  // Drag resize handler
  const onDragStart = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDragging.current = true
    const startY = e.clientY
    const startH = bottomHeight

    const onMove = (ev: MouseEvent): void => {
      if (!isDragging.current) return
      const delta = startY - ev.clientY
      const newH = Math.max(120, Math.min(window.innerHeight - 200, startH + delta))
      setBottomHeight(newH)
    }
    const onUp = (): void => {
      isDragging.current = false
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [bottomHeight])

  // Pop out / pop in
  const popOut = useCallback(() => {
    if (popupRef.current && !popupRef.current.closed) {
      popupRef.current.focus()
      return
    }
    const w = 900
    const h = 600
    const left = window.screenX + 50
    const top = window.screenY + 50
    const popup = window.open('', 'nekonote-terminal', `width=${w},height=${h},left=${left},top=${top}`)
    if (!popup) return

    popup.document.title = 'Nekonote Terminal'
    popup.document.body.style.margin = '0'
    popup.document.body.style.backgroundColor = '#0f0f23'
    popup.document.body.style.overflow = 'hidden'

    // Copy xterm CSS
    const xtermCss = Array.from(document.querySelectorAll('style, link[rel="stylesheet"]'))
    xtermCss.forEach((el) => {
      popup.document.head.appendChild(el.cloneNode(true))
    })

    const container = popup.document.createElement('div')
    container.style.width = '100vw'
    container.style.height = '100vh'
    popup.document.body.appendChild(container)

    popupRef.current = popup
    setIsPopped(true)
    setPopupContainer(container)

    popup.addEventListener('beforeunload', () => {
      popupRef.current = null
      setIsPopped(false)
      setPopupContainer(null)
    })
  }, [])

  const popIn = useCallback(() => {
    if (popupRef.current && !popupRef.current.closed) {
      popupRef.current.close()
    }
    popupRef.current = null
    setIsPopped(false)
    setPopupContainer(null)
  }, [])

  const tabStyle = (tab: BottomTab): React.CSSProperties => ({
    padding: '4px 16px',
    fontSize: 12,
    cursor: 'pointer',
    color: bottomTab === tab ? '#e2e8f0' : '#64748b',
    backgroundColor: bottomTab === tab ? '#0f0f23' : 'transparent',
    border: 'none',
    borderBottom: bottomTab === tab ? '2px solid #7c3aed' : '2px solid transparent',
    fontFamily: 'inherit',
  })

  const iconBtn: React.CSSProperties = {
    padding: '2px 8px',
    fontSize: 13,
    cursor: 'pointer',
    color: '#94a3b8',
    backgroundColor: 'transparent',
    border: 'none',
    fontFamily: 'inherit',
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        backgroundColor: '#0f0f23',
        color: '#e2e8f0'
      }}
    >
      <Toolbar viewMode={viewMode} onViewModeChange={setViewMode} />
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>
        {(viewMode === 'visual' || viewMode === 'split') && <NodePalette />}

        {viewMode === 'visual' && (
          <>
            <BlockEditor />
            <PropertiesPanel selectedNodeId={selectedBlockId} />
          </>
        )}

        {viewMode === 'code' && <CodePanel />}

        {viewMode === 'split' && (
          <>
            <BlockEditor />
            <div style={{ width: 450, borderLeft: '1px solid #334155' }}>
              <CodePanel />
            </div>
          </>
        )}
      </div>

      {/* Bottom panel — hidden when popped out */}
      {!isPopped && (
        <div style={{ height: bottomHeight, display: 'flex', flexDirection: 'column', flexShrink: 0 }}>
          {/* Drag handle */}
          <div
            onMouseDown={onDragStart}
            style={{
              height: 4,
              cursor: 'row-resize',
              backgroundColor: '#1e293b',
              flexShrink: 0,
            }}
            title="Drag to resize"
          />

          {/* Tab bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: '#0a0a1a',
            borderBottom: '1px solid #1e293b',
            flexShrink: 0,
          }}>
            <button style={tabStyle('execution')} onClick={() => setBottomTab('execution')}>
              Execution
            </button>
            <button style={tabStyle('terminal')} onClick={() => setBottomTab('terminal')}>
              Terminal
            </button>
            <div style={{ flex: 1 }} />
            {bottomTab === 'terminal' && (
              <button style={iconBtn} onClick={popOut} title="Pop out terminal">
                {'[ ]'}
              </button>
            )}
          </div>

          <div style={{ flex: 1, overflow: 'hidden' }}>
            {bottomTab === 'execution' && <ExecutionPanel />}
            {bottomTab === 'terminal' && <TerminalPanel />}
          </div>
        </div>
      )}

      {/* Collapsed bar when popped out */}
      {isPopped && (
        <div style={{
          height: 30,
          display: 'flex',
          alignItems: 'center',
          backgroundColor: '#0a0a1a',
          borderTop: '1px solid #1e293b',
          padding: '0 12px',
          gap: 8,
          flexShrink: 0,
        }}>
          <span style={{ fontSize: 12, color: '#64748b' }}>Terminal (external window)</span>
          <button
            style={{ ...iconBtn, color: '#7c3aed' }}
            onClick={popIn}
          >
            Pop in
          </button>
        </div>
      )}
    </div>
  )
}
