# Use prebuilt texlive image with full LaTeX support
FROM texlive/texlive:latest-full

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-full \
    python3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Create directories first
RUN mkdir -p /app/templates /tmp/cv_output

# Copy application files
COPY app.py .

# Copy templates and assets
COPY templates/resume_balz.tex /app/templates/
COPY templates/assets/profile_pic.jpg /app/templates/

# Expose port
EXPOSE 5001

# Environment variables
ENV FLASK_ENV=production
ENV TEMPLATES_DIR=/app/templates
ENV OUTPUT_DIR=/tmp/cv_output
ENV PORT=5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5001/health')" || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "--timeout", "120", "app:app"]