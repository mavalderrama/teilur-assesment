# LangSmith Observability Integration

## Overview

The AWS AI Agent now supports **dual observability providers**: **Langfuse** and **LangSmith**. Both providers are integrated through a unified `IObservabilityService` interface, ensuring complete adherence to Clean Architecture principles with dependency injection.

---

## Architecture

### Unified Observability Interface

The system uses a domain-level interface that both providers implement:

```
Domain Layer (src/domain/interfaces/)
    └── IObservabilityService  ← Interface definition

Infrastructure Layer (src/infrastructure/services/)
    ├── LangfuseObservabilityService  ← Langfuse implementation
    └── LangSmithObservabilityService  ← LangSmith implementation

DI Container (src/di/container.py)
    └── Dynamically injects the correct service based on env config
```

### Key Interface Methods

```python
class IObservabilityService(ABC):
    def create_trace(name, user_id, metadata) -> str
    def log_llm_generation(trace_id, name, model, input_data, output_data, metadata)
    def log_tool_execution(trace_id, tool_name, tool_input, tool_output, error, metadata)
    def log_span(trace_id, name, start_time, end_time, metadata)
    def complete_trace(trace_id, outputs, error)
    def get_trace_url(trace_id) -> str
    def flush()
```

---

## Configuration

### Environment Variables

Set the observability provider via environment variable:

```bash
# Choose provider: "langfuse" or "langsmith"
OBSERVABILITY_PROVIDER=langsmith

# LangSmith Configuration
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
LANGSMITH_PROJECT=aws-ai-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Langfuse Configuration (alternative)
# OBSERVABILITY_PROVIDER=langfuse
# LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# LANGFUSE_HOST=https://cloud.langfuse.com
```

### DI Container Logic

The `DIContainer` automatically instantiates the correct service:

```python
@property
def observability_service(self) -> IObservabilityService | None:
    if self.observability_provider == "langsmith":
        if self.langsmith_api_key:
            return LangSmithObservabilityService(
                api_key=self.langsmith_api_key,
                project_name=self.langsmith_project,
                endpoint=self.langsmith_endpoint,
            )
    elif self.observability_provider == "langfuse":
        if self.langfuse_public_key and self.langfuse_secret_key:
            return LangfuseObservabilityService(
                public_key=self.langfuse_public_key,
                secret_key=self.langfuse_secret_key,
                host=self.langfuse_host,
            )
    return None  # Observability is optional
```

---

## LangSmith Features

### Automatic LangChain Integration

LangSmith sets environment variables to enable automatic tracing for LangChain/LangGraph:

```python
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = api_key
os.environ["LANGCHAIN_PROJECT"] = project_name
os.environ["LANGCHAIN_ENDPOINT"] = endpoint
```

This means **all LangChain/LangGraph operations are automatically traced** without additional code!

### Trace Hierarchy

```
Run (Trace Root)
├── LLM Generation
│   ├── Input: User query
│   ├── Output: Agent response
│   └── Metadata: model, tokens, execution time
├── Tool Execution
│   ├── Input: Tool name + parameters
│   ├── Output: Tool result
│   └── Metadata: tool name, duration
└── Span (Time-bounded operation)
    ├── Start time
    ├── End time
    └── Metadata: custom data
```

### LangSmith Client API

The service uses the official LangSmith Python SDK:

```python
from langsmith import Client

client = Client(api_key=api_key, api_url=endpoint)

# Create runs
run = client.create_run(
    name="agent_query",
    run_type="chain",  # or "llm", "tool"
    inputs={"query": "..."},
    project_name="aws-ai-agent",
    parent_run_id=None,  # for nested runs
    tags=["production"],
    extra={"user_id": "..."},
)

# Update runs
client.update_run(
    run_id=run.id,
    outputs={"answer": "..."},
    error=None,
    end_time=datetime.now(),
)
```

---

## Usage Examples

### Example 1: Agent Query with LangSmith

