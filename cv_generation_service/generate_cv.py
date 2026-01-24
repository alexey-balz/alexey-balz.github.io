#!/usr/bin/env python3
"""
CV Generation CLI Script
Generates PDF CVs from LaTeX templates without requiring Docker or Flask.
Can be run directly from command line or scheduled via cron.

Usage:
    python3 generate_cv.py --template resume_balz --title "Senior Developer"
    python3 generate_cv.py --template resume_balz  # Uses default title
"""

import argparse
import os
import tempfile
import shutil
import subprocess
import logging
import re
from pathlib import Path
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVGenerationError(Exception):
    """Custom exception for CV generation errors."""
    pass


ALLOWED_STYLES = {"modern", "elegant", "bold", "luxe", "slate"}


def get_base_dir():
    """Get the base directory of the service."""
    return Path(__file__).parent.resolve()


def validate_title(title):
    """Validate and sanitize the CV title."""
    if not title:
        raise CVGenerationError("Title parameter is required")
    
    # Allow only alphanumeric, spaces, and basic punctuation
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_')
    if not all(c in allowed_chars for c in title):
        raise CVGenerationError("Title contains invalid characters")
    
    if len(title) > 200:
        raise CVGenerationError("Title is too long (max 200 characters)")
    
    return title.strip()


def validate_style(style):
    """Validate the LaTeX style theme."""
    if not style:
        return "modern"

    style = style.strip().lower()
    if style not in ALLOWED_STYLES:
        raise CVGenerationError(f"Style must be one of: {', '.join(sorted(ALLOWED_STYLES))}")

    return style


def validate_company(company):
    """Validate optional target company label."""
    if company is None:
        return ""

    company = company.strip()
    if not company:
        return ""

    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.,&()'/")
    if not all(c in allowed_chars for c in company):
        raise CVGenerationError("Company contains invalid characters")

    if len(company) > 120:
        raise CVGenerationError("Company is too long (max 120 characters)")

    return company


