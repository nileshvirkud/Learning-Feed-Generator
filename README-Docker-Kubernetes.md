# Docker & Kubernetes Deployment Guide

This guide explains how to containerize and deploy the Learning Feed Generator as a Kubernetes CronJob.

## Quick Start

### 1. Development with Dev Container

```bash
# Open in VS Code with Dev Containers extension
code .
# VS Code will prompt to reopen in container
```

### 2. Local Development with Docker

```bash
# Build and run locally
docker-compose up learning-feed-generator

# Development mode (interactive)
docker-compose up learning-feed-dev
docker exec -it learning-feed-dev bash
```

### 3. Build and Push to Docker Hub

```bash
# Set your Docker Hub username
export DOCKER_HUB_USERNAME=your-username

# Build and push
./scripts/build-and-push.sh

# Or with version tag
VERSION=v1.0.0 ./scripts/build-and-push.sh
```

### 4. Deploy to Kubernetes

```bash
# Update kubernetes/secret.yaml with your API keys
# Then deploy
./scripts/deploy-kubernetes.sh
```

## Configuration

### Environment Variables

Required secrets:
- `OPENAI_API_KEY`: OpenAI API key
- `PERPLEXITY_API_KEY`: Perplexity API key  
- `NOTION_TOKEN`: Notion integration token
- `NOTION_DATABASE_ID`: Notion database ID

Optional config (set in ConfigMap):
- `LOG_LEVEL`: Logging level (default: INFO)
- `DEFAULT_TOPICS`: Comma-separated topics
- `MAX_ARTICLES_PER_TOPIC`: Max articles per topic (default: 5)

### Kubernetes Secrets

Create secrets using kubectl:

```bash
kubectl create secret generic learning-feed-secrets \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --from-literal=PERPLEXITY_API_KEY="your-perplexity-key" \
  --from-literal=NOTION_TOKEN="your-notion-token" \
  --from-literal=NOTION_DATABASE_ID="your-database-id" \
  --namespace=learning-feed
```

## Schedule Configuration

The CronJob runs daily at 8:00 AM UTC. To change the schedule, edit `kubernetes/cronjob.yaml`:

```yaml
spec:
  schedule: "0 8 * * *"  # Daily at 8 AM UTC
  timeZone: "UTC"
```

Schedule formats:
- `"0 8 * * *"`: Daily at 8 AM
- `"0 */6 * * *"`: Every 6 hours
- `"0 8 * * 1-5"`: Weekdays at 8 AM
- `"0 8,18 * * *"`: Daily at 8 AM and 6 PM

## Management Commands

### View CronJob Status
```bash
kubectl get cronjob -n learning-feed
kubectl describe cronjob learning-feed-generator -n learning-feed
```

### View Job History
```bash
kubectl get jobs -n learning-feed --sort-by=.metadata.creationTimestamp
```

### View Logs
```bash
# Latest job logs
kubectl logs -l app=learning-feed-generator -n learning-feed --tail=100

# Specific job logs
kubectl logs job/learning-feed-generator-28442280 -n learning-feed
```

### Manual Trigger
```bash
kubectl create job --from=cronjob/learning-feed-generator manual-run-$(date +%s) -n learning-feed
```

### Update Image
```bash
kubectl set image cronjob/learning-feed-generator \
  learning-feed-generator=your-username/learning-feed-generator:v1.1.0 \
  -n learning-feed
```

## CI/CD with GitHub Actions

The included GitHub Actions workflow automatically:
1. Builds and tests the application
2. Creates multi-platform Docker images (amd64/arm64)
3. Pushes to Docker Hub on main branch

### Required Secrets

Add these to your GitHub repository secrets:
- `DOCKER_HUB_USERNAME`: Your Docker Hub username
- `DOCKER_HUB_TOKEN`: Docker Hub access token

### Workflow Triggers

- **Push to main/develop**: Build and push with branch tag
- **Tags (v*)**: Build and push with version tag
- **Pull Requests**: Build only (no push)

## Troubleshooting

### Common Issues

1. **Image Pull Errors**
   ```bash
   # Check if image exists
   docker pull your-username/learning-feed-generator:latest
   
   # Update CronJob image
   kubectl patch cronjob learning-feed-generator -n learning-feed -p '{"spec":{"jobTemplate":{"spec":{"template":{"spec":{"containers":[{"name":"learning-feed-generator","image":"your-username/learning-feed-generator:latest"}]}}}}}}'
   ```

2. **Secret Issues**
   ```bash
   # Check secrets
   kubectl get secrets -n learning-feed
   kubectl describe secret learning-feed-secrets -n learning-feed
   
   # Recreate secrets
   kubectl delete secret learning-feed-secrets -n learning-feed
   # Then create again with correct values
   ```

3. **CronJob Not Running**
   ```bash
   # Check CronJob status
   kubectl describe cronjob learning-feed-generator -n learning-feed
   
   # Check for suspended CronJobs
   kubectl patch cronjob learning-feed-generator -n learning-feed -p '{"spec":{"suspend":false}}'
   ```

### Resource Limits

Current limits in `kubernetes/cronjob.yaml`:
- Memory: 512Mi limit, 256Mi request
- CPU: 500m limit, 100m request

Adjust based on your needs and cluster capacity.

### Monitoring

Add monitoring with:
- Prometheus metrics
- Log aggregation (ELK stack)
- Alert manager for failed jobs
- Grafana dashboards

## Security Considerations

- Secrets are base64 encoded (not encrypted)
- Use external secret management for production
- Run as non-root user (UID 1000)
- Network policies for pod communication
- Image scanning for vulnerabilities
- Resource quotas and limits

## Cleanup

```bash
# Delete everything
kubectl delete namespace learning-feed

# Or individual resources
kubectl delete -f kubernetes/
```