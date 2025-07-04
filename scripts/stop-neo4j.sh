#!/bin/bash

# Stop Neo4j development container

echo "🛑 Stopping Neo4j database..."

docker stop neo4j-dev 2>/dev/null
docker rm neo4j-dev 2>/dev/null

echo "✅ Neo4j database stopped and removed"
echo "💾 Data is preserved in Docker volume 'neo4j-data'"
echo "📋 To remove all data: docker volume rm neo4j-data neo4j-logs"