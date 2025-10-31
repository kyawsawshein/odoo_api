# Frontend Integration Guide for Odoo Project Management

This guide explains how to integrate a frontend application (doo-frontend-api) with the Odoo API for project and task management.

## Base URL
```
http://localhost:8000/api/v1/frontend/projects
```

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Frontend API Endpoints

### 1. Create Project
**POST** `/`

Create a new project from frontend and sync with Odoo.

**Request Body:**
```json
{
  "name": "Production - Engineering 2025"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Project created and synced with Odoo",
  "odoo_id": 1,
  "local_id": 1,
  "errors": []
}
```

### 2. Get All Projects (Frontend)
**GET** `/`

Get all projects with full details for frontend display.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)
- `search` (string): Search term for project names

**Response:** Array of full Project objects with tasks and files.

### 3. Update Project
**PUT** `/{project_id}`

Update project details from frontend.

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

### 4. Create Project Task
**POST** `/{project_id}/tasks`

Create a new task in a project from frontend.

**Request Body:**
```json
{
  "id": 1,
  "name": "Design Phase",
  "description": "Complete initial design",
  "progress": 0,
  "assignees": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "tags": ["design", "urgent"],
  "blocked_by_task_id": null,
  "checklist": [
    {
      "id": "check1",
      "text": "Create wireframes",
      "completed": false
    }
  ],
  "planned_start": "2025-01-01",
  "planned_stop": "2025-01-15",
  "real_duration_seconds": 0,
  "timer_running": false,
  "subtasks": [],
  "files": []
}
```

### 5. Get Project Tasks
**GET** `/{project_id}/tasks`

Get all tasks for a specific project.

**Query Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum number of records to return (default: 100)

### 6. Get Task Details
**GET** `/tasks/{task_id}`

Get specific task details.

### 7. Update Task
**PATCH** `/tasks/{task_id}`

Update task progress, checklist, timer, or duration.

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

### 8. Create Timesheet
**POST** `/tasks/{task_id}/timesheets`

Log time spent on a task.

**Request Body:**
```json
{
  "task_id": 1,
  "duration_seconds": 7200,
  "description": "Worked on design phase"
}
```

### 9. Upload Project File
**POST** `/{project_id}/files/upload`

Upload file to project.

**Request:** Form data with file attachment

**Response:**
```json
{
  "file_id": 1,
  "upload_url": "/api/projects/files/1/upload"
}
```

## Example Frontend Integration Code

### JavaScript/TypeScript Example

```typescript
class OdooProjectAPI {
  private baseUrl = 'http://localhost:8000/api/v1/frontend/projects';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Create project
  async createProject(projectData: any) {
    return this.request('/', {
      method: 'POST',
      body: JSON.stringify(projectData),
    });
  }

  // Get all projects
  async getProjects(skip = 0, limit = 100, search?: string) {
    const params = new URLSearchParams({
      skip: skip.toString(),
      limit: limit.toString(),
      ...(search && { search }),
    });
    return this.request(`/?${params}`);
  }

  // Create task
  async createTask(projectId: number, taskData: any) {
    return this.request(`/${projectId}/tasks`, {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  // Update task
  async updateTask(taskId: number, updates: any) {
    return this.request(`/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  // Log timesheet
  async createTimesheet(taskId: number, timesheetData: any) {
    return this.request(`/tasks/${taskId}/timesheets`, {
      method: 'POST',
      body: JSON.stringify(timesheetData),
    });
  }
}
```

### Python Example

```python
import requests

class OdooProjectClient:
    def __init__(self, base_url, token):
        self.base_url = f"{base_url}/api/v1/frontend/projects"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def create_project(self, project_data):
        response = requests.post(
            f"{self.base_url}/",
            json=project_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_projects(self, skip=0, limit=100, search=None):
        params = {'skip': skip, 'limit': limit}
        if search:
            params['search'] = search
        
        response = requests.get(
            f"{self.base_url}/",
            params=params,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def create_task(self, project_id, task_data):
        response = requests.post(
            f"{self.base_url}/{project_id}/tasks",
            json=task_data,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def update_task(self, task_id, updates):
        response = requests.patch(
            f"{self.base_url}/tasks/{task_id}",
            json=updates,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
```

## Data Flow Diagram

```
Frontend Application (doo-frontend-api)
        ↓
Odoo FastAPI (odoo_api)
        ↓
Odoo 19 Database
```

## Synchronization Process

1. **Project Creation**: Frontend sends project data → Odoo API creates in Odoo → Returns Odoo ID
2. **Task Management**: Frontend sends task data → Odoo API creates/updates in Odoo → Real-time sync
3. **Time Tracking**: Frontend logs time → Odoo API creates timesheet entries → Sync with Odoo accounting
4. **File Management**: Frontend uploads files → Odoo API stores as attachments → Available in Odoo

## Error Handling

All endpoints return standardized error responses:

```json
{
  "detail": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid data)
- `401` - Unauthorized (invalid token)
- `404` - Not Found (resource not found)
- `500` - Internal Server Error

## Testing the Integration

1. **Get Authentication Token**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

2. **Create Project**:
```bash
curl -X POST "http://localhost:8000/api/v1/frontend/projects/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project"}'
```

3. **Create Task**:
```bash
curl -X POST "http://localhost:8000/api/v1/frontend/projects/1/tasks" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Task", "progress": 0}'
```

This integration provides a complete project management system where the frontend application can manage projects, tasks, timesheets, and files while maintaining real-time synchronization with Odoo 19.