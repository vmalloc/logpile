import re
import os
import errno
import httplib
import shutil

import flask
from flask.ext.openid import OpenID
from . import config
from . import db
from . import auth
from .utils import render_template

app = flask.Flask(__name__)
app.config.update(config.flask.__dict__)

oid = OpenID(app)

@app.route("/")
def index():
    if not auth.is_authenticated():
        return flask.redirect("/login")
    return render_template("index.html")

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

@app.route("/logs/<directory>", methods=["POST"])
def upload(directory):
    if not _is_valid_filename(directory) or any(not _is_valid_filename(f) for f in flask.request.files):
        flask.abort(httplib.BAD_REQUEST)
    directory = os.path.join(config.app.LOG_ROOT, directory)
    _ensure_directory(directory)
    for filename, fileobj in flask.request.files.iteritems():
        with open(os.path.join(directory, filename), "w") as outfile:
            shutil.copyfileobj(fileobj, outfile)
            db.get_log_directories_collection().update({"directory":directory}, {"$inc" : {"size_bytes":outfile.tell()}}, upsert=True)
    return flask.make_response("ok")

def _is_valid_filename(f):
    return re.match("[a-zA-Z0-9_.]+", f)

def _ensure_directory(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
