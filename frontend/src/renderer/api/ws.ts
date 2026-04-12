import type { ExecutionEvent } from '../types/api'
import type { Flow, FlowBlock } from '../types/flow'

const WS_URL = 'ws://127.0.0.1:18080/ws/execution'

type EventHandler = (event: ExecutionEvent) => void

/** Convert block tree to flat nodes/edges for the backend executor */
function blocksToNodesEdges(blocks: FlowBlock[]): {
  nodes: Array<{ id: string; type: string; label: string; params: Record<string, unknown>; position: { x: number; y: number } }>
  edges: Array<{ id: string; source: string; target: string; sourceHandle: string; targetHandle: string }>
} {
  const nodes: Array<{ id: string; type: string; label: string; params: Record<string, unknown>; position: { x: number; y: number } }> = []
  const edges: Array<{ id: string; source: string; target: string; sourceHandle: string; targetHandle: string }> = []
  let edgeId = 0

  function walk(blockList: FlowBlock[], prevId: string | null, handleName: string): string | null {
    let lastId = prevId
    for (const block of blockList) {
      nodes.push({
        id: block.id,
        type: block.type,
        label: block.label,
        params: block.params,
        position: { x: 0, y: 0 }
      })

      if (lastId) {
        edges.push({
          id: `e_${edgeId++}`,
          source: lastId,
          target: block.id,
          sourceHandle: handleName,
          targetHandle: 'in'
        })
        handleName = 'out' // after first edge, use 'out'
      }

      // Handle children for control blocks
      if (block.type === 'control.if') {
        if (block.children?.length) walk(block.children, block.id, 'true')
        if (block.elseChildren?.length) walk(block.elseChildren, block.id, 'false')
      } else if (block.type === 'control.tryCatch') {
        if (block.children?.length) walk(block.children, block.id, 'try')
        if (block.elseChildren?.length) walk(block.elseChildren, block.id, 'catch')
      } else if (block.type === 'control.loop' || block.type === 'control.forEach') {
        if (block.children?.length) walk(block.children, block.id, 'loop')
      }

      lastId = block.id
    }
    return lastId
  }

  walk(blocks, null, 'out')
  return { nodes, edges }
}

class WebSocketClient {
  private ws: WebSocket | null = null
  private handlers: Set<EventHandler> = new Set()
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return

    this.ws = new WebSocket(WS_URL)

    this.ws.onopen = (): void => {
      console.log('WebSocket connected')
    }

    this.ws.onmessage = (event): void => {
      try {
        const data = JSON.parse(event.data) as ExecutionEvent
        this.handlers.forEach((h) => h(data))
      } catch (e) {
        console.error('Failed to parse WS message:', e)
      }
    }

    this.ws.onclose = (): void => {
      console.log('WebSocket disconnected, reconnecting in 2s...')
      this.reconnectTimer = setTimeout(() => this.connect(), 2000)
    }

    this.ws.onerror = (err): void => {
      console.error('WebSocket error:', err)
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.ws?.close()
    this.ws = null
  }

  subscribe(handler: EventHandler): () => void {
    this.handlers.add(handler)
    return () => this.handlers.delete(handler)
  }

  executeFlow(flow: Flow): void {
    const { nodes, edges } = blocksToNodesEdges(flow.blocks)
    const backendFlow = {
      version: flow.version,
      id: flow.id,
      name: flow.name,
      description: flow.description,
      variables: flow.variables,
      nodes,
      edges
    }
    this.send({ type: 'execute', flow: backendFlow })
  }

  stopExecution(executionId: string): void {
    this.send({ type: 'stop', execution_id: executionId })
  }

  openPickerBrowser(url?: string): void {
    this.send({ type: 'picker.openBrowser', url: url || 'about:blank' })
  }

  startPicker(): void {
    this.send({ type: 'picker.start' })
  }

  private send(msg: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg))
    } else {
      console.warn('WebSocket not connected')
    }
  }
}

export const wsClient = new WebSocketClient()
