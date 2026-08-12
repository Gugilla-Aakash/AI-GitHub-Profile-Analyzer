import markdown
from weasyprint import HTML

PREMIUM_PDF_STYLES = """
@page {
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
    @bottom-right {
        content: "Page " counter(page) " of " counter(pages);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 8pt;
        color: #64748b;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.6;
    font-size: 10pt;
}

h1 {
    font-size: 20pt;
    color: #0f172a;
    border-bottom: 2px solid #2563eb;
    padding-bottom: 6px;
    margin-top: 0;
    margin-bottom: 12px;
}

h2 {
    font-size: 13pt;
    color: #1e3a8a;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 4px;
    margin-top: 18px;
    margin-bottom: 10px;
}

h3 {
    font-size: 11pt;
    color: #0f172a;
    margin-top: 12px;
    margin-bottom: 6px;
}

blockquote {
    background: #f8fafc;
    border-left: 4px solid #2563eb;
    margin: 12px 0;
    padding: 10px 14px;
    font-style: italic;
    color: #334155;
    border-radius: 0 6px 6px 0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 9pt;
}

th, td {
    border: 1px solid #cbd5e1;
    padding: 8px 10px;
    text-align: left;
}

th {
    background: #f1f5f9;
    color: #0f172a;
    font-weight: 600;
}

tr:nth-child(even) {
    background: #f8fafc;
}

ul, ol {
    margin-top: 6px;
    margin-bottom: 10px;
    padding-left: 20px;
}

li {
    margin-bottom: 4px;
}

code {
    background: #f1f5f9;
    color: #2563eb;
    padding: 2px 5px;
    border-radius: 4px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 8.5pt;
}

pre {
    background: #0f172a;
    color: #f8fafc;
    padding: 12px;
    border-radius: 6px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
    font-size: 8.5pt;
    overflow-x: auto;
}

hr {
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 16px 0;
}
"""


def convert_markdown_to_pdf(markdown_content: str) -> bytes:
    """Converts Markdown to an executive-styled PDF binary"""
    # Markdown to HTML
    html_body = markdown.markdown(
        markdown_content,
        extensions=["tables", "fenced_code", "nl2br"],
    )
    # Wrapping html with CSS

    full_html = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>{PREMIUM_PDF_STYLES}</style>
      </head>
      <body>
        {html_body}
      </body>
    </html>
    """

    # Render pdf with binary
    pdf_bytes = HTML(string=full_html).write_pdf()

    if pdf_bytes is None:
        raise RuntimeError("PDF generation failed, received None instead of bytes.")

    return pdf_bytes
