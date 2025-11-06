"""Frontend API router for project and task management with Odoo synchronization"""

from functools import wraps
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.models.models import SyncResponse
from app.auth.api.v1 import get_current_user, validate_token
from app.auth.models.models import User
from app.core.database import get_db
from app.dependency import odoo, db
from app.project.api.route_name import Route
from app.project.controllers.project_controller import ProjectController
from app.project.models.model import (
    CreateProjectTask,
    FileUploadResponse,
    ProjectCreate,
    ProjectUpdate,
    TaskUpdate,
    TimesheetCreate,
)
from app.project.schemas.project import ProjectRequest, ProjectSchema
from app.project.services.projeect_service import ProjectService

logger = structlog.get_logger()


router = APIRouter(
    prefix="/frontend/projects",
    tags=["Frontend Projects"],
    # The validate_token dependency is now handled by get_current_user,
    # which is implicitly required by the @require_roles decorator.
    dependencies=[Depends(validate_token)]
)


@router.post(Route.project, response_model=SyncResponse)
async def create_project_from_frontend(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Create a new project from frontend and sync with Odoo"""
    controller = ProjectController(
        current_user=current_user, db_connection=db_connection
    )
    return await controller.create_project(project)


@router.get(Route.project, response_model=List[ProjectSchema])
async def get_project_dashboard(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
    odoo_connection=Depends(odoo.connection),
):
    """Get project dashboard data"""
    return await ProjectController(current_user, db_connection).get_projects(
        skip=skip, limit=limit, search=search
    )


@router.post(Route.project_task, response_model=SyncResponse)
async def create_project_task(
    project_id: int,
    task_data: CreateProjectTask,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Create a new task in project from frontend and sync with Odoo"""
    return await ProjectController(
        current_user=current_user, db_connection=db_connection
    ).create_task(project_id, task_data)


@router.patch(Route.task, response_model=SyncResponse)
async def update_project_task_from_frontend(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Update task from frontend and sync with Odoo"""

    return await ProjectController(
        current_user=current_user, db_connection=db_connection
    ).update_task(task_id, task_update)


@router.post(Route.timesheets, response_model=SyncResponse)
async def create_task_timesheet_from_frontend(
    task_id: int,
    timesheet: TimesheetCreate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Create timesheet for task from frontend and sync with Odoo"""
    return await ProjectController(current_user, db_connection).create_timesheet(
        task_id, timesheet
    )


@router.post(Route.project_file_upload, response_model=FileUploadResponse)
async def upload_project_file_from_frontend(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Upload file to project from frontend and sync with Odoo"""
    return await ProjectController(current_user, db_connection).initiate_file_upload(
        project_id, file
    )


@router.get(Route.project_task, response_model=List[dict])
async def get_project_tasks_from_frontend(
    project_id: int,
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Get all tasks for a project from frontend"""
    return await ProjectController(current_user, db_connection).get_project(
        project_id, skip, limit
    )


@router.get(Route.task, response_model=dict)
async def get_project_task_from_frontend(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Get specific task details from frontend"""

    return await ProjectController(current_user, db_connection).get_task_details(
        task_id
    )


@router.put(Route.project_id, response_model=SyncResponse)
async def update_project_from_frontend(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db_connection=Depends(db.connection),
):
    """Update project from frontend and sync with Odoo"""
    return ProjectController(current_user, db_connection).update_project(
        project_id=project_id, project_data=project_update
    )
