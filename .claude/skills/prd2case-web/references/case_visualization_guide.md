Template source:
- `assets/test-case-tree-template.html`

Workflow:
0. If the source test case is markdown form, use `scripts/case_form_transfer.py` to convert it to JSON form under `$TEST_DIR`.
  - The script now supports both directions and auto-detects by input suffix:
  - `.md` / `.markdown` -> JSON
  - `.json` -> Markdown
  - In `json -> markdown`, headings are rendered strictly from `data.nodeType`. The script does not infer or inject `**测试内容**`.
1. Prepare case JSON data (shape may vary):
  - API wrapper: `{ code, msg, data: { case_form, case_data } }`
  - Core node: `{ data, children }`
  - Front-end node: `{ type, text, children }`
2. Copy the template into `$TEST_DIR`, and embed case JSON into `<script id="embedded-case-json" type="application/json">...</script>`.
3. Show the generated HTML file path to the user, and let the user open it directly in browser (no local HTTP server).
4. If test case changes, regenerate the HTML by embedding the latest JSON again.

Example commands:
```bash
# 1) optional: markdown -> json
python3 scripts/case_form_transfer.py "$TEST_DIR/case.md" -o "$TEST_DIR/case.json"

# 2) copy template
cp assets/test-case-tree-template.html "$TEST_DIR/test-case-tree.html"

# 3) embed JSON into HTML
python3 - "$TEST_DIR/case.json" "$TEST_DIR/test-case-tree.html" <<'PY'
import json, re, sys
json_path, html_path = sys.argv[1], sys.argv[2]
data = json.load(open(json_path, "r", encoding="utf-8"))
payload = json.dumps(data, ensure_ascii=False, indent=2)
html = open(html_path, "r", encoding="utf-8").read()
pattern = r'(<script id="embedded-case-json" type="application/json">)(.*?)(</script>)'
repl = r'\1\n' + payload + r'\n  \3'
new_html, count = re.subn(pattern, repl, html, flags=re.S)
if count != 1:
    raise SystemExit("Failed to find unique embedded-case-json block in template.")
open(html_path, "w", encoding="utf-8").write(new_html)
print("Generated:", html_path)
PY

# 4) tell the user the generated HTML path
echo "$TEST_DIR/test-case-tree.html"
```

Notes:
- The visualization now reads JSON only from the embedded `<script id="embedded-case-json" type="application/json">` block.
- Browser direct-open (`file://.../test-case-tree.html`) is supported; no server is required.
- For each case update, rerun step 3 to refresh embedded JSON, then ask the user to refresh the already-open page or open the HTML file manually.
