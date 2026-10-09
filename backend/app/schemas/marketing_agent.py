from pydantic import BaseModel
from typing import Optional


class MarketingChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{role: "user"|"assistant", content: "..."}]


class ContentGenerateRequest(BaseModel):
    type: str  # "social_post" | "email" | "ad_copy" | "blog_intro"
    topic: str
    tone: str = "professionale"
    language: str = "it"
    extra_context: Optional[str] = None


class ConversationSaveRequest(BaseModel):
    title: str
    messages: list[dict]  # [{role: "user"|"assistant", content: "..."}]