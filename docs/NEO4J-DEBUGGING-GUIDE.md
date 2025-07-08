# Neo4j Connectivity Deep Dive Debugging Guide

This comprehensive guide provides all the tools and techniques needed to diagnose Neo4j connectivity issues in Google Cloud Run.

## 🚀 Quick Start

### Deploy Debug Environment
```bash
# Deploy the debug version with comprehensive logging
./scripts/deploy-debug.sh

# Or use Cloud Build directly
gcloud builds submit --config=cloudbuild-debug.yaml
```

### Immediate Diagnostics
```bash
# Get debug service URL
DEBUG_URL=$(gcloud run services describe arrgh-fastapi-debug --region=us-central1 --format='value(status.url)')

# Test basic connectivity
curl $DEBUG_URL/health | jq

# Run comprehensive Neo4j diagnostics
curl $DEBUG_URL/test-connectivity | jq '.neo4j_detailed_diagnostics'
```

## 📊 Enhanced Logging Analysis

### 1. Application-Level Logs

#### Real-time Neo4j Connection Monitoring
```bash
# Live tail with Neo4j focus
gcloud logs tail --follow --service arrgh-fastapi-debug --region us-central1 --filter="jsonPayload.message=~\"Neo4j\""

# DNS resolution analysis
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.message=~\"DNS resolution\"" --limit 20 --format=json | jq -r '.[] | "\(.timestamp) [\(.severity)] \(.jsonPayload.message) - \(.jsonPayload.hostname) -> \(.jsonPayload.resolved_ips // [])"'

# Connection timing breakdown
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.total_connection_time_ms!=null" --limit 10 --format=json | jq -r '.[] | "\(.timestamp) Total: \(.jsonPayload.total_connection_time_ms)ms DNS: \(.jsonPayload.dns_time_ms)ms TCP: \(.jsonPayload.tcp_time_ms)ms Driver: \(.jsonPayload.driver_time_ms)ms"'

# Retry attempts tracking
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.message=~\"Retry attempt\"" --limit 50 --format=json | jq -r '.[] | "\(.timestamp) \(.jsonPayload.attempt)/\(.jsonPayload.max_retries) \(.jsonPayload.error_type): \(.jsonPayload.error_message)"'
```

#### Error Pattern Analysis
```bash
# Connection failures by error type
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND severity>=ERROR AND jsonPayload.error_type!=null" --limit 100 --format=json | jq -r 'group_by(.jsonPayload.error_type) | .[] | "\(.[0].jsonPayload.error_type): \(length) occurrences"'

# SSL/TLS specific errors
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND (jsonPayload.message=~\"SSL\" OR jsonPayload.message=~\"TLS\" OR jsonPayload.message=~\"certificate\")" --limit 50

# Timeout analysis
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND (jsonPayload.message=~\"timeout\" OR jsonPayload.message=~\"timed out\")" --limit 50 --format=json | jq -r '.[] | "\(.timestamp) \(.jsonPayload.message) (took: \(.jsonPayload.tcp_attempt_time_ms // .jsonPayload.session_attempt_time_ms // "unknown")ms)"'
```

### 2. Platform and Infrastructure Logs

#### Cloud Run Container Lifecycle
```bash
# Container startup issues
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=arrgh-fastapi-debug AND severity>=WARNING" --limit 50

# Memory and CPU constraints
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=arrgh-fastapi-debug AND (jsonPayload.message=~\"memory\" OR jsonPayload.message=~\"cpu\" OR jsonPayload.message=~\"resource\")" --limit 30

# Cold start analysis
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.message=~\"cold start\"" --limit 20
```

#### VPC and Network Infrastructure
```bash
# Enable VPC Flow Logs (if not already enabled)
gcloud compute networks subnets update default \
    --region=us-central1 \
    --enable-flow-logs \
    --logging-aggregation-interval=interval-5-sec \
    --logging-flow-sampling=0.1

# Analyze VPC flows to Neo4j
gcloud logs read "resource.type=gce_subnetwork AND jsonPayload.connection.dest_port=7687" --limit 50 --format=json | jq -r '.[] | "\(.timestamp) \(.jsonPayload.connection.src_ip):\(.jsonPayload.connection.src_port) -> \(.jsonPayload.connection.dest_ip):7687 \(.jsonPayload.connection.protocol) \(.jsonPayload.bytes_sent) bytes"'

# Network policy violations
gcloud logs read "resource.type=gce_firewall_rule AND severity>=WARNING" --limit 20
```

#### Cloud Build and Deployment Logs
```bash
# Latest builds
gcloud builds list --filter="source.repoSource.branchName=feature/neo4j-connectivity-investigation" --limit=5

# Build-time issues
BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)")
gcloud builds log $BUILD_ID | grep -E "(ERROR|FAILED|error:)"

# Environment variable injection
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.message=~\"environment\"" --limit 10
```

## 🔍 Deep Network Analysis

### Using the Debug Container Tools

#### SSH into Running Container (when possible)
```bash
# Get a shell in the debug container for direct investigation
gcloud run services describe arrgh-fastapi-debug --region=us-central1

# If Cloud Shell access is available, use these commands inside the container:
```

