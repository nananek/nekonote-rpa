import { useFlowStore } from '../../stores/flowStore'
import { BlockList } from './BlockList'
import { t } from '../../i18n'

export function BlockEditor(): JSX.Element {
  const flow = useFlowStore((s) => s.flow)

  return (
    <div
      style={{
        flex: 1,
        overflow: 'auto',
        padding: '16px 24px',
        backgroundColor: '#0f0f23'
      }}
      onClick={() => useFlowStore.getState().selectBlock(null)}
    >
      <div style={{ maxWidth: 700, margin: '0 auto' }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 12 }}>
          {flow.name || t('app.title')}
        </div>
        <BlockList blocks={flow.blocks} depth={0} />
      </div>
    </div>
  )
}
