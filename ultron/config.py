# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import os
import sys
import socket
from urllib.parse import quote_plus


VERSION = 'v1.1.15'
API_VERSION = 'v1.0'
PORT = int(os.environ.get('ULTRON_PORT', 5050))
BASE_URL = os.environ.get('ULTRON_BASE_URL',
                          'https://{}:{}'.format(socket.getfqdn(), PORT))
SSL_KEY_FILE = os.path.expanduser(os.environ.get('ULTRON_SSL_KEY_FILE', '~/.ultron_key.pem'))
SSL_CERT_FILE = os.path.expanduser(os.environ.get('ULTRON_SSL_CERT_FILE', '~/.ultron_cert.pem'))
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

PLUGINS_PATH = os.path.expanduser(os.environ.get('ULTRON_PLUGINS_PATH', '~/ultron_plugins'))
sys.path.append(PLUGINS_PATH)
