"""Frontend API router for project and task management with Odoo synchronization"""

import base64
from typing import Any, Dict, List, Optional

import asyncpg
import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.models.models import SyncResponse

from app.auth.models.models import User

# Database dependency is now passed as parameter, not imported at module level
from app.project.api.route_name import Route
from app.project.models.model import (
    Attachment,
    FileUploadResponse,
    Project,
    ProjectCreate,
    ProjectTag,
    ProjectTask,
    TaskUpdate,
    TimesheetCreate,
    User,
)
from app.project.schemas.project import (
    CreateProjectTask,
    ProjectSchema,
    ProjectTaskSchema,
)
from app.utils.model_name import Method, ModelName

# from app.config import settings

# from app.project.services.projeect_service import ProjectService

logger = structlog.get_logger()


class ProjectController:
    def __init__(
        self,
        odoo_connection,
        db_connection: asyncpg.connection,
    ):
        self.odoo = odoo_connection
        self.db = db_connection
        self.logger = logger

    def _create_sync_response(
        self,
        success: bool,
        message: str,
        odoo_id: Optional[int] = None,
        local_id: Optional[int] = None,
        errors: List[str] = None,
    ) -> SyncResponse:
        """Create standardized sync response"""
        if errors is None:
            errors = []

        return SyncResponse(
            success=success,
            message=message,
            odoo_id=odoo_id,
            local_id=local_id,
            errors=errors,
        )

    async def get_user(self, user_ids: List[int]) -> List[User]:
        user_fields = list(User.model_fields.keys())
        domain = [("id", "in", user_ids)]
        kwargs = {"fields": user_fields}
        users = await self.odoo.execute_kw(
            model=ModelName.USER,
            method=Method.SEARCH_READ,
            args=[domain],
            kwargs=kwargs,
        )
        return [User(**user) for user in users]

    async def get_tag(self, tag_ids: List[int]) -> List[ProjectTag]:
        tag_fields = list(ProjectTag.model_fields.keys())
        domain = [("id", "in", tag_ids)]
        kwargs = {"fields": tag_fields}
        tags = await self.odoo.execute_kw(
            model=ModelName.TAG, method=Method.SEARCH_READ, args=[domain], kwargs=kwargs
        )
        return [ProjectTag(**tag) for tag in tags]

    async def create_project(
        self,
        project: ProjectCreate,
    ) -> SyncResponse:
        """Create project in local database and sync with Odoo"""
        try:
            project = await self.odoo.execute_kw(
                model=ModelName.PROJECT,
                method=Method.CREATE,
                args=[project.model_dump(exclude=None)],
            )
            return self._create_sync_response(
                success=True,
                message="Project created and synced with Odoo",
                odoo_id=project,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create project: {str(e)}",
            )

    async def get_project_ids(
        self, model: str, method: str, domain: list, kwargs: dict = None
    ) -> List[int]:
        """Get projects with optional search"""
        try:
            # Search projects in Odoo
            return await self.odoo.execute_kw(
                model=model, method=method, args=[domain], kwargs=kwargs
            )
        except Exception as e:
            self.logger.error("Failed to fetch projects", error=str(e))
            raise

    async def update_task(self, task_id: int, task_data: TaskUpdate) -> SyncResponse:
        """Update task and sync with Odoo"""
        try:
            return await self.odoo.execute_kw(
                ModelName.TASK,
                Method.WRITE,
                args=[task_id],
                kwargs=task_data.model_dump(exclude=None),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update task: {str(e)}",
            )

    async def create_timesheet(
        self, task_id, timesheet_data: TimesheetCreate
    ) -> SyncResponse:
        """Create timesheet entry in Odoo"""
        try:
            timesheet_data.task_id = task_id
            timesheet_id = await self.odoo.execute_kw(
                model=ModelName.ANALYTIC_LINE,
                method=Method.CREATE,
                args=[timesheet_data.model_dump(exclude=None)],
            )
            self.logger.info(
                "Timesheet created successfully",
                timesheet_id=timesheet_id,
                task_id=timesheet_data.task_id,
            )
            return self._create_sync_response(
                success=True,
                message="Timesheet created successfully",
                odoo_id=timesheet_id,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create timesheet: {str(e)}",
            )

    async def initiate_file_upload(
        self, project_id: int, file: Dict[str, Any]
    ) -> Dict[str, Any]:
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
            # Encode file content to base64 for Odoo
            file_content_base64 = base64.b64encode(file_info["content"]).decode("utf-8")
            # Create attachment in Odoo
            values = (
                {
                    "name": file_info["filename"],
                    "datas": file_content_base64,  # Base64 encoded file content
                    "mimetype": file_info["content_type"],
                    "type": "binary",
                    "res_model": file_info.get("res_model", ModelName.PROJECT),
                    "res_id": file_info.get("res_id", 0),
                },
            )
            attachment_id = await self.odoo.execute_kw(
                model=ModelName.ATTACHMENT, method=Method.CREATE, args=[values]
            )
            # In a real implementation, you might return a pre-signed S3 URL
            # For now, we'll return a mock upload URL
            upload_url = f"/api/projects/files/{attachment_id}/upload"

            return {"file_id": attachment_id, "upload_url": upload_url}
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
            task_data.project_id = project_id
            task_id = await self.odoo.execute_kw(
                model=ModelName.TASK,
                method=Method.CREATE,
                args=[task_data.model_dump(exclude=None)],
            )
            self.logger.info(
                "Task created successfully",
                task_id=task_id,
                project_id=project_id,
            )

            return self._create_sync_response(
                success=True,
                message="Task created and synced with Odoo",
                odoo_id=task_id,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create task: {str(e)}",
            )

    async def get_task_details(self, task_id: int) -> ProjectTaskSchema:
        """Get specific task details"""
        try:
            # For now, we'll search through projects to find the task
            # Read task details
            task_fields = list(ProjectTask.model_fields.keys())
            domain = [("id", "=", task_id)]
            kwargs = {"fields": task_fields}
            task_data = await self.odoo.execute_kw(
                model=ModelName.TASK,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            if not task_data:
                return {}

            task = task_data[0]
            # Get assignees
            assignees = []
            if task.get("user_ids"):
                assignees = [
                    {"id": user.id, "name": user.name, "email": user.login}
                    for user in await self.get_user(user_ids=task.get("user_ids")[0])
                ]

            # Get tags
            tags = []
            if task.get("tag_ids"):
                tags = [
                    tag.name
                    for tag in await self.get_tag(tag_ids=task.get("tag_ids")[0])
                ]

            # Get blocking tasks
            blocked_by_task_id = None
            if task.get("depend_on_ids"):
                blocked_by_task_id = (
                    task["depend_on_ids"][0] if task["depend_on_ids"] else None
                )
            task = ProjectTaskSchema(
                id=task.get("id"),
                name=task.get("name"),
                project_id=task.get("project_id")[0],
                # description= task.get("description"),
                progress=task.get("progress", 0),
                assignees=assignees,
                tags=tags,
                blocked_by_task_id=blocked_by_task_id,
                # checklist= [],  # Odoo doesn't have built-in checklist
                planned_start=task.get("planned_date_begin"),
                planned_stop=task.get("planned_date_end"),
                real_duration_seconds=int(task.get("effective_hours", 0) * 3600),
                timer_running=task.get("is_timer_running", False),
                # subtasks= [],  # Would need recursive call for subtasks
                # files= [],  # Would need to fetch task files
            )

            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task with ID {task_id} not found",
                )
            return task

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch task: {str(e)}",
            )

    async def update_project(
        self, project_id: int, project_data: Project
    ) -> SyncResponse:
        """Update project and sync with Odoo"""
        try:
            return await self.odoo.execute_kw(
                ModelName.PROJECT,
                Method.WRITE,
                args=[project_id],
                kwargs=project_data.model_dump(exclude_unset=True),
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update project: {str(e)}",
            )

    async def _get_project_tasks(self, project_id: int) -> List[ProjectTaskSchema]:
        """Get tasks for a project"""
        try:
            # Search tasks for this project
            task_fields = list(ProjectTask.model_fields.keys())
            domain = [("project_id", "=", project_id)]
            kwargs = {"fields": task_fields}
            project_tasks = await self.odoo.execute_kw(
                model=ModelName.TASK,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            if not project_tasks:
                return []

            # Transform tasks to our format
            transformed_tasks = []
            for task in project_tasks:
                # Get assignees
                assignees = []
                if task.get("user_ids"):
                    assignees = [
                        {
                            "id": user.id,
                            "name": user.name,
                            "email": user.login,
                        }
                        for user in await self.get_user(user_ids=task.get("user_ids"))
                    ]

                # Get tags
                tags = []
                if task.get("tag_ids"):
                    tags = [
                        tag.name
                        for tag in await self.get_tag(tag_ids=task.get("tag_ids"))
                    ]

                # Get blocking tasks
                blocked_by_task_id = None
                if task.get("depend_on_ids"):
                    blocked_by_task_id = (
                        task["depend_on_ids"][0] if task["depend_on_ids"] else None
                    )

                transformed_tasks.append(
                    ProjectTaskSchema(
                        id=task["id"],
                        name=task["name"],
                        project_id=project_id,
                        status=task["state"],
                        # "description": task.get("description"),
                        progress=task.get("progress", 0),
                        assignees=assignees,
                        tags=tags,
                        blocked_by_task_id=blocked_by_task_id,
                        checklist=[],  # Odoo doesn't have built-in checklist
                        planned_start=task.get("planned_date_begin"),
                        planned_stop=task.get("planned_date_end"),
                        real_duration_seconds=int(
                            task.get("effective_hours", 0) * 3600
                        ),
                        timer_running=task.get("is_timer_running", False),
                        subtasks=[],  # Would need recursive call for subtasks
                        files=[],  # Would need to fetch task files
                    )
                )

            return transformed_tasks
        except Exception as err:
            self.logger.error("Failed to fetch project tasks", error=str(err))
            return []

    async def _get_project_files(self, project_id: int) -> List[Dict]:
        """Get files for a project"""
        try:
            # Search attachments for this project
            attachment_fiels = list(Attachment.model_fields.keys())
            domain = [
                ("res_model", "=", "project.project"),
                ("res_id", "=", project_id),
            ]
            kwargs = {"fields": attachment_fiels}
            attachments = await self.odoo.execute_kw(
                model=ModelName.ATTACHMENT,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )
            files = []
            for attachment in attachments:
                # Determine category based on mimetype or name
                category = "other"
                if "drawing" in attachment["name"].lower():
                    category = "drawing"
                elif "material" in attachment["name"].lower():
                    category = "material_doc"
                elif "template" in attachment["name"].lower():
                    category = "template"

                files.append(
                    {
                        "id": attachment["id"],
                        "name": attachment["name"],
                        "url": f"/api/projects/files/{attachment['id']}/download",
                        "category": category,
                        "created_at": attachment["create_date"],
                    }
                )
            return files

        except Exception as e:
            self.logger.error(
                "Failed to fetch project files", project_id=project_id, error=str(e)
            )
            return []

    async def get_project(self, project_id: int) -> ProjectSchema:
        """Get specific project by ID with full details"""
        try:
            # Read project details
            project_fields = list(Project.model_fields.keys())
            domain = [("id", "=", project_id)]
            kwargs = {"fields": project_fields}
            project_data = await self.odoo.execute_kw(
                model=ModelName.PROJECT,
                method=Method.SEARCH_READ,
                args=[domain],
                kwargs=kwargs,
            )

            if not project_data:
                return None
            project = project_data[0]

            # Get team members
            team = []
            if project.get("user_ids"):
                team = [
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.login,
                    }
                    for user in await self.get_user(user_ids=project["user_ids"][0])
                ]

            # Get project tasks
            tasks = await self._get_project_tasks(project_id)

            # Get project files
            files = await self._get_project_files(project_id)
            return ProjectSchema(
                id=project["id"],
                name=project["name"],
                category=project.get("category_id", [1, "General"])[1],
                project_color=str(project.get("color", "#000000")),
                priority=project.get("priority", "normal"),
                team=team,
                allocated_hours=project.get("allocated_hours", 0.0),
                deadline=project.get("date_deadline"),
                progress=project.get("progress", 0),
                sales_order=(
                    project.get("sale_order_id", [0, ""])[1]
                    if project.get("sale_order_id")
                    else None
                ),
                item_number=project.get("item_number"),
                description=project.get("description"),
                tasks=tasks,
                files=files,
            )
        except Exception as e:
            self.logger.error(
                "Failed to fetch project", project_id=project_id, error=str(e)
            )
            raise

    async def get_projects(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> List[ProjectSchema]:
        """Get project dashboard data"""
        try:
            # Get project list for dashboard
            domain = []
            if search:
                domain = [("name", "ilike", f"%{search}%")]
            kwargs = {"offset": skip, "limit": limit}
            project_list = await self.get_project_ids(
                model=ModelName.PROJECT,
                method=Method.SEARCH,
                domain=domain,
                kwargs=kwargs,
            )
            # Get full details for each project
            full_projects = []
            for project_id in project_list:
                full_project = await self.get_project(project_id)
                if full_project:
                    full_projects.append(full_project)
            return full_projects
        except Exception as e:
            self.logger.error("Error : %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch project dashboard: {str(e)}",
            )
