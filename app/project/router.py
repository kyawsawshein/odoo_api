"""Main API router for Odoo FastAPI integration"""

from typing import List, Optional

import structlog
from app.api.models import SyncResponse
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema
from app.project.projeect_service import ProjectService
from app.project.models.model import (
    ProjectUser,
    Project,
    ProjectList,
    TaskUpdate,
    TimesheetCreate,
    FileUploadResponse,
    ProjectCreate,
    ProjectUpdate,
)
from app.project.route_name import Route

# from app.kafka.producer import KafkaProducer
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/projects", tags=["Projects"])


# Project Endpoints
@router.get(Route.project, response_model=List[ProjectUser])
async def get_projects(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects (name, progress, deadline, team)"""
    service = ProjectService(db, current_user)
    try:
        return await service.get_projects(skip=skip, limit=limit, search=search)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}",
        )


@router.get(Route.project_id, response_model=Project)
async def get_project_by_id(
    project_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full project + tasks + files"""
    service = ProjectService(db, current_user)
    try:
        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project: {str(e)}",
        )


@router.patch(Route.task_id, response_model=SyncResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task: progress, checklist, timer_running, real_duration_seconds"""
    service = ProjectService(db, current_user)
    try:
        result = await service.update_task(
            task_id, task_update.model_dump(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.post(Route.timesheets, response_model=SyncResponse)
async def create_timesheet(
    timesheet: TimesheetCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log time: { task_id, duration_seconds, description }"""
    service = ProjectService(db, current_user)
    try:
        result = await service.create_timesheet(timesheet)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create timesheet: {str(e)}",
        )


@router.post(Route.upload, response_model=FileUploadResponse)
async def initiate_file_upload(
    file: UploadFile = File(...),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate file upload: returns { file_id, upload_url }"""
    service = ProjectService(db, current_user)
    try:
        # Read file content
        file_content = await file.read()
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "content": file_content,
        }
        result = await service.initiate_file_upload(file_info)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate file upload: {str(e)}",
        )


@router.get(Route.file_id, response_model=dict)
async def get_file_metadata(
    file_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get file metadata + download URL"""
    service = ProjectService(db, current_user)
    try:
        file_data = await service.get_file_metadata(file_id)
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with ID {file_id} not found",
            )
        return file_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch file metadata: {str(e)}",
        )


# Additional endpoints for project management
@router.post("/", response_model=SyncResponse)
async def create_project(
    project: ProjectCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project"""
    service = ProjectService(db, current_user)
    try:
        result = await service.create_project(project.dict())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}",
        )


@router.put("/{project_id}", response_model=SyncResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing project"""
    service = ProjectService(db, current_user)
    try:
        result = await service.update_project(
            project_id, project_update.dict(exclude_unset=True)
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}",
        )
