# nekonote

Windows RPA toolkit. Python API + Electron visual editor + Claude Code integration.

## PRIORITY: Use MCP tools to edit the open scenario

When the user asks you to create or modify an RPA scenario, **always use the MCP tools first** to edit the flow currently open in the visual editor. Do NOT just write a .py file.

### MCP flow editing workflow
1. `get_current_flow()` -- read the current flow
2. `add_block(block_type, label, params)` -- add blocks
3. `update_block_params(block_id, params)` -- adjust block parameters
4. `remove_block(block_id)` -- remove blocks
5. `update_flow(flow_json)` -- replace entire flow (for large changes)

The editor updates in real-time. The user sees blocks appear instantly.

### MCP inspect tools
- `inspect_windows(filter)` -- list open windows
- `inspect_ui_tree(title, depth, xpath)` -- dump UI element tree
- `inspect_browser()` -- browser page info
- `inspect_screenshot(output, region)` -- capture screen
- `run_script(script_path, variables)` -- execute a .py script
- `check_script(script_path)` -- syntax check
- `list_actions()` -- list all API functions

### hotkey params format
Use **comma-separated** key names: `{"keys": "ctrl,a"}`, `{"keys": "win,r"}`, `{"keys": "enter"}`

### Available block types
- `browser.open`, `browser.navigate`, `browser.click`, `browser.type`, `browser.getText`, `browser.wait`, `browser.screenshot`, `browser.close`
- `desktop.click`, `desktop.type`, `desktop.hotkey`, `desktop.screenshot`, `desktop.findImage`
- `control.if`, `control.loop`, `control.forEach`, `control.tryCatch`, `control.wait`
- `data.setVariable`, `data.log`, `data.comment`
- `subflow.call`

## Complete API Reference

All functions are synchronous (no async/await needed). Import: `from nekonote import browser, desktop, ...`

### nekonote.ai
- `ai.configure(*, provider='openai', api_key='', default_model='', base_url='')` -- Configure AI provider.
- `ai.generate(prompt, *, provider='', model='', api_key='', system='', temperature=0.7, max_tokens=4096) -> str` -- Generate text.
- `ai.generate_json(prompt, *, schema=None, ...) -> Any` -- Generate structured JSON.

### nekonote.browser
- `browser.open(browser_type='chromium', headless=False)` -- Launch browser.
- `browser.navigate(url) -> str` -- Navigate to URL, return final URL.
- `browser.click(selector, *, timeout=5000)` -- Click element.
- `browser.type(selector, text, *, clear=True, timeout=5000)` -- Type into input.
- `browser.get_text(selector, *, timeout=5000) -> str` -- Get element text.
- `browser.get_attribute(selector, attribute) -> str|None` -- Get attribute.
- `browser.get_html(selector) -> str` -- Get innerHTML.
- `browser.wait(selector, *, timeout=30000)` -- Wait for element.
- `browser.screenshot(path='') -> str` -- Screenshot (base64 if no path).
- `browser.execute_js(expression) -> Any` -- Run JavaScript.
- `browser.is_visible(selector) -> bool` -- Check visibility.
- `browser.count(selector) -> int` -- Count matching elements.
- `browser.select(selector, *, value='', label='', index=None)` -- Select dropdown.
- `browser.check(selector)` / `browser.uncheck(selector)` -- Checkbox.
- `browser.scroll(selector='', *, direction='down', amount=500)` -- Scroll.
- `browser.back()` / `browser.forward()` / `browser.reload()` -- Navigation.
- `browser.new_tab(url='')` / `browser.switch_tab(index)` / `browser.close_tab()` -- Tabs.
- `browser.upload(selector, file_path)` -- File upload.
- `browser.get_table(selector) -> list[dict]` -- Extract HTML table.
- `browser.get_page_info() -> dict` -- Page info (clickable, inputs, tables).
- `browser.get_tabs() -> list[dict]` -- All tab info.
- `browser.accept_dialog(prompt_text='')` / `browser.dismiss_dialog()` -- Dialogs.
- `browser.close()` -- Close browser.

### nekonote.config
- `config.get(key, default=None)` / `config.set(key, value)` -- Settings.
- `config.get_credential(name) -> dict` / `config.set_credential(name, **kwargs)` -- Credentials.
- `config.env(name, default='') -> str` -- Environment variable.

