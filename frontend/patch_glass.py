import re

with open('src/styles.css', 'r') as f:
    css = f.read()

# Update root variables
root_pattern = re.compile(r':root\s*\{.*?(?=^\})', re.DOTALL | re.MULTILINE)

new_root = """:root {
  --primary: #6366f1;
  --primary-hover: #4f46e5;
  --primary-light: rgba(99, 102, 241, 0.15);

  --bg: rgba(255, 255, 255, 0.15);
  --surface: rgba(255, 255, 255, 0.4);

  --text-main: #0f172a;
  --text-muted: #334155;

  --line: rgba(255, 255, 255, 0.4);

  --danger: #ef4444;
  --danger-bg: rgba(239, 68, 68, 0.15);
  --warn: #f59e0b;
  --warn-bg: rgba(245, 158, 11, 0.15);
  --ok: #10b981;
  --ok-bg: rgba(16, 185, 129, 0.15);

  --shadow-sm: 0 4px 6px -1px rgb(0 0 0 / 0.05);
  --shadow-md: 0 8px 32px 0 rgb(31 38 135 / 0.1);
  --shadow-lg: 0 12px 40px 0 rgb(31 38 135 / 0.15);

  --radius-sm: 12px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-full: 9999px;

  --glass-blur: blur(16px);

  --font-heading: "Plus Jakarta Sans", sans-serif;
  --font-body: "Inter", sans-serif;
  --font-mono: "IBM Plex Mono", monospace;
"""

css = root_pattern.sub(new_root, css)

# Update body background
body_pattern = re.compile(r'body\s*\{.*?(?=^\})', re.DOTALL | re.MULTILINE)
new_body = """body {
  margin: 0;
  font-family: var(--font-body);
  color: var(--text-main);
  background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
  background-size: 400% 400%;
  animation: gradientBG 15s ease infinite;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
"""
css = body_pattern.sub(new_body, css)

# Add keyframes for gradient
if '@keyframes gradientBG' not in css:
    css += """
@keyframes gradientBG {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
"""

# Inject backdrop-filter wherever var(--surface) or var(--bg) is used as background in blocks
# Skip html, body, :root
blocks = re.split(r'(\n[^{]+?\{[^}]+\})', css)
for i in range(1, len(blocks), 2):
    block = blocks[i]
    if 'body {' in block or ':root {' in block:
        continue
    
    # If the block has a background that uses --surface or --bg, add backdrop-filter, unless it already has it
    if ('background: var(--surface)' in block or 'background: var(--bg)' in block) and 'backdrop-filter' not in block:
        # insert before the closing brace
        blocks[i] = block.replace('}', '  backdrop-filter: var(--glass-blur);\n  -webkit-backdrop-filter: var(--glass-blur);\n}')

css = "".join(blocks)

with open('src/styles.css', 'w') as f:
    f.write(css)

print('Patched styles.css')
