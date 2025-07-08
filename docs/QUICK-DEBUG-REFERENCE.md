# Neo4j Debug Quick Reference Card

## 🚀 Deploy & Test
```bash
# Deploy debug service
./scripts/deploy-debug.sh

# Quick connectivity test
curl $(gcloud run services describe arrgh-fastapi-debug --region=us-central1 --format='value(status.url)')/test-connectivity | jq '.neo4j_detailed_diagnostics'
```

## 📊 Essential Log Commands

### Live Monitoring
```bash
# Real-time Neo4j logs
gcloud logs tail --follow --service arrgh-fastapi-debug --filter="jsonPayload.message=~\"Neo4j\""

# Connection timing analysis
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.total_connection_time_ms!=null" --limit 10 --format=json | jq -r '.[] | "\(.timestamp) Total: \(.jsonPayload.total_connection_time_ms)ms"'
```

### Error Analysis
```bash
# All connection errors
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND severity>=ERROR AND jsonPayload.message=~\"Neo4j\"" --limit 20

# DNS failures
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.message=~\"DNS resolution failed\"" --limit 10

# Retry attempts
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.message=~\"Retry attempt\"" --limit 20
```

## 🔍 Diagnostic Endpoints
```bash
DEBUG_URL="https://arrgh-fastapi-debug-860937201650.us-central1.run.app"

# Health check
curl "$DEBUG_URL/health" | jq

# DNS test
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.dns_resolution'

# TCP connectivity
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.tcp_connectivity'

# SSL certificate
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.ssl_certificate'
```

## 🛠️ Common Fixes

### DNS Issues
```bash
# Check if this shows resolved IPs
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.dns_resolution.addresses'
```

### Connection Timeouts
```bash
# Look for high connection times
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.tcp_connect_time_ms>5000" --limit 10
```

### SSL Problems
```bash
# Check certificate validity
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.ssl_certificate.certificate_info'
```

## 🔄 Cleanup
```bash
# Delete debug service when done
gcloud run services delete arrgh-fastapi-debug --region us-central1 --quiet

# Return to production
./scripts/deploy-production.sh
```