```python
# User query
query = "What is the stock price for Amazon right now?"

# 1. Create trace
trace_id = observability_service.create_trace(
    name="agent_query",
    user_id="user_123",
    metadata={"query": query}
)

# 2. Log LLM generation
observability_service.log_llm_generation(
    trace_id=trace_id,
    name="claude_reasoning",
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    input_data=query,
    output_data="Let me check the current price...",
    metadata={"temperature": 0.7}
)

# 3. Log tool execution
observability_service.log_tool_execution(
    trace_id=trace_id,
    tool_name="get_realtime_stock_price",
    tool_input={"symbol": "AMZN"},
    tool_output="Stock: AMZN\nCurrent Price: $185.42...",
    metadata={"duration_ms": 1200}
)

# 4. Complete trace
observability_service.complete_trace(
    trace_id=trace_id,
    outputs={"answer": "Amazon's current stock price is $185.42"}
)

# 5. Get trace URL
url = observability_service.get_trace_url(trace_id)
print(f"View trace: {url}")
```

### Example 2: Switching Between Providers

```bash
# Use Langfuse
export OBSERVABILITY_PROVIDER=langfuse
export LANGFUSE_PUBLIC_KEY=pk-lf-xxxxx
export LANGFUSE_SECRET_KEY=sk-lf-xxxxx

# Use LangSmith
export OBSERVABILITY_PROVIDER=langsmith
export LANGSMITH_API_KEY=lsv2_pt_xxxxx
export LANGSMITH_PROJECT=my-project

# Restart application - no code changes needed!
python -m src.presentation.api.main
```

---

## Benefits of Unified Interface

### 1. **Dependency Injection**
- Both services are injected via the same interface
- No hard dependencies on specific observability providers
- Fully testable with mock implementations

### 2. **Clean Architecture Compliance**
- Domain layer defines the contract (`IObservabilityService`)
- Infrastructure layer provides implementations
- Application and presentation layers depend only on the interface

### 3. **Swappable Implementations**
- Switch between Langfuse and LangSmith via env variable
- Add new observability providers by implementing the interface
- No code changes required to switch providers

### 4. **Consistent API**
- Same method calls regardless of provider
- Uniform trace structure across providers
- Simplified agent orchestrator code

---

## Comparison: Langfuse vs LangSmith

| Feature | Langfuse | LangSmith |
|---------|----------|-----------|
| **Provider** | Open-source, cloud/self-hosted | LangChain official |
| **Integration** | Manual trace logging | Automatic LangChain tracing |
| **SDK** | `langfuse` | `langsmith` + auto env vars |
| **Trace Model** | Trace → Generation/Event/Span | Run hierarchy with nesting |
| **UI** | Langfuse cloud dashboard | LangSmith UI |
| **Pricing** | Free tier available | Free tier available |
| **Best For** | Custom tracing, multi-framework | LangChain/LangGraph heavy apps |

---

## LangSmith Setup

