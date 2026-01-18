# CV Generation Service - Setup Guide

A REST API service for generating PDF CVs from LaTeX templates. This service runs on your NAS and can be called from your website to dynamically generate and download CVs.

## Quick Start (3 Steps)

### Step 1: Copy Files to Your NAS

```bash
# On your NAS, create service directory
mkdir -p ~/cv-generation-service/templates/assets

# Copy your LaTeX template and assets
cp resume_balz.tex ~/cv-generation-service/templates/
cp profile_pic.jpg ~/cv-generation-service/templates/assets/

# Copy service files (from this repository)
cp app.py ~/cv-generation-service/
cp requirements.txt ~/cv-generation-service/
cp Dockerfile ~/cv-generation-service/
cp docker-compose.yml ~/cv-generation-service/
```

### Step 2: Build and Run with Docker

```bash
cd ~/cv-generation-service

# Build the Docker image
docker-compose build

# Start the service
docker-compose up -d

# Check status
docker-compose ps
```

### Step 3: Configure Your Website

In `cv.html`, update the API endpoint:

```javascript
// Change this line from:
const CV_GENERATOR_API = 'http://localhost:5000';

// To your NAS IP (e.g., if NAS is at 192.168.1.100):
const CV_GENERATOR_API = 'http://192.168.1.100:5000';
```

Done! Your website will now generate PDFs dynamically from your NAS.

---

## Architecture

```
Website (GitHub Pages)
    ↓ (HTTP request on button click)
    ↓
NAS Server (Docker Container)
    ↓
Flask API (app.py)
    ↓
LaTeX Engine (pdflatex)
    ↓
PDF Generation
    ↓ (Returns PDF to browser)
User Downloads CV
```

## API Endpoints

### 1. Generate CV
```
POST /generate-cv
Content-Type: application/json

{
  "template": "resume_balz",
  "title": "CV"
}
```

Returns: PDF file as binary data with filename `Alexey_Balz_CV_YYYYMMDD.pdf`

### 2. Health Check
```
GET /health
```

Returns: `{"status": "healthy", "timestamp": "...", "service": "CV Generation Service"}`

### 3. List Templates
```
GET /available-templates
```

Returns: `{"templates": ["resume_balz", ...]}`

## API Testing

Test locally with curl:

```bash
# Test health
curl http://localhost:5000/health

# Generate CV
curl -X POST http://localhost:5000/generate-cv \
  -H "Content-Type: application/json" \
  -d '{"template": "resume_balz"}' \
  --output test_cv.pdf

# List templates
curl http://localhost:5000/available-templates
```

## Configuration

### Environment Variables (in docker-compose.yml)

```yaml
FLASK_ENV: production          # Set to 'development' for debugging
TEMPLATES_DIR: /app/templates  # Where .tex files are stored
OUTPUT_DIR: /tmp/cv_output     # Where to store temp files
PORT: 5000                     # API port
```

### File Structure

```
cv-generation-service/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Compose configuration
├── templates/                  # LaTeX templates
│   ├── resume_balz.tex        # Your CV template
│   └── assets/                # Assets (images, etc)
│       └── profile_pic.jpg    # Your profile picture
└── output/                     # Generated PDFs (for debugging)
```

## Service Management

### Start Service
```bash
docker-compose up -d
```

### Stop Service
```bash
docker-compose down
```

### Restart Service
```bash
docker-compose restart cv-generator
```

### View Logs
```bash
docker-compose logs -f cv-generator
```

### Check Status
```bash
docker-compose ps
```

## Website Integration Details

### How It Works

1. User clicks "View and Download CV" button on your website
2. JavaScript makes POST request to `CV_GENERATOR_API/generate-cv`
3. NAS service receives request and:
   - Reads your LaTeX template
   - Copies required assets (profile picture)
   - Compiles with pdflatex
   - Returns PDF as binary data
4. JavaScript displays PDF in iframe
5. User can download with "Download CV" button

### Fallback to Static PDF

If API is unavailable, the website automatically falls back to a static PDF file at `files/cv.pdf`. This ensures your CV is always accessible.

