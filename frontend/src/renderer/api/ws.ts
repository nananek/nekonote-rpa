import type { ExecutionEvent } from '../types/api'
import type { Flow, FlowBlock } from '../types/flow'

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
        handleName = 'out'
      }

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

declare global {
  interface Window {
    api?: {
      openFile: () => Promise<{ filePath: string; content: string } | null>
      saveFile: (content: string, currentPath?: string) => Promise<string | null>
      sendToBackend: (msg: unknown) => void
      onBackendEvent: (callback: (event: unknown) => void) => () => void
    }
  }
}

class BackendClient {
  private handlers: Set<EventHandler> = new Set()
  private unsub: (() => void) | null = null

  connect(): void {
    if (window.api?.onBackendEvent) {
      // Electron IPC mode (stdio) — no TCP
      this.unsub = window.api.onBackendEvent((event) => {
        const data = event as ExecutionEvent
        this.handlers.forEach((h) => h(data))
      })
      console.log('Backend connected via IPC (stdio)')
    } else {
      console.warn('No backend IPC available (running in browser?)')
    }
  }

  disconnect(): void {
    this.unsub?.()
    this.unsub = null
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
    if (window.api?.sendToBackend) {
      window.api.sendToBackend(msg)
    } else {
      console.warn('Backend not connected')
    }
  }
}

export const wsClient = new BackendClient()
