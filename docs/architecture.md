# AWS AI Agent - Architecture Documentation

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER / CLIENT                               │
│                     (Jupyter Notebook, HTTP Client)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       AWS Application Load Balancer                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS ECS Fargate Service                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      FastAPI Application                          │  │
│  │                                                                   │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │  │
│  │  │  /auth/login    │  │  /agent/query   │  │    /health      │  │  │
│  │  │  (Cognito JWT)  │  │  (SSE Stream)   │  │                 │  │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘  │  │
│  │                                                                   │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │           LangGraph Agent Orchestrator                     │  │  │
│  │  │              (ReAct Pattern)                               │  │  │
│  │  │                                                            │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐    │  │  │
│  │  │  │  Tool 1  │  │  Tool 2  │  │      Tool 3          │    │  │  │
│  │  │  │ Realtime │  │Historical│  │  Search Financial    │    │  │  │
│  │  │  │  Price   │  │  Prices  │  │     Documents        │    │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────────────────┘    │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
        │                    │                           │
        │                    │                           │
        ▼                    ▼                           ▼
┌──────────────┐   ┌──────────────────┐      ┌──────────────────────┐
│ AWS Cognito  │   │  AWS Bedrock     │      │   AWS Bedrock        │
│  User Pool   │   │  (Claude 3)      │      │  Knowledge Base      │
│              │   │                  │      │                      │
│  - JWT Auth  │   │  - LLM Calls     │      │  - Vector Search     │
│  - Users     │   │  - Streaming     │      │  - RAG Retrieval     │
└──────────────┘   └──────────────────┘      └──────────────────────┘
                                                        │
                                                        ▼
                                              ┌──────────────────────┐
                                              │      AWS S3          │
                                              │  Documents Bucket    │
                                              │                      │
                                              │  - Annual Reports    │
                                              │  - Earnings Releases │
                                              └──────────────────────┘

                    ┌─────────────────────────┐
                    │   Langfuse Cloud        │
                    │   (Observability)       │
                    │                         │
                    │  - Traces               │
                    │  - Generations          │
                    │  - Tool Executions      │
                    └─────────────────────────┘

                    ┌─────────────────────────┐
                    │   yfinance API          │
                    │   (Stock Prices)        │
                    │                         │
                    │  - Realtime Data        │
                    │  - Historical Data      │
                    └─────────────────────────┘
```

## Clean Architecture Layers

### Layer 1: Domain (Core)
**Location**: `src/domain/`
**Dependencies**: None (pure Python)

```python
# Entities
StockPrice              # Immutable value object
HistoricalStockPrice    # Collection of prices
Document                # Financial document
DocumentChunk           # RAG chunk
QueryResult             # Agent response
AgentStep               # Reasoning step
StreamEvent             # Streaming event

# Interfaces
IStockRepository        # Stock data access contract
IDocumentRepository     # Document access contract
ILLMService             # LLM service contract
```

### Layer 2: Application (Use Cases)
**Location**: `src/application/`
**Dependencies**: Domain layer only

```python
# Use Cases
GetRealtimeStockPriceUseCase
GetHistoricalStockPriceUseCase
QueryDocumentsUseCase

# Orchestrator Interface
IAgentOrchestrator
```

### Layer 3: Infrastructure (Implementations)
**Location**: `src/infrastructure/`
**Dependencies**: Domain, Application, External libs

```python
# Repositories
YFinanceStockRepository(IStockRepository)
BedrockDocumentRepository(IDocumentRepository)

# Services
BedrockLLMService(ILLMService)
CognitoAuthService
LangfuseObservabilityService

# Agent
LangGraphOrchestrator(IAgentOrchestrator)
AgentTools
```

### Layer 4: Presentation (API)
**Location**: `src/presentation/`
**Dependencies**: Application, Infrastructure (via DI)

```python
# FastAPI Application
main.py                 # App entry point
routes/agent.py         # Agent endpoints
routes/auth.py          # Auth endpoints
middleware/auth_middleware.py
streaming/event_stream.py
```

### Dependency Injection
**Location**: `src/di/`

```python
DIContainer             # Wires all layers
- Repositories
- Services
- Use Cases
- Orchestrator
```

## Request Flow

### Example: "What is the stock price for Amazon right now?"

```
1. Client → POST /agent/query
   Headers: Authorization: Bearer <JWT>
   Body: {"query": "What is the stock price for Amazon right now?", "stream": true}

