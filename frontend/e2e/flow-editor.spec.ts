import { test, expect } from '@playwright/test'

test.describe('Flow Editor', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForSelector('.react-flow', { timeout: 10000 })
    await page.waitForSelector('.react-flow__node', { state: 'attached', timeout: 10000 })
    await page.waitForTimeout(500)
  })

  test('renders initial flow with 2 nodes', async ({ page }) => {
    const nodes = page.locator('.react-flow__node')
    await expect(nodes).toHaveCount(2)
  })

  test('canvas container has proper dimensions', async ({ page }) => {
    const size = await page.evaluate(() => {
      const el = document.querySelector('.react-flow') as HTMLElement
      return { w: el.offsetWidth, h: el.offsetHeight }
    })
    expect(size.w).toBeGreaterThan(100)
    expect(size.h).toBeGreaterThan(100)
  })

  test('renders node palette with all categories', async ({ page }) => {
    await expect(page.getByText('ノード', { exact: true })).toBeVisible()
    // Use exact match for category headers
    await expect(page.locator('text=ブラウザ').first()).toBeVisible()
    await expect(page.locator('text=デスクトップ').first()).toBeVisible()
    await expect(page.locator('text=制御').first()).toBeVisible()
    await expect(page.locator('text=データ').first()).toBeVisible()
  })

  test('palette has draggable items', async ({ page }) => {
    const draggables = page.locator('[draggable="true"]')
    const count = await draggables.count()
    // We have 23 node types defined
    expect(count).toBeGreaterThanOrEqual(20)
  })

  test('drag and drop node from palette to canvas', async ({ page }) => {
    const nodesBefore = await page.locator('.react-flow__node').count()

    const dropTarget = page.locator('.react-flow').first()
    const dropBox = await dropTarget.boundingBox()
    expect(dropBox).not.toBeNull()

    const dropX = dropBox!.x + dropBox!.width / 2
    const dropY = dropBox!.y + dropBox!.height / 2

    // Find the draggable item index for ログ出力
    const logIndex = await page.locator('[draggable="true"]').evaluateAll((els) =>
      els.findIndex((el) => el.textContent?.includes('ログ出力'))
    )
    expect(logIndex).toBeGreaterThanOrEqual(0)

    // Dispatch HTML5 Drag events
    await page.evaluate(
      ({ itemIndex, dropX, dropY }) => {
        const source = document.querySelectorAll('[draggable="true"]')[itemIndex] as HTMLElement
        const target = document.querySelector('.react-flow') as HTMLElement

        const dt = new DataTransfer()
        dt.setData('application/nekonote-node-type', 'data.log')

        source.dispatchEvent(new DragEvent('dragstart', { bubbles: true, cancelable: true, dataTransfer: dt }))
        target.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer: dt, clientX: dropX, clientY: dropY }))
        target.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: dt, clientX: dropX, clientY: dropY }))
      },
      { itemIndex: logIndex, dropX, dropY }
    )

    await page.waitForTimeout(500)
    const nodesAfter = await page.locator('.react-flow__node').count()
    expect(nodesAfter).toBe(nodesBefore + 1)
  })

  test('drag and drop different node types', async ({ page }) => {
    const nodesBefore = await page.locator('.react-flow__node').count()

    const dropBox = await page.locator('.react-flow').first().boundingBox()
    expect(dropBox).not.toBeNull()

    // Drop a "条件分岐" (control.if) node
    const ifIndex = await page.locator('[draggable="true"]').evaluateAll((els) =>
      els.findIndex((el) => el.textContent?.includes('条件分岐'))
    )
    expect(ifIndex).toBeGreaterThanOrEqual(0)

    await page.evaluate(
      ({ itemIndex, dropX, dropY }) => {
        const source = document.querySelectorAll('[draggable="true"]')[itemIndex] as HTMLElement
        const target = document.querySelector('.react-flow') as HTMLElement

        const dt = new DataTransfer()
        dt.setData('application/nekonote-node-type', 'control.if')

        source.dispatchEvent(new DragEvent('dragstart', { bubbles: true, cancelable: true, dataTransfer: dt }))
        target.dispatchEvent(new DragEvent('dragover', { bubbles: true, cancelable: true, dataTransfer: dt, clientX: dropX, clientY: dropY }))
        target.dispatchEvent(new DragEvent('drop', { bubbles: true, cancelable: true, dataTransfer: dt, clientX: dropX, clientY: dropY }))
      },
      { itemIndex: ifIndex, dropX: dropBox!.x + 400, dropY: dropBox!.y + 200 }
    )

    await page.waitForTimeout(500)
    expect(await page.locator('.react-flow__node').count()).toBe(nodesBefore + 1)
  })

  test('toolbar buttons visible in Japanese', async ({ page }) => {
    await expect(page.getByRole('button', { name: '新規' })).toBeVisible()
    await expect(page.getByRole('button', { name: /保存/ })).toBeVisible()
    await expect(page.getByRole('button', { name: '実行' })).toBeVisible()
    await expect(page.getByRole('button', { name: '元に戻す' })).toBeVisible()
  })

  test('view mode switching: Visual -> Code -> Visual', async ({ page }) => {
    // Switch to Code
    await page.getByRole('button', { name: 'Code' }).click()
    await expect(page.getByText('コードビュー')).toBeVisible({ timeout: 5000 })
    // Canvas should be gone
    await expect(page.locator('.react-flow')).toHaveCount(0)

    // Switch back to Visual
    await page.getByRole('button', { name: 'Visual' }).click()
    await expect(page.locator('.react-flow')).toBeVisible()
  })

  test('view mode switching: Split shows both', async ({ page }) => {
    await page.getByRole('button', { name: 'Split' }).click()
    await expect(page.locator('.react-flow')).toBeVisible({ timeout: 5000 })
    await expect(page.getByText('コードビュー')).toBeVisible()
  })

  test('execution panel has log and variable tabs', async ({ page }) => {
    await expect(page.getByRole('button', { name: 'ログ' })).toBeVisible()
    await expect(page.getByRole('button', { name: '変数' })).toBeVisible()
  })

  test('run button executes flow and shows logs', async ({ page }) => {
    // This test needs the backend running on port 18080
    // and WebSocket connection to work
    await page.getByRole('button', { name: '実行' }).click()

    // Wait for execution to complete
    await expect(page.getByText('Execution success').first()).toBeVisible({ timeout: 10000 })
  })
})
