#!/bin/bash

# Deploy newsletter processing API to Google Cloud Run with secrets
# This script deploys the production version with all required secrets

set -e

echo "🚀 Deploying Newsletter Processing API to Google Cloud Run..."

# Set project and region
PROJECT_ID="paulbonneville-com"
REGION="us-central1"
SERVICE_NAME="arrgh-fastapi"

# Ensure we're using the correct project
gcloud config set project $PROJECT_ID

echo "📦 Building and pushing Docker image..."

# Build and push the image
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .

echo "🔧 Deploying to Cloud Run with secrets..."

# Deploy to Cloud Run with secrets and environment variables
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
  --set-env-vars GOOGLE_CLOUD_REGION=$REGION \
  --set-env-vars LLM_MODEL=gpt-4-turbo \
  --set-env-vars LLM_TEMPERATURE=0.1 \
  --set-env-vars LLM_MAX_TOKENS=2000 \
  --set-env-vars NEO4J_USER=neo4j \
  --set-env-vars NEO4J_DATABASE=neo4j \
  --set-env-vars MAX_ENTITIES_PER_NEWSLETTER=500 \
  --set-env-vars FACT_EXTRACTION_BATCH_SIZE=20 \
  --set-env-vars PROCESSING_TIMEOUT=600 \
  --set-env-vars ENTITY_CONFIDENCE_THRESHOLD=0.8 \
  --set-env-vars FACT_CONFIDENCE_THRESHOLD=0.85 \
  --set-env-vars API_HOST=0.0.0.0 \
  --set-env-vars API_PORT=8080 \
  --set-env-vars LOG_LEVEL=INFO \
  --set-env-vars ENABLE_METRICS=true \
  --set-env-vars METRICS_PORT=9090 \
  --set-env-vars ENABLE_ASYNC_PROCESSING=true \
  --set-env-vars ENABLE_ENTITY_CACHING=true \
  --set-env-vars ENABLE_DEBUG_MODE=false \
  --set-env-vars CORS_ORIGINS="[\"https://arrgh.paulbonneville.com\"]" \
  --set-secrets OPENAI_API_KEY=newsletter-openai-api-key:latest \
  --set-secrets NEO4J_PASSWORD=newsletter-neo4j-password:latest \
  --set-secrets NEO4J_URI=newsletter-neo4j-uri:latest \
  --set-secrets SECRET_KEY=newsletter-secret-key:latest \
  --set-secrets API_KEY=arrgh-fastapi-key:latest \
  --memory 2Gi \
  --cpu 1 \
  --concurrency 80 \
  --max-instances 10 \
  --timeout 900 \
  --vpc-connector neo4j-connector \
  --vpc-egress private-ranges-only \
  --allow-unauthenticated

echo "✅ Deployment complete!"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')

echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Health Check: $SERVICE_URL/health"
echo "📋 API Documentation: $SERVICE_URL/docs"
echo "🔍 Newsletter Health: $SERVICE_URL/newsletter/health"

echo ""
echo "🔑 To test the API, you'll need to authenticate:"
echo "gcloud auth print-identity-token | curl -H \"Authorization: Bearer \$(cat)\" $SERVICE_URL/newsletter/health"

echo ""
echo "📋 To view logs:"
echo "gcloud logs tail --follow --service $SERVICE_NAME --region $REGION"