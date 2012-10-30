import logging
import datetime
import re
import os
import errno
import httplib
import shutil

import flask
from flask.ext.openid import OpenID
from flask.ext.gravatar import Gravatar
from . import auth
from . import config
from . import db
from .utils import render_template

app = flask.Flask(__name__)
app.config.update(config.flask.__dict__)

db.db.init_app(app)

gravatar = Gravatar(app,
                    size=24,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False)

oid = OpenID(app)

@app.route("/")
def index():
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

@app.route("/logout")
def logout():
    if auth.is_authenticated():
        auth.deauthenticate()
    return flask.redirect(oid.get_next_url())

@oid.after_login
def create_or_login(resp):
    auth.authenticate_from_openid_response(resp)
    return flask.redirect(oid.get_next_url())

@app.route("/logs/<directory_name>")
def get_directory(directory_name):
    directory = db.db.LogDirectory.one({"name":directory_name})
    path = directory.get_path()
    if not os.path.isdir(path):
        abort(httlib.NOT_FOUND)
    listing = [{"filename" : filename, "size" : os.path.getsize(os.path.join(path, filename))}
               for filename in os.listdir(path)]
    return render_template("listing.html", directory=directory, listing=listing)

@app.route("/raw/<path:filename>")
def get_raw_log(filename):
    assert app.config["DEBUG"]
    return flask.send_from_directory(config.app.LOG_ROOT, filename)

@app.route("/logs/<directory_name>", methods=["POST"])
def upload(directory_name):
    if not _is_valid_filename(directory_name) or any(not _is_valid_filename(f) for f in flask.request.files):
        flask.abort(httplib.BAD_REQUEST)
    log_directory = _ensure_directory(directory_name)
    for filename, fileobj in flask.request.files.iteritems():
        file_path = os.path.join(log_directory.get_path(), filename)
        with open(file_path, "w") as outfile:
            shutil.copyfileobj(fileobj, outfile)
    log_directory.mark_updated()
    return flask.make_response("ok")

def _is_valid_filename(f):
    return re.match("[a-zA-Z0-9_.]+", f)

def _ensure_directory(directory_name):
    dirs = db.db["directories"]
    pred = {"name" : directory_name}
    dirs.update(pred,
                {
                    "$set" : dict(pred, updated=datetime.datetime.now(), watchers=[], deleted=False),
                },
                upsert=True, safe=True)
    log_directory = db.db.LogDirectory.one({"name" : directory_name})
    try:
        os.makedirs(log_directory.get_path())
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    return log_directory
