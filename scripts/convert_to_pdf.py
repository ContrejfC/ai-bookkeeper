#!/usr/bin/env python3
"""
Convert markdown documentation to print-ready HTML that can be saved as PDF.
Usage: python3 scripts/convert_to_pdf.py
Output: AI_BOOKKEEPER_COMPLETE_TECHNICAL_OUTLINE.html
"""

import re
import sys
from pathlib import Path

def markdown_to_html(md_content):
    """Convert markdown to HTML with basic formatting."""
    html = md_content
    
    # First, protect code blocks from other conversions
    code_blocks = []
    def save_code_block(match):
        lang = match.group(1) or ''
        code = match.group(2)
        # Escape HTML in code blocks
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        placeholder = f'___CODE_BLOCK_{len(code_blocks)}___'
        code_blocks.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
        return placeholder
    
    html = re.sub(
        r'```(\w+)?\n(.*?)```',
        save_code_block,
        html,
        flags=re.DOTALL
    )
    
    # Convert headers with anchor IDs
    def header_with_id(match):
        level = len(match.group(1))
        text = match.group(2)
        # Create anchor ID from text (lowercase, replace spaces with hyphens, remove special chars)
        anchor_id = re.sub(r'[^\w\s-]', '', text.lower())
        anchor_id = re.sub(r'[-\s]+', '-', anchor_id).strip('-')
        return f'<h{level} id="{anchor_id}">{text}</h{level}>'
    
    html = re.sub(r'^(#{1,5}) (.+)$', header_with_id, html, flags=re.MULTILINE)
    
    # Convert bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    
    # Convert italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    
    # Convert inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Convert horizontal rules
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
    
    # Convert links
    html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', html)
    
    # Convert unordered lists
    lines = html.split('\n')
    in_list = False
    result = []
    
    for line in lines:
        if re.match(r'^- ', line):
            if not in_list:
                result.append('<ul>')
                in_list = True
            result.append('<li>' + line[2:] + '</li>')
        else:
            if in_list:
                result.append('</ul>')
                in_list = False
            result.append(line)
    
    if in_list:
        result.append('</ul>')
    
    html = '\n'.join(result)
    
    # Convert tables
    table_pattern = r'\|(.+)\|\n\|[-:\| ]+\|\n((?:\|.+\|\n?)+)'
    
    def table_replace(match):
        header = match.group(1)
        rows = match.group(2)
        
        headers = [h.strip() for h in header.split('|') if h.strip()]
        header_html = '<thead><tr>' + ''.join(f'<th>{h}</th>' for h in headers) + '</tr></thead>'
        
        body_rows = []
        for row in rows.strip().split('\n'):
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if cells:
                body_rows.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
        
        body_html = '<tbody>' + ''.join(body_rows) + '</tbody>'
        
        return f'<table class="data-table">{header_html}{body_html}</table>'
    
    html = re.sub(table_pattern, table_replace, html, flags=re.MULTILINE)
    
    # Convert paragraphs
    html = re.sub(r'\n\n', r'\n<p>\n', html)
    
    # Restore code blocks
    for i, code_block in enumerate(code_blocks):
        html = html.replace(f'___CODE_BLOCK_{i}___', code_block)
    
    return html

