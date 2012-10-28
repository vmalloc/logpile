import datetime
from flask.ext import mongokit as flask_mongokit

class AutoclaveMongoKit(flask_mongokit.MongoKit):
    def connect(self):
        super(AutoclaveMongoKit, self).connect()
        flask_mongokit.ctx_stack.top.mongokit_connection.safe = True

db = AutoclaveMongoKit()

@db.register
class LogDirectory(Document):
    __collection__ = "directories"
    structure = {
        "directory" : unicode,
        "deleted" : bool,
        "size_bytes" : int,
        "updated" : datetime.datetime,
        "watchers" : [],
    }
    default_values = {"size_bytes" : 0, "deleted" : False}
    use_dot_notation = True
