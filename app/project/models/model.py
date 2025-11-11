"""Pydantic models for API requests and responses"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    id: int
    name: str
    login: str


class ProjectTag(BaseModel):
    id: int
    name: str


# User (assignee/team member)
class ProjectUser(BaseModel):
    id: int
    name: str
    # email: str
    # avatar: Optional[str] = None


# File attachment (linked to Odoo)
class ProjectFile(BaseModel):
    id: int
    name: str  # e.g., "Sewing_Drawing_v2.pdf"
    url: str  # pre-signed S3/Elest.io URL (GET)
    upload_url: Optional[str] = None  # pre-signed URL for PUT (if user can upload)
    category: str = Field(
        ..., description="File category: drawing, material_doc, template, other"
    )
    created_at: str


# Checklist item
class ChecklistItem(BaseModel):
    id: str
    text: str
    completed: bool


# Task (recursive, with dependencies)
class ProjectTask(BaseModel):
    id: int
    name: str
    project_id: int
    description: Optional[str] = None
    progress: int = Field(..., ge=0, le=100)  # 0–100
    user_ids: List[ProjectUser] = []
    tag_ids: List[str] = []
    checklist: List[ChecklistItem] = []
    subtasks: List["ProjectTask"] = []  # recursive


# Task (recursive, with dependencies)
class CreateProjectTask(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: Optional[int] = None
    progress: int = Field(..., ge=0, le=100)  # 0–100
    user_ids: Optional[List[ProjectUser]] = None
    tag_ids: Optional[List[str]] = None
    assignees: Optional[Optional[int]] = None
    project_id: Optional[Optional[int]] = None
    # blocked_by_task_id: Optional[int] = None  # ID of blocking task (null if none)
    checklist: Optional[List[ChecklistItem]] = None
    # planned_start: Optional[str] = None
    # planned_stop: Optional[str] = None
    # real_duration_seconds: int = 0  # e.g., 7200 = 2 hrs
    # timer_running: bool = False
    subtasks: Optional[List["ProjectTask"]] = None  # recursive
    files: Optional[List[ProjectFile]] = None  # linked documents


# Project (top-level)
class Project(BaseModel):
    id: int
    name: str
    color: Optional[int] = None
    user_id: Optional[List] = None
    allocated_hours: Optional[float] = None


class ProjectTask(BaseModel):
    id: int
    name: str
    project_id: int
    state: str
    description: Optional[str] = None
    progress: Optional[float] = None
    user_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    effective_hours: Optional[float] = 0.0
    parent_id: Optional[int] = None


class Attachment(BaseModel):
    id: int
    name: str
    mimetype: str
    datas: Optional[Any] = None
    create_date: datetime


# Request/Update models
class TaskUpdate(BaseModel):
    progress: Optional[float] = Field(None, ge=0, le=100)
    date_deadline: Optional[datetime] = None
    effective_hours: Optional[float] = None
    # checklist: Optional[List[ChecklistItem]] = None
    # timer_running: Optional[bool] = None
    # real_duration_seconds: Optional[int] = None


class TimesheetCreate(BaseModel):
    task_id: int
    unit_amount: int = Field(..., description="duration_seconds")
    name: str = Field(..., description="description")
    user_id: Optional[int] = None


class FileUploadResponse(BaseModel):
    file_id: int
    upload_url: str


class ProjectList(BaseModel):
    id: int
    name: str
    progress: int
    deadline: Optional[str] = None
    team: List[ProjectUser] = []


# Base models for inheritance
class ProjectBase(BaseModel):
    """Base project model"""

    name: str = Field(..., description="Project name")


class ProjectCreate(ProjectBase):
    """Project creation model"""

    pass


class ProjectUpdate(BaseModel):
    """Project update model"""

    pass