def create_html_document(content):
    """Wrap content in a complete HTML document with print styles."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Bookkeeper - Complete Technical Outline</title>
    <style>
        @page {{
            size: letter;
            margin: 0.75in;
        }}
        
        html {{
            scroll-behavior: smooth;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }}
        
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
            page-break-after: avoid;
            font-size: 28px;
        }}
        
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 8px;
            margin-top: 25px;
            page-break-after: avoid;
            font-size: 24px;
        }}
        
        h3 {{
            color: #2c3e50;
            margin-top: 20px;
            page-break-after: avoid;
            font-size: 20px;
        }}
        
        h4 {{
            color: #34495e;
            margin-top: 15px;
            page-break-after: avoid;
            font-size: 18px;
        }}
        
        h5 {{
            color: #555;
            margin-top: 12px;
            page-break-after: avoid;
            font-size: 16px;
        }}
        
        p {{
            margin: 10px 0;
            text-align: justify;
        }}
        
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 5px 0;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            color: #c7254e;
        }}
        
        pre {{
            background: #f8f8f8;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            page-break-inside: avoid;
            margin: 15px 0;
            white-space: pre;
            font-family: 'Courier New', 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            line-height: 1.4;
        }}
        
        pre code {{
            background: transparent;
            padding: 0;
            color: #333;
            font-size: 12px;
            font-family: inherit;
            white-space: pre;
            display: block;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            page-break-inside: avoid;
            font-size: 14px;
        }}
        
        th, td {{
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
        }}
        
        th {{
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 30px 0;
        }}
        
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        /* Highlight target section when jumped to */
        :target {{
            animation: highlight 2s ease;
        }}
        
        @keyframes highlight {{
            0% {{
                background-color: #fff3cd;
            }}
            100% {{
                background-color: transparent;
            }}
        }}
        
        /* Table of contents styling */
        #table-of-contents + ul {{
            list-style: none;
            padding-left: 0;
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px 20px;
            margin: 20px 0;
        }}
        
        #table-of-contents + ul li {{
            margin: 8px 0;
        }}
        
        #table-of-contents + ul a {{
            font-weight: 500;
        }}
        
        /* Back to Top Button */
        #back-to-top {{
            position: fixed;
            bottom: 40px;
            right: 40px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 50%;
            width: 56px;
            height: 56px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        #back-to-top.show {{
            opacity: 1;
            visibility: visible;
        }}
        
        #back-to-top:hover {{
            background: #2980b9;
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.4);
        }}
        
        #back-to-top:active {{
            transform: translateY(-1px);
        }}
        
        .page-break {{
            page-break-before: always;
        }}
        
        @media print {{
            body {{
                padding: 0;
            }}
            
            h1, h2, h3, h4, h5, h6 {{
                page-break-after: avoid;
            }}
            
            pre, table {{
                page-break-inside: avoid;
            }}
            
            ul, ol {{
                page-break-inside: avoid;
            }}
            
            #back-to-top {{
                display: none;
            }}
        }}
        
        /* Header styling */
        .document-header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #3498db;
        }}
        
        .document-header h1 {{
            border: none;
            margin-top: 0;
        }}
        
        .document-info {{
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    {content}
    
    <!-- Back to Top Button -->
    <button id="back-to-top" title="Back to Top">↑</button>
    
    <script>
        // Back to Top Button functionality
        const backToTopButton = document.getElementById('back-to-top');
        
        // Show button when user scrolls down 300px
        window.addEventListener('scroll', function() {{
            if (window.pageYOffset > 300) {{
                backToTopButton.classList.add('show');
            }} else {{
                backToTopButton.classList.remove('show');
            }}
        }});
        
        // Smooth scroll to top when button is clicked
        backToTopButton.addEventListener('click', function() {{
            window.scrollTo({{
                top: 0,
                behavior: 'smooth'
            }});
        }});
    </script>
</body>
</html>"""

def main():
    # Read the markdown file
    md_file = Path(__file__).parent.parent / 'AI_BOOKKEEPER_COMPLETE_TECHNICAL_OUTLINE.md'
    
    if not md_file.exists():
        print(f"Error: File not found: {md_file}")
        sys.exit(1)
    
    print(f"Reading {md_file}...")
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    print("Converting markdown to HTML...")
    html_content = markdown_to_html(md_content)
    
    print("Creating HTML document...")
    html_document = create_html_document(html_content)
    
    # Write the HTML file
    output_file = md_file.with_suffix('.html')
    print(f"Writing {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_document)
    
    print(f"\n✅ Success!")
    print(f"\nHTML file created: {output_file}")
    print(f"\nTo create a PDF:")
    print(f"1. Open {output_file} in your web browser")
    print(f"2. Press Cmd+P (Mac) or Ctrl+P (Windows)")
    print(f"3. Select 'Save as PDF' as the destination")
    print(f"4. Click 'Save'")
    print(f"\nThe HTML file is already optimized for printing with proper page breaks.")

if __name__ == '__main__':
    main()

