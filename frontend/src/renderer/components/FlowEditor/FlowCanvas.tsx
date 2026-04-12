import { useCallback, useMemo, useRef, type DragEvent as ReactDragEvent } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type OnSelectionChangeFunc,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  useReactFlow
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { useFlowStore } from '../../stores/flowStore'
import { useExecutionStore } from '../../stores/executionStore'
import { CustomNode } from './CustomNode'
import { getNodeDef } from '../../types/nodeDefinitions'

const nodeTypes = { custom: CustomNode }

interface FlowCanvasProps {
  onSelectionChange: (nodeId: string | null) => void
}

let nodeIdCounter = 100

export function FlowCanvas({ onSelectionChange }: FlowCanvasProps): JSX.Element {
  const flow = useFlowStore((s) => s.flow)
  const updateFlow = useFlowStore((s) => s.updateFlow)
  const activeNodeId = useExecutionStore((s) => s.activeNodeId)
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()

  const nodes: Node[] = useMemo(
    () =>
      flow.nodes.map((n) => ({
        id: n.id,
        type: 'custom',
        position: n.position,
        data: {
          nodeType: n.type,
          label: n.label,
          params: n.params,
          isActive: n.id === activeNodeId,
          hasError: false
        }
      })),
    [flow.nodes, activeNodeId]
  )

  const edges: Edge[] = useMemo(
    () =>
      flow.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
        animated: activeNodeId === e.source,
        style: { stroke: '#64748b', strokeWidth: 2 }
      })),
    [flow.edges, activeNodeId]
  )

  // Use getState() to always read the latest flow, avoiding stale closure issues
  const onNodesChange: OnNodesChange = useCallback(
    (changes) => {
      const latest = useFlowStore.getState().flow
      const currentNodes = latest.nodes.map((n) => ({
        id: n.id,
        type: 'custom' as const,
        position: n.position,
        data: {}
      }))
      const updatedNodes = applyNodeChanges(changes, currentNodes)
      const newFlowNodes = updatedNodes.map((n) => {
        const existing = latest.nodes.find((fn) => fn.id === n.id)
        return existing
          ? { ...existing, position: n.position }
          : {
              id: n.id,
              type: 'data.log',
              label: '',
              position: n.position,
              params: {}
            }
      })
      updateFlow({ ...latest, nodes: newFlowNodes })
    },
    [updateFlow]
  )

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => {
      const latest = useFlowStore.getState().flow
      const currentEdges = latest.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle
      }))
      const updatedEdges = applyEdgeChanges(changes, currentEdges)
      const newFlowEdges = updatedEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle ?? 'out',
        targetHandle: e.targetHandle ?? 'in'
      }))
      updateFlow({ ...latest, edges: newFlowEdges })
    },
    [updateFlow]
  )

  const onConnect: OnConnect = useCallback(
    (connection) => {
      const latest = useFlowStore.getState().flow
      const currentEdges = latest.edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle
      }))
      const newEdges = addEdge(
        { ...connection, style: { stroke: '#64748b', strokeWidth: 2 } },
        currentEdges
      )
      const newFlowEdges = newEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle ?? 'out',
        targetHandle: e.targetHandle ?? 'in'
      }))
      updateFlow({ ...latest, edges: newFlowEdges })
    },
    [updateFlow]
  )

  const handleSelectionChange: OnSelectionChangeFunc = useCallback(
    ({ nodes: selectedNodes }) => {
      onSelectionChange(selectedNodes.length === 1 ? selectedNodes[0].id : null)
    },
    [onSelectionChange]
  )

  const onDragOver = useCallback((e: ReactDragEvent | DragEvent) => {
    e.preventDefault()
    if ('dataTransfer' in e && e.dataTransfer) {
      e.dataTransfer.dropEffect = 'move'
    }
  }, [])

  const onDrop = useCallback(
    (e: ReactDragEvent | DragEvent) => {
      e.preventDefault()
      if (!('dataTransfer' in e) || !e.dataTransfer) return

      const nodeType = e.dataTransfer.getData('application/nekonote-node-type')
      if (!nodeType) return

      const latest = useFlowStore.getState().flow
      const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
      const def = getNodeDef(nodeType)
      const newId = `node_${++nodeIdCounter}_${Date.now()}`

      const defaultParams: Record<string, unknown> = {}
      if (def) {
        for (const p of def.params) {
          if (p.default !== undefined) defaultParams[p.name] = p.default
        }
      }

      const newNode = {
        id: newId,
        type: nodeType,
        label: def?.label ?? nodeType,
        position,
        params: defaultParams
      }

      updateFlow({ ...latest, nodes: [...latest.nodes, newNode] })
    },
    [updateFlow, screenToFlowPosition]
  )

  return (
    <div
      ref={reactFlowWrapper}
      style={{ flex: 1, position: 'relative' }}
      onDragOver={onDragOver as React.DragEventHandler}
      onDrop={onDrop as React.DragEventHandler}
    >
      <div style={{ position: 'absolute', inset: 0 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onSelectionChange={handleSelectionChange}
          onDragOver={onDragOver as React.DragEventHandler}
          onDrop={onDrop as React.DragEventHandler}
          fitView
          deleteKeyCode={['Backspace', 'Delete']}
          style={{ width: '100%', height: '100%', backgroundColor: '#0f0f23' }}
        >
          <Background color="#334155" gap={20} />
          <Controls
            style={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
          />
        </ReactFlow>
      </div>
    </div>
  )
}
