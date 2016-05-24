"""A Flask app for using the Annotator Store blueprint.
"""

import logging
import os

import flask

import settings
from annotator import auth, authz, es, store
from tests import helpers

# Elastic Search
# ------------------------------------------------------------------------------
es.host = settings.ELASTICSEARCH_HOST

es.index = settings.ELASTICSEARCH_INDEX

# Logging
# ------------------------------------------------------------------------------
logging.basicConfig()

logging.getLogger('elasticsearch').setLevel(logging.WARNING)

log = logging.getLogger('annotator')

# Application
# ------------------------------------------------------------------------------
app = flask.Flask(__name__)

app.debug = settings.DEBUG

app.register_blueprint(store.store)


@app.before_request
def before_request():
    # We defer to nginx for authentication and authorization. Consequently,
    # we trust the JSON that's in the request.
    userid = None

    if flask.request.json:
        userid = flask.request.json.get('user', userid)

    flask.g.user = helpers.MockUser(userid=userid)
    flask.g.auth = auth.Authenticator(flask.g.user)
    flask.g.authorize = authz.authorize


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
