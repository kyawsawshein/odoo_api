# """Optimized project router using prepared statements and query builder for faster API operations"""

# from typing import List, Optional

# import structlog
# from app.api.models import SyncResponse
# from app.auth.router import get_current_user
# from app.auth.models.models import User
# from app.core.database import get_db
# from app.project.models.model import (
#     CreateProjectTask,
#     FileUploadResponse,
#     Project,
#     ProjectCreate,
#     ProjectTask,
#     ProjectUpdate,
#     TaskUpdate,
#     TimesheetCreate,
# )
# from app.project.services.projeect_service import ProjectService
# from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
# from sqlalchemy.ext.asyncio import AsyncSession

# logger = structlog.get_logger()

# router = APIRouter(prefix="/api/v1/optimized/projects", tags=["Optimized Projects"])


# @router.post("/", response_model=SyncResponse)
# async def create_project_optimized(
#     project: ProjectCreate,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Create project using optimized client with prepared statements"""
#     service = ProjectService(db, current_user)
#     try:
#         # Get optimized client
#         odoo_client = await service._get_optimized_odoo_client()
        
#         # Prepare project query for future operations
#         await odoo_client.prepare_query(
#             query_name="project_details",
#             model="project.project",
#             base_fields=["id", "name", "description", "progress", "user_ids"]
#         )
        
#         # Create project using optimized method
#         odoo_project_data = project.model_dump(exclude_none=True)
#         odoo_id = await odoo_client.create_record_optimized("project.project", odoo_project_data)
        
#         logger.info("Project created with optimized client", odoo_id=odoo_id)
#         return service._create_sync_response(
#             success=True,
#             message="Project created using optimized client",
#             odoo_id=odoo_id,
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create project: {str(e)}",
#         )


# @router.get("/", response_model=List[dict])
# async def get_projects_optimized(
#     skip: int = 0,
#     limit: int = 100,
#     search: Optional[str] = None,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Get projects using optimized search with query builder"""
#     service = ProjectService(db, current_user)
#     try:
#         odoo_client = await service._get_optimized_odoo_client()
        
#         # Build query using filter dictionary
#         filters = {}
#         if search:
#             filters["name"] = ("ilike", f"%{search}%")
            
#         projects = await odoo_client.build_query(
#             model="project.project",
#             filters=filters,
#             fields=["id", "name", "description", "progress", "user_ids"],
#             order_by="name ASC",
#             limit=limit,
#             offset=skip
#         )
        
#         logger.info("Projects fetched with optimized query", count=len(projects))
#         return projects
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to fetch projects: {str(e)}",
#         )


# @router.get("/{project_id}", response_model=dict)
# async def get_project_optimized(
#     project_id: int,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Get specific project using optimized client with prepared query"""
#     service = ProjectService(db, current_user)
#     try:
#         odoo_client = await service._get_optimized_odoo_client()
        
#         # Use prepared query for faster execution
#         project = await odoo_client.execute_prepared_query(
#             query_name="project_details",
#             additional_domain=[("id", "=", project_id)],
#             additional_fields=["color", "allocated_hours", "date_deadline"]
#         )
        
#         if not project:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Project with ID {project_id} not found",
#             )
            
#         logger.info("Project fetched with prepared query", project_id=project_id)
#         return project[0] if project else {}
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to fetch project: {str(e)}",
#         )


# @router.post("/{project_id}/tasks", response_model=SyncResponse)
# async def create_project_task_optimized(
#     project_id: int,
#     task: CreateProjectTask,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Create task using optimized client with batch update support"""
#     service = ProjectService(db, current_user)
#     try:
#         odoo_client = await service._get_optimized_odoo_client()
        
#         # Transform task data
#         odoo_task_data = {
#             "name": task.name,
#             "description": task.description,
#             "project_id": project_id,
#             "user_ids": [(6, 0, [task.assignees])] if task.assignees else [],
#             "progress": task.progress,
#         }
        
