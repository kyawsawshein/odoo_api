"""Frontend API router for project and task management with Odoo synchronization"""

from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, File, UploadFile

from app.api.models.models import SyncResponse
from app.auth.api.v1 import validate_token
from app.auth.session_auth import get_odoo_session_user, get_session_odoo_connection
from app.dependency import odoo, db
from app.project.api.route_name import Route
from app.project.controllers.project_controller import ProjectController
from app.project.models.model import (
    FileUploadResponse,
    ProjectCreate,
    ProjectUpdate,
    TaskUpdate,
    TimesheetCreate,
)
from app.project.schemas.project import ProjectSchema, CreateProjectTask

logger = structlog.get_logger()


router = APIRouter(
    prefix="/projects",
    tags=["Frontend Projects"],
    dependencies=[Depends(validate_token)],
)


@router.post(Route.project, response_model=SyncResponse)
async def create_project_from_frontend(
    project: ProjectCreate,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Create a new project from frontend and sync with Odoo"""
    controller = ProjectController(
        odoo_connection=odoo_connection, db_connection=db_connection
    )
    return await controller.create_project(project)


@router.get(Route.project, response_model=List[ProjectSchema])
async def get_project_dashboard(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get project dashboard data"""
    return await ProjectController(odoo_connection, db_connection).get_projects(
        skip=skip, limit=limit, search=search
    )


@router.post(Route.project_task, response_model=SyncResponse)
async def create_project_task(
    project_id: int,
    task_data: CreateProjectTask,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Create a new task in project from frontend and sync with Odoo"""
    return await ProjectController(odoo_connection, db_connection).create_task(
        project_id, task_data
    )


@router.patch(Route.task, response_model=SyncResponse)
async def update_project_task_from_frontend(
    task_id: int,
    task_update: TaskUpdate,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Update task from frontend and sync with Odoo"""

    return await ProjectController(odoo_connection, db_connection).update_task(
        task_id, task_update
    )


@router.post(Route.timesheets, response_model=SyncResponse)
async def create_task_timesheet_from_frontend(
    task_id: int,
    timesheet: TimesheetCreate,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Create timesheet for task from frontend and sync with Odoo"""
    return await ProjectController(odoo_connection, db_connection).create_timesheet(
        task_id, timesheet
    )


@router.post(Route.project_file_upload, response_model=FileUploadResponse)
async def upload_project_file_from_frontend(
    project_id: int,
    file: UploadFile = File(...),
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Upload file to project from frontend and sync with Odoo"""
    return await ProjectController(odoo_connection, db_connection).initiate_file_upload(
        project_id, file
    )


@router.get(Route.project_task, response_model=ProjectSchema)
async def get_project_tasks_from_frontend(
    project_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get all tasks for a project from frontend"""
    return await ProjectController(odoo_connection, db_connection).get_project(
        project_id
    )


@router.get(Route.task, response_model=dict)
async def get_project_task_from_frontend(
    task_id: int,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Get specific task details from frontend"""

    return await ProjectController(odoo_connection, db_connection).get_task_details(
        task_id
    )


@router.put(Route.project_id, response_model=SyncResponse)
async def update_project_from_frontend(
    project_id: int,
    project_update: ProjectUpdate,
    odoo_connection=Depends(get_session_odoo_connection),
    db_connection=Depends(db.connection),
):
    """Update project from frontend and sync with Odoo"""
    return ProjectController(odoo_connection, db_connection).update_project(
        project_id=project_id, project_data=project_update
    )
