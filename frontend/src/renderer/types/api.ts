export interface ExecutionEvent {
  type:
    | 'execution.started'
    | 'execution.completed'
    | 'execution.failed'
    | 'node.enter'
    | 'node.exit'
    | 'node.error'
    | 'log'
    | 'variable.changed'
    | 'pong'
    | 'error'
    | 'picker.browserReady'
    | 'picker.started'
    | 'picker.result'
    | 'picker.error'
  execution_id?: string
  node_id?: string
  status?: string
  error?: string
  message?: string
  level?: string
  name?: string
  value?: unknown
  duration_ms?: number
  // Picker fields
  selector?: string
  tagName?: string
  text?: string
  cancelled?: boolean
  url?: string
  title?: string
}
