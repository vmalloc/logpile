import datetime
from celery import Celery
from celery.utils.log import get_task_logger
import shutil
from .config import celery as celery_config
from .config import app as config
from .db import db
from .app import app

_logger = get_task_logger(__name__)

celery = Celery("tasks", broker=celery_config.BROKER_URL)

## Add your tasks here, for instance
@celery.task()
def purge_old():
    with app.app_context():
        cutoff = datetime.datetime.now() - config.MAX_AGE
        for deleted in db.LogDirectory.find({"updated" : {"$lt" : cutoff}, "deleted" : False, "watchers" : []}):
            _logger.info("Deleting %s", deleted)
            _delete(deleted)

def _delete(deleted_directory):
    deleted_directory["deleted"] = True
    deleted_directory.save()
    shutil.rmtree(deleted_directory["directory"])
    deleted_directory.delete()

