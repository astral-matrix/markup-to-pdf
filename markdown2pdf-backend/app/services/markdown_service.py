# markdown_service.py
"""Markdown to HTML conversion with built‑in glyph sanitisation.
This module converts CommonMark+GitHub‑style Markdown into styled HTML that is ready to be
handed to a PDF renderer (WeasyPrint).

Key fixes
----------
1. **Removed** the inline `<style>` injection that ReportLab was treating as literal text.
2. **Added** a `sanitize_glyphs` pass to translate problematic Unicode (curly quotes,
   em/en dashes, etc.) into safe ASCII equivalents when the chosen fonts do not contain
   the glyphs.
3. The function can optionally receive a CSS string so that the caller (our PDF service)
   can inject page / font sizing rules that depend on the user's selections.
4. **Fixed** whitespace preservation in code blocks to ensure proper formatting.
5. **Styled** code blocks with light gray background, rounded corners, and proper padding.
6. **Added** support for nested ordered and unordered lists with proper indentation.
"""
from __future__ import annotations

import re
import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.extra import ExtraExtension
from markdown.extensions import Extension
from markdown.inlinepatterns import SubstituteTagInlineProcessor

# Import font service to get the monospace font
from app.services.font_service import font_service

# ---------- helpers ---------------------------------------------------------

# This is a dictionary of glyphs that are problematic in markdown and need to be replaced with safe ASCII equivalents.
# The key is the problematic glyph, and the value is the safe ASCII equivalent.
# it also handles cases were optional backslashes are found in chatGPT's markdown output:
#   - if a tilde is inside markdown formatting, chatGPT will output it as "\~"
#   - if an ampersand is inside markdown formatting, chatGPT will output it as "\&"
# this is a problem because the backslash will remain intact after the markdown to HTML conversion, and it will appear in the PDF output
# This is an imperfect solution, because in some cases (inside code blocks) a backslashed character should be preserved.
# TODO: add conditional logic to ignore backslashes inside code blocks.

_GLYPH_MAP: dict[str, str] = {
    "\u2013": "-",   # en dash
    "\u2014": "-",   # em dash
    "\u00a0": " ",  # nbsp → normal space
    "\u2018": "'",   # left single quote
    "\u2019": "'",   # right single quote
    "\u201c": '"',   # left double quote
    "\u201d": '"',   # right double quote
    "\\~": '~',   # tilde
    r"\~": '~',   # tilde
    "\\&": '&amp;',   # ampersand
    r"\&": '&amp;',   # ampersand
    r"\$": '$',   # dollar sign
    r"\#": '#',   # hash
    "\\#": '#',   # hash
    "\\*": '*',   # asterisk
    "\\_": '_',   # underscore
    "\\+": '+',   # plus
    "\\-": '-',   # dash
    "\\=": '=',   # equals

}

def sanitize_glyphs(text: str) -> str:
    for bad, good in _GLYPH_MAP.items():
        text = text.replace(bad, good)
    return text

def optimize_for_pdf_wrapping(html: str) -> str:
    """Post-process HTML to ensure better text wrapping in WeasyPrint/PDF generation."""
    # Add zero-width spaces after certain characters to encourage breaking
    # This helps WeasyPrint break long lines at better positions
    
    # Add break opportunities after commas, semicolons, and other punctuation in code blocks
    def add_break_opportunities(match):
        code_content = match.group(1)
        # Add zero-width space (&#8203;) after punctuation to encourage line breaks
        code_content = re.sub(r'([,;])', r'\1&#8203;', code_content)
        code_content = re.sub(r'(\[)', r'\1&#8203;', code_content)
        code_content = re.sub(r'(\()', r'\1&#8203;', code_content)
        # Add break opportunities in long quoted strings
        code_content = re.sub(r'(&quot;[^&]{10,}?)([^&]{5})', r'\1&#8203;\2', code_content)
        return f'<code>{code_content}</code>'
    
    # Apply to code blocks
    html = re.sub(r'<code>(.*?)</code>', add_break_opportunities, html, flags=re.DOTALL)
    
    return html

def ensure_nested_lists(html: str) -> str:
    """Ensure nested lists have proper class for styling in PDF."""
    # First, add a class to all nested lists - this regex handles both basic list items and those with formatted content
    html = re.sub(r'(<li>(?:.*?<\/[^>]+>)?\s*<[ou]l)', r'\1 class="nested-list"', html, flags=re.DOTALL)
    
    # Handle specific case where list item starts with formatted text like <strong>
    html = re.sub(r'(<li>\s*<p>(?:.*?<\/[^>]+>)?\s*<\/p>\s*<[ou]l)', 
                  r'\1 class="nested-list"', html, flags=re.DOTALL)
    
    # Process HTML as a DOM tree to properly handle nesting
    # This is a simplified approach using string operations
    all_list_starts = re.finditer(r'<([ou])l(?: class="nested-list")?', html)
    all_list_ends = re.finditer(r'</([ou])l>', html)
    
    # Track nesting level for each list tag
    list_positions = []
    for match in all_list_starts:
        list_positions.append((match.start(), "open", match.group(1)))
    
    for match in all_list_ends:
        list_positions.append((match.end(), "close", match.group(1)))
    
    # Sort by position
    list_positions.sort(key=lambda x: x[0])
    
    # Calculate nesting level at each point
    modified_html = html
    offset = 0
    current_level = 0
    list_with_levels = []
    
    for pos, action, list_type in list_positions:
        if action == "open":
            current_level += 1
            # Only add data-level to lists after the first level
            if current_level > 1:
                list_with_levels.append((pos, list_type, current_level))
        else:  # action == "close"
            current_level = max(0, current_level - 1)
    
    # Apply data-level attributes
    for pos, list_type, level in list_with_levels:
        actual_pos = pos + offset
        
        # Find the end of this tag
        tag_end = modified_html.find('>', actual_pos)
        
        # Check if this is a nested list (should have class="nested-list")
        tag_content = modified_html[actual_pos:tag_end]
        
        if 'class="nested-list"' in tag_content:
            # Already has class, add or update data-level
            if 'data-level=' in tag_content:
                # Update existing data-level
                modified_tag = re.sub(r'data-level="[^"]*"', f'data-level="{level-1}"', tag_content)
            else:
                # Add data-level
                modified_tag = tag_content + f' data-level="{level-1}"'
        else:
            # Add both class and data-level
            if '<ul' in tag_content or '<ol' in tag_content:
                modified_tag = f'<{list_type}l class="nested-list" data-level="{level-1}"'
            else:
                # This shouldn't happen, but just in case
                modified_tag = tag_content
                
        # Apply the modification
        if modified_tag != tag_content:
            modified_html = modified_html[:actual_pos] + modified_tag + modified_html[tag_end:]
            offset += len(modified_tag) - len(tag_content)
    
    return modified_html

