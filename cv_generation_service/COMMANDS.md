#!/bin/bash
# Common commands for CV Generation Service

# SERVICE MANAGEMENT
docker-compose up -d          # Start service
docker-compose down           # Stop service  
docker-compose restart cv-generator  # Restart service
docker-compose logs -f cv-generator  # View logs
docker-compose ps             # Check status

# API TESTING
curl http://localhost:5000/health  # Health check
curl http://localhost:5000/available-templates  # List templates

# GENERATE PDF
curl -X POST http://localhost:5000/generate-cv \
  -H "Content-Type: application/json" \
  -d '{"template": "resume_balz"}' \
  --output cv.pdf

# DOCKER DEBUGGING
docker-compose exec cv-generator bash  # Access container shell
docker stats cv-generator             # Check resource usage

# UPDATE & RESTART
cp new_resume.tex templates/resume_balz.tex
docker-compose restart cv-generator
