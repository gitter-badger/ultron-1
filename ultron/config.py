# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import socket
from urllib.parse import quote_plus


VERSION = 'v1.1.8'
API_VERSION = 'v1.0'
PORT = int(os.environ.get('ULTRON_PORT', 8080))
BASE_URL = os.environ.get('ULTRON_BASE_URL',
                          'http://{}:{}'.format(socket.getfqdn(), PORT))
SECRET = os.environ.get('ULTRON_SECRET', '%$%^#^*!hgs(()adsdas&^)&%$^sftegbtr$%')
AUTH_METHOD = os.environ.get('ULTRON_AUTH_METHOD', 'pam_auth')
TOKEN_TIMEOUT = int(os.environ.get('ULTRON_TOKEN_TIMEOUT', 3600))

DB_USER = os.environ.get('ULTRON_DB_USER', None)
DB_PASS = os.environ.get('ULTRON_DB_PASS', None)
DB_HOST = os.environ.get('ULTRON_DB_HOST', 'localhost:27017')
if DB_USER is not None and DB_PASS is not None:
    DB_URL = 'mongodb://%s:%s@%s' % (
        quote_plus(DB_USER.encode()), quote_plus(DB_PASS.encode()), DB_HOST)
else:
    DB_URL = DB_HOST

CELERY_BACKEND = os.environ.get('ULTRON_CELERY_BACKEND', 'rpc://')
CELERY_BROKER = os.environ.get('ULTRON_CELERY_BROKER', 'redis://localhost:6379/')
