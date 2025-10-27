from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime

router = APIRouter()

# Data file path
DATA_FILE = "/home/pilote/projet/primaire/AGI/.claude/data/brain/tasks.json"

# Pydantic models
class ChecklistItemCreate(BaseModel):
    text: str
    completed: bool = False

class ChecklistItemUpdate(BaseModel):
    text: Optional[str] = None
    completed: Optional[bool] = None

class SubtaskCreate(BaseModel):
    title: str
    completed: bool = False

class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

class TaskCreate(BaseModel):
    title: str
    priority: str = "medium"
    completed: bool = False
    subtasks: List[SubtaskCreate] = []
    items: List[ChecklistItemCreate] = []

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    priority: Optional[str] = None
    completed: Optional[bool] = None
    subtasks: Optional[List[Dict[str, Any]]] = None
    items: Optional[List[Dict[str, Any]]] = None

class TaskMove(BaseModel):
    source_project: str
    target_project: str

# Helper functions
def load_tasks_data():
    """Load tasks data from JSON file"""
    try:
        if not os.path.exists(DATA_FILE):
            # Create default data structure if file doesn't exist
            default_data = {
                "version": "1.0.0",
                "last_update": datetime.now().isoformat(),
                "projects": {
                    "GOALS": {
                        "id": "goals",
                        "name": "GOALS",
                        "color": "#10B981",
                        "view_mode": "list",
                        "tasks": []
                    },
                    "CODE": {
                        "id": "code",
                        "name": "CODE",
                        "color": "#3B82F6",
                        "view_mode": "list",
                        "tasks": []
                    },
                    "PENTEST": {
                        "id": "pentest",
                        "name": "PENTEST",
                        "color": "#EF4444",
                        "view_mode": "list",
                        "tasks": []
                    },
                    "BRAIN": {
                        "id": "brain",
                        "name": "BRAIN",
                        "color": "#8B5CF6",
                        "view_mode": "list",
                        "tasks": []
                    }
                }
            }
            save_tasks_data(default_data)
            return default_data
        
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tasks data: {str(e)}"
        )

def save_tasks_data(data: dict):
    """Save tasks data to JSON file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        
        # Update last_update timestamp
        data["last_update"] = datetime.now().isoformat()
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save tasks data: {str(e)}"
        )

def generate_task_id(data: dict) -> str:
    """Generate a unique task ID"""
    max_id = 0
    for project in data["projects"].values():
        for task in project["tasks"]:
            try:
                task_num = int(task["id"].split("-")[-1])
                max_id = max(max_id, task_num)
            except (ValueError, IndexError):
                continue
    return f"task-{max_id + 1}"

def generate_subtask_id(task: dict) -> str:
    """Generate a unique subtask ID within a task"""
    max_id = 0
    for subtask in task.get("subtasks", []):
        try:
            subtask_num = int(subtask["id"].split("-")[-1])
            max_id = max(max_id, subtask_num)
        except (ValueError, IndexError):
            continue
    return f"subtask-{max_id + 1}"

def generate_item_id(task: dict) -> str:
    """Generate a unique item ID within a task"""
    max_id = 0
    for item in task.get("items", []):
        try:
            item_num = int(item["id"].split("-")[-1])
            max_id = max(max_id, item_num)
        except (ValueError, IndexError):
            continue
    return f"item-{max_id + 1}"

# API Routes
@router.get("/tasks")
async def get_tasks():
    """Get all tasks data"""
    return load_tasks_data()

@router.post("/tasks/{project_key}")
async def create_task(project_key: str, task_data: TaskCreate):
    """Create a new task in the specified project"""
    data = load_tasks_data()
    
    if project_key not in data["projects"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_key}' not found"
        )
    
    # Generate new task
    task_id = generate_task_id(data)
    new_task = {
        "id": task_id,
        "title": task_data.title,
        "priority": task_data.priority,
        "completed": task_data.completed,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "subtasks": [],
        "items": []
    }
    
    # Add subtasks if provided
    for subtask_data in task_data.subtasks:
        subtask_id = generate_subtask_id(new_task)
        subtask = {
            "id": subtask_id,
            "title": subtask_data.title,
            "completed": subtask_data.completed,
            "created_at": datetime.now().isoformat()
        }
        new_task["subtasks"].append(subtask)
    
    # Add items if provided
    for item_data in task_data.items:
        item_id = generate_item_id(new_task)
        item = {
            "id": item_id,
            "text": item_data.text,
            "completed": item_data.completed,
            "created_at": datetime.now().isoformat()
        }
        new_task["items"].append(item)
    
    # Add task to project
    data["projects"][project_key]["tasks"].append(new_task)
    save_tasks_data(data)
    
    return new_task

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, task_update: TaskUpdate):
    """Update an existing task"""
    data = load_tasks_data()
    
    # Find the task
    task = None
    project_key = None
    for pk, project in data["projects"].items():
        for t in project["tasks"]:
            if t["id"] == task_id:
                task = t
                project_key = pk
                break
        if task:
            break
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found"
        )
    
    # Update task fields
    if task_update.title is not None:
        task["title"] = task_update.title
    if task_update.priority is not None:
        task["priority"] = task_update.priority
    if task_update.completed is not None:
        task["completed"] = task_update.completed
    if task_update.subtasks is not None:
        task["subtasks"] = task_update.subtasks
    if task_update.items is not None:
        task["items"] = task_update.items
    
    task["updated_at"] = datetime.now().isoformat()
    
    save_tasks_data(data)
    return task

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    data = load_tasks_data()
    
    # Find and remove the task
    for project in data["projects"].values():
        for i, task in enumerate(project["tasks"]):
            if task["id"] == task_id:
                deleted_task = project["tasks"].pop(i)
                save_tasks_data(data)
                return {"message": f"Task '{task_id}' deleted successfully", "task": deleted_task}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task '{task_id}' not found"
    )

@router.post("/tasks/{task_id}/move")
async def move_task(task_id: str, move_data: TaskMove):
    """Move a task from one project to another"""
    data = load_tasks_data()
    
    # Validate projects exist
    if move_data.source_project not in data["projects"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source project '{move_data.source_project}' not found"
        )
    
    if move_data.target_project not in data["projects"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target project '{move_data.target_project}' not found"
        )
    
    # Find and remove task from source project
    task = None
    source_tasks = data["projects"][move_data.source_project]["tasks"]
    for i, t in enumerate(source_tasks):
        if t["id"] == task_id:
            task = source_tasks.pop(i)
            break
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found in project '{move_data.source_project}'"
        )
    
    # Add task to target project
    task["updated_at"] = datetime.now().isoformat()
    data["projects"][move_data.target_project]["tasks"].append(task)
    
    save_tasks_data(data)
    return {
        "message": f"Task '{task_id}' moved from '{move_data.source_project}' to '{move_data.target_project}'",
        "task": task
    }