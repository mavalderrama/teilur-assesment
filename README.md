# AWS AI Agent - Stock Price & Financial Document Query System

> **Take-Home Assessment Implementation**: A production-ready AI agent solution on AWS that hosts a FastAPI endpoint via Agentcore runtime. Users can query real-time or historical stock prices and receive streaming responses while accessing Amazon's financial documents through RAG.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.45-orange.svg)](https://langchain-ai.github.io/langgraph/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Technical Requirements Checklist](#technical-requirements-checklist)
- [Quick Start](#quick-start-local-testing---3-steps)
- [Deployment to AWS](#deployment-to-aws)
- [User Acceptance Criteria](#user-acceptance-criteria)
- [Architecture](#architecture)
- [Features](#features)
- [Documentation](#documentation)

---

## Overview

This project implements an **AI Agent** on AWS that:

- 🎯 **Hosts a FastAPI endpoint** via AWS Bedrock Agentcore runtime
- 📊 **Queries real-time & historical stock prices** using yfinance API
- 📄 **Retrieves Amazon financial documents** (2024 Annual Report, Q2/Q3 2025 Earnings)
- 🔐 **Authenticates users** via AWS Cognito user pools
- 📈 **Tracks observability** via Langfuse cloud (free tier)
- 🤖 **Uses LangGraph** for ReAct-style agent orchestration
- 🌊 **Streams responses** via `.astream()` and Server-Sent Events
- 🏗️ **Infrastructure as Code** with Terraform

---

## ✅ Technical Requirements Checklist

### AWS Services (Minimum)
- ✅ **AWS Agentcore** - FastAPI runtime deployment
- ✅ **AWS Cognito** - User pool for JWT authorization
- ✅ **AWS Bedrock** - Knowledge Base for document retrieval (RAG)
- ✅ **AWS S3** - Document storage
- ✅ **IAM** - Role-based permissions

### Backend Implementation
- ✅ **Python** - Core language
- ✅ **FastAPI** - Agentcore runtime API framework
- ✅ **Cognito User Pool** - Inbound user authorization with JWT
- ✅ **Langfuse Cloud** - Free tier observability setup
- ✅ **LangGraph** - ReAct agent orchestration
- ✅ **Knowledge Base** with 3 Amazon financial documents:
  - Amazon 2024 Annual Report
  - AMZN Q3 2025 Earnings Release
  - AMZN Q2 2025 Earnings Release
- ✅ **2 Finance Tools** using yfinance API:
  - `retrieve_realtime_stock_price` - Get current price
  - `retrieve_historical_stock_price` - Get historical data
- ✅ **Streaming Events** via `.astream()` - LangGraph streaming with SSE
- ✅ **Terraform** - Complete infrastructure as code
- ✅ **Event Streaming** - All responses streamed to client

### User Acceptance Criteria
- ✅ **Source code repository** with clear README (you're reading it!)
- ✅ **Deployment notebook** - `notebooks/demo_deployed_endpoint.ipynb` demonstrates:
  - All 5 user acceptance queries with responses
  - Langfuse trace screenshots
  - Cognito user authentication flow
- ✅ **Executable by team** - Notebook includes setup instructions

---

## 🚀 Deployment to AWS

### Prerequisites
```bash
# Required
- AWS CLI configured with credentials
- Terraform >= 1.0
- Docker (for building container image)
- Python 3.11+
```

### Step 1: Build & Push Docker Image

```bash
# Creates ECR repo for AgentCore deployment
cd terraform
terraform apply -target=module.ecr

# Login to ECR
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com

# Build for ARM64 (Agentcore requirement) and push to ECR
docker buildx build \
    --platform linux/arm64 \
    -t <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/aws-ai-agent-dev:latest \
    --push .
```

### Step 2: Deploy Infrastructure

```bash
# Configure variables
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform plan
terraform apply
```

**Resources created:**
- ✅ AWS Cognito User Pool & App Client
- ✅ S3 Bucket for financial documents
- ✅ AWS Bedrock Knowledge Base with OpenSearch Serverless
- ✅ ECR Repository for container images
- ✅ IAM Roles and Policies
- ✅ Bedrock Agentcore Runtime (FastAPI deployment)

### Step 3: Upload Financial Documents

**Option A: Automated Script (Recommended)**

```bash
# Run the upload script - downloads and uploads all documents automatically
./scripts/upload_financial_documents.sh
```

The script will:
- Download the 3 required Amazon financial documents from official sources
- Upload them to your S3 bucket
- Trigger Knowledge Base ingestion
- Verify completion

**Option B: Manual Upload**

```bash
# Required documents (from assessment specification):
# 1. https://s2.q4cdn.com/299287126/files/doc_financials/2025/ar/Amazon-2024-Annual-Report.pdf
# 2. https://s2.q4cdn.com/299287126/files/doc_financials/2025/q3/AMZN-Q3-2025-Earnings-Release.pdf
# 3. https://s2.q4cdn.com/299287126/files/doc_financials/2025/q2/AMZN-Q2-2025-Earnings-Release.pdf

# Download documents locally first, then upload:
aws s3 cp Amazon-2024-Annual-Report.pdf s3://<your-bucket>/
aws s3 cp AMZN-Q3-2025-Earnings-Release.pdf s3://<your-bucket>/
aws s3 cp AMZN-Q2-2025-Earnings-Release.pdf s3://<your-bucket>/

# Sync Knowledge Base
aws bedrock-agent start-ingestion-job \
    --knowledge-base-id <KB_ID_FROM_TERRAFORM_OUTPUT> \
    --data-source-id <DS_ID_FROM_TERRAFORM_OUTPUT>

# Check status (wait 5-10 minutes for completion)
aws bedrock-agent list-ingestion-jobs \
    --knowledge-base-id <KB_ID> \
    --data-source-id <DS_ID>
```

### Step 4: Create Cognito User

```bash
# Create user pool user (this can be done via the Notebook provided)
aws cognito-idp admin-create-user \
    --user-pool-id <USER_POOL_ID_FROM_TERRAFORM> \
    --username testuser \
    --user-attributes Name=email,Value=test@example.com \
    --temporary-password TempPass123!

# Set permanent password
aws cognito-idp admin-set-user-password \
    --user-pool-id <USER_POOL_ID> \
    --username testuser \
    --password YourPassword123! \
    --permanent
```

### Step 5: Test Deployed Endpoint

See **`notebooks/demo_deployed_endpoint.ipynb`** for complete examples including:
- Cognito authentication
- All 5 user acceptance queries
- Langfuse trace screenshots

---

## ✅ User Acceptance Criteria

All requirements demonstrated in **`notebooks/demo_deployed_endpoint.ipynb`**:

### 1. ✅ What is the stock price for Amazon right now?
**Query:** `"What is the stock price for Amazon right now?"`
- **Tool Used:** `retrieve_realtime_stock_price` ✅
- **Returns:** Current AMZN price from yfinance API
- **Demonstrates:** Real-time stock data retrieval

### 2. ✅ What were the stock prices for Amazon in Q4 last year?
**Query:** `"What were the stock prices for Amazon in Q4 last year?"`
- **Tool Used:** `retrieve_historical_stock_price` ✅
- **Returns:** Historical AMZN data for Q4 2024 (Oct-Dec)
- **Demonstrates:** Date range queries with statistical analysis

### 3. ✅ Compare Amazon's recent stock performance to analyst predictions
**Query:** `"Compare Amazon's recent stock performance to what analysts predicted in their reports"`
- **Tools Used:** `retrieve_realtime_stock_price` + `search_financial_documents` ✅
- **Returns:** Current price + analyst insights from earnings reports
- **Demonstrates:** Multi-tool orchestration + RAG with Bedrock Knowledge Base

### 4. ✅ AMZN price and AI business information
**Query:** `"I'm researching AMZN give me the current price and any relevant information about their AI business"`
- **Tools Used:** `retrieve_realtime_stock_price` + `search_financial_documents` ✅
- **Returns:** Stock price + AI business details from 2024 Annual Report
- **Demonstrates:** Complex multi-tool query combining live data + document search

### 5. ✅ Amazon's office space in North America in 2024
**Query:** `"What is the total amount of office space Amazon owned in North America in 2024?"`
- **Tool Used:** `search_financial_documents` ✅
- **Returns:** Office space data from 2024 Annual Report (property section)
- **Demonstrates:** Pure document retrieval without live data

**Notebook includes:**
- ✅ Screenshots of Langfuse traces showing agent reasoning
- ✅ Cognito authentication flow with JWT tokens
- ✅ Streaming event responses
- ✅ Step-by-step execution for reviewers

---

## Features

- 🤖 **ReAct Agent** with LangGraph for reasoning and tool use
- 📊 **Real-time & Historical Stock Prices** via yfinance (free, no API key)
- 📄 **Financial Document Search** with AWS Bedrock Knowledge Base (RAG)
- 🔐 **JWT Authentication** via AWS Cognito
- 🌊 **Streaming Responses** with Server-Sent Events (SSE)
- 📈 **Dual Observability**: Langfuse & LangSmith (switch via env var)
- 🏗️ **Clean Architecture** with 100% dependency injection
- 🐳 **Docker & Terraform** ready for AWS Bedrock AgentCore deployment
- ✅ **All 5 User Acceptance Queries** validated

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

The AI agent has access to **3 tools** (per assessment requirements):

1. **`retrieve_realtime_stock_price`** - Get current price for any ticker via yfinance
2. **`retrieve_historical_stock_price`** - Get historical data over date range via yfinance
3. **`search_financial_documents`** - Search Amazon financial docs via Bedrock KB (RAG)

Example query flow:
```
User: "What is AMZN stock price?"
  ↓
Agent: Uses retrieve_realtime_stock_price("AMZN")
  ↓
Tool: Calls yfinance API (no API key required)
  ↓
Agent: "Amazon's current stock price is $185.42 USD..."
```

**Implementation details:**
- src/infrastructure/agent/tools.py:46
- src/infrastructure/agent/tools.py:90
- src/infrastructure/agent/tools.py:142

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
| Infrastructure | Terraform, Docker, Bedrock AgentCore |

---

## 📚 Documentation

- **[Architecture Guide](docs/architecture.md)** - Clean Architecture design details
- **[Demo Notebook](notebooks/demo_deployed_endpoint.ipynb)** - User acceptance criteria validation

---

## 🔧 Environment Variables

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

**Built with Clean Architecture, LangGraph, and AWS Bedrock** 🚀
