export interface Variable {
  name: string
  type: string
  default: unknown
}

export interface FlowBlock {
  id: string
  type: string
  label: string
  params: Record<string, unknown>
  /** Nested children for control blocks (if/loop/tryCatch) */
  children?: FlowBlock[]
  /** Second branch for if-else (false branch) or catch */
  elseChildren?: FlowBlock[]
}

export interface Flow {
  version: string
  id: string
  name: string
  description: string
  variables: Variable[]
  blocks: FlowBlock[]
}
