from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base
from app.models import Task
from app.worker import process_task

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

QUEUE_MAP = {
    "HIGH": "high_priority",
    "MEDIUM": "medium_priority",
    "LOW": "low_priority"
}

@app.post("/tasks")
def create_task(payload: dict, priority: str, db: Session = Depends(get_db)):
    task = Task(payload=payload, priority=priority)
    db.add(task)
    db.commit()
    db.refresh(task)

    queue = QUEUE_MAP.get(priority, "low_priority")

    process_task.apply_async(args=[task.id], queue=queue)

    return {"task_id": task.id}

@app.get("/tasks/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    return db.query(Task).filter(Task.id == task_id).first()

@app.get("/tasks")
def list_tasks(status: str = None, priority: str = None, db: Session = Depends(get_db)):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    return query.all()