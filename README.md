Prioritized Async Task Processing System
## Overview
This project implements a Prioritized Asynchronous Task Processing System using FastAPI + Celery + Redis + PostgreSQL. It allows:

Submitting tasks with JSON payloads and priority levels (HIGH, MEDIUM, LOW).
Getting task status or listing tasks filtered by status and/or priority.
Asynchronous processing with multiple workers while respecting strict priority.
Retries and failure handling with idempotency and at-least-once guarantees.

## Queue Design
Separate queues for each priority:high_priority,medium_priority,low_priority
Workers poll queues in priority order (HIGH → MEDIUM → LOW) to ensure high-priority tasks are always processed first.
Celery configuration:
acks_late=True ensures tasks are retried if a worker crashes mid-processing.
worker_prefetch_multiplier=1 prevents workers from prefetching too many low-priority tasks before high-priority ones.

## Benefits:

Strict priority enforcement.
Multiple workers can process tasks without priority inversion.
## Priority Handling
Each task has one of three priorities: HIGH, MEDIUM, LOW.
During submission, the task is enqueued in the corresponding queue.
Workers always check higher-priority queues first, even with multiple concurrent workers.
Avoids naive sorting in a single queue, which can break priority guarantees under concurrency.
## Concurrency Strategy
Transactional DB updates prevent multiple workers from processing the same task simultaneously:
PENDING → IN_PROGRESS → COMPLETED/FAILED

## Retries:
Max 3 attempts per task.
retry_count tracked in PostgreSQL for monitoring.
Retry safety:
Task state is stored in DB; retries do not create duplicates.
Celery automatically retries tasks with exponential backoff if a worker fails mid-task.

## Trade-offs

In this system, strict priority enforcement is achieved by using separate queues for HIGH, MEDIUM, and LOW priority tasks. This guarantees that high-priority tasks are always processed first, even with multiple workers, but it adds slight configuration complexity compared to a single-queue approach. The retry mechanism is limited to three attempts per task to balance reliability with system load—allowing more retries would improve fault tolerance but could overload the system. Concurrency handling relies on transactional database updates combined with Celery’s **acks_late=True**, which prevents duplicate task execution but introduces minor latency. Worker crash recovery ensures that tasks marked **IN_PROGRESS** are safely reprocessed if a worker fails, though this can cause small delays in task completion. Finally, the system simulates a 30% random failure rate to test retry robustness. While this improves resilience testing, it introduces non-determinism, meaning task outcomes may vary slightly during testing.

## Setup

1. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Redis:**
   Ensure you have Redis running locally.

3. **Start the API Server:**
   ```bash
   uvicorn app.main:app --reload
   ```

4. **Start the Celery Worker:**
   ```bash
   celery -A app.worker.celery worker -Q high_priority,medium_priority,low_priority --loglevel=info
   ```

## Endpoints

- `POST /tasks`: Create a new task.
  - Body: `{"payload": {"data": "my_data"}, "priority": "HIGH"}`
- `GET /tasks/{task_id}`: Fetch task details by ID.
- `GET /tasks`: List all tasks (can filter with `?status=` or `?priority=`).
