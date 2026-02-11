# Local Testing Guide

This guide explains how to test the AWS AI Agent project locally before deploying to AWS.

---

## Prerequisites

### Required Software
- **Python 3.11+** (check: `python --version`)
- **Docker & Docker Compose** (optional, for containerized testing)
- **Git** (for cloning the repository)

### Required Accounts (Free Tier)
1. **AWS Account** - For Bedrock API access
2. **Langfuse** OR **LangSmith** - For observability (optional but recommended)

---

## Quick Start (5 minutes)

### 1. Clone & Setup

```bash
# Clone repository
git clone <your-repo-url>
cd assesment

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

**Minimum configuration for local testing:**

```bash
# AWS Configuration (REQUIRED)
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key

# Bedrock Model (uses default if not set)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Observability (OPTIONAL - can skip for basic testing)
OBSERVABILITY_PROVIDER=none  # Set to "langfuse" or "langsmith" if you have credentials

# Mock Cognito (for local testing without AWS Cognito)
COGNITO_USER_POOL_ID=local-test-pool
COGNITO_APP_CLIENT_ID=local-test-client
```

### 3. Run Locally

```bash
# Start FastAPI server
uvicorn src.presentation.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 4. Test Health Check

```bash
# Open new terminal
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-11T10:30:00.123456",
  "version": "1.0.0"
}
```

---

## Testing Without AWS Cognito

For local testing, you can **bypass Cognito authentication** by creating a mock auth service.

### Option 1: Disable Authentication (Quick Test)

Create a mock auth file:

```bash
# Create mock auth service
cat > src/infrastructure/aws/mock_cognito_auth.py << 'EOF'
"""Mock Cognito auth for local testing."""
from typing import Any

class MockCognitoAuthService:
    """Mock authentication service for local development."""

    def __init__(self, *args, **kwargs):
        pass

    async def verify_token(self, token: str) -> dict[str, Any]:
        """Mock token verification - always returns valid user."""
        return {
            "sub": "local-test-user-123",
            "email": "test@localhost.dev",
            "cognito:username": "testuser"
        }

    async def authenticate_user(self, username: str, password: str) -> dict[str, str]:
        """Mock authentication - returns fake tokens."""
        return {
            "access_token": "mock-access-token",
            "id_token": "mock-id-token",
            "refresh_token": "mock-refresh-token"
        }
EOF
```

Update DI container to use mock auth:

```python
# In src/di/container.py, add at top:
import os

# Modify cognito_service property:
@property
def cognito_service(self):
    if os.getenv("ENVIRONMENT") == "development":
        from src.infrastructure.aws.mock_cognito_auth import MockCognitoAuthService
        if self._cognito_service is None:
            self._cognito_service = MockCognitoAuthService()
    else:
        # Production Cognito auth
        if self._cognito_service is None:
            if not self.cognito_user_pool_id or not self.cognito_app_client_id:
                raise ValueError("Cognito environment variables not set")
            self._cognito_service = CognitoAuthService(
                user_pool_id=self.cognito_user_pool_id,
                app_client_id=self.cognito_app_client_id,
                region=self.aws_region,
            )
    return self._cognito_service
```

Set environment:
```bash
export ENVIRONMENT=development
```

### Option 2: Use Postman/cURL with Mock Token

Skip the `/auth/login` endpoint and use any token value:

```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is 2+2?", "stream": false}'
```

---

## Testing Stock Price Queries

### Test 1: Realtime Stock Price (yfinance - No AWS Required)

```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the current stock price for Amazon (AMZN)?",
    "stream": false
  }'
```

**Expected:** Agent uses `get_realtime_stock_price` tool and returns current AMZN price from yfinance.

### Test 2: Historical Stock Prices

```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What were the stock prices for Amazon in October 2024?",
    "stream": false
  }'
```

**Expected:** Agent uses `get_historical_stock_prices` tool with date range.

### Test 3: Document Search (Requires Bedrock Knowledge Base)

⚠️ **Note:** This requires AWS Bedrock Knowledge Base setup. Skip if not configured.

```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Amazon'\''s AI strategy according to their annual report?",
    "stream": false
  }'
```

---

## Testing with Streaming (Server-Sent Events)

