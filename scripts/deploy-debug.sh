#!/bin/bash

# Deploy newsletter processing API to Google Cloud Run with DEBUG settings
# This script deploys with comprehensive logging and debugging capabilities

set -e

echo "🔍 Deploying Newsletter Processing API with DEBUG configuration..."
echo "⚠️  WARNING: This deployment includes debug logging and network tools!"

# Set project and region
PROJECT_ID="paulbonneville-com"
REGION="us-central1"
SERVICE_NAME="arrgh-fastapi"
DEBUG_SERVICE_NAME="arrgh-fastapi-debug"

# Ensure we're using the correct project
gcloud config set project $PROJECT_ID

echo "📦 Building and pushing DEBUG Docker image..."

# Build debug image with comprehensive tools
gcloud builds submit --config=cloudbuild-debug.yaml --substitutions=_SERVICE_NAME=$DEBUG_SERVICE_NAME .

echo "🔧 Deploying DEBUG service to Cloud Run..."

# Deploy debug version with enhanced settings
gcloud run deploy $DEBUG_SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/arrgh-fastapi-debug \
  --platform managed \
  --region $REGION \
  --set-env-vars ENVIRONMENT=debug \
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
  --set-env-vars LOG_LEVEL=DEBUG \
  --set-env-vars ENABLE_METRICS=true \
  --set-env-vars METRICS_PORT=9090 \
  --set-env-vars ENABLE_ASYNC_PROCESSING=true \
  --set-env-vars ENABLE_ENTITY_CACHING=true \
  --set-env-vars ENABLE_DEBUG_MODE=true \
  --set-env-vars PYTHONUNBUFFERED=1 \
  --set-env-vars PYTHONFAULTHANDLER=1 \
  --set-env-vars PYTHONASYNCIODEBUG=1 \
  --set-env-vars CORS_ORIGINS="[\"*\"]" \
  --set-secrets OPENAI_API_KEY=newsletter-openai-api-key:latest \
  --set-secrets NEO4J_PASSWORD=newsletter-neo4j-password:latest \
  --set-secrets NEO4J_URI=newsletter-neo4j-uri:latest \
  --set-secrets SECRET_KEY=newsletter-secret-key:latest \
  --set-secrets API_KEY=arrgh-fastapi-key:latest \
  --memory 4Gi \
  --cpu 2 \
  --concurrency 10 \
  --max-instances 3 \
  --min-instances 1 \
  --timeout 900 \
  --vpc-egress all \
  --network default \
  --subnet default \
  --allow-unauthenticated

echo "✅ DEBUG deployment complete!"

# Get the service URL
DEBUG_SERVICE_URL=$(gcloud run services describe $DEBUG_SERVICE_NAME --region=$REGION --format='value(status.url)')

echo ""
echo "🌐 DEBUG Service URL: $DEBUG_SERVICE_URL"
echo "📊 Health Check: $DEBUG_SERVICE_URL/health"
echo "📋 API Documentation: $DEBUG_SERVICE_URL/docs"
echo "🔍 Newsletter Health: $DEBUG_SERVICE_URL/newsletter/health"
echo "🔌 Connectivity Test: $DEBUG_SERVICE_URL/test-connectivity"

echo ""
echo "🔑 Testing endpoints (no auth required for debug):"
echo "curl $DEBUG_SERVICE_URL/health"
echo "curl $DEBUG_SERVICE_URL/test-connectivity | jq '.neo4j_detailed_diagnostics'"

echo ""
echo "📋 To view comprehensive logs:"
echo "gcloud logs tail --follow --service $DEBUG_SERVICE_NAME --region $REGION"

echo ""
echo "🔍 To filter for specific log types:"
echo "# Neo4j connection logs"
echo "gcloud logs read \"resource.labels.service_name=$DEBUG_SERVICE_NAME AND jsonPayload.message=~\\\"Neo4j\\\"\" --limit 50"
echo ""
echo "# DNS resolution logs"
echo "gcloud logs read \"resource.labels.service_name=$DEBUG_SERVICE_NAME AND jsonPayload.message=~\\\"DNS resolution\\\"\" --limit 20"
echo ""
echo "# Retry attempt logs"
echo "gcloud logs read \"resource.labels.service_name=$DEBUG_SERVICE_NAME AND jsonPayload.message=~\\\"Retry attempt\\\"\" --limit 20"

echo ""
echo "⚠️  Remember to delete the debug service when done:"
echo "gcloud run services delete $DEBUG_SERVICE_NAME --region $REGION --quiet"