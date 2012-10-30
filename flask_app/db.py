import os
import datetime
import flask
from . import config
from flask.ext import mongokit as flask_mongokit

class AutoclaveMongoKit(flask_mongokit.MongoKit):
    def connect(self):
        super(AutoclaveMongoKit, self).connect()
        flask_mongokit.ctx_stack.top.mongokit_connection.safe = True

db = AutoclaveMongoKit()

@db.register
class LogDirectory(flask_mongokit.Document):
    __collection__ = "directories"
    structure = {
        "name" : unicode,
        "deleted" : bool,
        "updated" : datetime.datetime,
        "stars" : list,
    }
    required_fields = ["name"]
    default_values = {
        "deleted" : False,
        "stars" : [],
    }
    use_dot_notation = True
    indexes = [
        {
            "fields" : ["name"],
            "unique" : True,
        },
    ]
    def get_path(self):
        return os.path.join(config.app.LOG_ROOT, str(self._id))
    def mark_updated(self):
        self["updated"] = datetime.datetime.now()
        self.save()
    def is_starred_by_current_user(self):
        if "user" not in flask.session:
            return False
        return flask.session["user"]["email"] in self["stars"]