### Using cURL

```bash
curl -N -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the stock price for Amazon?",
    "stream": true
  }'
```

**Expected output (streaming):**
```
data: {"event_type": "agent_step", "data": {...}, "timestamp": "..."}

data: {"event_type": "tool_call", "data": {"tool": "get_realtime_stock_price", ...}, "timestamp": "..."}

data: {"event_type": "tool_execution", "data": {...}, "timestamp": "..."}

data: {"event_type": "final_answer", "data": {"answer": "Amazon's current stock price is $185.42..."}, "timestamp": "..."}
```

### Using Python Client

```python
import requests
import json

url = "http://localhost:8000/agent/query"
headers = {
    "Authorization": "Bearer mock-token",
    "Content-Type": "application/json"
}
data = {
    "query": "What is the stock price for Amazon?",
    "stream": True
}

response = requests.post(url, headers=headers, json=data, stream=True)

for line in response.iter_lines():
    if line:
        line_str = line.decode('utf-8')
        if line_str.startswith('data: '):
            event_data = json.loads(line_str[6:])
            print(f"Event: {event_data['event_type']}")
            print(f"Data: {event_data['data']}\n")
```

---

## Testing with Docker Compose

### 1. Build and Run

```bash
# Build image
docker-compose build

# Start container
docker-compose up
```

### 2. Test API

```bash
# Health check
curl http://localhost:8000/health

# Query agent
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AMZN stock price?", "stream": false}'
```

### 3. View Logs

```bash
# Follow logs
docker-compose logs -f api

# Stop container
docker-compose down
```

---

## Testing Individual Components

### Test 1: YFinance Stock Repository

```python
import asyncio
from src.infrastructure.repositories.yfinance_stock_repository import YFinanceStockRepository

async def test_stock_repo():
    repo = YFinanceStockRepository()

    # Test realtime price
    price = await repo.get_realtime_price("AMZN")
    print(f"Symbol: {price.symbol}")
    print(f"Price: ${price.price}")
    print(f"Volume: {price.volume:,}")

    # Test historical prices
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)

    hist = await repo.get_historical_prices("AMZN", start_date, end_date)
    print(f"\nHistorical prices: {len(hist.prices)} data points")
    print(f"Average: ${hist.average_price:.2f}")
    print(f"Highest: ${hist.highest_price:.2f}")
    print(f"Lowest: ${hist.lowest_price:.2f}")

asyncio.run(test_stock_repo())
```

Run:
```bash
python -c "
import asyncio
from src.infrastructure.repositories.yfinance_stock_repository import YFinanceStockRepository
from datetime import datetime, timedelta

async def test():
    repo = YFinanceStockRepository()
    price = await repo.get_realtime_price('AMZN')
    print(f'AMZN Price: \${price.price}')

asyncio.run(test())
"
```

### Test 2: LangGraph Agent (Mock LLM)

Create a test script:

```python
# test_agent.py
import asyncio
from src.infrastructure.agent.tools import AgentTools
from src.application.use_cases.get_realtime_stock_price import GetRealtimeStockPriceUseCase
from src.application.use_cases.get_historical_stock_price import GetHistoricalStockPriceUseCase
from src.application.use_cases.query_documents import QueryDocumentsUseCase
from src.infrastructure.repositories.yfinance_stock_repository import YFinanceStockRepository

async def test_tools():
    # Setup
    stock_repo = YFinanceStockRepository()
    realtime_uc = GetRealtimeStockPriceUseCase(stock_repo)
    historical_uc = GetHistoricalStockPriceUseCase(stock_repo)

    # Create tools (without document search for now)
    tools = AgentTools(
        get_realtime_price_uc=realtime_uc,
        get_historical_price_uc=historical_uc,
        query_documents_uc=None  # Skip for local test
    )

    # Get tools
    tool_list = tools.create_tools()

    # Test realtime price tool
    realtime_tool = tool_list[0]
    result = await realtime_tool.ainvoke({"symbol": "AMZN"})
    print("Realtime Price Tool Result:")
    print(result)

asyncio.run(test_tools())
```

Run:
```bash
python test_agent.py
```

---

## Common Issues & Solutions

### Issue 1: AWS Credentials Error

