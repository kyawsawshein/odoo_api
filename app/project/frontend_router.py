"""Frontend API router for project and task management with Odoo synchronization"""

from typing import List, Optional

import structlog
from app.api.models import SyncResponse
from app.auth.router import get_current_user
from app.auth.schemas import User as UserSchema
from app.project.projeect_service import ProjectService
from app.project.models.model import (
    Project, ProjectCreate, ProjectUpdate, ProjectTask, 
    TaskUpdate, TimesheetCreate, FileUploadResponse
)
from app.core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

router = APIRouter(prefix="/frontend/projects", tags=["Frontend Projects"])


@router.post("/", response_model=SyncResponse)
async def create_project_from_frontend(
    project: ProjectCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project from frontend and sync with Odoo"""
    service = ProjectService(db, current_user)
    try:
        # Transform frontend data to Odoo format
        odoo_project_data = {
            'name': project.name,
            # Add other project fields as needed
        }
        
        result = await service.create_project(odoo_project_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}",
        )


@router.post("/{project_id}/tasks", response_model=SyncResponse)
async def create_project_task(
    project_id: int,
    task: ProjectTask,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task in project from frontend and sync with Odoo"""
    service = ProjectService(db, current_user)
    try:
        # Transform frontend task data to Odoo format
        odoo_task_data = {
            'name': task.name,
            'description': task.description,
            'project_id': project_id,
            'user_ids': [(6, 0, [user.id for user in task.assignees])] if task.assignees else [],
            'planned_date_begin': task.planned_start,
            'planned_date_end': task.planned_stop,
            'progress': task.progress,
        }
        
        result = await service.create_task(project_id, odoo_task_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}",
        )


@router.patch("/tasks/{task_id}", response_model=SyncResponse)
async def update_project_task_from_frontend(
    task_id: int,
    task_update: TaskUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update task from frontend and sync with Odoo"""
    service = ProjectService(db, current_user)
    try:
        result = await service.update_task(task_id, task_update.dict(exclude_unset=True))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}",
        )


@router.post("/tasks/{task_id}/timesheets", response_model=SyncResponse)
async def create_task_timesheet_from_frontend(
    task_id: int,
    timesheet: TimesheetCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create timesheet for task from frontend and sync with Odoo"""
    service = ProjectService(db, current_user)
    try:
        result = await service.create_timesheet(timesheet.dict())
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create timesheet: {str(e)}",
        )


@router.post("/{project_id}/files/upload", response_model=FileUploadResponse)
async def upload_project_file_from_frontend(
    project_id: int,
    file: UploadFile = File(...),
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload file to project from frontend and sync with Odoo"""
    service = ProjectService(db, current_user)
    try:
        # Read file content
        file_content = await file.read()
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "content": file_content,
            "res_model": "project.project",
            "res_id": project_id
        }
        
        result = await service.initiate_file_upload(file_info)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )


@router.get("/{project_id}/tasks", response_model=List[ProjectTask])
async def get_project_tasks_from_frontend(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all tasks for a project from frontend"""
    service = ProjectService(db, current_user)
    try:
        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        return project.get('tasks', [])[skip:skip+limit]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project tasks: {str(e)}",
        )


@router.get("/tasks/{task_id}", response_model=ProjectTask)
async def get_project_task_from_frontend(
    task_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific task details from frontend"""
    service = ProjectService(db, current_user)
    try:
        # This would need to be implemented in the service
        # For now, we'll search through projects to find the task
        task = await service.get_task_details(task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch task: {str(e)}",
        )


@router.put("/{project_id}", response_model=SyncResponse)
async def update_project_from_frontend(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update project from frontend and sync with Odoo"""
    service = ProjectService(db, current_user)
    try:
        result = await service.update_project(project_id, project_update.dict(exclude_unset=True))
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}",
        )


@router.get("/", response_model=List[Project])
async def get_all_projects_from_frontend(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all projects for frontend with full details"""
    service = ProjectService(db, current_user)
    try:
        # Get project list first
        project_list = await service.get_projects(skip=skip, limit=limit, search=search)
        
        # Get full details for each project
        full_projects = []
        for project_summary in project_list:
            full_project = await service.get_project(project_summary['id'])
            if full_project:
                full_projects.append(full_project)
        
        return full_projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}",
        )