# Custom extension to handle line breaks
# TODO: VERIFY THIS IS STILL NEEDED
class LineBreakExtension(Extension):
    """Extension to convert newlines to <br> tags."""
    def extendMarkdown(self, md):
        # This pattern matches newlines not in code blocks
        pattern = r'(?<!\n)\n(?!\n)'  # Match single newlines
        processor = SubstituteTagInlineProcessor(pattern, 'br')
        md.inlinePatterns.register(processor, 'linebreaks', 175)  # Priority higher than nl2br

class MarkdownService:
    """Singleton service that converts Markdown to HTML."""

    # to generate new pygment stylesheet run: 
    # pygmentize -S lightbulb -f html -a .code-highlight > code.css
    _extensions = [
        TableExtension(),
        CodeHiliteExtension(css_class="code-highlight", pygments_style="native", linenums=False),
        #CodeHiliteExtension(css_class="code-highlight", pygments_style="monokai", linenums=False),
        FencedCodeExtension(),  # Explicitly add fenced code extension
        ExtraExtension(),       # Add Extra extension which includes proper list support
        LineBreakExtension(),   # Add our custom line break extension
    ]

    def preprocess_nested_lists(self, markdown_text: str) -> str:
        """
        Preprocess markdown text to ensure proper handling of nested lists.
        This specifically handles 2-space indentation that indicates nested lists
        and fixes cases where blank lines appear between parent and nested items.
        """
        lines = markdown_text.split('\n')
        processed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is a parent list item
            parent_list_match = re.match(r'^([*+-]|\d+\.)\s', line)
            
            if parent_list_match:
                # This is a parent list item - add it
                processed_lines.append(line)
                
                # Check ahead for blank line followed by nested list
                if i + 2 < len(lines) and lines[i+1].strip() == '':
                    # Look for a nested list item after the blank line
                    potential_nested = lines[i+2]
                    nested_match = re.match(r'^(\s+)([*+-]|\d+\.)\s', potential_nested)
                    
                    if nested_match:
                        # Found a nested list item after a blank line - skip the blank line
                        i += 1  # Skip the blank line
                
            elif re.match(r'^(\s+)([*+-]|\d+\.)\s', line):
                # This is a nested list item
                # Calculate indentation level (each 2 spaces = 1 level)
                indent_match = re.match(r'^(\s+)', line)
                indentation = indent_match.group(1)
                indent_level = len(indentation) // 2
                
                # Use 4 spaces for each level in the output for proper markdown parsing
                new_indentation = '    ' * indent_level
                processed_lines.append(new_indentation + line.lstrip())
            else:
                # Not a list item - add as is
                processed_lines.append(line)
            
            i += 1  # Move to next line
        
        # Join all lines back together
        return '\n'.join(processed_lines)

    def convert_to_html(self, markdown_text: str, css: str | None = None) -> str:
        """Return **full HTML** (optionally wrapped with a `<style>` tag)."""
        # Preprocess markdown to handle nested lists
        markdown_text = self.preprocess_nested_lists(markdown_text)
        
        cleaned = sanitize_glyphs(markdown_text)
        
        # Convert markdown to HTML
        html_body = markdown.markdown(cleaned, extensions=self._extensions)
        
        # Post-process for PDF-specific text wrapping
        html_body = optimize_for_pdf_wrapping(html_body)
        
        # Ensure nested lists are properly styled
        html_body = ensure_nested_lists(html_body)
        
        # Handle paragraph breaks more explicitly to ensure they render in PDF
        # This replaces double newlines with properly spaced paragraphs
        html_body = re.sub(r'</p>\s*<p>', '</p>\n\n<p>', html_body)
        
        # Ensure single line breaks within paragraphs are preserved (CommonMark treats single newlines as spaces)
        # We need to do this after markdown conversion for content not in code blocks
        html_body = re.sub(r'([^>])\n([^<])', r'\1<br>\n\2', html_body)
        
        # Get the monospace font for CSS
        monospace_font = font_service.get_monospace_font()
        
        if css:
            return f"""
<!DOCTYPE html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <style>
    {css}
    </style>
  </head>
  <body>
    {html_body}
  </body>
</html>"""
        # Caller will inject CSS later
        return html_body


# Expose a ready‑to‑use instance
markdown_service = MarkdownService()