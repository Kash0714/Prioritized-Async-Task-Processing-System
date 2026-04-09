from celery import Celery
import random
from app.db import SessionLocal
from app.models import Task

celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery.conf.task_acks_late = True
celery.conf.worker_prefetch_multiplier = 1

@celery.task(bind=True, max_retries=3)
def process_task(self, task_id):
    db = SessionLocal()

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task or task.status == "COMPLETED":
        db.close()
        return

    updated = db.query(Task).filter(
        Task.id == task_id,
        Task.status == "PENDING"
    ).update({"status": "IN_PROGRESS"})
    db.commit()

    if not updated:
        db.close()
        return

    try:
        if random.random() < 0.3:
            raise Exception("Random failure")

        print("Processing:", task.payload)

        db.query(Task).filter(Task.id == task_id).update({
            "status": "COMPLETED"
        })
        db.commit()

    except Exception as e:
        db.query(Task).filter(Task.id == task_id).update({
            "retry_count": Task.retry_count + 1,
            "last_error": str(e)
        })
        db.commit()

        task = db.query(Task).filter(Task.id == task_id).first()

        if task.retry_count >= 3:
            db.query(Task).filter(Task.id == task_id).update({
                "status": "FAILED"
            })
            db.commit()
        else:
            raise self.retry(exc=e, countdown=2 ** task.retry_count)

    finally:
        db.close()