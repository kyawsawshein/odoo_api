"""Frontend API router for project and task management with Odoo synchronization"""

from typing import Any, Dict, List, Optional
import asyncpg
import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.models.models import SyncResponse
from app.auth.api.v1 import get_current_user
from app.auth.models.models import User
# Database dependency is now passed as parameter, not imported at module level
from app.project.api.route_name import Route
from app.project.models.model import (
    CreateProjectTask,
    FileUploadResponse,
    ProjectCreate,
    ProjectUpdate,
    ProjectUser,
    TaskUpdate,
    TimesheetCreate,
)
from app.project.schemas.project import ProjectSchema, ProjectTaskSchema
from app.project.services.projeect_service import ProjectService

logger = structlog.get_logger()


class ProjectController:
    def __init__(self, current_user: User, db_connection:asyncpg.connection):
        self.db = db_connection
        self.current_user = current_user
        # ProjectService now accepts db as optional parameter
        self.service = ProjectService(self.current_user, self.db)
        self.logger = logger

    async def create_project(
        self,
        project: ProjectCreate,
    ) -> SyncResponse:
        """Create project in local database and sync with Odoo"""
        try:
            return await self.service.create_project(project)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create project: {str(e)}",
            )

    async def get_projects(self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ):
        """Get project dashboard data"""
        try:
            # Get project list for dashboard
            project_list = await self.service.get_projects(skip=skip, limit=limit, search=search)
            # Get full details for each project
            full_projects = []
            for project in project_list:
                full_project = await self.service.get_project(project.id)
                if full_project:
                    full_projects.append(full_project)
            return full_projects
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch project dashboard: {str(e)}",
            )

    async def get_project(self, project_id: int, skip:int, limit: int) -> ProjectSchema:
        """Get specific project by ID with full details"""
        try:
            project = await self.service.get_project(project_id)
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

    async def update_task(
        self, task_id: int, task_data: TaskUpdate
    ) -> SyncResponse:
        """Update task and sync with Odoo"""
        try:
            return await self.service.update_task(task_id, task_data.model_dump(exclude_unset=True))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update task: {str(e)}",
            )

    async def create_timesheet(self, task_id, timesheet_data: TimesheetCreate) -> SyncResponse:
        """Create timesheet entry in Odoo"""
        try:
            result = await self.service.create_timesheet(task_id, timesheet_data)
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create timesheet: {str(e)}",
            )

    async def initiate_file_upload(self, project_id:int, file: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate file upload and return upload URL"""
        try:
            # Read file content
            file_content = await file.read()
            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(file_content),
                "content": file_content,
                "res_model": "project.project",
                "res_id": project_id,
            }
            return await self.service.initiate_file_upload(file_info)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}",
            )

    async def create_task(
        self, project_id: int, task_data: CreateProjectTask
    ) -> SyncResponse:
        """Create task in project and sync with Odoo"""
        try:
            # Transform frontend task data to Odoo format
            return await  self.service.create_task(project_id, task_data.model_dump())
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create task: {str(e)}",
            )

    async def get_task_details(self, task_id: int) -> Optional[ProjectTaskSchema]:
        """Get specific task details"""
        try:
            # This would need to be implemented in the service
            # For now, we'll search through projects to find the task
            task = await self.service.get_task_details(task_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found",
                )
            return task
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch task: {str(e)}",
            )


    async def update_project(
        self, project_id: int, project_data: Dict[str, Any]
    ) -> SyncResponse:
        """Update project and sync with Odoo"""
        try:
            result = await self.service.update_project(
                project_id, project_data.dict(exclude_unset=True)
            )
            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update project: {str(e)}",
            )