2. FastAPI → Auth Middleware
   - Extract JWT token
   - Verify with Cognito
   - Extract user_id

3. FastAPI → LangGraph Orchestrator
   - Initialize ReAct agent
   - Create Langfuse trace

4. Agent → Claude 3 (Bedrock)
   - System prompt + user query
   - Agent decides to use tool

5. Agent → Tool: get_realtime_stock_price("AMZN")
   - Calls GetRealtimeStockPriceUseCase
   - YFinanceStockRepository.get_realtime_price("AMZN")
   - yfinance API call

6. yfinance → Returns stock data
   - Price: $185.42
   - Volume, market cap, etc.

7. Tool → Returns formatted result to Agent

8. Agent → Claude 3 (Bedrock)
   - Observation: stock data
   - Agent formulates final answer

9. Agent → Streams events via .astream()
   - Event: agent_step
   - Event: tool_call
   - Event: tool_execution
   - Event: final_answer

10. FastAPI → Server-Sent Events (SSE)
    - Formats events as SSE
    - Streams to client

11. Client → Receives streaming response
    - Real-time updates
    - Final answer displayed

12. Langfuse → Logs trace
    - Query
    - Tool calls
    - Execution time
    - Final answer
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       Client Request                         │
│  {"query": "What is AMZN price?", "stream": true}           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Cognito JWT Verification                    │
│  Extract user_id from token claims                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Agent Orchestrator                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  State Graph:                                         │  │
│  │  1. agent_node → decides action                       │  │
│  │  2. tool_node → executes tool                         │  │
│  │  3. agent_node → processes observation                │  │
│  │  4. END → returns final answer                        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
    ┌───────────┐      ┌──────────┐      ┌───────────────┐
    │  Claude 3 │      │ yfinance │      │ Bedrock KB    │
    │ (Bedrock) │      │   API    │      │ (S3 Docs)     │
    └───────────┘      └──────────┘      └───────────────┘
           │                   │                   │
           └───────────────────┴───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Stream Events (SSE)                        │
│  data: {"event_type": "agent_step", ...}                    │
│  data: {"event_type": "tool_call", "tool": "get_price"}     │
│  data: {"event_type": "final_answer", "answer": "..."}      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Langfuse Trace Logging                      │
│  Trace ID, timestamps, tool executions, final answer        │
└─────────────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (User)                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              POST /auth/login
              {"username": "...", "password": "..."}
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   AWS Cognito                                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Validate credentials                              │  │
│  │  2. Generate JWT tokens                               │  │
│  │     - access_token (1 hour)                           │  │
│  │     - id_token                                        │  │
│  │     - refresh_token                                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              Return tokens to client
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Subsequent Requests                             │
│  Authorization: Bearer <access_token>                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              Auth Middleware (FastAPI)                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Extract token from Authorization header           │  │
│  │  2. Verify signature with Cognito JWKS                │  │
│  │  3. Validate expiration                               │  │
│  │  4. Extract user_id (sub claim)                       │  │
│  │  5. Inject user_id into request context               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
              Authenticated request proceeds
```

## Observability

### Langfuse Trace Structure

```
Trace: agent_query
├── user_id: <cognito_sub>
├── timestamp: 2025-02-10T10:30:00Z
├── metadata: {"query": "What is AMZN price?"}
│
├── Span: agent_reasoning
│   ├── duration: 450ms
│   └── events:
│       ├── agent_step (tool selection)
│       └── tool_call (get_realtime_stock_price)
│
├── Generation: llm_call_1
│   ├── model: anthropic.claude-3-sonnet
│   ├── input: "What is AMZN price?"
│   ├── output: [tool_call]
│   └── tokens: {prompt: 245, completion: 78}
│
├── Span: tool_execution
│   ├── tool: get_realtime_stock_price
│   ├── input: {"symbol": "AMZN"}
│   ├── duration: 1200ms
│   └── output: "Stock: AMZN\nCurrent Price: $185.42..."
│
├── Generation: llm_call_2
│   ├── model: anthropic.claude-3-sonnet
│   ├── input: [observation with stock data]
│   ├── output: "Amazon's current stock price is $185.42..."
│   └── tokens: {prompt: 412, completion: 156}
│
└── Result:
    ├── execution_time_ms: 2150
    ├── answer: "Amazon's current stock price is $185.42..."
    └── trace_url: https://cloud.langfuse.com/trace/...
