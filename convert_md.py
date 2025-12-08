import re
import html
import sys
import os

if len(sys.argv) < 3:
    print("Usage: python convert_md.py <input_md_file> <output_html_file>")
    sys.exit(1)

INPUT_FILE = sys.argv[1]
OUTPUT_FILE = sys.argv[2]

HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Singleton Pattern Guide</title>
    <!-- Syntax Highlighting -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <style>
        :root {
            --primary: #2c3e50;
            --secondary: #34495e;
            --accent: #3498db;
            --bg: #f0f2f5;
            --card-bg: #ffffff;
            --text: #333;
            --border: #e0e0e0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            line-height: 1.6;
            color: var(--text);
            background-color: var(--bg);
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: var(--card-bg);
            padding: 50px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }

        h1 {
            color: var(--primary);
            font-size: 2.5rem;
            border-bottom: 3px solid var(--accent);
            padding-bottom: 15px;
            margin-top: 0;
            margin-bottom: 30px;
        }

        h2 {
            color: var(--secondary);
            font-size: 1.8rem;
            margin-top: 40px;
            margin-bottom: 20px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }

        h3 {
            color: var(--secondary);
            font-size: 1.4rem;
            margin-top: 30px;
            margin-bottom: 15px;
        }

        p {
            margin-bottom: 16px;
        }

        ul {
            margin-bottom: 16px;
            padding-left: 25px;
        }

        li {
            margin-bottom: 8px;
        }

        strong {
            color: var(--primary);
            font-weight: 700;
        }

        code {
            font-family: 'Fira Code', Consolas, Monaco, 'Andale Mono', monospace;
            background-color: #f4f4f4;
            padding: 2px 5px;
            border-radius: 4px;
            color: #e01e5a;
            font-size: 0.9em;
        }

        pre {
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        pre code {
            background-color: transparent;
            color: inherit;
            padding: 0;
        }

        /* Table Styles */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.95em;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
            border-radius: 8px;
            overflow: hidden;
        }

        table thead tr {
            background-color: var(--primary);
            color: #ffffff;
            text-align: left;
        }

        table th, table td {
            padding: 12px 15px;
        }

        table tbody tr {
            border-bottom: 1px solid #dddddd;
        }

        table tbody tr:nth-of-type(even) {
            background-color: #f9f9f9;
        }

        table tbody tr:last-of-type {
            border-bottom: 2px solid var(--primary);
        }

        hr {
            border: 0;
            height: 1px;
            background: #ddd;
            margin: 40px 0;
        }
        
        blockquote {
            border-left: 4px solid var(--accent);
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #f9f9f9;
            color: #555;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div class="container">
"""

HTML_FOOTER = """
    </div>
    <!-- Scripts -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-java.min.js"></script>
</body>
</html>
"""

def format_inline(text):
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic (careful not to match inside bold if possible, but basic is fine)
    text = re.sub(r'(?<!\*)\*(?!\*)(.*?)\*', r'<em>\1</em>', text)
    # Code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    # Links
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
    return text

def render_table(rows):
    if not rows: return ""
    html_parts = ["<table>"]
    
    # Process header
    header_row = rows[0]
    cols = [c.strip() for c in header_row.strip("|").split("|")]
    html_parts.append("<thead><tr>")
    for c in cols:
        if not c: continue # Skip empty splits from ends
        html_parts.append(f"<th>{format_inline(c)}</th>")
    html_parts.append("</tr></thead>")
    
    # Determine data start (skip separator if present)
    start_idx = 1
    if len(rows) > 1 and "---" in rows[1]:
        start_idx = 2
        
    html_parts.append("<tbody>")
    for row in rows[start_idx:]:
        cols = [c.strip() for c in row.strip("|").split("|")]
        html_parts.append("<tr>")
        for c in cols:
            if not c and not row.strip().endswith("|"): continue # strict check?
            # actually simpler: filter empty strings from split result if they are just artifacts
            # But | val | val | splits to ['', 'val', 'val', '']
            pass
        
        # Better split logic for table rows
        clean_cols = [c.strip() for c in row.strip().strip("|").split("|")]
        for c in clean_cols:
             html_parts.append(f"<td>{format_inline(c)}</td>")
        html_parts.append("</tr>")
        
    html_parts.append("</tbody></table>")
    return "".join(html_parts)

def main():
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    out = [HTML_HEADER]
    
    in_code_block = False
    code_lang = ""
    in_table = False
    in_list = False
    table_buffer = []
    
    for line in lines:
        raw_line = line
        stripped = line.strip()
        
        # Code Blocks
        if stripped.startswith("```"):
            if in_code_block:
                out.append("</code></pre>")
                in_code_block = False
            else:
                code_lang = stripped[3:].strip()
                if not code_lang: code_lang = "java" # default
                out.append(f'<pre><code class="language-{code_lang}">')
                in_code_block = True
            continue
            
        if in_code_block:
            # Escape HTML in code
            out.append(html.escape(raw_line))
            continue
            
        # Tables
        if stripped.startswith("|"):
            if not in_table:
                if table_buffer: # Flush previous if any (shouldn't happen)
                    out.append(render_table(table_buffer))
                    table_buffer = []
                in_table = True
            table_buffer.append(stripped)
            continue
        else:
            if in_table:
                out.append(render_table(table_buffer))
                table_buffer = []
                in_table = False
        
        # Lists
        if stripped.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{format_inline(stripped[2:])}</li>")
            continue
        else:
            if in_list:
                out.append("</ul>")
                in_list = False
                
        # Headers
        if stripped.startswith("#"):
            level = 0
            for char in stripped:
                if char == '#': level += 1
                else: break
            
            content = stripped[level:].strip()
            out.append(f"<h{level}>{format_inline(content)}</h{level}>")
            continue
            
        # HR
        if stripped.startswith("---") or stripped.startswith("***"):
            # Only if it's the whole line mostly
            if len(stripped) >= 3 and all(c in "-* " for c in stripped):
                out.append("<hr>")
                continue
                
        # Empty lines
        if not stripped:
            continue
            
        # Paragraphs
        out.append(f"<p>{format_inline(stripped)}</p>")
        
    # Flush ends
    if in_code_block: out.append("</code></pre>")
    if in_list: out.append("</ul>")
    if in_table: out.append(render_table(table_buffer))
    
    out.append(HTML_FOOTER)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(out))
    
    print(f"Successfully converted {INPUT_FILE} to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
