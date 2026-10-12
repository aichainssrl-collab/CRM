import json
import logging
from google.cloud import tasks_v2
from app.config import settings

logger = logging.getLogger(__name__)

tasks_client = None
try:
    tasks_client = tasks_v2.CloudTasksAsyncClient()
except Exception:
    pass

async def enqueue_task(task_name: str, payload: dict, delay_seconds: int = 0) -> bool:
    """
    Crea un task su Cloud Tasks. Non lancia mai: i job in background
    non devono far fallire la risposta di salvataggio al client.
    Ritorna True se accodato (o no-op locale), False se il fallimento.
    """
    if not tasks_client:
        return True

    try:
        parent = tasks_client.queue_path(
            settings.FIREBASE_PROJECT_ID,
            settings.GCP_LOCATION,
            settings.CLOUD_TASKS_QUEUE,
        )

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{settings.BACKEND_INTERNAL_URL}/tasks/handlers/{task_name}",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
                "oidc_token": {
                    "service_account_email": f"crm-backend@{settings.FIREBASE_PROJECT_ID}.iam.gserviceaccount.com",
                },
            }
        }

        if delay_seconds > 0:
            from google.protobuf.timestamp_pb2 import Timestamp
            from datetime import datetime, timezone, timedelta
            schedule_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            ts = Timestamp()
            ts.FromDatetime(schedule_time)
            task["schedule_time"] = ts

        await tasks_client.create_task(parent=parent, task=task)
        return True
    except Exception:
        logger.warning("enqueue_task(%s) failed", task_name, exc_info=True)
        return False
