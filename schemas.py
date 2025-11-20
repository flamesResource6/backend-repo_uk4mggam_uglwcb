"""
Database Schemas for Campus Companion MVP

Collections are derived from class names in lowercase.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Course(BaseModel):
    code: str = Field(..., description="Course code, e.g., CS101")
    name: str = Field(..., description="Course name")
    semester: Optional[str] = Field(None, description="e.g., Fall 2025")
    instructor: Optional[str] = None
    location: Optional[str] = None
    color: Optional[str] = Field(None, description="Hex color for UI")

class Classsession(BaseModel):
    course_id: str = Field(..., description="Reference to course document _id as string")
    weekday: int = Field(..., ge=0, le=6, description="0=Mon .. 6=Sun")
    start_time: str = Field(..., description="HH:MM 24h")
    end_time: str = Field(..., description="HH:MM 24h")
    location: Optional[str] = None

class Subtask(BaseModel):
    title: str
    done: bool = False

class Assignment(BaseModel):
    course_id: Optional[str] = Field(None, description="Reference to course doc _id as string")
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = Field("medium", description="low|medium|high")
    subtasks: List[Subtask] = []
    completed: bool = False

class Note(BaseModel):
    title: str
    content: str = Field("", description="Markdown content")
    subject: Optional[str] = None
    tags: List[str] = []

class Focussession(BaseModel):
    started_at: datetime
    duration_minutes: int = Field(..., ge=1)
    type: str = Field("work", description="work|break")
