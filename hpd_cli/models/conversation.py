"""Conversation model — stores AI chat history for context persistence."""
from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
import enum


class ConversationRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True, comment="Grouping key for a single chat session"
    )
    role: Mapped[ConversationRole] = mapped_column(
        SAEnum(ConversationRole, name="conversation_role"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Conversation(session={self.session_id}, role='{self.role}', len={len(self.content)})>"
