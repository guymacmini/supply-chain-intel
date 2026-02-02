"""PDF export utility for research reports using ReportLab."""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents


class NumberedCanvas:
    """Custom canvas for page numbering."""
    
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc
    
    def __getattr__(self, name):
        return getattr(self.canvas, name)
    
    def showPage(self):
        self.canvas.showPage()
    
    def save(self):
        num_pages = self.canvas.getPageNumber()
        for page_num in range(1, num_pages + 1):
            self.canvas.setPageNum(page_num)
            self.draw_page_number(page_num, num_pages)
        self.canvas.save()
    
    def draw_page_number(self, page_num, num_pages):
        # Draw page number at bottom center
        self.canvas.setFont("Helvetica", 9)
        self.canvas.setFillColor(colors.grey)
        text = f"Supply Chain Intelligence Report - Page {page_num} of {num_pages}"
        width = letter[0]
        self.canvas.drawCentredText(width / 2, 0.75 * inch, text)


class PDFExporter:
    """Export markdown research reports to professional PDF format using ReportLab."""

    def __init__(self):
        """Initialize the PDF exporter."""
        self.styles = self._create_styles()

    def _create_styles(self):
        """Create custom paragraph styles for the PDF."""
        styles = getSampleStyleSheet()
        
        # Title style
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a365d'),
            borderWidth=2,
            borderColor=colors.HexColor('#e53e3e'),
            borderPadding=(0, 0, 8, 0),
        ))
        
        # Heading styles
        styles.add(ParagraphStyle(
            name='CustomHeading1',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=16,
            spaceBefore=24,
            textColor=colors.HexColor('#2d3748'),
            keepWithNext=True,
        ))
        
        styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=18,
            textColor=colors.HexColor('#4a5568'),
            keepWithNext=True,
        ))
        
        # TLDR style
        styles.add(ParagraphStyle(
            name='TLDR',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=20,
            rightIndent=20,
            spaceBefore=12,
            spaceAfter=12,
            borderWidth=2,
            borderColor=colors.HexColor('#f6ad55'),
            borderPadding=12,
            backColor=colors.HexColor('#fffbeb'),
        ))
        
        # Body text
        styles.add(ParagraphStyle(
            name='CustomBodyText',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            spaceAfter=6,
            alignment=0,  # Left justified
        ))
        
        # List item style
        styles.add(ParagraphStyle(
            name='CustomListItem',
            parent=styles['Normal'],
            fontSize=11,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=3,
        ))
        
        return styles

    def _clean_text(self, text: str) -> str:
        """Clean text for PDF rendering."""
        # Remove markdown formatting that we don't handle
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)      # Italic
        text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', text)  # Code
        
        # Handle emoji indicators specially
        emoji_map = {
            '🔴': '<font color="red">🔴 CRITICAL</font>',
            '🟡': '<font color="#D69E2E">🟡 WATCH</font>',
            '🟢': '<font color="green">🟢 ADEQUATE</font>',
        }
        
        for emoji, replacement in emoji_map.items():
            text = text.replace(emoji, replacement)
        
        return text

    def _parse_markdown_to_elements(self, markdown_content: str) -> list:
        """Parse markdown content and convert to ReportLab elements."""
        elements = []
        lines = markdown_content.split('\n')
        
        current_table = []
        in_table = False
        current_list_items = []
        in_list = False
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:  # Empty line
                if in_table and current_table:
                    # End current table
                    elements.append(self._create_table(current_table))
                    current_table = []
                    in_table = False
                elif in_list and current_list_items:
                    # End current list
                    elements.extend(self._create_list(current_list_items))
                    current_list_items = []
                    in_list = False
                else:
                    elements.append(Spacer(1, 6))
                i += 1
                continue
            
            # Headers
            if line.startswith('# '):
                title = self._clean_text(line[2:])
                elements.append(Paragraph(title, self.styles['CustomTitle']))
                elements.append(Spacer(1, 12))
                
            elif line.startswith('## '):
                heading = self._clean_text(line[3:])
                # Check if this is TLDR section
                if 'tldr' in heading.lower():
                    # Collect TLDR content
                    tldr_content = []
                    j = i + 1
                    while j < len(lines) and not lines[j].startswith('#'):
                        if lines[j].strip():
                            tldr_content.append(lines[j].strip())
                        j += 1
                    
                    if tldr_content:
                        tldr_text = ' '.join(tldr_content)
                        tldr_text = self._clean_text(tldr_text)
                        elements.append(Paragraph(f"<b>{heading}</b>", self.styles['TLDR']))
                        elements.append(Paragraph(tldr_text, self.styles['TLDR']))
                        elements.append(Spacer(1, 12))
                        i = j - 1
                    else:
                        elements.append(Paragraph(heading, self.styles['CustomHeading1']))
                else:
                    elements.append(Paragraph(heading, self.styles['CustomHeading1']))
                    
            elif line.startswith('### '):
                heading = self._clean_text(line[4:])
                elements.append(Paragraph(heading, self.styles['CustomHeading2']))
                
            # Tables
            elif '|' in line:
                if not in_table:
                    in_table = True
                current_table.append(line)
                
            # Lists
            elif line.startswith('- ') or line.startswith('* ') or re.match(r'^\d+\.\s', line):
                if not in_list:
                    in_list = True
                current_list_items.append(line)
                
            # Regular paragraph
            else:
                if in_table and current_table:
                    # End current table
                    elements.append(self._create_table(current_table))
                    current_table = []
                    in_table = False
                elif in_list and current_list_items:
                    # End current list
                    elements.extend(self._create_list(current_list_items))
                    current_list_items = []
                    in_list = False
                
                text = self._clean_text(line)
                elements.append(Paragraph(text, self.styles['CustomBodyText']))
            
            i += 1
        
        # Handle remaining content
        if in_table and current_table:
            elements.append(self._create_table(current_table))
        elif in_list and current_list_items:
            elements.extend(self._create_list(current_list_items))
        
        return elements

    def _create_table(self, table_lines: list) -> Table:
        """Create a ReportLab table from markdown table lines."""
        if not table_lines:
            return None
        
        # Parse table data
        table_data = []
        header_processed = False
        
        for line in table_lines:
            if '|' in line:
                # Split by | and clean up
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                if cells and not (header_processed and all(c in '-:' for c in ''.join(cells))):
                    # Clean cell content
                    cells = [self._clean_text(cell) for cell in cells]
                    table_data.append(cells)
                    if not header_processed:
                        header_processed = True
        
        if not table_data:
            return None
        
        # Create table
        table = Table(table_data, hAlign='LEFT')
        
        # Apply styling
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f7fafc')),  # Header background
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),   # Header text
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),              # Header font
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ]
        
        # Alternate row colors
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')))
        
        table.setStyle(TableStyle(table_style))
        
        return KeepTogether([Spacer(1, 6), table, Spacer(1, 6)])

    def _create_list(self, list_lines: list) -> list:
        """Create ReportLab paragraphs for list items."""
        elements = []
        for line in list_lines:
            # Remove list markers and clean text
            if line.startswith('- ') or line.startswith('* '):
                text = self._clean_text(line[2:])
                elements.append(Paragraph(f"• {text}", self.styles['CustomListItem']))
            elif re.match(r'^\d+\.\s', line):
                text = self._clean_text(re.sub(r'^\d+\.\s', '', line))
                number = re.match(r'^(\d+)\.', line).group(1)
                elements.append(Paragraph(f"{number}. {text}", self.styles['CustomListItem']))
        
        return elements

    def export_to_pdf(self, 
                     markdown_content: str, 
                     output_path: Path,
                     title: Optional[str] = None) -> Path:
        """
        Export markdown content to PDF.
        
        Args:
            markdown_content: Raw markdown content
            output_path: Path where PDF should be saved
            title: Document title (optional)
            
        Returns:
            Path to the generated PDF file
        """
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            leftMargin=72,
            rightMargin=72,
            topMargin=100,
            bottomMargin=100,
            title=title or "Supply Chain Intelligence Report"
        )
        
        # Parse markdown content
        elements = self._parse_markdown_to_elements(markdown_content)
        
        # Add footer with generation date
        generation_date = datetime.now().strftime("%B %d, %Y")
        footer = Paragraph(
            f"<para align='center'><font size='8' color='gray'>"
            f"Generated on {generation_date} | Supply Chain Intelligence Platform"
            f"</font></para>",
            self.styles['Normal']
        )
        
        # Build PDF with custom page numbering
        def numbered_page(canvas, doc):
            canvas.saveState()
            # Footer text
            canvas.setFont('Helvetica', 8)
            canvas.setFillGray(0.5)
            page_num = canvas.getPageNumber()
            text = f"Supply Chain Intelligence Report - Page {page_num}"
            canvas.drawCentredString(A4[0]/2, 50, text)
            canvas.restoreState()
        
        doc.build(elements, onFirstPage=numbered_page, onLaterPages=numbered_page)
        
        return output_path

    def _extract_title(self, markdown_content: str) -> str:
        """Extract title from markdown content."""
        # Try to find the first H1 heading
        h1_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Fallback: look for filename in content or use default
        filename_match = re.search(r'(\w+_\w+_\d{4}_\d{2}_\d{2}_\d{6})', markdown_content)
        if filename_match:
            return f"Research Report - {filename_match.group(1)}"
        
        return "Supply Chain Intelligence Report"

    def export_research_file(self, 
                           research_file_path: Path, 
                           output_dir: Optional[Path] = None) -> Path:
        """
        Export a research markdown file to PDF.
        
        Args:
            research_file_path: Path to the markdown research file
            output_dir: Output directory (defaults to same dir as source)
            
        Returns:
            Path to the generated PDF file
        """
        if not research_file_path.exists():
            raise FileNotFoundError(f"Research file not found: {research_file_path}")
        
        # Read markdown content
        with open(research_file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Determine output path
        if output_dir is None:
            output_dir = research_file_path.parent
        
        pdf_filename = research_file_path.stem + '.pdf'
        output_path = output_dir / pdf_filename
        
        # Extract title
        title = self._extract_title(markdown_content)
        
        return self.export_to_pdf(markdown_content, output_path, title)