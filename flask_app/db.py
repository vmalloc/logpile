from flask.ext.mongokit import MongoKit, Document

db = MongoKit()

@db.register
class LogDirectory(Document):
    __collection__ = "directories"
    structure = {
        "directory" : unicode,
        "size_bytes" : int,
    }
    default_values = {"size_bytes" : 0}
    use_dot_notation = True