### nekonote.db
- `db.connect(driver='sqlite', *, database='', host='localhost', port=0, username='', password='') -> Connection`
- `conn.query(sql, params) -> list[dict]` -- SELECT.
- `conn.execute(sql, params) -> int` -- INSERT/UPDATE/DELETE.
- `conn.execute_many(sql, params_list) -> int` -- Bulk execute.
- `conn.transaction()` -- Context manager (commit/rollback).
- `conn.close()`

### nekonote.desktop
- `desktop.click(x=None, y=None, *, image='', confidence=0.8, button='left', clicks=1) -> dict` -- Click.
- `desktop.double_click(x, y)` / `desktop.right_click(x, y)` -- Mouse.
- `desktop.drag(from_x, from_y, to_x, to_y, *, duration=0.5)` -- Drag.
- `desktop.mouse_move(x, y)` / `desktop.scroll(direction='down', clicks=3)` -- Move/scroll.
- `desktop.type(text, *, interval=0.02)` -- Type text (Japanese via clipboard).
- `desktop.hotkey(*keys)` -- Key combo: `hotkey("ctrl", "s")`.
- `desktop.press(key)` -- Single key press.
- `desktop.screenshot(path='', *, region=None) -> str` -- Screenshot.
- `desktop.find_image(template, *, confidence=0.8) -> dict` -- Image search.
- `desktop.wait_image(template, *, timeout=10, confidence=0.8) -> dict` -- Wait for image.
- `desktop.get_screen_size() -> (w, h)` / `desktop.get_pixel_color(x, y) -> (r, g, b)`.
- `desktop.get_clipboard() -> str` / `desktop.set_clipboard(text)` -- Clipboard.
- `desktop.start_process(executable, *, args=None) -> int` / `desktop.kill_process(*, name='', pid=0)`.
- `desktop.get_ui_tree(*, title='', handle=0, depth=4) -> str` -- UI tree XML (uitree).
- `desktop.find_elements(*, title, xpath, depth=5) -> list[dict]` -- XPath search.
- `desktop.find_element(*, title, xpath, depth=5) -> dict` -- Single element.
- `desktop.click_element(*, title, xpath, depth=5)` -- Click by XPath.
- `desktop.type_element(*, title, xpath, text, depth=5)` -- Type by XPath.
- `desktop.get_element_value(*, title, xpath, depth=5) -> str` -- Get value by XPath.

### nekonote.dialog
- `dialog.show_message(message, *, title='Nekonote')` -- Message box.
- `dialog.confirm(message, *, title='Nekonote') -> bool` -- Yes/No.
- `dialog.input(message, *, title='Nekonote', default='') -> str|None` -- Text input.
- `dialog.select(message, options, *, title='Nekonote') -> str|None` -- Selection.
- `dialog.open_file(*, title, filter) -> str|None` / `dialog.save_file(...)` / `dialog.select_folder(...)`.

### nekonote.excel
- `excel.read(path, *, sheet='', header=True) -> list[dict]|list[list]` -- Read Excel.
- `excel.write(path, data, *, sheet='Sheet1') -> str` -- Write Excel.
- `excel.read_cell(path, *, sheet='', cell='A1')` / `excel.write_cell(path, *, cell, value)`.
- `excel.append(path, rows, *, sheet='')` -- Append rows.
- `excel.get_sheet_names(path) -> list[str]`.
- `excel.read_csv(path, *, encoding='utf-8', delimiter=',', header=True)` / `excel.write_csv(...)`.

### nekonote.file
- `file.copy(src, dst)` / `file.move(src, dst)` / `file.delete(path)` / `file.rename(src, new_name)`.
- `file.exists(path) -> bool` / `file.get_info(path) -> dict`.
- `file.create_dir(path)` / `file.delete_dir(path)`.
- `file.list_files(directory, *, pattern='*')` / `file.list_dirs(directory)`.
- `file.read_text(path)` / `file.write_text(path, content)` / `file.append_text(path, content)`.
- `file.zip(archive, files)` / `file.unzip(archive, dest='.')`.

### nekonote.http
- `http.get(url, *, headers=None, params=None) -> Response` -- GET.
- `http.post(url, *, json=None, data=None, headers=None) -> Response` -- POST.
- `http.put(...)` / `http.patch(...)` / `http.delete(...)` -- Other methods.
- `http.download(url, save_to, *, headers=None) -> str` -- Download file.
- Response: `.status_code`, `.text()`, `.json()`.

### nekonote.log
- `log.info(message)` / `log.warning(message)` / `log.error(message)` / `log.debug(message)`.

