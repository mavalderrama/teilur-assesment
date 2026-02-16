"""API routes for agent interactions."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.di.container import get_agent_orchestrator
from src.presentation.api.middleware.auth_middleware import get_user_id
from src.presentation.api.schemas.request import QueryRequest
from src.presentation.api.schemas.response import (
    AgentStepResponse,
    ErrorResponse,
    QueryResponse,
)
from src.presentation.streaming.event_stream import EventStreamFormatter

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post(
    "/query",
    response_model=None,
    responses={
        200: {"description": "Successful query response"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def query_agent(
    request: QueryRequest,
    user_id: str = Depends(get_user_id),
    orchestrator = Depends(get_agent_orchestrator),
) -> QueryResponse | StreamingResponse:
    """
    Query the AI agent with a natural language question.

    This endpoint processes user queries through the AI agent, which can:
    - Retrieve realtime stock prices
    - Get historical stock data
    - Search financial documents (annual reports, earnings releases)

    Supports both streaming and non-streaming responses.
    """
    try:
        if request.stream:
            # Stream response
            event_stream = orchestrator.process_query_stream(request.query, user_id)
            formatted_stream = EventStreamFormatter.stream_events(event_stream)

            return StreamingResponse(
                formatted_stream,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable buffering in nginx
                },
            )
        else:
            # Non-streaming response
            result = await orchestrator.process_query(request.query, user_id)

            return QueryResponse(
                query=result.query,
                answer=result.answer,
                reasoning_steps=[
                    AgentStepResponse(
                        step_number=step.step_number,
                        action=step.action,
                        action_input=step.action_input,
                        observation=step.observation,
                        timestamp=step.timestamp,
                    )
                    for step in result.reasoning_steps
                ],
                sources=result.sources,
                execution_time_ms=result.execution_time_ms,
                timestamp=result.timestamp,
                trace_id=result.trace_id,
            )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
