import { useEffect, useRef, useState } from 'react'
import { useExecutionStore } from '../../stores/executionStore'
import { t } from '../../i18n'

type Tab = 'logs' | 'variables'

function LogsView(): JSX.Element {
  const logs = useExecutionStore((s) => s.logs)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '8px 12px', fontFamily: 'monospace', fontSize: '12px' }}>
      {logs.map((log, i) => (
        <div
          key={i}
          style={{
            color: log.level === 'error' ? '#ef4444' : log.level === 'warning' ? '#f59e0b' : '#e2e8f0',
            marginBottom: '2px'
          }}
        >
          <span style={{ color: '#64748b' }}>{log.timestamp}</span> {log.message}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

function VariablesView(): JSX.Element {
  const variables = useExecutionStore((s) => s.variables)
  const entries = Object.entries(variables).filter(([k]) => !k.startsWith('_'))

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '8px 12px', fontSize: '12px' }}>
      {entries.length === 0 ? (
        <div style={{ color: '#64748b', fontStyle: 'italic' }}>{t('execution.noVariables')}</div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155' }}>
              <th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8', fontWeight: 600 }}>{t('variables.name')}</th>
              <th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8', fontWeight: 600 }}>{t('variables.value')}</th>
              <th style={{ textAlign: 'left', padding: '4px 8px', color: '#94a3b8', fontWeight: 600 }}>{t('variables.type')}</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, value]) => (
              <tr key={name} style={{ borderBottom: '1px solid #1e293b' }}>
                <td style={{ padding: '3px 8px', color: '#60a5fa', fontFamily: 'monospace' }}>{name}</td>
                <td style={{ padding: '3px 8px', color: '#e2e8f0', fontFamily: 'monospace', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {formatValue(value)}
                </td>
                <td style={{ padding: '3px 8px', color: '#64748b' }}>{typeof value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'string') return `"${value}"`
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function ExecutionPanel(): JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('logs')
  const isRunning = useExecutionStore((s) => s.isRunning)
  const clearLogs = useExecutionStore((s) => s.clearLogs)

  const tabStyle = (tab: Tab) => ({
    padding: '4px 12px',
    cursor: 'pointer' as const,
    fontSize: '11px',
    color: activeTab === tab ? '#e2e8f0' : '#64748b',
    borderBottom: activeTab === tab ? '2px solid #3b82f6' : '2px solid transparent',
    background: 'none',
    border: 'none',
    borderBottomWidth: 2,
    borderBottomStyle: 'solid' as const,
    borderBottomColor: activeTab === tab ? '#3b82f6' : 'transparent'
  })

  return (
    <div
      style={{
        height: '220px',
        borderTop: '1px solid #333',
        backgroundColor: '#1a1a2e',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 12px',
          backgroundColor: '#16213e',
          borderBottom: '1px solid #333'
        }}
      >
        <button onClick={() => setActiveTab('logs')} style={tabStyle('logs')}>
          {t('execution.logs')}
        </button>
        <button onClick={() => setActiveTab('variables')} style={tabStyle('variables')}>
          {t('execution.variables')}
        </button>

        <div style={{ flex: 1 }} />

        {isRunning && <span style={{ color: '#22c55e', fontSize: '11px' }}>● {t('execution.running')}</span>}

        <button
          onClick={clearLogs}
          style={{
            background: 'none',
            border: '1px solid #555',
            color: '#aaa',
            padding: '2px 8px',
            cursor: 'pointer',
            borderRadius: '3px',
            fontSize: '10px'
          }}
        >
          {t('execution.clear')}
        </button>
      </div>

      {activeTab === 'logs' ? <LogsView /> : <VariablesView />}
    </div>
  )
}
