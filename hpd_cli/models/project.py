"""Project model — tracks VPS project directories and metadata."""
from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, TimestampMixin
import enum


class ProjectType(str, enum.Enum):
    WEB = "web"
    API = "api"
    CLI = "cli"
    WORDPRESS = "wordpress"
    DOCKER = "docker"
    OTHER = "other"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    project_type: Mapped[ProjectType] = mapped_column(
        SAEnum(ProjectType, name="project_type"), default=ProjectType.OTHER
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    repo_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(255), nullable=True, default="master")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', type='{self.project_type}')>"
