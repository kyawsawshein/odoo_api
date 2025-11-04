class Route:
    project = "/"
    project_id = "/{project_id}"
    project_task = "/{project_id}/tasks"
    task = "/tasks/{task_id}"
    timesheets = "/{task_id}/timesheets"
    project_file_upload = "/{project_id}/files/upload"
    task_file_upload = "/{task_id}/files/upload"
    # Additional routes for frontend API
    project_dashboard = "/dashboard"
    project_tasks = "/{project_id}/task"
