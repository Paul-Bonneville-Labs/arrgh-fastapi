#!/bin/bash

# Start Neo4j using Docker for development
# This script starts a Neo4j container with the configuration needed for the notebook

echo "🚀 Starting Neo4j database for development..."

# Stop any existing neo4j container
docker stop neo4j-dev 2>/dev/null || true
docker rm neo4j-dev 2>/dev/null || true

# Start Neo4j container
docker run -d \
  --name neo4j-dev \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-neo4j-password \
  -e NEO4J_PLUGINS='["apoc"]' \
  -v neo4j-data:/data \
  -v neo4j-logs:/logs \
  neo4j:5.15.0

echo "⏳ Waiting for Neo4j to start..."
sleep 10

# Check if Neo4j is running
echo "🔍 Checking Neo4j status..."
if curl -s http://localhost:7474 > /dev/null; then
    echo "✅ Neo4j is running!"
    echo "📊 Neo4j Browser: http://localhost:7474"
    echo "🔗 Bolt URL: bolt://localhost:7687"
    echo "👤 Username: neo4j"
    echo "🔑 Password: your-neo4j-password"
    echo ""
    echo "💡 To stop Neo4j: docker stop neo4j-dev"
else
    echo "❌ Neo4j failed to start"
    echo "📋 Check logs with: docker logs neo4j-dev"
fi