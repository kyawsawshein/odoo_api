"""Logging API endpoints for Odoo FastAPI integration"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.api.v1 import get_current_user, validate_token
from app.auth.models.models import User
from app.core.logger import tail_logs, get_log_files, logger

PREFIX = "/logs"
TAG_NAME = "Logs"

router = APIRouter(
    prefix=PREFIX, tags=[TAG_NAME], dependencies=[Depends(validate_token)]
)


class LogResponse(BaseModel):
    """Response model for log data"""
    lines: list[str]
    file: str
    total_lines: int


class LogFilesResponse(BaseModel):
    """Response model for available log files"""
    files: list[str]


@router.get("/tail", response_model=LogResponse)
async def tail_application_logs(
    lines: Optional[int] = 100,
    log_file: Optional[str] = "logs/odoo_api.log",
    current_user: User = Depends(get_current_user)
):
    """
    Tail the last N lines from application logs
    
    Args:
        lines: Number of lines to return (default: 100)
        log_file: Path to log file (default: logs/odoo_api.log)
        current_user: Authenticated user
        
    Returns:
        LogResponse with log lines
    """
    try:
        # Validate lines parameter
        if lines is not None and (lines < 1 or lines > 1000):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lines parameter must be between 1 and 1000"
            )
        
        # Get log lines
        log_lines = tail_logs(log_file=log_file, lines=lines or 100)
        
        logger.info(f"User {current_user.username} accessed logs from {log_file}")
        
        return LogResponse(
            lines=log_lines,
            file=log_file,
            total_lines=len(log_lines)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accessing logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read log file: {str(e)}"
        )


@router.get("/files", response_model=LogFilesResponse)
async def get_available_log_files(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available log files
    
    Args:
        current_user: Authenticated user
        
    Returns:
        LogFilesResponse with list of log files
    """
    try:
        log_files = get_log_files()
        
        logger.info(f"User {current_user.username} requested log files list")
        
        return LogFilesResponse(files=log_files)
        
    except Exception as e:
        logger.error(f"Error getting log files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log files: {str(e)}"
        )


@router.get("/health")
async def log_health_check():
    """
    Health check for logging system
    
    Returns:
        Health status
    """
    try:
        # Test logging by writing a test message
        logger.info("Logging health check - test message")
        
        # Check if we can access log files
        log_files = get_log_files()
        
        return {
            "status": "healthy",
            "log_files_available": len(log_files),
            "message": "Logging system is operational"
        }
        
    except Exception as e:
        logger.error(f"Logging health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Logging system has issues"
        }