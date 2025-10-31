"""Project service for managing projects, tasks, timesheets and Odoo synchronization"""

from typing import Any, Dict, List, Optional

import structlog

# from app.auth.schemas import User as UserSchema
from app.api.models import SyncResponse
from app.project.models.model import ProjectUser, TimesheetCreate
from app.services.base_service import BaseService

# from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

logger = structlog.get_logger()


class ProjectService(BaseService):
    """Service for project operations"""

    async def create_project(self, project_data: Dict[str, Any]) -> SyncResponse:
        """Create project in local database and sync with Odoo"""
        try:
            # Then sync with Odoo
            odoo_client = await self._get_odoo_client()
            odoo_id = await odoo_client.create_project(project_data)
            self.logger.info(
                "Project created successfully",
                odoo_id=odoo_id,
            )
            return self._create_sync_response(
                success=True,
                message="Project created and synced with Odoo",
                odoo_id=odoo_id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "project creation")

    async def get_projects(
        self, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> List[ProjectUser]:
        """Get projects with optional search"""
        odoo_client = await self._get_odoo_client()
        try:
            # Search projects in Odoo
            domain = []
            if search:
                domain = [("name", "ilike", f"%{search}%")]
            fields = list(ProjectUser.model_fields.keys())

            projects = await odoo_client.search_records(
                model="project.project",
                domain=domain,
                limit=limit,
                fields=fields,
                offset=skip,
            )
            if not projects:
                return []

            # Transform to ProjectList format
            project_list = []
            for project in projects:
                project_list.append(ProjectUser(**project).model_dump())

            return project_list

        except Exception as e:
            self.logger.error("Failed to fetch projects", error=str(e))
            raise

    async def get_project(self, project_id: int) -> Optional[Any]:
        """Get specific project by ID with full details"""
        odoo_client = await self._get_odoo_client()
        try:
            # Read project details
            project = await odoo_client.read_record(
                model="project.project",
                record_id=project_id,
                fields=[
                    "id",
                    "name",
                    "category_id",
                    "color",
                    "priority",
                    "user_ids",
                    "allocated_hours",
                    "date_deadline",
                    "progress",
                    "sale_order_id",
                    "item_number",
                    "description",
                ],
            )

            if not project:
                return None

            print("#=========================", project)
            # Get team members
            team = []
            if project.get("user_ids"):
                user_ids = project["user_ids"]
                users = await odoo_client.read_records(
                    model="res.users",
                    record_ids=user_ids,
                    fields=["id", "name", "email", "image_1920"],
                )
                team = [
                    {
                        "id": user["id"],
                        "name": user["name"],
                        "email": user.get("email", ""),
                        "avatar": user.get("image_1920"),
                    }
                    for user in users
                ]

            # Get project tasks
            tasks = await self._get_project_tasks(odoo_client, project_id)

            # Get project files
            files = await self._get_project_files(odoo_client, project_id)

            return {
                "id": project["id"],
                "name": project["name"],
                "category": project.get("category_id", [1, "General"])[1],
                "project_color": project.get("color", "#000000"),
                "priority": project.get("priority", "normal"),
                "team": team,
                "allocated_hours": project.get("allocated_hours", 0.0),
                "deadline": project.get("date_deadline"),
                "progress": project.get("progress", 0),
                "sales_order": (
                    project.get("sale_order_id", [0, ""])[1]
                    if project.get("sale_order_id")
                    else None
                ),
                "item_number": project.get("item_number"),
                "description": project.get("description"),
                "tasks": tasks,
                "files": files,
            }

        except Exception as e:
            self.logger.error(
                "Failed to fetch project", project_id=project_id, error=str(e)
            )
            raise

    async def _get_project_tasks(self, odoo_client, project_id: int) -> List[Dict]:
        """Get tasks for a project"""
        try:
            # Search tasks for this project
            task_ids = await odoo_client.search_records(
                model="project.task",
                domain=[("project_id", "=", project_id)],
                fields=[
                    "id",
                    "name",
                    "description",
                    "progress",
                    "user_ids",
                    "tag_ids",
                    "planned_date_begin",
                    "planned_date_end",
                    "effective_hours",
                    "is_timer_running",
                    "parent_id",
                    "depend_on_ids",
                ],
            )

            if not task_ids:
                return []

            tasks = await odoo_client.read_records(
                model="project.task",
                record_ids=task_ids,
                fields=[
                    "id",
                    "name",
                    "description",
                    "progress",
                    "user_ids",
                    "tag_ids",
                    "planned_date_begin",
                    "planned_date_end",
                    "effective_hours",
                    "is_timer_running",
                    "parent_id",
                    "depend_on_ids",
                ],
            )

            # Transform tasks to our format
            transformed_tasks = []
            for task in tasks:
                # Get assignees
                assignees = []
                if task.get("user_ids"):
                    user_ids = task["user_ids"]
                    users = await odoo_client.read_records(
                        model="res.users",
                        record_ids=user_ids,
                        fields=["id", "name", "email", "image_1920"],
                    )
                    assignees = [
                        {
                            "id": user["id"],
                            "name": user["name"],
                            "email": user.get("email", ""),
                            "avatar": user.get("image_1920"),
                        }
                        for user in users
                    ]

                # Get tags
                tags = []
                if task.get("tag_ids"):
                    tag_ids = task["tag_ids"]
                    tag_records = await odoo_client.read_records(
                        model="project.tags", record_ids=tag_ids, fields=["name"]
                    )
                    tags = [tag["name"] for tag in tag_records]

                # Get blocking tasks
                blocked_by_task_id = None
                if task.get("depend_on_ids"):
                    blocked_by_task_id = (
                        task["depend_on_ids"][0] if task["depend_on_ids"] else None
                    )

                transformed_tasks.append(
                    {
                        "id": task["id"],
                        "name": task["name"],
                        "description": task.get("description"),
                        "progress": task.get("progress", 0),
                        "assignees": assignees,
                        "tags": tags,
                        "blocked_by_task_id": blocked_by_task_id,
                        "checklist": [],  # Odoo doesn't have built-in checklist
                        "planned_start": task.get("planned_date_begin"),
                        "planned_stop": task.get("planned_date_end"),
                        "real_duration_seconds": int(
                            task.get("effective_hours", 0) * 3600
                        ),
                        "timer_running": task.get("is_timer_running", False),
                        "subtasks": [],  # Would need recursive call for subtasks
                        "files": [],  # Would need to fetch task files
                    }
                )

            return transformed_tasks

        except Exception as e:
            self.logger.error(
                "Failed to fetch project tasks", project_id=project_id, error=str(e)
            )
            return []

    async def _get_project_files(self, odoo_client, project_id: int) -> List[Dict]:
        """Get files for a project"""
        try:
            # Search attachments for this project
            attachment_ids = await odoo_client.search_records(
                model="ir.attachment",
                domain=[
                    ("res_model", "=", "project.project"),
                    ("res_id", "=", project_id),
                ],
            )

            if not attachment_ids:
                return []

            attachments = await odoo_client.read_records(
                model="ir.attachment",
                record_ids=attachment_ids,
                fields=["id", "name", "mimetype", "datas", "create_date"],
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

    async def update_task(
        self, task_id: int, task_data: Dict[str, Any]
    ) -> SyncResponse:
        """Update task and sync with Odoo"""
        try:
            odoo_client = await self._get_odoo_client()
            await odoo_client.update_record(
                model="project.task", record_id=task_id, values=task_data
            )

            self.logger.info("Task updated successfully", task_id=task_id)
            return self._create_sync_response(
                success=True,
                message="Task updated and synced with Odoo",
                odoo_id=task_id,
            )
        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "task update")

    async def create_timesheet(self, timesheet_data: TimesheetCreate) -> SyncResponse:
        """Create timesheet entry in Odoo"""
        try:
            odoo_client = await self._get_odoo_client()
            timesheet_data.user_id = 2
            # Create timesheet in Odoo
            timesheet_id = await odoo_client.create_record(
                model="account.analytic.line",
                values=timesheet_data.model_dump(exclude=None),
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
            await self.db.rollback()
            return await self._handle_odoo_error(e, "timesheet creation")

    async def initiate_file_upload(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initiate file upload and return upload URL"""
        try:
            odoo_client = await self._get_odoo_client()

            # Create attachment in Odoo
            attachment_id = await odoo_client.create_record(
                model="ir.attachment",
                values={
                    "name": file_info["filename"],
                    "datas": file_info["content"],  # Base64 encoded file content
                    "mimetype": file_info["content_type"],
                    "type": "binary",
                },
            )

            # In a real implementation, you might return a pre-signed S3 URL
            # For now, we'll return a mock upload URL
            upload_url = f"/api/projects/files/{attachment_id}/upload"

            return {"file_id": attachment_id, "upload_url": upload_url}

        except Exception as e:
            self.logger.error("Failed to initiate file upload", error=str(e))
            raise

    async def get_file_metadata(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file metadata and download URL"""
        try:
            odoo_client = await self._get_odoo_client()

            attachment = await odoo_client.read_record(
                model="ir.attachment",
                record_id=file_id,
                fields=["id", "name", "mimetype", "datas", "create_date"],
            )

            if not attachment:
                return None

            # Determine category based on mimetype or name
            category = "other"
            if "drawing" in attachment["name"].lower():
                category = "drawing"
            elif "material" in attachment["name"].lower():
                category = "material_doc"
            elif "template" in attachment["name"].lower():
                category = "template"

            return {
                "id": attachment["id"],
                "name": attachment["name"],
                "url": f"/api/projects/files/{attachment['id']}/download",
                "category": category,
                "created_at": attachment["create_date"],
            }

        except Exception as e:
            self.logger.error(
                "Failed to fetch file metadata", file_id=file_id, error=str(e)
            )
            raise

    async def create_task(
        self, project_id: int, task_data: Dict[str, Any]
    ) -> SyncResponse:
        """Create task in project and sync with Odoo"""
        try:
            odoo_client = await self._get_odoo_client()
            
            # Ensure project_id is included
            task_data['project_id'] = project_id
            
            task_id = await odoo_client.create_record(
                model="project.task",
                values=task_data
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
            await self.db.rollback()
            return await self._handle_odoo_error(e, "task creation")

    async def get_task_details(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get specific task details"""
        odoo_client = await self._get_odoo_client()
        try:
            # Read task details
            task = await odoo_client.read_record(
                model="project.task",
                record_id=task_id,
                fields=[
                    'id', 'name', 'description', 'progress', 'user_ids', 'tag_ids',
                    'planned_date_begin', 'planned_date_end', 'effective_hours',
                    'is_timer_running', 'parent_id', 'depend_on_ids', 'project_id'
                ]
            )
            
            if not task:
                return None
            
            # Get assignees
            assignees = []
            if task.get('user_ids'):
                user_ids = task['user_ids']
                users = await odoo_client.read_records(
                    model="res.users",
                    record_ids=user_ids,
                    fields=['id', 'name', 'email', 'image_1920']
                )
                assignees = [
                    {
                        'id': user['id'],
                        'name': user['name'],
                        'email': user.get('email', ''),
                        'avatar': user.get('image_1920')
                    }
                    for user in users
                ]
            
            # Get tags
            tags = []
            if task.get('tag_ids'):
                tag_ids = task['tag_ids']
                tag_records = await odoo_client.read_records(
                    model="project.tags",
                    record_ids=tag_ids,
                    fields=['name']
                )
                tags = [tag['name'] for tag in tag_records]
            
            # Get blocking tasks
            blocked_by_task_id = None
            if task.get('depend_on_ids'):
                blocked_by_task_id = task['depend_on_ids'][0] if task['depend_on_ids'] else None
            
            return {
                'id': task['id'],
                'name': task['name'],
                'description': task.get('description'),
                'progress': task.get('progress', 0),
                'assignees': assignees,
                'tags': tags,
                'blocked_by_task_id': blocked_by_task_id,
                'checklist': [],  # Odoo doesn't have built-in checklist
                'planned_start': task.get('planned_date_begin'),
                'planned_stop': task.get('planned_date_end'),
                'real_duration_seconds': int(task.get('effective_hours', 0) * 3600),
                'timer_running': task.get('is_timer_running', False),
                'subtasks': [],  # Would need recursive call for subtasks
                'files': []  # Would need to fetch task files
            }
            
        except Exception as e:
            self.logger.error("Failed to fetch task details", task_id=task_id, error=str(e))
            return None

    async def update_project(
        self, project_id: int, project_data: Dict[str, Any]
    ) -> SyncResponse:
        """Update project and sync with Odoo"""
        try:
            odoo_client = await self._get_odoo_client()

            await odoo_client.update_record(
                model="project.project", record_id=project_id, values=project_data
            )

            self.logger.info(
                "Project updated successfully",
                project_id=project_id,
            )

            return self._create_sync_response(
                success=True,
                message="Project updated and synced with Odoo",
                odoo_id=project_id,
            )

        except Exception as e:
            await self.db.rollback()
            return await self._handle_odoo_error(e, "project update")
