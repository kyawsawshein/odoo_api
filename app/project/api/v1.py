"""Frontend API router for project and task management with Odoo synchronization"""

from functools import wraps
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models.models import SyncResponse
from app.auth.api.v1 import get_current_user
from app.auth.models.models import User
from app.core.database import get_db
from app.auth.auth import validate_token
from app.dependency import db, odoo
from app.project.api.route_name import Route
from app.project.controllers.controller import ProjectController
from app.project.models.model import (
    CreateProjectTask,
    FileUploadResponse,
    ProjectCreate,
    ProjectUpdate,
    TaskUpdate,
    TimesheetCreate,
)
from app.project.schemas.project import ProjectSchema
from app.project.services.projeect_service import ProjectService

logger = structlog.get_logger()


router = APIRouter(
    prefix="/frontend/projects",
    tags=["Frontend Projects"],
    dependencies=[Depends(validate_token)],
)


def check_authenticate(func):
    """Decorator to check if user is authenticated"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if current_user is in kwargs and is not None
        current_user = kwargs.get("current_user")
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return await func(*args, **kwargs)

    return wrapper


@router.post(Route.project, response_model=SyncResponse)
@check_authenticate
async def create_project_from_frontend(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project from frontend and sync with Odoo"""
    return await ProjectController(current_user=current_user, db=db).create_project(
        project
    )


@router.post(Route.project_task, response_model=SyncResponse)
@check_authenticate
async def create_project_task(
    project_id: int,
    task_data: CreateProjectTask,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task in project from frontend and sync with Odoo"""

    return await ProjectController(current_user=current_user, db=db).create_task(
        project_id, task_data
    )


@router.patch(Route.task, response_model=SyncResponse)
@check_authenticate
async def update_project_task_from_frontend(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task from frontend and sync with Odoo"""

    return await ProjectController(current_user=current_user, db=db).update_task(
        task_id, task_update
    )


@router.post(Route.timesheets, response_model=SyncResponse)
@check_authenticate
async def create_task_timesheet_from_frontend(
    task_id: int,
    timesheet: TimesheetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create timesheet for task from frontend and sync with Odoo"""
    return await ProjectController(current_user=current_user, db=db).create_timesheet(
        task_id, timesheet
    )


@router.post(Route.project_file_upload, response_model=FileUploadResponse)
@check_authenticate
async def upload_project_file_from_frontend(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload file to project from frontend and sync with Odoo"""
    return await ProjectController(
        current_user=current_user, db=db
    ).initiate_file_upload(project_id, file)


@router.get(Route.project_task, response_model=List[dict])
@check_authenticate
async def get_project_tasks_from_frontend(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all tasks for a project from frontend"""
    return await ProjectController(current_user=current_user, db=db).get_project(
        project_id, skip, limit
    )


@router.get(Route.task, response_model=dict)
@check_authenticate
async def get_project_task_from_frontend(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific task details from frontend"""

    return await ProjectController(current_user=current_user, db=db).get_task_details(
        task_id
    )


@router.put(Route.project_id, response_model=SyncResponse)
@check_authenticate
async def update_project_from_frontend(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project from frontend and sync with Odoo"""
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


@router.get(Route.project, response_model=List[ProjectSchema])
@check_authenticate
async def get_all_projects_from_frontend(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all projects for frontend with full details"""
    service = ProjectService(db, current_user)
    try:
        # Get project list first
        project_list = await service.get_projects(skip=skip, limit=limit, search=search)
        # Get full details for each project
        full_projects = []
        for project in project_list:
            full_project = await service.get_project(project.id)
            if full_project:
                full_projects.append(full_project)
        return full_projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}",
        )


@router.get(Route.project_dashboard, response_model=List[ProjectSchema])
@check_authenticate
async def get_project_dashboard(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project dashboard data"""
    service = ProjectService(db, current_user)
    try:
        # Get project list for dashboard
        project_list = await service.get_projects(skip=skip, limit=limit, search=search)
        # Get full details for each project
        full_projects = []
        for project in project_list:
            full_project = await service.get_project(project.id)
            if full_project:
                full_projects.append(full_project)
        return full_projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project dashboard: {str(e)}",
        )


@router.get(Route.project_tasks, response_model=List[dict])
@check_authenticate
async def get_project_tasks_singular(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all tasks for a project from frontend (singular endpoint)"""
    service = ProjectService(db, current_user)
    try:
        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found",
            )
        return project.get("tasks", [])[skip : skip + limit]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project tasks: {str(e)}",
        )