```

## Infrastructure Components

### AWS Resources (Terraform)

```
VPC
├── CIDR: 10.0.0.0/16
├── Public Subnets (2 AZs)
│   ├── 10.0.1.0/24 (us-east-1a)
│   └── 10.0.2.0/24 (us-east-1b)
├── Private Subnets (2 AZs)
│   ├── 10.0.11.0/24 (us-east-1a)
│   └── 10.0.12.0/24 (us-east-1b)
├── Internet Gateway
├── NAT Gateway
└── Route Tables

Cognito
├── User Pool
│   ├── MFA: Optional
│   ├── Password Policy: Strong
│   └── Email Verification
└── App Client
    ├── Auth Flow: USER_PASSWORD_AUTH
    └── Token Expiration: 1 hour

S3
└── Documents Bucket
    ├── amazon-2024-annual-report.pdf
    ├── amazon-q3-2025-earnings.pdf
    └── amazon-q2-2025-earnings.pdf

Bedrock
└── Knowledge Base
    ├── Vector Store: OpenSearch Serverless
    ├── Embedding Model: Titan Embeddings
    └── Data Source: S3 Bucket

ECS
├── Cluster: ai-agent-cluster
├── Task Definition
│   ├── Image: <ecr_repo>/aws-ai-agent:latest
│   ├── CPU: 1 vCPU
│   ├── Memory: 2 GB
│   ├── Port: 8000
│   └── Environment Variables
│       ├── AWS_REGION
│       ├── COGNITO_USER_POOL_ID
│       ├── BEDROCK_KNOWLEDGE_BASE_ID
│       └── LANGFUSE_PUBLIC_KEY
├── Service
│   ├── Desired Count: 2
│   ├── Launch Type: FARGATE
│   └── Load Balancer: ALB
└── Application Load Balancer
    ├── Scheme: internet-facing
    ├── Target Group: ECS tasks on port 8000
    └── Health Check: /health

IAM Roles
├── ECS Task Execution Role
│   ├── ecr:GetAuthorizationToken
│   ├── logs:CreateLogStream
│   └── logs:PutLogEvents
└── ECS Task Role
    ├── bedrock:InvokeModel
    ├── bedrock:Retrieve
    ├── s3:GetObject
    └── cognito-idp:*
```

## Deployment Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                         Developer                               │
│  git push → GitHub → CI/CD Pipeline                            │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                     Build & Push Image                          │
│  1. docker build -t aws-ai-agent:latest .                      │
│  2. docker tag → ECR                                           │
│  3. docker push → ECR                                          │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                   Terraform Apply                               │
│  1. terraform init                                             │
│  2. terraform plan                                             │
│  3. terraform apply                                            │
│     - Creates/updates infrastructure                           │
│     - Deploys ECS service                                      │
│     - Updates ALB configuration                                │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                    ECS Deployment                               │
│  1. Pull image from ECR                                        │
│  2. Start new tasks                                            │
│  3. Health check: /health                                      │
│  4. Drain old tasks                                            │
│  5. Complete deployment                                        │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│                  Application Running                            │
│  ALB DNS: ai-agent-123456.us-east-1.elb.amazonaws.com         │
│  API: https://ai-agent-123456.us-east-1.elb.amazonaws.com     │
└────────────────────────────────────────────────────────────────┘
```

---

**Last Updated**: 2025-02-10
**Version**: 1.0.0
**Status**: Scaffolding Complete ✅
