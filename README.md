# Daily Learning Feed Generator

A comprehensive Python application that automatically curates, summarizes, and organizes educational content using modern APIs and saves everything to Notion for easy access and review.

## Features

- **Smart Content Discovery**: Fetches fresh educational content using Perplexity API with RSS fallbacks
- **AI-Powered Summarization**: Creates concise, educational summaries using GPT-4  
- **Interactive Learning**: Generates quiz questions and flashcards for active learning
- **Notion Integration**: Organizes everything in a structured Notion database
- **Automated Scheduling**: Runs daily to build a continuous learning feed
- **Quality Control**: Filters content by recency and source reliability
- **Comprehensive CLI**: Command-line interface with interactive options

## Development Setup

### Option 1: Dev Container (Recommended)

The easiest way to get started is using VS Code with Dev Containers:

#### Prerequisites
- [VS Code](https://code.visualstudio.com/)
- [Docker](https://www.docker.com/get-started)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Setup Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Learning-Feed-Generator.git
   cd Learning-Feed-Generator
   ```

2. Create your environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see Configuration section)
   ```

3. Open in VS Code:
   ```bash
   code .
   ```

4. When prompted, click "Reopen in Container" or press `Ctrl+Shift+P` and select "Dev Containers: Reopen in Container"

5. The dev container will automatically:
   - Build the development environment
   - Install all dependencies
   - Set up Python tools (black, pylint, pytest)
   - Mount your workspace and .env file

6. Test the setup:
   ```bash
   python -m daily_learning.main --help
   ```

### Option 2: Local Python Environment

#### Prerequisites
- Python 3.11 or higher
- pip package manager

#### Setup Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/Learning-Feed-Generator.git
   cd Learning-Feed-Generator
   ```

2. Create a virtual environment:
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Or using conda
   conda create -n learning-feed python=3.11
   conda activate learning-feed
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. Install development dependencies (optional):
   ```bash
   pip install pytest pytest-cov black isort pylint mypy jupyter
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## Configuration

### Required API Keys

Edit your `.env` file with the following credentials:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here

# Optional but recommended
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Content Settings
MAX_ARTICLES_PER_TOPIC=5
CONTENT_MAX_AGE_HOURS=48
SUMMARY_SENTENCE_COUNT=4
QUIZ_QUESTIONS_PER_ARTICLE=2
FLASHCARDS_PER_ARTICLE=3

# Scheduler Settings
SCHEDULER_ENABLED=true
SCHEDULER_RUN_TIME=08:00
SCHEDULER_WEEKDAYS_ONLY=true
SCHEDULER_RETRY_ATTEMPTS=3
```

### API Setup Guide

#### OpenAI API
1. Go to [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` as `OPENAI_API_KEY`

#### Notion API
1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the Internal Integration Token to `.env` as `NOTION_TOKEN`
4. Create a database in Notion
5. Share the database with your integration
6. Copy database ID from URL to `.env` as `NOTION_DATABASE_ID`

#### Perplexity API (Optional)
1. Sign up at [Perplexity AI](https://www.perplexity.ai/)
2. Get API key from your account
3. Add to `.env` as `PERPLEXITY_API_KEY`

## Usage

### Setup Notion Database
```bash
python -m daily_learning.main --setup-db
```

### Basic Usage
```bash
# Generate feed for default topics
python -m daily_learning.main

# Custom topics
python -m daily_learning.main --topics "python,machine learning,data science"

# Interactive mode
python -m daily_learning.main --interactive

# View database statistics
python -m daily_learning.main --stats
```

### Scheduled Automation
```bash
# Run scheduler
python run_scheduler.py
```

## Docker Deployment

### Building Docker Images

#### Development Image
```bash
# Build development image
docker build -f Dockerfile.dev -t learning-feed-generator:dev .

# Run development container
docker run -it --env-file .env -v $(pwd):/workspace learning-feed-generator:dev
```

#### Production Image
```bash
# Build production image
docker build -t learning-feed-generator:latest .

# Run production container
docker run --env-file .env learning-feed-generator:latest

docker tag learning-feed-generator: virkudnilesh/learning-feed-generator:latest

# Run scheduler in production
docker run -d --name learning-scheduler --env-file .env learning-feed-generator:latest python run_scheduler.py
```

### Docker Compose

#### Development
```bash
# Start development environment
docker-compose -f .devcontainer/docker-compose.yml up -d

# Access the container
docker-compose -f .devcontainer/docker-compose.yml exec app bash
```

#### Production
```bash
# Start production services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Building and Pushing to Registry

```bash
# Build and tag for your registry
docker build -t your-registry/learning-feed-generator:v1.0.0 .
docker build -t your-registry/learning-feed-generator:latest .

# Push to registry
docker push your-registry/learning-feed-generator:v1.0.0
docker push your-registry/learning-feed-generator:latest
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (local or cloud)
- kubectl configured
- Docker registry access

### Deployment Steps

#### 1. Prepare Your Environment
```bash
# Create namespace
kubectl apply -f kubernetes/namespace.yaml

# Create secrets with your API keys
kubectl create secret generic learning-feed-secrets \
  --from-literal=OPENAI_API_KEY=your_key_here \
  --from-literal=NOTION_TOKEN=your_token_here \
  --from-literal=NOTION_DATABASE_ID=your_db_id_here \
  --from-literal=PERPLEXITY_API_KEY=your_perplexity_key_here \
  -n learning-feed

# Or apply the secret template (edit kubernetes/secret.yaml first)
kubectl apply -f kubernetes/secret.yaml
```

#### 2. Deploy Configuration
```bash
# Apply configuration
kubectl apply -f kubernetes/configmap.yaml
```

#### 3. Deploy the Application
```bash
# Deploy CronJob for scheduled runs
kubectl apply -f kubernetes/cronjob.yaml

# Verify deployment
kubectl get cronjobs -n learning-feed
kubectl get pods -n learning-feed
```

#### 4. Manual Job Execution
```bash
# Create a one-time job from the cronjob
kubectl create job --from=cronjob/learning-feed-cronjob manual-run-$(date +%s) -n learning-feed

# Check job status
kubectl get jobs -n learning-feed

# View logs
kubectl logs -l job-name=manual-run-xyz -n learning-feed
```

### Kubernetes Management

#### Monitoring
```bash
# Check CronJob status
kubectl describe cronjob learning-feed-cronjob -n learning-feed

# View recent jobs
kubectl get jobs -n learning-feed --sort-by=.metadata.creationTimestamp

# Check pod logs
kubectl logs -l app=learning-feed -n learning-feed --tail=100
```

#### Scaling and Updates
```bash
# Suspend CronJob
kubectl patch cronjob learning-feed-cronjob -p '{"spec":{"suspend":true}}' -n learning-feed

# Resume CronJob
kubectl patch cronjob learning-feed-cronjob -p '{"spec":{"suspend":false}}' -n learning-feed

# Update image
kubectl patch cronjob learning-feed-cronjob -p '{"spec":{"jobTemplate":{"spec":{"template":{"spec":{"containers":[{"name":"learning-feed","image":"your-registry/learning-feed-generator:v1.1.0"}]}}}}}}' -n learning-feed
```

#### Cleanup
```bash
# Delete all resources
kubectl delete namespace learning-feed

# Or delete individual components
kubectl delete cronjob learning-feed-cronjob -n learning-feed
kubectl delete configmap learning-feed-config -n learning-feed
kubectl delete secret learning-feed-secrets -n learning-feed
```

### Automated Deployment Script

Use the provided script for easy deployment:

```bash
# Make script executable
chmod +x scripts/deploy-kubernetes.sh

# Deploy to Kubernetes
./scripts/deploy-kubernetes.sh

# Build and deploy (includes docker build and push)
./scripts/build-and-push.sh && ./scripts/deploy-kubernetes.sh
```

## Architecture

```
daily_learning/
├── main.py              # Main CLI application
├── config.py            # Configuration management
├── content_fetcher.py   # Content discovery (Perplexity + RSS)
├── summarizer.py        # GPT-4 summarization
├── quiz_generator.py    # Quiz and flashcard creation
├── notion_client.py     # Notion database operations
└── scheduler.py         # Automation and scheduling
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=daily_learning tests/

# Run specific test
pytest tests/test_content_fetcher.py -v
```

### Code Quality
```bash
# Format code
black daily_learning/

# Sort imports
isort daily_learning/

# Lint code
pylint daily_learning/

# Type checking
mypy daily_learning/
```

### Development Workflow
1. Make changes in your dev container or local environment
2. Run tests: `pytest`
3. Format code: `black . && isort .`
4. Test Docker build: `docker build -f Dockerfile.dev .`
5. Test Kubernetes deployment locally

## Troubleshooting

### Common Issues

#### Dev Container Issues
- **Container won't start**: Check Docker is running and you have sufficient resources
- **Extensions not loading**: Rebuild container with `Ctrl+Shift+P` > "Dev Containers: Rebuild Container"
- **Environment variables not available**: Ensure `.env` file exists and is properly mounted

#### Docker Issues
- **Build failures**: Check Dockerfile syntax and ensure all files exist
- **Permission errors**: Use `docker run --user $(id -u):$(id -g)` on Linux
- **Port conflicts**: Change port mappings in docker-compose.yml

#### Kubernetes Issues
- **Pods not starting**: Check `kubectl describe pod <pod-name> -n learning-feed`
- **CronJob not running**: Verify schedule format and timezone settings
- **Secret not found**: Ensure secrets are created in the correct namespace

#### API Issues
- **API Key Errors**: Verify all API keys are correctly set and have proper permissions
- **Rate limiting**: Check API usage quotas and implement backoff strategies
- **Network timeouts**: Configure appropriate timeout values in config.py

### Logs and Debugging
```bash
# Application logs
tail -f daily_learning.log

# Docker logs
docker logs learning-scheduler

# Kubernetes logs
kubectl logs -l app=learning-feed -n learning-feed --tail=100 -f

# Debug mode
python -m daily_learning.main --debug --topics "test"
```

## License

MIT License - see LICENSE file for details.

## Support

- Create an issue for bugs or feature requests
- Check existing issues for solutions
- Contribute improvements via pull requests