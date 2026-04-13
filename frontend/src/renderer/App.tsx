import { useEffect, useState } from 'react'
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

  useEffect(() => {
    wsClient.connect()
    const unsub = wsClient.subscribe(handleEvent)
    return () => {
      unsub()
      wsClient.disconnect()
    }
  }, [handleEvent])

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

      {/* Bottom panel with tabs */}
      <div style={{ height: 280, display: 'flex', flexDirection: 'column', borderTop: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', backgroundColor: '#0a0a1a', borderBottom: '1px solid #1e293b' }}>
          <button style={tabStyle('execution')} onClick={() => setBottomTab('execution')}>
            Execution
          </button>
          <button style={tabStyle('terminal')} onClick={() => setBottomTab('terminal')}>
            Terminal
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {bottomTab === 'execution' && <ExecutionPanel />}
          {bottomTab === 'terminal' && <TerminalPanel />}
        </div>
      </div>
    </div>
  )
}
