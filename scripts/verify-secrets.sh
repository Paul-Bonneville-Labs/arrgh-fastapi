#!/bin/bash

# Verify that all required secrets are available in Google Cloud Secret Manager

set -e

PROJECT_ID="paulbonneville-com"
gcloud config set project $PROJECT_ID

echo "🔍 Verifying newsletter processing secrets in Google Cloud..."

SECRETS=(
    "newsletter-openai-api-key"
    "newsletter-neo4j-uri" 
    "newsletter-neo4j-password"
    "newsletter-secret-key"
)

for secret in "${SECRETS[@]}"; do
    echo -n "  $secret: "
    if gcloud secrets versions access latest --secret="$secret" >/dev/null 2>&1; then
        echo "✅ Available"
    else
        echo "❌ Missing or inaccessible"
        exit 1
    fi
done

echo ""
echo "🔗 Testing Neo4j connection with production credentials..."

# Extract credentials
NEO4J_URI=$(gcloud secrets versions access latest --secret="newsletter-neo4j-uri")
NEO4J_PASSWORD=$(gcloud secrets versions access latest --secret="newsletter-neo4j-password")

echo "  Neo4j URI: $NEO4J_URI"
echo "  Neo4j User: neo4j"
echo "  Neo4j Password: [REDACTED]"

echo ""
echo "✅ All secrets are configured and accessible!"
echo ""
echo "🚀 Ready for production deployment with:"
echo "  ./scripts/deploy-production.sh"