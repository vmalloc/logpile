import logging
import datetime
import re
import os
import errno
import httplib
import shutil

import flask
from flask.ext.openid import OpenID
from . import auth
from . import config
from . import db
from .utils import render_template

app = flask.Flask(__name__)
app.config.update(config.flask.__dict__)

db.db.init_app(app)

oid = OpenID(app)

@app.route("/")
def index():
    if not auth.is_authenticated():
        return flask.redirect("/login")
    return flask.redirect("/directories")

@app.route("/directories")
def view_directories():
    dirs = db.db.LogDirectory.find()
    return render_template("directories.html", dirs=dirs)

@app.route('/login')
@oid.loginhandler
def login():
    """
    Does the login via OpenID.  Has to call into `oid.try_login`
    to start the OpenID machinery.
    """
    # if we are already logged in, go back to were we came from
    if auth.is_authenticated():
        return flask.redirect(oid.get_next_url())
    return oid.try_login("https://www.google.com/accounts/o8/id",
                         ask_for=['email', 'fullname', 'nickname'])

@oid.after_login
def create_or_login(resp):
    auth.authenticate_from_openid_response(resp)
    return flask.redirect(oid.get_next_url())

@app.route("/logs/<directory>")
def get_directory(directory):
    directory_path = os.path.join(config.app.LOG_ROOT, directory)
    if not os.path.isdir(directory_path):
        abort(httlib.NOT_FOUND)
    listing = [{"filename" : filename, "size" : os.path.getsize(os.path.join(directory_path, filename))}
               for filename in os.listdir(directory_path)]
    return render_template("listing.html", directory=directory, listing=listing)

@app.route("/logs/<directory>", methods=["POST"])
def upload(directory):
    if not _is_valid_filename(directory) or any(not _is_valid_filename(f) for f in flask.request.files):
        flask.abort(httplib.BAD_REQUEST)
    directory_path = os.path.join(config.app.LOG_ROOT, directory)
    _ensure_directory(directory_path)
    for filename, fileobj in flask.request.files.iteritems():
        file_path = os.path.join(directory_path, filename)
        previous_size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
        with open(file_path, "w") as outfile:
            shutil.copyfileobj(fileobj, outfile)
            dirs = db.db["directories"]
            pred = {"name" : directory}
            dirs.update(pred,
                        {
                            "$set" : dict(pred, updated=datetime.datetime.now(), watchers=[], deleted=False, directory=directory_path),
                            "$inc" : {"size_bytes" : outfile.tell() - previous_size},
                        },
                        upsert=True, safe=True)
    return flask.make_response("ok")

def _is_valid_filename(f):
    return re.match("[a-zA-Z0-9_.]+", f)

def _ensure_directory(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