### 1. Create LangSmith Account
- Go to [smith.langchain.com](https://smith.langchain.com)
- Sign up for free account
- Create a new project (e.g., "aws-ai-agent")

### 2. Get API Key
- Navigate to Settings → API Keys
- Create new API key
- Copy the key (starts with `lsv2_pt_`)

### 3. Configure Application
```bash
# .env file
OBSERVABILITY_PROVIDER=langsmith
LANGSMITH_API_KEY=lsv2_pt_your_key_here
LANGSMITH_PROJECT=aws-ai-agent
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

### 4. Run Application
```bash
# Load environment
source .env

# Start FastAPI
uvicorn src.presentation.api.main:app --reload

# Or use Docker
docker-compose up
```

### 5. View Traces
- Go to [smith.langchain.com](https://smith.langchain.com)
- Select your project
- View traces in real-time as queries are processed

---

## Trace Structure in LangSmith

### Root Trace (Chain)
```
agent_query
├── user_id: "user_123"
├── query: "What is the stock price for Amazon?"
├── tags: ["agent", "production"]
└── metadata: {...}
```

### LLM Generation (Child Run)
```
claude_reasoning
├── parent: agent_query
├── type: llm
├── input: "What is the stock price for Amazon?"
├── output: "Let me check the current price..."
├── model: "anthropic.claude-3-sonnet-20240229-v1:0"
└── tokens: {prompt: 245, completion: 78}
```

### Tool Execution (Child Run)
```
tool_get_realtime_stock_price
├── parent: agent_query
├── type: tool
├── input: {"symbol": "AMZN"}
├── output: "Stock: AMZN\nCurrent Price: $185.42..."
└── duration: 1200ms
```

---

## Testing

### Unit Test with Mock Observability

```python
from unittest.mock import Mock
from src.domain.interfaces.observability_service import IObservabilityService

# Create mock
mock_observability = Mock(spec=IObservabilityService)
mock_observability.create_trace.return_value = "trace_123"

# Inject into orchestrator
orchestrator = LangGraphOrchestrator(
    llm_model_id="...",
    region="us-east-1",
    agent_tools=agent_tools,
    observability_service=mock_observability,
)

# Execute query
result = await orchestrator.process_query("What is AMZN price?", "user_123")

# Verify trace was created
mock_observability.create_trace.assert_called_once_with(
    name="agent_query",
    user_id="user_123",
    metadata={"query": "What is AMZN price?"}
)
```

### Integration Test with Real LangSmith

```python
import os
from src.infrastructure.services.langsmith_observability import LangSmithObservabilityService

# Set up test environment
os.environ["LANGSMITH_API_KEY"] = "test_key"
os.environ["LANGSMITH_PROJECT"] = "test-project"

# Create service
service = LangSmithObservabilityService(
    api_key=os.getenv("LANGSMITH_API_KEY"),
    project_name="test-project"
)

# Test trace creation
trace_id = service.create_trace(
    name="test_query",
    user_id="test_user",
    metadata={"test": True}
)

assert trace_id is not None
print(f"Trace created: {service.get_trace_url(trace_id)}")
```

---

## Troubleshooting

### Issue: Traces not appearing in LangSmith

**Solution:**
1. Check API key is valid
2. Verify `LANGCHAIN_TRACING_V2=true` is set
3. Ensure `LANGCHAIN_PROJECT` matches your project name
4. Check network connectivity to `https://api.smith.langchain.com`

### Issue: "Invalid API key" error

**Solution:**
- Regenerate API key in LangSmith UI
- Ensure key starts with `lsv2_pt_`
- Check for extra spaces in env variable

### Issue: Want to use both Langfuse AND LangSmith

**Solution:**
Currently, only one provider can be active at a time. To use both:
1. Create a composite observability service that implements `IObservabilityService`
2. Forward calls to both Langfuse and LangSmith services
3. Inject the composite service into the DI container

Example:
```python
class CompositeObservabilityService(IObservabilityService):
    def __init__(self, langfuse: LangfuseObservabilityService, langsmith: LangSmithObservabilityService):
        self.langfuse = langfuse
        self.langsmith = langsmith

    def create_trace(self, name, user_id, metadata):
        trace_id_lf = self.langfuse.create_trace(name, user_id, metadata)
        trace_id_ls = self.langsmith.create_trace(name, user_id, metadata)
        return f"{trace_id_lf}|{trace_id_ls}"  # Composite ID
```

---

## Summary

✅ **LangSmith fully integrated** with dependency injection
✅ **Unified interface** (`IObservabilityService`) for both providers
✅ **Environment-based switching** (no code changes)
✅ **Clean Architecture compliant** (domain interface, infrastructure implementations)
✅ **Automatic LangChain tracing** when using LangSmith
✅ **Trace URLs** for viewing in LangSmith UI

The system can now use **either Langfuse or LangSmith** for observability by simply changing the `OBSERVABILITY_PROVIDER` environment variable!

---

**Last Updated**: 2026-02-11
**Version**: 1.0.0
**Status**: Integration Complete ✅