## Adding Multiple CV Versions

To support multiple CV templates:

### Step 1: Add New Template
```bash
cp my_resume_short.tex ~/cv-generation-service/templates/
cp my_resume_detailed.tex ~/cv-generation-service/templates/
```

### Step 2: Restart Service
```bash
docker-compose restart cv-generator
```

### Step 3: Call Different Templates from Website
```javascript
// Generate short version
const response = await fetch(`${CV_GENERATOR_API}/generate-cv`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        template: 'my_resume_short'  // Different template
    })
});
```

## Troubleshooting

### Service won't start

Check Docker logs:
```bash
docker-compose logs cv-generator
```

Common issues:
- **Port 5000 already in use**: Change port in `docker-compose.yml` and update website config
- **Template not found**: Ensure `.tex` file is in `templates/` directory
- **Missing profile picture**: Add `profile_pic.jpg` to `templates/assets/`

### PDF generation fails

```bash
# Test LaTeX locally
pdflatex -interaction=nonstopmode templates/resume_balz.tex

# Check LaTeX syntax errors
cat resume_balz.log
```

### CORS errors from website

Ensure:
1. API endpoint is correct in `cv.html`
2. CORS is enabled in `app.py` (it is by default with `CORS(app)`)
3. NAS port 5000 is accessible from your network

### API not reachable from website

```bash
# Test from local machine
ping YOUR_NAS_IP
curl http://YOUR_NAS_IP:5000/health

# Check firewall
sudo ufw allow 5000
```

## Production Setup

### Using Systemd for Auto-Start

Create `/etc/systemd/system/cv-generator.service`:

```ini
[Unit]
Description=CV Generation Service
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/root/cv-generation-service
ExecStart=/usr/bin/docker-compose up
ExecStop=/usr/bin/docker-compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cv-generator
sudo systemctl start cv-generator
sudo systemctl status cv-generator
```

### Using HTTPS (Recommended for Production)

Use Nginx reverse proxy on your NAS:

```nginx
server {
    listen 443 ssl;
    server_name cv-api.yourdomain.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then update website:
```javascript
const CV_GENERATOR_API = 'https://cv-api.yourdomain.com';
```

## Performance

- **Compilation time**: ~10-15 seconds per PDF
- **Cache strategy**: PDFs are not cached (generated fresh each time)
- **Max file size**: 50MB
- **Timeout**: 120 seconds

To add caching, modify `app.py` to store PDFs with a TTL.

## Security Considerations

✓ Input validation (template names, titles)
✓ File size limits
✓ CORS enabled (can be restricted if needed)
✓ Timeout protection

For production:
- Use HTTPS with valid certificates
- Implement rate limiting
- Restrict CORS to trusted domains
- Use firewall rules

## Updating Your CV

To update your CV:

```bash
# 1. Edit your LaTeX file locally
nano resume_balz.tex

# 2. Copy updated file to NAS
cp resume_balz.tex ~/cv-generation-service/templates/

# 3. Restart service
cd ~/cv-generation-service
docker-compose restart cv-generator

# 4. Test
curl -X POST http://localhost:5000/generate-cv \
  -H "Content-Type: application/json" \
  -d '{"template": "resume_balz"}' \
  --output test.pdf
```

## Monitoring

Check service health regularly:

```bash
# Manual check
curl http://localhost:5000/health

# Add to crontab for automated monitoring
*/5 * * * * curl http://localhost:5000/health || systemctl restart cv-generator
```

## Next Steps

- [x] Set up Docker and NAS directory
- [x] Copy templates and assets
- [x] Build Docker image
- [x] Start service
- [x] Test API locally
- [ ] Update `cv.html` with your NAS IP
- [ ] Test from website
- [ ] Deploy to production with HTTPS

## Support

For issues or questions:
1. Check service logs: `docker-compose logs -f cv-generator`
2. Test API locally: `curl http://localhost:5000/health`
3. Verify template files exist: `ls -la templates/`
4. Check LaTeX syntax: `pdflatex -interaction=nonstopmode templates/resume_balz.tex`
