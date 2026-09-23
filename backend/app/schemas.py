from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class DataCreate(BaseModel):
    date: date
    value: float = Field(ge=0, le=10_000_000)
    memo: str = Field(min_length=1, max_length=280)


class DataUpdate(DataCreate):
    pass


class DataPoint(DataCreate):
    id: str


class Summary(BaseModel):
    count: int
    period_start: date | None
    period_end: date | None
    average: float
    minimum: float
    maximum: float
    trend: Literal["increase", "decrease", "steady", "insufficient"]
    trend_detail: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)
    created_at: datetime | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


class ConversationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)


class Conversation(BaseModel):
    id: str
    title: str
    messages: list[ChatMessage]
    created_at: datetime | None = None
    updated_at: datetime | None = None