**Error:**
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Solution:**
```bash
# Option 1: Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1

# Option 2: Use AWS CLI configuration
aws configure

# Option 3: Add to .env file
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue 2: Bedrock Model Access Error

**Error:**
```
You don't have access to the model with the specified model ID
```

**Solution:**
1. Go to AWS Console → Bedrock → Model Access
2. Request access to Claude 3 Sonnet model
3. Wait for approval (usually instant)
4. Retry

**Alternative:** Test without Bedrock by mocking the LLM service (see below).

### Issue 3: Port Already in Use

**Error:**
```
ERROR:    [Errno 48] Address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill the process
kill -9 $(lsof -ti:8000)

# Or use different port
uvicorn src.presentation.api.main:app --port 8001
```

### Issue 4: Module Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Or install specific module
pip install langchain
```

---

## Testing Without AWS Bedrock

If you don't have Bedrock access, you can mock the LLM for basic testing:

### Create Mock LLM Service

```python
# src/infrastructure/services/mock_llm_service.py
from typing import Any, AsyncIterator
from src.domain.interfaces.llm_service import ILLMService

class MockLLMService(ILLMService):
    """Mock LLM for local testing without Bedrock."""

    async def generate(self, prompt: str, **kwargs) -> str:
        return f"Mock response to: {prompt}"

    async def generate_stream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        words = ["This", "is", "a", "mock", "streaming", "response"]
        for word in words:
            yield f"{word} "

    async def embed_text(self, text: str) -> list[float]:
        return [0.1] * 1536  # Mock embedding
```

Update DI container:
```python
# In src/di/container.py
if os.getenv("USE_MOCK_LLM") == "true":
    from src.infrastructure.services.mock_llm_service import MockLLMService
    # Use mock instead of Bedrock
```

Set environment:
```bash
export USE_MOCK_LLM=true
```

---

## Observability Testing

### Test with Langfuse (Free Tier)

1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com)
2. Get API keys from Settings
3. Configure:
```bash
OBSERVABILITY_PROVIDER=langfuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```
4. Run queries and view traces in Langfuse dashboard

### Test with LangSmith (Free Tier)

1. Sign up at [smith.langchain.com](https://smith.langchain.com)
2. Create project and get API key
3. Configure:
```bash
OBSERVABILITY_PROVIDER=langsmith
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=aws-ai-agent
```
4. Run queries and view traces in LangSmith UI

### Test Without Observability

```bash
OBSERVABILITY_PROVIDER=none
```

Agent will work normally without tracing.

---

## Running Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/domain/test_stock_price.py

# View coverage report
open htmlcov/index.html
```

---

## Interactive Testing with Jupyter Notebook

Create a test notebook:

```bash
# Install Jupyter
pip install jupyter

# Start Jupyter
jupyter notebook
```

Create `local_test.ipynb`:

```python
# Cell 1: Setup
import asyncio
from src.di.container import DIContainer

container = DIContainer()

# Cell 2: Test Stock Repository
stock_repo = container.stock_repository
price = await stock_repo.get_realtime_price("AMZN")
print(f"AMZN: ${price.price}")

# Cell 3: Test Agent
orchestrator = container.agent_orchestrator
result = await orchestrator.process_query(
    "What is the stock price for Amazon?",
    user_id="test-user"
)
print(result.answer)

# Cell 4: Test Streaming
async for event in orchestrator.process_query_stream(
    "What is AMZN stock price?",
    user_id="test-user"
):
    print(f"{event.event_type}: {event.data}")
```

---

## Summary: Minimal Local Testing Setup

**1. Install dependencies:**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure (minimal):**
```bash
# .env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
ENVIRONMENT=development
OBSERVABILITY_PROVIDER=none
```

**3. Run:**
```bash
uvicorn src.presentation.api.main:app --reload
```

**4. Test:**
```bash
curl http://localhost:8000/health

curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer test" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is AMZN stock price?", "stream": false}'
```

---

**That's it!** You can now test the entire agent locally with just AWS credentials (for Bedrock) and yfinance (free, no API key needed).

For full UAC testing with document retrieval, you'll need to set up AWS Bedrock Knowledge Base with the 3 Amazon financial documents.