def prepare_tex_content(template_path, title, style, company):
    r"""
    Read the LaTeX template and replace the title and style in the CV header.
    Looks for title: {\Large\color{text} ...}
    Looks for style: \newcommand{\cvstyle}{modern}
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the hardcoded title in the header section
        # Pattern matches: {\Large\color{text} [ANY TEXT]} 
        pattern = r'(\{\\Large\\color\{text\}\s+)[^}]+(\})'
        replacement = r'\g<1>' + title + r'\g<2>'
        content = re.sub(pattern, replacement, content)

        # Replace style marker
        style_pattern = r'(\\newcommand\{\\cvstyle\}\{)[^}]+(\})'
        style_replacement = r'\g<1>' + style + r'\g<2>'
        content = re.sub(style_pattern, style_replacement, content)

        # Replace company marker
        company_pattern = r'(\\newcommand\{\\company\}\{)[^}]*(\})'
        company_replacement = r'\g<1>' + company + r'\g<2>'
        content = re.sub(company_pattern, company_replacement, content)
        
        return content
    except Exception as e:
        raise CVGenerationError(f"Failed to read template: {str(e)}")


def generate_pdf(template_path, output_filename, working_dir):
    """
    Compile LaTeX template to PDF using pdflatex.
    """
    try:
        # Run pdflatex
        cmd = [
            'pdflatex',
            '-interaction=nonstopmode',
            '-output-directory=' + working_dir,
            '-jobname=' + Path(output_filename).stem,
            template_path
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Check if PDF was created (pdflatex may return non-zero for warnings)
        pdf_path = os.path.join(working_dir, Path(output_filename).stem + '.pdf')
        if not os.path.exists(pdf_path):
            logger.error(f"pdflatex stderr: {result.stderr}")
            logger.error(f"pdflatex stdout: {result.stdout}")
            raise CVGenerationError("PDF file was not generated")
        
        return pdf_path
    
    except subprocess.TimeoutExpired:
        raise CVGenerationError("LaTeX compilation timed out")
    except Exception as e:
        raise CVGenerationError(f"PDF generation failed: {str(e)}")


def generate_cv(template_name='resume_balz', title='CV', style='modern', company='', output_dir=None):
    """
    Generate a PDF CV from LaTeX template.
    
    Args:
        template_name: Name of the template (without .tex extension)
        title: Title for the CV document
        style: Visual style to apply (modern, elegant, bold)
        output_dir: Directory to save the PDF (defaults to ./cv_output/)
    
    Returns:
        Path to the generated PDF file
    """
    base_dir = get_base_dir()
    templates_dir = base_dir / 'templates'
    temp_dir = None
    
    # Set default output directory (use cv_output to avoid permission issues)
    if output_dir is None:
        output_dir = base_dir / 'cv_output'
    else:
        output_dir = Path(output_dir)
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Validate inputs
        title = validate_title(title)
        style = validate_style(style)
        company = validate_company(company)
        
        # Sanitize template name
        if not all(c.isalnum() or c in '-_' for c in template_name):
            raise CVGenerationError("Invalid template name")
        
        # Find template
        template_path = templates_dir / f'{template_name}.tex'
        if not template_path.exists():
            raise CVGenerationError(f"Template '{template_name}' not found at {template_path}")
        
        # Create temporary working directory
        temp_dir = tempfile.mkdtemp(prefix='cv_gen_')
        logger.info(f"Using temporary directory: {temp_dir}")
        
        # Prepare LaTeX content with custom title
        tex_content = prepare_tex_content(str(template_path), title, style, company)
        
        # Write prepared template to temp directory
        temp_template = Path(temp_dir) / f'{template_name}.tex'
        with open(temp_template, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        
        # Copy profile picture to working directory
        profile_pic = templates_dir / 'profile_pic.jpg'
        if profile_pic.exists():
            shutil.copy(profile_pic, temp_dir)
            logger.info("Copied profile picture")
        
        # Copy any required assets
        templates_assets = templates_dir / 'assets'
        if templates_assets.exists():
            for asset in os.listdir(templates_assets):
                src = templates_assets / asset
                dst = Path(temp_dir) / asset
                if src.is_file():
                    shutil.copy(src, dst)
                elif src.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
            logger.info("Copied assets")
        
        # Generate PDF with new naming format
        title_slug = title.replace(' ', '_')
        date_formatted = datetime.now().strftime("%d.%m.%Y")
        output_filename = f'cv_balz_{title_slug}_{date_formatted}.pdf'
        pdf_path = generate_pdf(str(temp_template), output_filename, temp_dir)
        
        # Copy PDF to output directory
        final_pdf_path = output_dir / output_filename
        shutil.copy(pdf_path, final_pdf_path)
        
        logger.info(f"✓ Successfully generated CV: {final_pdf_path}")
        
        return final_pdf_path
    
    except CVGenerationError as e:
        logger.error(f"CV generation error: {str(e)}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise CVGenerationError(f"Unexpected error: {str(e)}")
    
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temporary directory")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {str(e)}")


def main():
    """Command-line interface for CV generation."""
    parser = argparse.ArgumentParser(
        description='Generate a PDF CV from LaTeX template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with default title
  python3 generate_cv.py

  # Generate with custom title
  python3 generate_cv.py --title "Senior Python Developer"

  # Use specific template
  python3 generate_cv.py --template my_template --title "Title"

  # Save to custom output directory
  python3 generate_cv.py --output /path/to/output
        """
    )
    
    parser.add_argument(
        '--template',
        default='resume_balz',
        help='Template name without .tex extension (default: resume_balz)'
    )
    
    parser.add_argument(
        '--title',
        default='CV',
        help='CV title/subtitle (default: CV)'
    )

    parser.add_argument(
        '--style',
        default='modern',
        help='CV style (modern, elegant, bold)'
    )

    parser.add_argument(
        '--company',
        help='Target company label (optional)'
    )
    
    parser.add_argument(
        '--output',
        help='Output directory for PDF (default: ./output/)'
    )
    
    args = parser.parse_args()
    
    try:
        pdf_path = generate_cv(
            template_name=args.template,
            title=args.title,
            style=args.style,
            company=args.company,
            output_dir=args.output
        )
        print(f"\n✓ PDF generated successfully: {pdf_path}")
        return 0
    
    except CVGenerationError as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        return 1
    
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
