import { useMemo } from 'react'
import Editor from '@monaco-editor/react'
import { useFlowStore } from '../../stores/flowStore'
import { generatePython } from '../../codegen/generatePython'
import { t } from '../../i18n'

export function CodePanel(): JSX.Element {
  const flow = useFlowStore((s) => s.flow)

  const code = useMemo(() => generatePython(flow), [flow])

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#1e1e1e'
      }}
    >
      <div
        style={{
          padding: '6px 12px',
          fontSize: 11,
          color: '#94a3b8',
          backgroundColor: '#16213e',
          borderBottom: '1px solid #334155',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <span style={{ fontWeight: 600, color: '#e2e8f0' }}>{t('codeview.title')}</span>
        <span>{t('codeview.readonly')}</span>
      </div>
      <div style={{ flex: 1 }}>
        <Editor
          defaultLanguage="python"
          value={code}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            padding: { top: 8 }
          }}
        />
      </div>
    </div>
  )
}
