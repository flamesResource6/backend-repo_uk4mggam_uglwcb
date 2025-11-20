import os
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Campus Companion API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for requests
class CourseIn(BaseModel):
    code: str
    name: str
    semester: Optional[str] = None
    instructor: Optional[str] = None
    location: Optional[str] = None
    color: Optional[str] = None

class ClassSessionIn(BaseModel):
    course_id: str
    weekday: int
    start_time: str
    end_time: str
    location: Optional[str] = None

class SubtaskIn(BaseModel):
    title: str
    done: bool = False

class AssignmentIn(BaseModel):
    course_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"
    subtasks: List[SubtaskIn] = []
    completed: bool = False

class NoteIn(BaseModel):
    title: str
    content: str = ""
    subject: Optional[str] = None
    tags: List[str] = []

class FocusSessionIn(BaseModel):
    started_at: datetime
    duration_minutes: int
    type: str = "work"

# Helpers

def to_str_id(doc):
    if not doc:
        return doc
    doc["_id"] = str(doc.get("_id"))
    return doc

@app.get("/")
def read_root():
    return {"message": "Campus Companion API running"}

# Courses
@app.post("/api/courses")
def create_course(course: CourseIn):
    _id = create_document("course", course.model_dump())
    return {"_id": _id}

@app.get("/api/courses")
def list_courses():
    items = get_documents("course")
    return [to_str_id(i) for i in items]

# Class sessions
@app.post("/api/classsessions")
def create_class_session(cs: ClassSessionIn):
    # validate course exists
    if not ObjectId.is_valid(cs.course_id):
        raise HTTPException(400, "Invalid course_id")
    course = db["course"].find_one({"_id": ObjectId(cs.course_id)})
    if not course:
        raise HTTPException(404, "Course not found")
    _id = create_document("classsession", cs.model_dump())
    return {"_id": _id}

@app.get("/api/classsessions")
def list_class_sessions(course_id: Optional[str] = None):
    filter_obj = {}
    if course_id and ObjectId.is_valid(course_id):
        filter_obj["course_id"] = course_id
    items = get_documents("classsession", filter_obj)
    return [to_str_id(i) for i in items]

# Assignments
@app.post("/api/assignments")
def create_assignment(payload: AssignmentIn):
    data = payload.model_dump()
    _id = create_document("assignment", data)
    return {"_id": _id}

@app.get("/api/assignments")
def list_assignments(course_id: Optional[str] = None, completed: Optional[bool] = None):
    filt = {}
    if course_id:
        filt["course_id"] = course_id
    if completed is not None:
        filt["completed"] = completed
    items = get_documents("assignment", filt)
    return [to_str_id(i) for i in items]

# Notes
@app.post("/api/notes")
def create_note(note: NoteIn):
    _id = create_document("note", note.model_dump())
    return {"_id": _id}

@app.get("/api/notes")
def list_notes(subject: Optional[str] = None):
    filt = {"subject": subject} if subject else {}
    items = get_documents("note", filt)
    return [to_str_id(i) for i in items]

# Focus sessions
@app.post("/api/focus-sessions")
def create_focus_session(fs: FocusSessionIn):
    _id = create_document("focussession", fs.model_dump())
    return {"_id": _id}

@app.get("/api/focus-sessions")
def list_focus_sessions():
    items = get_documents("focussession")
    return [to_str_id(i) for i in items]

# Simple chatbot answering from stored data (very basic)
@app.get("/api/chatbot")
def chatbot(q: str):
    ql = q.lower()
    if "next class" in ql or "upcoming class" in ql:
        today = datetime.utcnow().weekday()
        sessions = list(db["classsession"].find({"weekday": today}))
        sessions = sorted(sessions, key=lambda x: x.get("start_time", ""))
        if not sessions:
            return {"answer": "No classes scheduled for today."}
        courses_map = {str(c["_id"]): c for c in db["course"].find({})}
        lines = []
        for s in sessions:
            course = courses_map.get(s.get("course_id"))
            cname = (course.get("code") + " - " + course.get("name")) if course else "Course"
            lines.append(f"{cname} at {s.get('start_time')} in {s.get('location') or 'TBA'}")
        return {"answer": "Today: " + "; ".join(lines)}
    if "due" in ql or "assignment" in ql:
        items = list(db["assignment"].find({"completed": False}))
        if not items:
            return {"answer": "No pending assignments."}
        items = sorted(items, key=lambda x: x.get("due_date") or datetime.max)
        top = items[:5]
        titles = [i.get("title") for i in top]
        return {"answer": "Top upcoming: " + ", ".join(titles)}
    if "note" in ql:
        count = db["note"].count_documents({})
        return {"answer": f"You have {count} notes. Try 'list notes' to view in the app."}
    return {"answer": "I'm a simple helper. Ask about classes, assignments, or notes."}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, 'name', '✅ Connected')
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
