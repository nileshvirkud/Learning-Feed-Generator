#!/bin/bash

# Kubernetes Deployment Script for Learning Feed Generator
# This script deploys the application to Kubernetes

set -e  # Exit on any error

# Configuration
NAMESPACE="learning-feed"
KUBECTL_CONTEXT="${KUBECTL_CONTEXT:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Learning Feed Generator - Kubernetes Deployment ===${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if we can connect to cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    echo "Please check your kubeconfig and cluster connection"
    exit 1
fi

# Set context if provided
if [ -n "$KUBECTL_CONTEXT" ]; then
    echo -e "${BLUE}Setting kubectl context to: $KUBECTL_CONTEXT${NC}"
    kubectl config use-context "$KUBECTL_CONTEXT"
fi

echo -e "${BLUE}Current cluster info:${NC}"
kubectl cluster-info | head -1

echo ""
echo -e "${BLUE}Step 1: Creating namespace...${NC}"
kubectl apply -f kubernetes/namespace.yaml

echo -e "${BLUE}Step 2: Applying ConfigMap...${NC}"
kubectl apply -f kubernetes/configmap.yaml

echo -e "${BLUE}Step 3: Applying Secrets...${NC}"
echo -e "${YELLOW}Note: Make sure to update kubernetes/secret.yaml with your actual secrets${NC}"
kubectl apply -f kubernetes/secret.yaml

echo -e "${BLUE}Step 4: Deploying CronJob...${NC}"
kubectl apply -f kubernetes/cronjob.yaml

echo ""
echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo ""

# Show deployment status
echo -e "${BLUE}Deployment Status:${NC}"
echo ""
echo -e "${YELLOW}Namespace:${NC}"
kubectl get namespace "$NAMESPACE"
echo ""

echo -e "${YELLOW}ConfigMap:${NC}"
kubectl get configmap -n "$NAMESPACE"
echo ""

echo -e "${YELLOW}Secrets:${NC}"
kubectl get secrets -n "$NAMESPACE"
echo ""

echo -e "${YELLOW}CronJob:${NC}"
kubectl get cronjob -n "$NAMESPACE"
echo ""

echo -e "${YELLOW}Recent Jobs:${NC}"
kubectl get jobs -n "$NAMESPACE" --sort-by=.metadata.creationTimestamp
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo "  # View CronJob details"
echo "  kubectl describe cronjob learning-feed-generator -n $NAMESPACE"
echo ""
echo "  # View job logs"
echo "  kubectl logs -l app=learning-feed-generator -n $NAMESPACE"
echo ""
echo "  # Manually trigger a job"
echo "  kubectl create job --from=cronjob/learning-feed-generator manual-run-\$(date +%s) -n $NAMESPACE"
echo ""
echo "  # View all resources"
echo "  kubectl get all -n $NAMESPACE"
echo ""
echo "  # Delete everything"
echo "  kubectl delete namespace $NAMESPACE"