#!/usr/bin/env python3
"""
Minimal HTTP Server for CV Generation
Lightweight alternative to Docker/Flask that runs CV generation per request.
Uses built-in HTTP server - no external dependencies except Flask-CORS for CORS support.

Usage:
    python3 http_server.py --port 5000
    # Then POST to http://localhost:5000/generate-cv with JSON body:
    # {"title": "Senior Developer", "template": "resume_balz"}
"""

import argparse
import json
import logging
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import sys
import traceback

# Import the CV generation module
from generate_cv import generate_cv, CVGenerationError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CVRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for CV generation."""
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(format % args)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.send_health_check()
        elif parsed_path.path == '/available-templates':
            self.send_available_templates()
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/generate-cv':
            self.handle_generate_cv()
        else:
            self.send_error_response(404, "Endpoint not found")
    
    def handle_generate_cv(self):
        """Handle CV generation request."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Parse JSON
            try:
                data = json.loads(body.decode('utf-8')) if body else {}
            except json.JSONDecodeError:
                self.send_error_response(400, "Invalid JSON in request body")
                return
            
            # Extract parameters
            title = data.get('title', 'CV')
            template = data.get('template', 'resume_balz')
            output_dir = data.get('output_dir')
            
            logger.info(f"Generating CV: template={template}, title={title}")
            
            # Generate PDF
            pdf_path = generate_cv(
                template_name=template,
                title=title,
                output_dir=output_dir
            )
            
            # Read PDF file
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Length', str(len(pdf_data)))
            self.send_header('Content-Disposition', f'attachment; filename="{pdf_path.name}"')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(pdf_data)
            
            logger.info(f"✓ Successfully sent PDF: {pdf_path.name}")
        
        except CVGenerationError as e:
            logger.error(f"CV generation error: {str(e)}")
            self.send_error_response(400, str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            self.send_error_response(500, "Internal server error")
    
    def send_health_check(self):
        """Send health check response."""
        response = {
            'status': 'healthy',
            'service': 'CV Generation Service (Standalone)'
        }
        self.send_json_response(200, response)
    
    def send_available_templates(self):
        """Send list of available templates."""
        try:
            templates_dir = Path(__file__).parent / 'templates'
            templates = [
                f.stem for f in templates_dir.glob('*.tex')
            ] if templates_dir.exists() else []
            
            response = {'templates': templates}
            self.send_json_response(200, response)
        
        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            self.send_error_response(500, "Failed to list templates")
    
    def send_json_response(self, status_code, data):
        """Send JSON response."""
        response_body = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response_body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response_body)
    
    def send_error_response(self, status_code, error_message):
        """Send error response."""
        response = {'error': error_message}
        self.send_json_response(status_code, response)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def main():
    """Start the HTTP server."""
    parser = argparse.ArgumentParser(
        description='HTTP server for CV generation'
    )
    
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    
    args = parser.parse_args()
    
    server_address = (args.host, args.port)
    httpd = HTTPServer(server_address, CVRequestHandler)
    
    logger.info(f"Starting CV Generation Server at http://{args.host}:{args.port}")
    logger.info("Endpoints:")
    logger.info("  POST /generate-cv - Generate CV")
    logger.info("  GET  /health - Health check")
    logger.info("  GET  /available-templates - List templates")
    logger.info("\nPress Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
