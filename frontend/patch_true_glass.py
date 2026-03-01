import re

with open('src/styles.css', 'r') as f:
    css = f.read()

# 1. Update root variables for TRUE Dark Glassmorphism
root_pattern = re.compile(r':root\s*\{.*?(?=^\})', re.DOTALL | re.MULTILINE)

new_root = """/* TRUE DARK GLASSMORPHISM THEME */
:root {
  --primary: #8b5cf6; /* Vibrant Purple */
  --primary-hover: #a78bfa;
  --primary-light: rgba(139, 92, 246, 0.2);

  --bg: #0f1016; /* Deep dark background */
  
  /* Glass card surface */
  --surface: rgba(255, 255, 255, 0.03);
  --surface-hover: rgba(255, 255, 255, 0.08);

  --text-main: #ffffff;
  --text-muted: rgba(255, 255, 255, 0.6);

  /* Light catching borders */
  --line: rgba(255, 255, 255, 0.1);
  --glass-border: 1px solid rgba(255, 255, 255, 0.12);
  --glass-border-light: 1px solid rgba(255, 255, 255, 0.25);

  --danger: #ff4757;
  --danger-bg: rgba(255, 71, 87, 0.15);
  --warn: #ffa502;
  --warn-bg: rgba(255, 165, 2, 0.15);
  --ok: #2ed573;
  --ok-bg: rgba(46, 213, 115, 0.15);

  --shadow-sm: 0 4px 15px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  --shadow-lg: 0 12px 40px 0 rgba(0, 0, 0, 0.5);

  --radius-sm: 12px;
  --radius-md: 20px;
  --radius-lg: 32px;
  --radius-full: 9999px;

  --glass-blur: blur(24px);

  --font-heading: "Plus Jakarta Sans", sans-serif;
  --font-body: "Inter", sans-serif;
  --font-mono: "IBM Plex Mono", monospace;
"""

css = root_pattern.sub(new_root, css)

# 2. Update body and blobs for the deep dark + rich colorful orbs look
body_pattern = re.compile(r'body\s*\{.*?(?=^\})', re.DOTALL | re.MULTILINE)
new_body = """body {
  margin: 0;
  font-family: var(--font-body);
  color: var(--text-main);
  background-color: var(--bg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

/* Beautiful vibrant orbs in the background */
body::before, body::after, .orb-3 {
  content: "";
  position: fixed;
  border-radius: 50%;
  z-index: -1;
  filter: blur(100px);
  animation: float 25s infinite ease-in-out alternate;
}

body::before {
  width: 45vw;
  height: 45vw;
  max-width: 600px;
  max-height: 600px;
  background: #ff5e62; /* Vibrant coral/orange */
  top: -5%;
  left: -5%;
}

body::after {
  width: 50vw;
  height: 50vw;
  max-width: 700px;
  max-height: 700px;
  background: #00d2ff; /* Vibrant cyan */
  bottom: -10%;
  right: -5%;
  animation-delay: -5s;
}

/* Inject third orb via a pseudo-element on the root app shell or just add raw CSS for a generic class */
.bg-orb-3 {
  position: fixed;
  border-radius: 50%;
  z-index: -1;
  filter: blur(120px);
  animation: float 30s infinite ease-in-out alternate-reverse;
  width: 40vw;
  height: 40vw;
  max-width: 500px;
  max-height: 500px;
  background: #8b5cf6; /* Vibrant purple */
  top: 40%;
  left: 30%;
  animation-delay: -15s;
}
"""
css = body_pattern.sub(new_body, css)

# 3. Clean up the messy backdrop-filters I added before
# Replace every instance of 'backdrop-filter: var(--glass-blur);' inside blocks with a cleaner unified glass class approach or correct it.
css = css.replace("  backdrop-filter: var(--glass-blur);\n", "")
css = css.replace("  -webkit-backdrop-filter: var(--glass-blur);\n", "")

# We need to selectively add the glassmorphism properties to actual cards and surfaces.
def apply_glass(match):
    block = match.group(0)
    # Only if it strictly sets background to surface and it's a structural element
    if 'background: var(--surface)' in block or 'background: var(--bg)' in block:
        # Avoid double applying if already exists (it shouldn't because we stripped it)
        block = block.replace('border: 1px solid var(--line);', 'border: var(--glass-border);')
        block = block.replace('border: 2px solid var(--line);', 'border: var(--glass-border);')
        block = block.replace('}', '  backdrop-filter: var(--glass-blur);\n  -webkit-backdrop-filter: var(--glass-blur);\n  box-shadow: var(--shadow-md);\n}')
    return block

blocks = re.split(r'(\n[^{]+?\{[^}]+\})', css)
for i in range(1, len(blocks), 2):
    if 'body {' not in blocks[i] and ':root {' not in blocks[i]:
        blocks[i] = apply_glass(re.match(r'.*', blocks[i], re.DOTALL))

# Let's fix buttons to match the sleek glass look
# Primary button -> Gradient background
btn_primary_pattern = re.compile(r'\.btn-primary\s*\{.*?\}', re.DOTALL)
css = btn_primary_pattern.sub(""".btn-primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
  color: #fff;
  border: none;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
}""", css)

btn_primary_hover = re.compile(r'\.btn-primary:hover:not\(:disabled\)\s*\{.*?\}', re.DOTALL)
css = btn_primary_hover.sub(""".btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  box-shadow: 0 6px 20px rgba(139, 92, 246, 0.6);
  transform: translateY(-2px);
}""", css)

# Input fields should also be glassy
input_pattern = re.compile(r'input\[type="text"\],.*?textarea\s*\{.*?\}', re.DOTALL)
css = input_pattern.sub("""input[type="text"],
input[type="email"],
input[type="password"],
textarea {
  width: 100%;
  border: var(--glass-border);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  font-family: var(--font-body);
  font-size: 1rem;
  background: rgba(0, 0, 0, 0.2);
  color: var(--text-main);
  transition: all 0.2s;
}""", css)

input_focus = re.compile(r'input:focus,.*?textarea:focus\s*\{.*?\}', re.DOTALL)
css = input_focus.sub("""input:focus,
textarea:focus {
  outline: none;
  border-color: var(--primary);
  background: rgba(0, 0, 0, 0.4);
  box-shadow: 0 0 0 2px var(--primary-light);
}""", css)

with open('src/styles.css', 'w') as f:
    f.write(css)

print("Glassmorphism styles radically updated!")