### nekonote.mail
- `mail.send(*, to, subject, body, cc=None, bcc=None, attachments=None, smtp_server, smtp_port, username, password)`.
- `mail.receive(*, imap_server, username, password, folder='INBOX', filter_subject='', unread_only=True, limit=10) -> list[dict]`.
- `mail.send_outlook(*, to, subject, body, attachments=None)` -- Windows Outlook COM.

### nekonote.ocr
- `ocr.read(path, *, lang='jpn+eng', region=None) -> str` -- OCR image.
- `ocr.read_screen(*, region=None, lang='jpn+eng') -> str` -- OCR screenshot.
- `ocr.read_blocks(path, *, lang='jpn+eng') -> list[dict]` -- Text blocks with bbox.

### nekonote.pdf
- `pdf.read_text(path, *, pages=None) -> str` -- Extract text.
- `pdf.read_tables(path, *, pages=None) -> list[list[dict]]` -- Extract tables.
- `pdf.get_info(path) -> dict` -- Page count, metadata.

### nekonote.text
- `text.replace(s, old, new)` / `text.split(s, sep)` / `text.join(parts, sep)` / `text.trim(s)`.
- `text.to_upper(s)` / `text.to_lower(s)` / `text.length(s)` / `text.substring(s, start, end)`.
- `text.contains(s, sub)` / `text.starts_with(s, prefix)` / `text.ends_with(s, suffix)`.
- `text.regex_match(s, pattern) -> list` / `text.regex_find_all(s, pattern)` / `text.regex_replace(s, pattern, repl)`.
- `text.base64_encode(s)` / `text.base64_decode(s)` / `text.url_encode(s)` / `text.url_decode(s)`.
- `text.now(fmt='')` / `text.today(fmt='')` / `text.format_datetime(dt_str, fmt)` / `text.parse_datetime(s, fmt='')`.
- `text.add_time(dt_str, *, days=0, hours=0, minutes=0, seconds=0)` / `text.diff_time(dt1, dt2) -> dict`.

### nekonote.window
- `window.find(*, title='', class_name='') -> WindowInfo` -- Find window (partial match).
- `window.find_all(*, title='', class_name='') -> list` / `window.list_windows(*, visible_only=True)`.
- `window.exists(*, title='', class_name='') -> bool` / `window.wait(*, title='', timeout=10)`.
- `window.launch(executable, *, args=None) -> int` -- Launch app, return PID.
- `window.activate(win)` / `window.maximize(win)` / `window.minimize(win)` / `window.restore(win)`.
- `window.close(win)` / `window.resize(win, *, width, height)` / `window.move(win, *, x, y)`.

### nekonote.scheduler
- `scheduler.add(name, *, cron, script, variables=None)` / `scheduler.remove(name)`.
- `scheduler.list() -> dict` / `scheduler.enable(name)` / `scheduler.disable(name)`.
- `scheduler.run_job(name) -> str` / `scheduler.start()` -- APScheduler daemon.

### nekonote.recorder
- `recorder.record(*, duration=30, include_mouse=True, include_keyboard=True) -> list[dict]` -- Record operations as blocks.

### nekonote.history
- `history.record_event(run_id, event)` / `history.list_runs(*, limit=20) -> list[dict]`.
- `history.get_run_logs(run_id) -> list[dict]` / `history.clear(*, older_than_days=0) -> int`.

### nekonote.retry
- `@retry.retry(max_attempts=3, delay=1.0, backoff=1.0, exceptions=(Exception,))` -- Retry decorator.

### nekonote.teams
- `teams.post_webhook(*, webhook_url, message, title='')` -- Post to Teams via webhook.

### nekonote.gsheets
- `gsheets.open(spreadsheet_id, *, credentials='service_account.json') -> Sheet`.
- `sheet.read(range)` / `sheet.write(range, values)` / `sheet.append(range, values)` / `sheet.clear(range)`.

## CLI

```bash
nekonote run script.py [--verbose] [--format json] [--var key=value]
nekonote inspect windows [--filter TITLE]
nekonote inspect ui-tree TITLE [--depth N] [--xpath EXPR]
nekonote inspect screenshot [--output FILE]
nekonote check script.py
nekonote list-actions
```

## Development

```bash
cd backend && pip install -e ".[automation,data,uitree,mcp,dev]"
python -m pytest tests/ -v   # 267 tests, must pass before committing
cd frontend && npm install --include=dev && npx electron-vite dev
```
