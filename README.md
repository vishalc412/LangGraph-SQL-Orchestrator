# PostgreSQL AI Agent

Natural Language to SQL Query System powered by LangGraph, OpenAI GPT-4o-mini, and local LLMs.

## Features

- **Natural Language to SQL**: Convert plain English questions into PostgreSQL queries
- **Multi-LLM Support**: Use OpenAI GPT-4o-mini (cloud) or Llama 3.1 (local) via Ollama
- **LangGraph Orchestration**: Sophisticated agent workflow with state management
- **Memory Checkpointing**: Resume conversations seamlessly across sessions
- **Complex Query Support**: Handles JOINs, aggregations, window functions, CTEs, subqueries
- **Security First**: SQL injection prevention, query validation, read-only enforcement
- **Learning-Friendly**: Extensive documentation and commented code
- **Production-Ready**: Connection pooling, retry logic, comprehensive error handling
- **Multiple Deployment Options**: Local, Docker, AWS, Azure, GCP

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- OpenAI API key (for cloud LLM) OR Ollama (for local LLM)

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/postgresql-ai-agent.git
cd postgresql-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your credentials
```

### 2. Database Setup

```bash
# Create database
createdb movies_db

# Initialize schema and data
psql -d movies_db -f data/schema.sql
psql -d movies_db -f data/sample_data.sql
```

### 3. Run the Agent

```bash
# Interactive mode
python -m src.postgres_agent.main --interactive

# Single query
python -m src.postgres_agent.main --query "What are the highest-rated movies?"
```

### 4. Docker (Alternative)

```bash
# Start all services (PostgreSQL + Agent)
docker-compose up -d

# Access interactive mode
docker-compose exec agent python -m src.postgres_agent.main --interactive
```

## Example Queries

**Simple Queries:**
- "Show me all movies from 2020"
- "What are the highest-rated movies?"
- "Find movies starring Tom Hanks"

**Aggregations:**
- "What's the average rating by genre?"
- "How many movies were released each year?"
- "Which studios produced the most movies?"

**Complex Queries:**
- "Top 5 directors by average movie rating"
- "Movies that won Academy Awards with their cast"
- "Compare revenue trends between action and drama genres"

**Analytical:**
- "Rank movies by revenue within each genre"
- "Calculate budget-to-revenue ratio for high performers"
- "Show year-over-year growth in movie production"

## Architecture

```
User Input (Natural Language)
           |
           v
  +------------------+
  |   LangGraph      |
  |   State Machine  |
  +------------------+
           |
    +------+------+
    |             |
    v             v
+-------+    +--------+
|  LLM  |    |  DB    |
| (GPT/ |    | (Post- |
| Llama)|    | greSQL)|
+-------+    +--------+
    |             |
    +------+------+
           |
           v
  +------------------+
  | Formatted        |
  | Response         |
  +------------------+
```

### Workflow Steps:

1. **Schema Retrieval**: Get database structure
2. **SQL Generation**: Convert natural language to SQL using LLM
3. **Query Validation**: Security checks and syntax validation
4. **Query Execution**: Run SQL against PostgreSQL
5. **Result Formatting**: Present results in natural language

## Project Structure

```
postgresql-ai-agent/
├── src/
│   └── postgres_agent/
│       ├── config/           # Configuration management
│       ├── providers/        # LLM providers (OpenAI, Ollama)
│       ├── database/         # PostgreSQL client, validator, schema
│       ├── agents/           # LangGraph nodes and workflow
│       ├── prompts/          # Prompt templates and examples
│       ├── utils/            # Logging, retry logic, formatters
│       └── main.py           # Entry point
├── tests/                    # Unit and integration tests
├── data/                     # Database schema and sample data
├── docker-compose.yml        # Docker orchestration
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# LLM Provider
DEFAULT_LLM_PROVIDER="openai"  # or "ollama"
OPENAI_API_KEY="sk-..."
OPENAI_MODEL="gpt-4o-mini"

# Database
POSTGRES_DATABASE_URL="postgresql://user:pass@host:5432/movies_db"
POSTGRES_MAX_ROWS=1000
POSTGRES_QUERY_TIMEOUT=30

# Security
SECURITY_ENABLE_SQL_VALIDATION=true

# Memory
CHECKPOINTER_TYPE="sqlite"
CHECKPOINTER_SQLITE_PATH="./data/checkpoints.db"
```

## Security Features

- **SQL Injection Prevention**: Parameterized queries and input validation
- **Read-Only Enforcement**: Blocks INSERT, UPDATE, DELETE, DROP
- **Query Validation**: Syntax checking and security pattern detection
- **Connection Encryption**: SSL/TLS support
- **Audit Logging**: All queries logged for compliance

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/postgres_agent

# Run specific test file
pytest tests/test_query_validator.py

# Run with verbose output
pytest -v
```

## Deployment

### Local Development
```bash
python -m src.postgres_agent.main --interactive
```

### Docker
```bash
docker-compose up -d
```

### Cloud Deployment

The system supports deployment to:
- **AWS**: RDS + ECS
- **Azure**: Azure Database + Container Instances
- **GCP**: Cloud SQL + Cloud Run

See the documentation for detailed deployment guides.

## Database Schema

The sample movie database includes:
- **movies**: Main movie information
- **genres**: Genre categories
- **movie_genres**: Movie-genre relationships
- **people**: Actors, directors, writers
- **movie_cast**: Actor roles in movies
- **movie_crew**: Directors, writers, producers
- **ratings**: IMDb, Rotten Tomatoes, Metacritic scores
- **studios**: Production companies
- **movie_studios**: Movie-studio relationships
- **awards**: Academy Awards and other awards

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- LangChain team for LangGraph framework
- OpenAI for GPT-4o-mini
- Meta for Llama models
- PostgreSQL community
