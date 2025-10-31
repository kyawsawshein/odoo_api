# Project Management API Documentation

This document describes the project management endpoints for the Odoo FastAPI integration.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. List All Projects
**GET** `/projects`

List all projects with basic information (name, progress, deadline, team).

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)
- `search` (string): Search term for project names

**Response:**
```json
[
  {
    "id": 1,
    "name": "Production - Engineering 2025",
    "progress": 75,
    "deadline": "2025-12-31",
    "team": [
      {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "avatar": "https://example.com/avatar.jpg"
      }
    ]
  }
]
```

### 2. Get Project Details
**GET** `/projects/{project_id}`

Get full project details including tasks and files.

**Response:**
```json
{
  "id": 1,
  "name": "Production - Engineering 2025",
  "category": "#RB",
  "project_color": "#FF5733",
  "priority": "high",
  "team": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "avatar": "https://example.com/avatar.jpg"
    }
  ],
  "allocated_hours": 20.0,
  "deadline": "2025-12-31",
  "progress": 75,
  "sales_order": "SO012345",
  "item_number": "ITEM001",
  "graphics_project_link": "https://graphics.example.com/project/1",
  "zervi_website": "https://zervi.example.com/project/1",
  "description": "Engineering project for 2025 production",
  "tasks": [
    {
      "id": 1,
      "name": "Design Phase",
      "description": "Complete initial design",
      "progress": 100,
      "assignees": [...],
      "tags": ["design", "urgent"],
      "blocked_by_task_id": null,
      "checklist": [
        {
          "id": "check1",
          "text": "Create wireframes",
          "completed": true
        }
      ],
      "planned_start": "2025-01-01",
      "planned_stop": "2025-01-15",
      "real_duration_seconds": 7200,
      "timer_running": false,
      "subtasks": [...],
      "files": [...]
    }
  ],
  "files": [
    {
      "id": 1,
      "name": "Sewing_Drawing_v2.pdf",
      "url": "/api/projects/files/1/download",
      "upload_url": "/api/projects/files/1/upload",
      "category": "drawing",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

### 3. Update Task
**PATCH** `/projects/tasks/{task_id}`

Update task progress, checklist, timer status, or duration.

**Request Body:**
```json
{
  "progress": 50,
  "checklist": [
    {
      "id": "check1",
      "text": "Create wireframes",
      "completed": true
    }
  ],
  "timer_running": true,
  "real_duration_seconds": 3600
}
```

**Response:**
```json
{
  "success": true,
  "message": "Task updated and synced with Odoo",
  "odoo_id": 1,
  "local_id": 1,
  "errors": []
}
```

### 4. Create Timesheet
**POST** `/projects/timesheets`

Log time spent on a task.

**Request Body:**
```json
{
  "task_id": 1,
  "duration_seconds": 7200,
  "description": "Worked on design phase"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Timesheet created successfully",
  "odoo_id": 1,
  "local_id": 1,
  "errors": []
}
```

### 5. Upload File
**POST** `/projects/files/upload`

Initiate file upload and get upload URL.

**Request:**
- Form data with file attachment

**Response:**
```json
{
  "file_id": 1,
  "upload_url": "/api/projects/files/1/upload"
}
```

### 6. Get File Metadata
**GET** `/projects/files/{file_id}`

Get file metadata and download URL.

**Response:**
```json
{
  "id": 1,
  "name": "Sewing_Drawing_v2.pdf",
  "url": "/api/projects/files/1/download",
  "category": "drawing",
  "created_at": "2025-01-01T10:00:00Z"
}
```

## Data Models

### ProjectUser
```typescript
interface ProjectUser {
  id: number;
  name: string;
  email: string;
  avatar?: string;
}
```

### ProjectFile
```typescript
interface ProjectFile {
  id: number;
  name: string;
  url: string;
  upload_url?: string;
  category: 'drawing' | 'material_doc' | 'template' | 'other';
  created_at: string;
}
```

### ProjectTask
```typescript
interface ProjectTask {
  id: number;
  name: string;
  description?: string;
  progress: number;        // 0–100
  assignees: ProjectUser[];
  tags: string[];
  blocked_by_task_id?: number;
  checklist: { id: string; text: string; completed: boolean }[];
  planned_start: string | null;
  planned_stop: string | null;
  real_duration_seconds: number;
  timer_running: boolean;
  subtasks: ProjectTask[];
  files: ProjectFile[];
}
```

### Project
```typescript
interface Project {
  id: number;
  name: string;
  category: string;
  project_color: string;
  priority: 'low' | 'normal' | 'high';
  team: ProjectUser[];
  allocated_hours: number;
  deadline: string | null;
  progress: number;
  sales_order?: string;
  item_number?: string;
  graphics_project_link?: string;
  zervi_website?: string;
  description?: string;
  tasks: ProjectTask[];
  files: ProjectFile[];
}
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Integration with Odoo

The API automatically synchronizes with Odoo for:
- Project creation and updates
- Task management
- Timesheet entries
- File attachments
- Team member assignments

All operations are performed in real-time with Odoo's project management module.