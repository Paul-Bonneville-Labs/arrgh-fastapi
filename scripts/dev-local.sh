#!/bin/bash

# Stop and remove any running container named 'arrgh-fastapi'
if [ $(docker ps -q -f name=arrgh-fastapi) ]; then
  echo "Stopping running 'arrgh-fastapi' container..."
  docker stop arrgh-fastapi
  docker rm arrgh-fastapi
fi

# Build the Docker image
echo "Building Docker image 'arrgh-fastapi'..."
docker build -t arrgh-fastapi .

# Run the Docker container
echo "Running Docker container 'arrgh-fastapi' on port 8080..."
docker run -d --name arrgh-fastapi -p 8080:8080 arrgh-fastapi

# Wait for the app to start
echo "Waiting for the app to start..."
sleep 3

# Test the endpoint
echo "Testing the local endpoint: http://localhost:8080/"
curl --fail http://localhost:8080/ || { echo "App did not respond as expected."; exit 1; }
echo -e "\nApp is running and responded successfully." 