#### Network Path Analysis
```bash
# DNS troubleshooting
dig ab2b5664.databases.neo4j.io
nslookup ab2b5664.databases.neo4j.io 8.8.8.8

# Connectivity testing
ping -c 4 ab2b5664.databases.neo4j.io
traceroute ab2b5664.databases.neo4j.io
mtr --report --report-cycles 10 ab2b5664.databases.neo4j.io

# Port connectivity
nc -zv ab2b5664.databases.neo4j.io 7687
telnet ab2b5664.databases.neo4j.io 7687

# SSL certificate verification
openssl s_client -connect ab2b5664.databases.neo4j.io:7687 -servername ab2b5664.databases.neo4j.io -verify_return_error

# MTU discovery
ping -M do -s 1472 ab2b5664.databases.neo4j.io
```

### API-Based Network Diagnostics

#### Automated Testing Endpoints
```bash
DEBUG_URL="https://arrgh-fastapi-debug-860937201650.us-central1.run.app"

# Basic health check
curl "$DEBUG_URL/health" | jq

# Comprehensive connectivity test
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics'

# Focus on specific test results
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.dns_resolution'
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.tcp_connectivity'
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.ssl_certificate'
```

## 📈 Performance Monitoring

### Cloud Monitoring Integration

#### Key Metrics to Track
```bash
# Create custom dashboard for Neo4j connectivity
# Monitor these metrics:
# - Connection attempt count
# - Connection success rate
# - Average connection time
# - DNS resolution time
# - Retry attempt frequency
```

#### Setting Up Alerts
```bash
# Alert on high connection failure rate
gcloud alpha monitoring policies create \
    --notification-channels=[YOUR_CHANNEL_ID] \
    --display-name="Neo4j Connection Failures" \
    --condition-display-name="High Neo4j Error Rate" \
    --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="arrgh-fastapi-debug" AND jsonPayload.message=~"Neo4j connection failed"' \
    --condition-threshold-value=5 \
    --condition-threshold-duration=300s

# Alert on slow connections
gcloud alpha monitoring policies create \
    --notification-channels=[YOUR_CHANNEL_ID] \
    --display-name="Slow Neo4j Connections" \
    --condition-display-name="High Connection Latency" \
    --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="arrgh-fastapi-debug" AND jsonPayload.total_connection_time_ms>5000' \
    --condition-threshold-value=3 \
    --condition-threshold-duration=180s
```

## 🔧 Advanced Troubleshooting

### Common Issues and Solutions

#### 1. DNS Resolution Failures
```bash
# Check if DNS is working at all
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.dns_resolution'

# If DNS fails, check:
# - Cloud Run VPC settings
# - Custom DNS configuration
# - Firewall rules for DNS (port 53)
```

#### 2. TCP Connection Timeouts
```bash
# Analyze TCP connection timing
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.tcp_connect_time_ms>5000" --limit 20

# Solutions:
# - Check VPC egress settings
# - Verify no intermediate firewalls
# - Test with different Neo4j endpoints
```

#### 3. SSL/TLS Handshake Failures
```bash
# Check SSL certificate details
curl "$DEBUG_URL/test-connectivity" | jq '.neo4j_detailed_diagnostics.tests.ssl_certificate'

# Common fixes:
# - Verify certificate chain
# - Check cipher suite compatibility
# - Validate hostname in certificate
```

#### 4. Authentication Failures
```bash
# Check if authentication is the issue
gcloud logs read "resource.labels.service_name=arrgh-fastapi-debug AND jsonPayload.message=~\"authentication\"" --limit 20

# Verify:
# - Secret values are correctly mounted
# - Username/password are valid
# - Neo4j user has proper permissions
```

### Performance Optimization

#### Connection Pool Tuning
```python
# Optimize these settings based on your findings:
{
    "max_connection_lifetime": 3600,
    "max_connection_pool_size": 50,
    "connection_acquisition_timeout": 30,
    "connection_timeout": 30,
    "keep_alive": True
}
```

#### Retry Strategy Tuning
```python
# Adjust retry parameters based on error patterns:
@retry_with_exponential_backoff(
    max_retries=3,
    initial_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True
)
```

## 📋 Debugging Checklist

### Pre-Investigation Setup
- [ ] Deploy debug service: `./scripts/deploy-debug.sh`
- [ ] Verify debug service is running: `curl $DEBUG_URL/health`
- [ ] Check VPC Flow Logs are enabled
- [ ] Set up monitoring alerts

### During Investigation
- [ ] Run comprehensive connectivity test
- [ ] Analyze DNS resolution patterns
- [ ] Check TCP connectivity timing
- [ ] Verify SSL certificate if using encryption
- [ ] Review retry attempt patterns
- [ ] Check for resource constraints (memory/CPU)

### Post-Resolution
- [ ] Document the root cause and solution
- [ ] Update monitoring thresholds if needed
- [ ] Consider adding permanent diagnostic endpoints
- [ ] Delete debug service: `gcloud run services delete arrgh-fastapi-debug --region us-central1`

## 🔄 Return to Production

```bash
# When debugging is complete, return to production deployment
./scripts/deploy-production.sh

# Verify production service is healthy
curl https://arrgh-fastapi-860937201650.us-central1.run.app/health
```

## 📚 Additional Resources

- [Neo4j Aura Connection Troubleshooting](https://neo4j.com/docs/aura/current/getting-started/connect/)
- [Google Cloud Run Networking](https://cloud.google.com/run/docs/configuring/connecting-vpc)
- [Cloud Logging Query Language](https://cloud.google.com/logging/docs/view/logging-query-language)
- [VPC Flow Logs](https://cloud.google.com/vpc/docs/using-flow-logs)