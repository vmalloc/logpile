import datetime
from flask.ext.mongokit import MongoKit, Document

db = MongoKit()

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
