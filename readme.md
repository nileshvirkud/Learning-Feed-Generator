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

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Learning-Feed-Generator.git
cd Learning-Feed-Generator

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### 2. Configuration

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your API credentials:

```bash
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here  # Optional but recommended
```

### 3. Setup Notion Database

First, create a Notion database and get your integration token and database ID. Then run:

```bash
python -m daily_learning.main --setup-db
```

### 4. Run Your First Learning Feed

```bash
# Run with default topics
python -m daily_learning.main

# Run with custom topics
python -m daily_learning.main --topics "python,machine learning,data science"

# Interactive topic selection
python -m daily_learning.main --interactive

# View database statistics
python -m daily_learning.main --stats
```

## Usage Examples

### Basic Usage

```bash
# Generate feed for default topics
python -m daily_learning.main

# Custom topics
python -m daily_learning.main -t "artificial intelligence,web development"

# Interactive mode
python -m daily_learning.main --interactive
```

### Scheduled Automation

Set up automated daily runs:

```bash
# Configure scheduler in .env
SCHEDULER_ENABLED=true
SCHEDULER_RUN_TIME=08:00
SCHEDULER_WEEKDAYS_ONLY=true

# Run scheduler
python run_scheduler.py
```

### Docker Deployment

```bash
# Build image
docker build -t learning-feed-generator .

# Run with environment file
docker run --env-file .env learning-feed-generator

# Run scheduler
docker run -d --env-file .env --name learning-scheduler learning-feed-generator python run_scheduler.py
```

## API Setup Guide

### OpenAI API
1. Go to [OpenAI API](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` as `OPENAI_API_KEY`

### Notion API
1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the Internal Integration Token to `.env` as `NOTION_TOKEN`
4. Create a database in Notion
5. Share the database with your integration
6. Copy database ID from URL to `.env` as `NOTION_DATABASE_ID`

### Perplexity API (Optional)
1. Sign up at [Perplexity AI](https://www.perplexity.ai/)
2. Get API key from your account
3. Add to `.env` as `PERPLEXITY_API_KEY`

## Configuration Options

### Content Settings
```bash
MAX_ARTICLES_PER_TOPIC=5          # Articles to fetch per topic
CONTENT_MAX_AGE_HOURS=48          # Only include recent content
SUMMARY_SENTENCE_COUNT=4          # Length of summaries
QUIZ_QUESTIONS_PER_ARTICLE=2      # Quiz questions to generate
FLASHCARDS_PER_ARTICLE=3          # Flashcards to create
```

### Scheduler Settings
```bash
SCHEDULER_ENABLED=true            # Enable automated runs
SCHEDULER_RUN_TIME=08:00          # Daily run time (24h format)
SCHEDULER_WEEKDAYS_ONLY=true      # Skip weekends
SCHEDULER_RETRY_ATTEMPTS=3        # Retry failed runs
```

## Notion Database Schema

The application creates a database with these properties:

- **Title**: Article title
- **Topic**: Multi-select categories
- **Summary**: AI-generated summary
- **Source URL**: Original article link
- **Date Added**: When content was processed
- **Quiz Questions**: Generated quiz content
- **Flashcards**: Q&A pairs for review
- **Status**: New, Reviewed, Archived
- **Priority**: High, Medium, Low
- **Key Points**: Bullet point highlights
- **Learning Objectives**: Clear takeaways

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

## Error Handling & Monitoring

- Comprehensive logging to file and console
- API rate limiting and retry logic
- Graceful failure handling with fallbacks
- Health monitoring for scheduled runs
- Quality assessment for generated content

## Development

### Running Tests
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=daily_learning tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Troubleshooting

### Common Issues

**API Key Errors**
- Verify all API keys are correctly set in `.env`
- Check API key permissions and quotas

**Notion Connection Issues**
- Ensure database is shared with your integration
- Verify database ID is correct
- Check integration permissions

**Content Fetching Problems**
- Perplexity API may have rate limits
- RSS fallback will be used automatically
- Check network connectivity

### Logs
Check `daily_learning.log` for detailed error information.

## License

MIT License - see LICENSE file for details.

## Support

- Create an issue for bugs or feature requests
- Check existing issues for solutions
- Contribute improvements via pull requests
