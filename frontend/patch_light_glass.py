import re

with open('src/styles.css', 'r') as f:
    css = f.read()

# 1. Update root variables for TRUE LIGHT GLASSMORPHISM
root_pattern = re.compile(r':root\s*\{.*?(?=^\})', re.DOTALL | re.MULTILINE)

new_root = """/* TRUE LIGHT GLASSMORPHISM THEME */
:root {
  --primary: #3b82f6; /* Vibrant Blue */
  --primary-hover: #2563eb;
  --primary-light: rgba(59, 130, 246, 0.1);

  --bg: #e2e8f0; /* Soft off-white / light grey background */
  
  /* Glass card surface - slightly white with high transparency */
  --surface: rgba(255, 255, 255, 0.4);
  --surface-hover: rgba(255, 255, 255, 0.5);

  --text-main: #0f172a; /* Dark sleek text */
  --text-muted: rgba(15, 23, 42, 0.6);

  /* Distinct frosted borders */
  --line: rgba(255, 255, 255, 0.5);
  --glass-border: 1px solid rgba(255, 255, 255, 0.6);
  --glass-border-light: 1px solid rgba(255, 255, 255, 0.8);

  --danger: #ef4444;
  --danger-bg: rgba(239, 68, 68, 0.1);
  --warn: #f59e0b;
  --warn-bg: rgba(245, 158, 11, 0.1);
  --ok: #10b981;
  --ok-bg: rgba(16, 185, 129, 0.1);

  /* Soft, clean drop shadows */
  --shadow-sm: inset 0 1px 0 rgba(255, 255, 255, 0.6), 0 4px 6px -1px rgb(0 0 0 / 0.05);
  --shadow-md: inset 0 1px 0 rgba(255, 255, 255, 0.7), 0 10px 30px -5px rgb(0 0 0 / 0.1);
  --shadow-lg: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 20px 40px -5px rgb(0 0 0 / 0.15);

  --radius-sm: 12px;
  --radius-md: 20px;
  --radius-lg: 32px;
  --radius-full: 9999px;

  /* Frosted look */
  --glass-blur: blur(24px);

  --font-heading: "Plus Jakarta Sans", sans-serif;
  --font-body: "Inter", sans-serif;
  --font-mono: "IBM Plex Mono", monospace;
"""

css = root_pattern.sub(new_root, css)

# 2. Update body background
# Remove the heavy animated gradients and replace with a very subtle, almost static light background
body_pattern = re.compile(r'body\s*\{.*?(?=^\})', re.DOTALL | re.MULTILINE)
new_body = """body {
  margin: 0;
  font-family: var(--font-body);
  color: var(--text-main);
  background: radial-gradient(circle at top left, #f8fafc, #e2e8f0 40%, #cbd5e1);
  background-attachment: fixed;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

/* Optional soft, slow-moving blurred orbs (grey/blueish) in the background so it is not 100% plain */
body::before, body::after {
  content: "";
  position: fixed;
  border-radius: 50%;
  z-index: -1;
  filter: blur(100px);
  animation: float 30s infinite ease-in-out alternate;
}

body::before {
  width: 50vw;
  height: 50vw;
  max-width: 600px;
  max-height: 600px;
  background: rgba(255, 255, 255, 0.8); /* Pure white soft light */
  top: -10%;
  left: -10%;
}

body::after {
  width: 60vw;
  height: 60vw;
  max-width: 700px;
  max-height: 700px;
  background: rgba(148, 163, 184, 0.3); /* Soft slate shadow */
  bottom: -20%;
  right: -10%;
  animation-delay: -15s;
}
"""
css = body_pattern.sub(new_body, css)

# Remove the old gradientBG keyframe
css = re.sub(r'@keyframes gradientBG\s*\{.*?\}\s*}?', '', css, flags=re.DOTALL)

# 3. Fix Inputs for light mode
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
  background: rgba(255, 255, 255, 0.3);
  color: var(--text-main);
  transition: all 0.2s;
}""", css)

input_placeholder = re.compile(r'input::placeholder,.*?textarea::placeholder\s*\{.*?\}', re.DOTALL)
css = input_placeholder.sub("""input::placeholder,
textarea::placeholder {
  color: rgba(15, 23, 42, 0.4);
}""", css)

input_focus = re.compile(r'input:focus,.*?textarea:focus\s*\{.*?\}', re.DOTALL)
css = input_focus.sub("""input:focus,
textarea:focus {
  outline: none;
  border-color: var(--primary);
  background: rgba(255, 255, 255, 0.6);
  box-shadow: 0 0 0 3px var(--primary-light);
}""", css)

# 4. Fix primary buttons for light mode
btn_primary_pattern = re.compile(r'\.btn-primary\s*\{.*?\}', re.DOTALL)
css = btn_primary_pattern.sub(""".btn-primary {
  background: var(--text-main); /* Dark sleek button on light theme */
  color: #fff;
  border: none;
  box-shadow: 0 4px 15px rgba(15, 23, 42, 0.2);
}""", css)

btn_primary_hover = re.compile(r'\.btn-primary:hover:not\(:disabled\)\s*\{.*?\}', re.DOTALL)
css = btn_primary_hover.sub(""".btn-primary:hover:not(:disabled) {
  background: #334155;
  box-shadow: 0 6px 20px rgba(15, 23, 42, 0.3);
  transform: translateY(-2px);
}""", css)

with open('src/styles.css', 'w') as f:
    f.write(css)

print("Applied Light Glassmorphism")
