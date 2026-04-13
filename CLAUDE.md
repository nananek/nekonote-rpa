# nekonote

Windows RPA toolkit. Electron (frontend) + Python (backend).

## Important: MCP tools for editing scenarios

When the user asks you to create or modify an RPA scenario, **always use the MCP tools first** to edit the flow that is currently open in the nekonote visual editor. Do NOT just write a .py file — edit the visual flow so the user can see the changes in the UI.

### Workflow for scenario editing
1. `get_current_flow()` — read the current flow open in the editor
2. `add_block(block_type, label, params)` — add blocks to build the scenario
3. `update_block_params(block_id, params)` — adjust existing block parameters
4. `remove_block(block_id)` — remove blocks that aren't needed
5. `update_flow(flow_json)` — replace the entire flow if doing large restructuring

The editor updates in real-time as you call these tools. The user will see blocks appear/change instantly.

### IMPORTANT: hotkey params format
The `desktop.hotkey` block uses **comma-separated** key names in the `keys` parameter.
Do NOT use `+` as separator — `+` itself is a valid key name.

Examples:
- `{"keys": "ctrl,a"}` — Select all
- `{"keys": "ctrl,c"}` — Copy
- `{"keys": "win,r"}` — Open Run dialog
- `{"keys": "shift,;"}` — Type "+" on Japanese keyboard
- `{"keys": "enter"}` — Press Enter
- `{"keys": "alt,f4"}` — Close window

### Available block types
- `browser.open`, `browser.navigate`, `browser.click`, `browser.type`, `browser.getText`, `browser.wait`, `browser.screenshot`, `browser.close`
- `desktop.click`, `desktop.type`, `desktop.hotkey`, `desktop.screenshot`, `desktop.findImage`
- `control.if`, `control.loop`, `control.forEach`, `control.tryCatch`, `control.wait`
- `data.setVariable`, `data.log`, `data.comment`

### Example: user says "Googleを開いてスクリーンショットを撮って"
```
add_block("browser.open", "Open Browser", '{}')
add_block("browser.navigate", "Go to Google", '{"url": "https://www.google.com"}')
add_block("browser.screenshot", "Screenshot", '{"path": "google.png"}')
add_block("browser.close", "Close", '{}')
```

## Architecture

- `backend/nekonote/` — Python scripting API + execution engine
- `frontend/` — Electron + React + TypeScript visual editor

## Writing RPA scripts (Python API)

```bash
# Run a script
nekonote run script.py
nekonote run script.py --verbose
nekonote run script.py --format json   # structured output for AI agents

# Inspect desktop state before writing scripts
nekonote inspect windows               # list open windows (JSON)
nekonote inspect ui-tree "App Name"    # dump UI element tree (XPath-capable XML)
nekonote inspect screenshot --output screen.png

# Validate without executing
nekonote check script.py

# List all available API functions
nekonote list-actions
```

## Script basics

```python
from nekonote import browser, desktop, window, file, excel, text, http, db, pdf, log

# Browser automation
browser.open()
browser.navigate("https://example.com")
browser.click("#submit")
browser.type("#input", "hello")
table = browser.get_table("table#data")
browser.close()

# Desktop automation (coordinates, image match, or XPath via uitree)
desktop.click(x=100, y=200)
desktop.click(image="button.png")
desktop.click_element(title="App", xpath='.//Button[@name="OK"]')
desktop.type("hello")
desktop.hotkey("ctrl", "s")

# Window management
win = window.find(title="Notepad")
window.activate(win)

# File operations
file.copy("src.txt", "dst.txt")
files = file.list_files("dir/", pattern="*.xlsx")
content = file.read_text("data.txt")

# Excel / CSV
data = excel.read("input.xlsx")
excel.write("output.xlsx", [{"name": "Taro", "age": 25}])
rows = excel.read_csv("data.csv")

# HTTP requests
resp = http.get("https://api.example.com/data")
resp = http.post("https://api.example.com/submit", json={"key": "value"})

# Database
conn = db.connect("sqlite", database="app.db")
rows = conn.query("SELECT * FROM users")
conn.close()

# Text / DateTime utilities
result = text.replace("hello world", "world", "python")
today = text.today("yyyy/MM/dd")

# PDF
pdf_text = pdf.read_text("document.pdf")

# Logging
log.info("Done")
```

## Error handling

All errors include structured context for AI debugging:
- `code`: machine-readable error code (ELEMENT_NOT_FOUND, TIMEOUT, etc.)
- `line`: line number in the script
- `context`: relevant state (page URL, similar selectors, open windows)
- `suggestion`: fix recommendation

## Development

```bash
# Backend
cd backend
pip install -e ".[automation,data,uitree,dev]"
python -m pytest tests/ -v           # run tests (must pass before committing)

# Frontend
cd frontend
npm install --include=dev
npx electron-vite dev                # dev server
npx electron-vite build              # production build
```

## Workflow

- All changes go through PRs with CI checks (pytest + CodeQL + build)
- Branch protection on master: CI must pass
- Dependabot monitors pip, npm, and GitHub Actions dependencies
