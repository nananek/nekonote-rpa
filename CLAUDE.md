# nekonote

Windows RPA toolkit. Electron (frontend) + Python (backend).

## Architecture

- `backend/nekonote/` — Python scripting API + execution engine
- `frontend/` — Electron + React + TypeScript visual editor

## Writing RPA scripts

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
