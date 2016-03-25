"""A Flask app for using the Annotator Store blueprint.
"""

import logging

import elasticsearch
import flask

import settings
from annotator import annotation, auth, authz, document, es, store
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

with app.test_request_context():
    try:
        annotation.Annotation.create_all()
        document.Document.create_all()
    except elasticsearch.exceptions.RequestError as e:
        if e.error.startswith('MergeMappingException'):
            log.fatal('Please reindex Elastic Search')

        raise


@app.before_request
def before_request():
    # We defer to nginx for authentication and authorization. Consequently,
    # we trust the JSON that's in the request.
    userid = None

    if flask.request.json:
        userid = flask.request.json.get('user', userid)

    flask.g.user = helpers.MockUser(userid=userid)
    flask.g.auth = auth.Authenticator(flask.g.user)
    flask.g.authz = authz.authorize


if __name__ == '__main__':
    app.run(
        host=settings.ANNOTATOR_STORE_HOST,
        port=settings.ANNOTATOR_STORE_PORT,
    )
