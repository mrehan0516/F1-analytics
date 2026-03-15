#!/bin/bash
# ============================================
# F1 Pit Wall AI - Google Cloud Deployment Script
# Automated Cloud Run deployment
# ============================================

set -e  # Exit on error

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-f1-pit-wall-ai}"
REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
SERVICE_NAME="f1-pit-wall-ai"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  F1 Pit Wall AI - Cloud Deployment    ${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not found. Please install Google Cloud SDK.${NC}"
    exit 1
fi

# Check authentication
echo -e "${YELLOW}Checking authentication...${NC}"
gcloud auth list --filter=status:ACTIVE --format="value(account)" || {
    echo -e "${RED}Not authenticated. Please run: gcloud auth login${NC}"
    exit 1
}

# Set project
echo -e "${YELLOW}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com

# Build the container image
echo -e "${YELLOW}Building container image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-secrets "GOOGLE_API_KEY=gemini-api-key:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format="value(status.url)")

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!                 ${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Service URL: ${SERVICE_URL}"
echo -e "Health Check: ${SERVICE_URL}/health"
echo -e "API Docs: ${SERVICE_URL}/docs"
echo -e "Demo: ${SERVICE_URL}/demo"
echo ""
echo -e "${YELLOW}To view logs:${NC}"
echo "  gcloud run logs read ${SERVICE_NAME} --region ${REGION}"
