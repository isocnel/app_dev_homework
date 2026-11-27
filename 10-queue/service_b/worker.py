"""Сервис B: читает задачи, «обрабатывает» их и публикует результат."""

import json
import logging
import os
import time
from datetime import datetime, timezone

import pika

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://app:app_secret@localhost:5672/%2F",
)
TASKS_QUEUE = "tasks"
RESULTS_QUEUE = "results"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [service-b] %(message)s",
)
log = logging.getLogger(__name__)


def now():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def main():
    connection = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    channel = connection.channel()
    channel.queue_declare(queue=TASKS_QUEUE, durable=True)
    channel.queue_declare(queue=RESULTS_QUEUE, durable=True)
    # Ждём подтверждения брокера при публикации результата.
    channel.confirm_delivery()
    channel.basic_qos(prefetch_count=1)

    # Простая защита от дублей в рамках жизни одного процесса.
    processed = set()

    def on_task(ch, method, properties, body):
        try:
            task = json.loads(body.decode("utf-8"))
            job_id = task["id"]
            topic = task["topic"]
        except Exception:
            log.exception("Некорректная задача, сообщение отбрасываю")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        if job_id in processed:
            log.info("Повторная задача %s, пропускаю", job_id)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        log.info("Взял задачу %s: %s", job_id, topic)
        time.sleep(2.5)  # имитация долгой работы

        event = {
            "type": "JobCompleted",
            "id": job_id,
            "result": f"Задача '{topic}' выполнена",
            "completedAt": now(),
        }

        try:
            ch.basic_publish(
                exchange="",
                routing_key=RESULTS_QUEUE,
                body=json.dumps(event, ensure_ascii=False).encode("utf-8"),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type="application/json",
                ),
            )
        except Exception:
            log.exception("Не удалось отправить результат, задача вернётся в очередь")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return

        processed.add(job_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        log.info("Задача %s выполнена и подтверждена", job_id)

    channel.basic_consume(
        queue=TASKS_QUEUE,
        on_message_callback=on_task,
        auto_ack=False,
    )
    log.info("Жду задачи в очереди %s", TASKS_QUEUE)
    channel.start_consuming()


if __name__ == "__main__":
    main()
