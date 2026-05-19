from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message to the AI")
    conversation_history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    message: str
    conversation_history: list[ChatMessage]


class FinancialSummaryRequest(BaseModel):
    period: str = Field(default="month", description="Period: 'week', 'month', 'quarter', 'year'")
