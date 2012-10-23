import mongokit
import os
from . import config

_connection = mongokit.Connection(config.app.DATABASE_HOST, safe=True)

def get_connection():
    return _connection

def get_log_directories_collection():
    return _connection.logpile.directories

#################################### models ####################################
