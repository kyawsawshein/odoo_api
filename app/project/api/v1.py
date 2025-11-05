"""Frontend API router for project and task management with Odoo synchronization"""

from functools import wraps
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.models.models import SyncResponse
from app.auth.api.v1 import get_current_user
from app.auth.decorators import require_roles
from app.auth.models.models import User
from app.core.database import get_db
from app.dependency import odoo, db
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
    # The validate_token dependency is now handled by get_current_user,
    # which is implicitly required by the @require_roles decorator.
)

async def get_db_connection():
    """Dependency to get database connection at runtime"""
    from app.dependency import db

    if db is None:
        raise RuntimeError("Database not configured")
    async with db.connection() as connection:
        yield connection


@router.post(Route.project, response_model=SyncResponse)
@require_roles("Project / Manager")
async def create_project_from_frontend(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Create a new project from frontend and sync with Odoo"""
    controller = ProjectController(
        current_user=current_user, db_connection=db_connection
    )
    return await controller.create_project(project)


@router.post(Route.project_task, response_model=SyncResponse)
async def create_project_task(
    project_id: int,
    task_data: CreateProjectTask,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Create a new task in project from frontend and sync with Odoo"""

    return await ProjectController(current_user=current_user, db_connection=db_connection).create_task(
        project_id, task_data
    )


@router.patch(Route.task, response_model=SyncResponse)
async def update_project_task_from_frontend(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Update task from frontend and sync with Odoo"""

    return await ProjectController(current_user=current_user, db_connection=db_connection).update_task(
        task_id, task_update
    )


@router.post(Route.timesheets, response_model=SyncResponse)
async def create_task_timesheet_from_frontend(
    task_id: int,
    timesheet: TimesheetCreate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Create timesheet for task from frontend and sync with Odoo"""
    return await ProjectService(current_user, db_connection).create_timesheet(task_id, timesheet)


@router.post(Route.project_file_upload, response_model=FileUploadResponse)
async def upload_project_file_from_frontend(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Upload file to project from frontend and sync with Odoo"""
    return await ProjectService(current_user, db_connection).initiate_file_upload(project_id, file)


@router.get(Route.project_task, response_model=List[dict])
async def get_project_tasks_from_frontend(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Get all tasks for a project from frontend"""
    return await ProjectService(current_user, db_connection).get_project(project_id)


@router.get(Route.task, response_model=dict)
async def get_project_task_from_frontend(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Get specific task details from frontend"""

    return await ProjectService(current_user, db_connection).get_task_details(task_id)


@router.put(Route.project_id, response_model=SyncResponse)
async def update_project_from_frontend(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Update project from frontend and sync with Odoo"""
    service = ProjectService(current_user, db_connection)
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
async def get_all_projects_from_frontend(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Get all projects for frontend with full details"""
    service = ProjectService(current_user, db_connection)
    try:
        # Get project list first
        print("#===== Service : ", service, current_user)
        project_list = await service.get_projects(skip=skip, limit=limit, search=search)
        print("#+++++ project list ", project_list)
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
async def get_project_dashboard(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Get project dashboard data"""
    service = ProjectService(current_user, db_connection)
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
async def get_project_tasks_singular(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(get_db_connection),
):
    """Get all tasks for a project from frontend (singular endpoint)"""
    service = ProjectService(current_user, db_connection)
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
