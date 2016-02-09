#!/usr/bin/env python
"""
run.py: A simple example app for using the Annotator Store blueprint

This file creates and runs a Flask[1] application which mounts the Annotator
Store blueprint at its root. It demonstrates how the major components of the
Annotator Store (namely the 'store' blueprint, the annotation model and the
auth and authz helper modules) fit together, but it is emphatically NOT
INTENDED FOR PRODUCTION USE.

[1]: http://flask.pocoo.org
"""

from __future__ import print_function

import os
import logging
import sys
import time

from flask import Flask, g, request
import elasticsearch
from annotator import es, annotation, auth, authz, document, store
from tests.helpers import MockUser


logging.basicConfig(format='%(asctime)s %(process)d %(name)s [%(levelname)s] '
                           '%(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.getLogger('elasticsearch').setLevel(logging.WARN)
logging.getLogger('urllib3').setLevel(logging.WARN)
log = logging.getLogger('annotator')

here = os.path.dirname(__file__)


def main(argv):
    app = Flask(__name__)

    cfg_file = 'annotator.cfg'
    if len(argv) == 2:
        cfg_file = argv[1]

    cfg_path = os.path.join(here, cfg_file)

    try:
        app.config.from_pyfile(cfg_path)
    except IOError:
        print("Could not find config file %s" % cfg_path, file=sys.stderr)
        print("Perhaps copy annotator.cfg.example to annotator.cfg",
              file=sys.stderr)
        sys.exit(1)

    if app.config.get('ELASTICSEARCH_HOST') is not None:
        es.host = app.config['ELASTICSEARCH_HOST']

    # We do need to set this one (the other settings have fine defaults)
    default_index = app.name
    es.index = app.config.get('ELASTICSEARCH_INDEX', default_index)

    if app.config.get('AUTHZ_ON') is not None:
        es.authorization_enabled = app.config['AUTHZ_ON']

    if app.config.get('DEBUG') is not None:
        app.debug = app.config['DEBUG']

    with app.test_request_context():
        try:
            annotation.Annotation.create_all()
            document.Document.create_all()
        except elasticsearch.exceptions.RequestError as e:
            if e.error.startswith('MergeMappingException'):
                date = time.strftime('%Y-%m-%d')
                log.fatal("Elasticsearch index mapping is incorrect! Please "
                          "reindex it. You can use reindex.py for this, e.g. "
                          "python reindex.py --host %s %s %s-%s",
                          es.host,
                          es.index,
                          es.index,
                          date)
            raise

    @app.before_request
    def before_request():
        userid = None

        if request.json:
            userid = request.json.get('user')

        g.user = MockUser(userid=userid)

        g.auth = auth.Authenticator(lambda x: g.user)

        g.authorize = authz.authorize

    app.register_blueprint(store.store)

    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port)

if __name__ == '__main__':
    main(sys.argv)
