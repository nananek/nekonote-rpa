import { create } from 'zustand'
import type { ExecutionEvent } from '../types/api'

interface LogEntry {
  timestamp: string
  level: string
  message: string
  nodeId?: string
}

interface ExecutionState {
  isRunning: boolean
  executionId: string | null
  activeNodeId: string | null
  logs: LogEntry[]
  variables: Record<string, unknown>
  error: string | null

  handleEvent: (event: ExecutionEvent) => void
  clearLogs: () => void
  reset: () => void
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  isRunning: false,
  executionId: null,
  activeNodeId: null,
  logs: [],
  variables: {},
  error: null,

  handleEvent: (event: ExecutionEvent): void => {
    const now = new Date().toLocaleTimeString()

    switch (event.type) {
      case 'execution.started':
        set({
          isRunning: true,
          executionId: event.execution_id ?? null,
          activeNodeId: null,
          error: null,
          variables: {}
        })
        set((s) => ({
          logs: [...s.logs, { timestamp: now, level: 'info', message: 'Execution started' }]
        }))
        break

      case 'node.enter':
        set({ activeNodeId: event.node_id ?? null })
        set((s) => ({
          logs: [
            ...s.logs,
            {
              timestamp: now,
              level: 'info',
              message: `▶ ${event.node_id}`,
              nodeId: event.node_id
            }
          ]
        }))
        break

      case 'node.exit':
        set((s) => ({
          activeNodeId: null,
          logs: [
            ...s.logs,
            {
              timestamp: now,
              level: 'info',
              message: `✓ ${event.node_id} (${event.duration_ms}ms)`,
              nodeId: event.node_id
            }
          ]
        }))
        break

      case 'node.error':
        set((s) => ({
          activeNodeId: null,
          logs: [
            ...s.logs,
            {
              timestamp: now,
              level: 'error',
              message: `✗ ${event.node_id}: ${event.error}`,
              nodeId: event.node_id
            }
          ]
        }))
        break

      case 'log':
        set((s) => ({
          logs: [
            ...s.logs,
            { timestamp: now, level: event.level ?? 'info', message: event.message ?? '' }
          ]
        }))
        break

      case 'variable.changed':
        if (event.name) {
          set((s) => ({
            variables: { ...s.variables, [event.name!]: event.value }
          }))
        }
        break

      case 'execution.completed':
        set({ isRunning: false, activeNodeId: null })
        set((s) => ({
          logs: [
            ...s.logs,
            { timestamp: now, level: 'info', message: `Execution ${event.status ?? 'completed'}` }
          ]
        }))
        break

      case 'execution.failed':
        set({ isRunning: false, activeNodeId: null, error: event.error ?? null })
        set((s) => ({
          logs: [
            ...s.logs,
            { timestamp: now, level: 'error', message: `Execution failed: ${event.error}` }
          ]
        }))
        break
    }
  },

  clearLogs: () => set({ logs: [] }),
  reset: () =>
    set({
      isRunning: false,
      executionId: null,
      activeNodeId: null,
      logs: [],
      variables: {},
      error: null
    })
}))
