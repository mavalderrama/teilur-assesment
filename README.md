# AWS AI Agent - Stock Price & Financial Document Query System

A production-ready AI agent built with **Clean Architecture**, **LangGraph**, and **AWS Bedrock** that answers questions about stock prices and financial documents using streaming responses.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.45-orange.svg)](https://langchain-ai.github.io/langgraph/)

---

## Quick Start (Local Testing - 3 Steps)

### 1. Install

```bash
# Clone repository
git clone <repo-url>
cd assesment

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy environment template
cp .env.example .env
```

Edit `.env` with **minimum configuration**:
```bash
# AWS credentials (REQUIRED)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# For local testing (bypass Cognito)
ENVIRONMENT=development

# Optional: disable observability for quick testing
OBSERVABILITY_PROVIDER=none
```

### 3. Run & Test

```bash
# Start server
uvicorn src.presentation.api.main:app --reload

# In another terminal - test it!
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AMZN stock price?", "stream": false}'
```

**✅ That's it! The agent will fetch realtime stock prices using yfinance (no API key needed).**

📖 **For detailed testing guide, see:** [docs/LOCAL_TESTING_GUIDE.md](docs/LOCAL_TESTING_GUIDE.md)

---

## Features

- 🤖 **ReAct Agent** with LangGraph for reasoning and tool use
- 📊 **Real-time & Historical Stock Prices** via yfinance (free, no API key)
- 📄 **Financial Document Search** with AWS Bedrock Knowledge Base (RAG)
- 🔐 **JWT Authentication** via AWS Cognito
- 🌊 **Streaming Responses** with Server-Sent Events (SSE)
- 📈 **Dual Observability**: Langfuse & LangSmith (switch via env var)
- 🏗️ **Clean Architecture** with 100% dependency injection
- 🐳 **Docker & Terraform** ready for AWS deployment
- ✅ **5 User Acceptance Queries** demonstrated

---

## Architecture

Built following **Clean Architecture** principles:

```
┌──────────────────────────────────────────┐
│   Presentation (FastAPI + SSE)           │
├──────────────────────────────────────────┤
│   Application (Use Cases)                │
├──────────────────────────────────────────┤
│   Domain (Entities + Interfaces)         │ ← Core (ZERO dependencies)
├──────────────────────────────────────────┤
│   Infrastructure (AWS + Repos + Agent)   │
└──────────────────────────────────────────┘
              ↑
    Dependency Injection Container
```

**Key Principles:**
- ✅ Domain layer has ZERO external dependencies
- ✅ All dependencies injected via constructors
- ✅ Interface-based design (can swap implementations)
- ✅ 100% testable with mocks

---

## Agent Tools

The AI agent has access to **3 tools**:

1. **`get_realtime_stock_price`** - Get current price for any ticker
2. **`get_historical_stock_prices`** - Get historical data over date range
3. **`search_financial_documents`** - Search Amazon financial docs (RAG)

Example query flow:
```
User: "What is AMZN stock price?"
  ↓
Agent: Uses get_realtime_stock_price("AMZN")
  ↓
Tool: Calls yfinance API
  ↓
Agent: "Amazon's current stock price is $185.42 USD..."
```

---

## API Endpoints

### Health Check
```bash
GET /health
```

### Agent Query (Non-streaming)
```bash
POST /agent/query
{
  "query": "What is the stock price for Amazon?",
  "stream": false
}
```

### Agent Query (Streaming SSE)
```bash
POST /agent/query
{
  "query": "What is the stock price for Amazon?",
  "stream": true
}
```

Response: Server-Sent Events with real-time agent progress

---

## Testing Locally

See comprehensive guide: **[docs/LOCAL_TESTING_GUIDE.md](docs/LOCAL_TESTING_GUIDE.md)**

Covers:
- Testing without AWS Cognito (mock auth)
- Testing without Bedrock (mock LLM)
- Stock price queries (works out of the box)
- Streaming responses
- Docker Compose testing
- Jupyter notebook examples

---

## Observability

**Dual provider support** via unified interface:

### Langfuse (Default)
```bash
OBSERVABILITY_PROVIDER=langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxx
```

### LangSmith
```bash
OBSERVABILITY_PROVIDER=langsmith
LANGSMITH_API_KEY=lsv2_pt_xxxxx
LANGSMITH_PROJECT=aws-ai-agent
```

**Switch providers with zero code changes!**

See: [docs/LANGSMITH_INTEGRATION.md](docs/LANGSMITH_INTEGRATION.md)

---

## Deployment

### Docker
```bash
docker-compose up --build
curl http://localhost:8000/health
```

### AWS (Terraform)
```bash
cd terraform
terraform init
terraform apply
# Creates: VPC, Cognito, S3, Bedrock KB, ECS Fargate, ALB
```

---

## Project Structure

```
src/
├── domain/              # Core entities & interfaces (ZERO dependencies)
│   ├── entities/        # StockPrice, Document, QueryResult
│   └── interfaces/      # IStockRepository, ILLMService, IObservabilityService
├── application/         # Business logic (use cases)
│   ├── use_cases/       # GetRealtimePrice, GetHistoricalPrice
│   └── interfaces/      # IAgentOrchestrator
├── infrastructure/      # External integrations
│   ├── repositories/    # YFinance, Bedrock
│   ├── services/        # LLM, Auth, Observability
│   ├── agent/           # LangGraph ReAct orchestrator
│   └── aws/             # AWS clients
├── presentation/        # API layer
│   └── api/             # FastAPI routes + streaming
└── di/                  # Dependency injection container
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.115.0 |
| Agent | LangGraph 0.2.45 (ReAct) |
| LLM | AWS Bedrock (Claude 3 Sonnet) |
| RAG | AWS Bedrock Knowledge Base |
| Auth | AWS Cognito (JWT) |
| Stock Data | yfinance 0.2.48 |
| Observability | Langfuse / LangSmith |
| Infrastructure | Terraform, Docker, ECS |

---

## Documentation

- **[Local Testing Guide](docs/LOCAL_TESTING_GUIDE.md)** - How to test locally
- **[Architecture](docs/architecture.md)** - System design
- **[LangSmith Integration](docs/LANGSMITH_INTEGRATION.md)** - Observability setup
- **[Scaffolding Complete](SCAFFOLDING_COMPLETE.md)** - Implementation summary

---

## User Acceptance Criteria

All 5 queries demonstrated in `notebooks/demo.ipynb`:

1. ✅ "What is the stock price for Amazon right now?"
2. ✅ "What were the stock prices for Amazon in Q4 last year?"
3. ✅ "Compare Amazon's recent stock performance to analyst predictions"
4. ✅ "Give me AMZN price and AI business information"
5. ✅ "What is Amazon's total office space in North America in 2024?"

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AWS_REGION` | Yes | us-east-2 | AWS region |
| `BEDROCK_LLM_REGION` | No | us-east-2 | Region where Bedrock LLM runs (can differ from AWS_REGION) |
| `AWS_ACCESS_KEY_ID` | Yes | - | AWS credentials |
| `BEDROCK_MODEL_ID` | No | claude-3-sonnet | Bedrock model |
| `OBSERVABILITY_PROVIDER` | No | langfuse | langfuse/langsmith/none |
| `ENVIRONMENT` | No | production | Set to "development" for local testing |

See `.env.example` for complete list.

---

## License

MIT

---

**Built with Clean Architecture, LangGraph, and AWS Bedrock** 🚀


1. Upload documents to S3

# Single file
aws s3 cp /path/to/document.pdf s3://maval-bedrock-knowledge-base-dev/

# Entire folder
aws s3 cp /path/to/docs/ s3://maval-bedrock-knowledge-base-dev/ --recursive

Supported formats: PDF, TXT, MD, HTML, DOC/DOCX, CSV, XLS/XLSX, and more.

2. Sync the Knowledge Base data source

aws bedrock-agent start-ingestion-job \
--knowledge-base-id DYAHO3ATNU \
--data-source-id 7XHJWC0VDD

3. Check ingestion status

aws bedrock-agent list-ingestion-jobs \
--knowledge-base-id DYAHO3ATNU \
--data-source-id 7XHJWC0VDD
