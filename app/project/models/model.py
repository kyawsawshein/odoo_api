"""Pydantic models for API requests and responses"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


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
    
    blocked_by_task_id: Optional[int] = None  # ID of blocking task (null if none)
    checklist: List[ChecklistItem] = []
    planned_start: Optional[str] = None
    planned_stop: Optional[str] = None
    real_duration_seconds: int = 0  # e.g., 7200 = 2 hrs
    timer_running: bool = False
    subtasks: List["ProjectTask"] = []  # recursive
    files: List[ProjectFile] = []  # linked documents


# Project (top-level)
class Project(BaseModel):
    id: int
    name: str  # e.g., "Production - Engineering 2025"
    category: str  # e.g., "#RB"
    project_color: str  # hex or CSS color
    priority: str = Field(..., description="Priority: low, normal, high")
    team: List[ProjectUser] = []
    allocated_hours: float  # e.g., 20.0 → "20:00"
    deadline: Optional[str] = None
    progress: int = Field(..., ge=0, le=100)  # roll-up from tasks
    sales_order: Optional[str] = None  # e.g., "SO012345"
    item_number: Optional[str] = None
    graphics_project_link: Optional[str] = None  # URL
    zervi_website: Optional[str] = None  # URL
    description: Optional[str] = None
    tasks: List[ProjectTask] = []
    files: List[ProjectFile] = []  # project-level docs


# Request/Update models
class TaskUpdate(BaseModel):
    progress: Optional[int] = Field(None, ge=0, le=100)
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
