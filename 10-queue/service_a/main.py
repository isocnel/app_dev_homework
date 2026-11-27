"""Сервис A: HTTP API для постановки задач и получения результата."""

import json
import logging
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import pika
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://app:app_secret@localhost:5672/%2F",
)
TASKS_QUEUE = "tasks"
RESULTS_QUEUE = "results"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [service-a] %(message)s",
)
log = logging.getLogger(__name__)

# Статусы задач храним в памяти, как разрешено в задании.
JOBS = {}
JOBS_LOCK = threading.Lock()


def now():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def connect():
    return pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))


def publish_task(job_id, topic):
    """Публикует задачу в очередь tasks и закрывает соединение."""
    connection = connect()
    try:
        channel = connection.channel()
        channel.queue_declare(queue=TASKS_QUEUE, durable=True)
        # Ждём подтверждения брокера, что сообщение действительно принято.
        channel.confirm_delivery()
        channel.basic_publish(
            exchange="",
            routing_key=TASKS_QUEUE,
            body=json.dumps(
                {"id": job_id, "topic": topic},
                ensure_ascii=False,
            ).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
        )
    finally:
        connection.close()


def read_results():
    """В фоне читает очередь results и обновляет статусы задач."""
    while True:
        connection = None
        try:
            connection = connect()
            channel = connection.channel()
            channel.queue_declare(queue=RESULTS_QUEUE, durable=True)

            def on_result(ch, method, properties, body):
                try:
                    event = json.loads(body.decode("utf-8"))
                    job_id = event["id"]

                    with JOBS_LOCK:
                        job = JOBS.get(job_id)
                        if job is None:
                            log.warning("Неизвестная задача: %s", job_id)
                        elif job["status"] == "DONE":
                            log.info("Повторный результат для %s проигнорирован", job_id)
                        else:
                            job["status"] = "DONE"
                            job["result"] = event["result"]
                            job["completedAt"] = event["completedAt"]
                            log.info("Задача %s выполнена", job_id)
                except Exception:
                    log.exception("Не удалось разобрать сообщение из results")
                finally:
                    # Подтверждаем всегда: битое сообщение не должно крутиться вечно.
                    ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(
                queue=RESULTS_QUEUE,
                on_message_callback=on_result,
                auto_ack=False,
            )
            log.info("Жду результаты в очереди %s", RESULTS_QUEUE)
            channel.start_consuming()
        except Exception as exc:
            log.warning("Нет соединения с RabbitMQ (%s), повтор через 5 секунд", exc)
            time.sleep(5)
        finally:
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass


@asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=read_results, daemon=True).start()
    yield


app = FastAPI(title="Service A", lifespan=lifespan)


class JobRequest(BaseModel):
    topic: str


@app.post("/jobs", status_code=202)
def create_job(request: JobRequest):
    topic = request.topic.strip()
    if not topic:
        raise HTTPException(status_code=422, detail="topic must not be empty")

    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "topic": topic,
        "status": "ACCEPTED",
        "result": None,
        "completedAt": None,
    }

    with JOBS_LOCK:
        JOBS[job_id] = job

    try:
        publish_task(job_id, topic)
    except Exception as exc:
        with JOBS_LOCK:
            JOBS.pop(job_id, None)
        log.exception("Не удалось отправить задачу в RabbitMQ")
        raise HTTPException(
            status_code=503,
            detail="RabbitMQ is unavailable",
        ) from exc

    log.info("Принята задача %s: %s", job_id, topic)
    return {"id": job_id, "status": "ACCEPTED"}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return dict(job)


@app.get("/health")
def health():
    return {"status": "ok"}
