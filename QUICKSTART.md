# Quick Start - CV Generation Service

## 🚀 Local Setup

### Start Services
```bash
# 1. Start Docker CV Generator
cd ~/git-projects/alexey-balz.github.io/cv_generation_service
sudo docker-compose up -d

# 2. Verify it's running
curl http://localhost:5000/health
# Expected: {"service":"CV Generation Service","status":"healthy",...}

# 3. (Optional) Serve website locally for testing
cd ~/git-projects/alexey-balz.github.io
python3 -m http.server 8080
```

### Stop Services
```bash
cd ~/git-projects/alexey-balz.github.io/cv_generation_service
sudo docker-compose down
```

---

## 📱 Access the CV Generator

**From Your PC:**
- http://localhost:8080/cv.html

**From Your Smartphone (same WiFi network):**
- http://{YOUR_PC_IP}:8080/cv.html
- Auto-detects device and connects to API

---

## ✨ Features

- ✅ **Dynamic Job Titles** - Enter any title or use quick presets
- ✅ **6 Quick Presets** - Python Developer, Senior ML Engineer, Data Scientist, etc.
- ✅ **Live PDF Preview** - See your CV before downloading
- ✅ **Smart Filename** - Auto-saves as `cv_balz_{title}_{DD.MM.YYYY}.pdf`
- ✅ **Profile Picture** - Your photo included in every CV
- ✅ **Mobile Optimized** - Works perfectly on smartphones
- ✅ **Education on Page 2** - Clean page break before Education section

---

## 🎯 How to Use

1. Open the CV page on your device
2. Select a preset or enter custom job title
3. Click **"Generate CV"** - preview loads
4. Click **"Download CV"** - saves with correct filename

**Example filenames:**
- `cv_balz_Senior_ML_Engineer_18.01.2026.pdf`
- `cv_balz_Data_Scientist_18.01.2026.pdf`
- `cv_balz_Python_Developer_18.01.2026.pdf`

---

## 🔧 Common Commands

```bash
# Check if services are running
sudo docker-compose ps

# View API logs
sudo docker-compose logs -f cv-generator

# Restart after template changes
sudo docker-compose down
sudo docker-compose up -d --build

# Test API directly
curl -X POST http://localhost:5000/generate-cv \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Title","template":"resume_balz"}' \
  --output test.pdf
```

---

## 📂 Project Structure

```
cv_generation_service/
├── Dockerfile              # Container specification
├── docker-compose.yml      # Orchestration config
├── app.py                  # Flask API server
├── requirements.txt        # Python dependencies
├── resume_balz.tex        # LaTeX CV template
└── profile_pic.jpg        # Your profile picture

cv.html                    # Web interface with title selector
```

---

## 🚀 Migration to NAS

When ready to deploy to your NAS:

1. **Copy service to NAS:**
   ```bash
   scp -r cv_generation_service/ user@nas-ip:/path/to/services/
   ```

2. **Start on NAS:**
   ```bash
   ssh user@nas-ip
   cd /path/to/services/cv_generation_service
   docker-compose up -d
   ```

3. **Update cv.html:**
   Change API endpoint (auto-detected by hostname, so just access via NAS IP)

4. **Deploy website:**
   Push updated cv.html to your web host

---

## 💡 Tips

- **Template Changes**: Edit `resume_balz.tex`, then rebuild Docker
- **Add More Presets**: Edit cv.html, add button with `data-title` attribute
- **Custom Styling**: Colors and layout in `resume_balz.tex` (Navy Blue theme)
- **Testing**: Use both PC and smartphone to verify functionality

---

**Version**: 1.0  
**Last Updated**: January 18, 2026  
**Status**: ✅ Production Ready
