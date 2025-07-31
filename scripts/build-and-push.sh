#!/bin/bash

# Build and Push Script for Learning Feed Generator
# This script builds the Docker image and pushes it to Docker Hub

set -e  # Exit on any error

# Configuration
DOCKER_HUB_USERNAME="${DOCKER_HUB_USERNAME:-your-dockerhub-username}"
IMAGE_NAME="learning-feed-generator"
VERSION="${VERSION:-latest}"
FULL_IMAGE_NAME="${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:${VERSION}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Learning Feed Generator - Docker Build & Push ===${NC}"
echo -e "${YELLOW}Image: ${FULL_IMAGE_NAME}${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Check if Docker Hub username is set
if [ "$DOCKER_HUB_USERNAME" = "your-dockerhub-username" ]; then
    echo -e "${RED}Error: Please set your Docker Hub username${NC}"
    echo "Set the DOCKER_HUB_USERNAME environment variable:"
    echo "export DOCKER_HUB_USERNAME=your-actual-username"
    exit 1
fi

# Build the Docker image
echo -e "${BLUE}Step 1: Building Docker image...${NC}"
docker build -t "${FULL_IMAGE_NAME}" .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
else
    echo -e "${RED}✗ Docker image build failed${NC}"
    exit 1
fi

# Tag as latest if not already
if [ "$VERSION" != "latest" ]; then
    echo -e "${BLUE}Step 2: Tagging as latest...${NC}"
    docker tag "${FULL_IMAGE_NAME}" "${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest"
fi

# Push to Docker Hub
echo -e "${BLUE}Step 3: Pushing to Docker Hub...${NC}"
echo "Pushing ${FULL_IMAGE_NAME}"

docker push "${FULL_IMAGE_NAME}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully pushed ${FULL_IMAGE_NAME}${NC}"
else
    echo -e "${RED}✗ Failed to push ${FULL_IMAGE_NAME}${NC}"
    exit 1
fi

# Push latest tag if we created one
if [ "$VERSION" != "latest" ]; then
    echo "Pushing ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest"
    docker push "${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully pushed ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest${NC}"
    else
        echo -e "${RED}✗ Failed to push ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}=== Build and Push Complete! ===${NC}"
echo -e "${YELLOW}Image available at:${NC}"
echo "  docker pull ${FULL_IMAGE_NAME}"
if [ "$VERSION" != "latest" ]; then
    echo "  docker pull ${DOCKER_HUB_USERNAME}/${IMAGE_NAME}:latest"
fi
echo ""
echo -e "${YELLOW}To update Kubernetes deployment, run:${NC}"
echo "  kubectl set image cronjob/learning-feed-generator learning-feed-generator=${FULL_IMAGE_NAME} -n learning-feed"
echo ""
echo -e "${BLUE}Image size:${NC}"
docker images "${FULL_IMAGE_NAME}" --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"