#         # Create task using optimized method
#         task_id = await odoo_client.create_record_optimized("project.task", odoo_task_data)
        
#         logger.info("Task created with optimized client", task_id=task_id, project_id=project_id)
#         return service._create_sync_response(
#             success=True,
#             message="Task created using optimized client",
#             odoo_id=task_id,
#         )
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to create task: {str(e)}",
#         )


# @router.patch("/tasks/{task_id}", response_model=SyncResponse)
# async def update_project_task_optimized(
#     task_id: int,
#     task_update: TaskUpdate,
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Update task using optimized client with batch mode"""
#     service = ProjectService(db, current_user)
#     try:
#         odoo_client = await service._get_optimized_odoo_client()
        
#         # Use batch mode for potential multiple updates
#         update_data = task_update.dict(exclude_unset=True)
#         success = await odoo_client.update_record_optimized(
#             model="project.task",
#             record_id=task_id,
#             values=update_data,
#             batch_mode=True  # Enable batch mode for performance
#         )
        
#         # Execute batch updates
#         await odoo_client.execute_batch_updates("project.task")
        
#         logger.info("Task updated with optimized batch mode", task_id=task_id)
#         return service._create_sync_response(
#             success=True,
#             message="Task updated using optimized batch mode",
#             odoo_id=task_id,
#         )
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to update task: {str(e)}",
#         )


# @router.post("/{project_id}/files/upload", response_model=FileUploadResponse)
# async def upload_project_file_optimized(
#     project_id: int,
#     file: UploadFile = File(...),
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Upload file using optimized client with optimized file handling"""
#     service = ProjectService(db, current_user)
#     try:
#         odoo_client = await service._get_optimized_odoo_client()
        
#         # Read file content
#         file_content = await file.read()
        
#         # Use optimized attachment creation
#         attachment_id = await odoo_client.create_attachment_optimized(
#             filename=file.filename,
#             file_content=file_content,
#             content_type=file.content_type,
#             res_model="project.project",
#             res_id=project_id
#         )
        
#         upload_url = f"/api/optimized/projects/files/{attachment_id}/upload"
        
#         logger.info("File uploaded with optimized client", 
#                    attachment_id=attachment_id, project_id=project_id)
#         return {"file_id": attachment_id, "upload_url": upload_url}
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to upload file: {str(e)}",
#         )


# @router.get("/performance/stats")
# async def get_performance_stats(
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Get performance statistics for optimized client"""
#     service = ProjectService(db, current_user)
#     try:
#         odoo_client = await service._get_optimized_odoo_client()
#         stats = await odoo_client.get_performance_stats()
        
#         return {
#             "optimized_client_stats": stats,
#             "message": "Performance statistics retrieved successfully"
#         }
        
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to get performance stats: {str(e)}",
#         )


# @router.get("/batch/search")
# async def batch_search_projects(
#     project_ids: str,  # Comma-separated project IDs
#     current_user: User = Depends(get_current_user),
#     db: AsyncSession = Depends(get_db),
# ):
#     """Batch search multiple projects using optimized client"""
#     service = ProjectService(db, current_user)
#     try:
#         odoo_client = await service._get_optimized_odoo_client()
        
#         # Parse project IDs
#         project_id_list = [int(pid.strip()) for pid in project_ids.split(",") if pid.strip()]
        
#         if not project_id_list:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="No valid project IDs provided",
#             )
        
#         # Use optimized batch read
#         projects = await odoo_client.read_records_optimized(
#             model="project.project",
#             record_ids=project_id_list,
#             fields=["id", "name", "description", "progress"],
#             batch_size=50  # Process in batches of 50
#         )
        
#         logger.info("Batch search completed", 
#                    requested_count=len(project_id_list), 
#                    found_count=len(projects))
        
#         return {
#             "requested_ids": project_id_list,
#             "found_projects": projects,
#             "count": len(projects)
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to perform batch search: {str(e)}",
#         )