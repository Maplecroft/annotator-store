"""A Flask app for using the Annotator Store blueprint.
"""

import logging
import os

import flask

import settings
from annotator import annotation, auth, authz, document, es, store

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


class Authenticator(object):
    def request_user(self, request):
        userid = None

        if request.json:
            userid = request.json.get('user', userid)

        return auth.User(userid, auth.Consumer('key'), False)


@app.before_request
def before_request():
    annotation.Annotation.create_all()
    document.Document.create_all()

    flask.g.auth = Authenticator()
    flask.g.authorize = authz.authorize


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)
