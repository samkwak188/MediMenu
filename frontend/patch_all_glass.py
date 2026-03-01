import re

with open('src/styles.css', 'r') as f:
    css = f.read()

def inject_glass(match):
    block = match.group(0)
    # Don't touch auth-card or role-card since we just fixed them manually
    if '.auth-card ' in block or '.role-card ' in block or '.auth-card{' in block or '.role-card{' in block:
        return block
        
    if 'background: var(--surface)' in block:
        # Prevent double injection
        if 'backdrop-filter: var(--glass-blur)' not in block:
            # Replace basic border with glass border
            block = re.sub(r'border:\s*1px\s*solid\s*var\(--line\);', 'border: var(--glass-border);', block)
            block = re.sub(r'border:\s*2px\s*solid\s*var\(--line\);', 'border: var(--glass-border);', block)
            block = re.sub(r'border-color:\s*var\(--line\);', 'border-color: rgba(255,255,255,0.12);', block)
            
            # Inject glass properties before closing brace
            glass_props = "  backdrop-filter: var(--glass-blur);\n  -webkit-backdrop-filter: var(--glass-blur);\n  box-shadow: var(--shadow-md);\n}"
            block = re.sub(r'\}$', glass_props, block)
            
    return block

# Split CSS into blocks and process each block safely
blocks = re.split(r'(\n[^{]+?\{[^}]+\})', css)
for i in range(1, len(blocks), 2):
    blocks[i] = inject_glass(re.match(r'.*', blocks[i], re.DOTALL))

new_css = "".join(blocks)

with open('src/styles.css', 'w') as f:
    f.write(new_css)

print("Applied glass properties globally")
