"""
PDF CV Generation Service
Generates PDF CVs from LaTeX templates with customizable parameters.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import logging
from datetime import datetime
import io
import re

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TEMPLATES_DIR = os.getenv('TEMPLATES_DIR', '/app/templates')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', '/tmp/cv_output')
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
ALLOWED_STYLES = {"modern", "elegant", "bold", "luxe", "slate"}

# Ensure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


class CVGenerationError(Exception):
    """Custom exception for CV generation errors."""
    pass


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
    """Validate the style/theme selection."""
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
    Read the LaTeX template and replace the visible header title and style marker.
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Match header like: {\Large\color{text} Python Developer}
        pattern = r'(\{\\Large\\color\{text\}\s+)[^}]+(\})'
        replacement = r'\g<1>' + title + r'\g<2>'
        content = re.sub(pattern, replacement, content)

        style_pattern = r'(\\newcommand\{\\cvstyle\}\{)[^}]+(\})'
        style_replacement = r'\g<1>' + style + r'\g<2>'
        content = re.sub(style_pattern, style_replacement, content)

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


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'CV Generation Service'
    })


@app.route('/generate-cv', methods=['POST'])
def generate_cv():
    """
    Generate a PDF CV from LaTeX template.
    
    Expected JSON payload:
    {
        "title": "Senior Python Developer",  # Optional - for future use
        "template": "resume_balz",            # Template name (without .tex)
        "style": "modern",                  # Style key (modern, elegant, bold)
        "company": "ACME"                  # Target company (optional)
    }
    
    Returns: PDF file as binary data
    """
    temp_dir = None
    try:
        # Get request data (support both JSON and form data for mobile compatibility)
        if request.is_json:
            data = request.get_json() or {}
        else:
            # Support form data (for direct downloads from mobile)
            data = request.form.to_dict() or {}
        
        title = data.get('title', 'CV')
        template_name = data.get('template', 'resume_balz')
        style = data.get('style', 'modern')
        company = data.get('company', '')
        
        # Validate inputs
        title = validate_title(title)
        style = validate_style(style)
        company = validate_company(company)
        
        # Sanitize template name
        if not all(c.isalnum() or c in '-_' for c in template_name):
            raise CVGenerationError("Invalid template name")
        
        # Find template
        template_path = os.path.join(TEMPLATES_DIR, f'{template_name}.tex')
        if not os.path.exists(template_path):
            raise CVGenerationError(f"Template '{template_name}' not found")
        
        # Create temporary working directory
        temp_dir = tempfile.mkdtemp(prefix='cv_gen_')
        
        # Prepare LaTeX content with custom title
        tex_content = prepare_tex_content(template_path, title, style, company)
        
        # Write prepared template to temp directory
        temp_template = os.path.join(temp_dir, f'{template_name}.tex')
        with open(temp_template, 'w', encoding='utf-8') as f:
            f.write(tex_content)
        
        # Copy profile picture to working directory
        profile_pic = os.path.join(TEMPLATES_DIR, 'profile_pic.jpg')
        if os.path.exists(profile_pic):
            shutil.copy(profile_pic, temp_dir)
        
        # Copy any required assets (like profile picture)
        templates_assets = os.path.join(TEMPLATES_DIR, 'assets')
        if os.path.exists(templates_assets):
            for asset in os.listdir(templates_assets):
                src = os.path.join(templates_assets, asset)
                dst = os.path.join(temp_dir, asset)
                if os.path.isfile(src):
                    shutil.copy(src, dst)
                elif os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
        
        # Generate PDF with new naming format
        title_slug = title.replace(' ', '_')
        date_formatted = datetime.now().strftime("%d.%m.%Y")
        output_filename = f'cv_balz_{title_slug}_{date_formatted}.pdf'
        pdf_path = generate_pdf(temp_template, output_filename, temp_dir)
        
        # Read PDF and prepare response
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        # Check file size
        if len(pdf_data) > MAX_FILE_SIZE:
            raise CVGenerationError("Generated PDF exceeds size limit")
        
        logger.info(f"Successfully generated CV: {output_filename}")
        
        # Return PDF file with the same filename as generated
        response = send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=output_filename
        )
        
        return response
    
    except CVGenerationError as e:
        logger.error(f"CV generation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp directory: {str(e)}")


@app.route('/available-templates', methods=['GET'])
def available_templates():
    """List all available CV templates."""
    try:
        if not os.path.exists(TEMPLATES_DIR):
            return jsonify({'templates': []})
        
        templates = [
            f[:-4] for f in os.listdir(TEMPLATES_DIR)
            if f.endswith('.tex')
        ]
        
        return jsonify({'templates': templates})
    
    except Exception as e:
        logger.error(f"Failed to list templates: {str(e)}")
        return jsonify({'error': 'Failed to list templates'}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # For development only - use gunicorn in production
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5001)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
