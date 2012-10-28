from datetime import timedelta

BROKER_URL="amqp://guest:guest@localhost:5672//"

CELERY_IMPORTS = ("flask_app.tasks", )

CELERYBEAT_SCHEDULE = {
 "purge-old" : {
    "task" : "flask_app.tasks.purge_old",
     "schedule" : timedelta(seconds=5),
 }
}
