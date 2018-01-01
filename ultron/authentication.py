# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

from __future__ import absolute_import, unicode_literals
from flask import request
from flask_restful import abort
from werkzeug.security import check_password_hash
from functools import wraps
from ultron.models import Admins
from ultron.objects import Admin
from ultron.config import AUTH_METHOD, SECRET


admins = Admins()


class Authentication:
    """
    For authentication
    """
    def __init__(self, method=AUTH_METHOD, secret=SECRET):
        self.method = method
        self.secret = secret

    def authenticate(self, func):
        """
        Returns a decorator for authentication
        """
        @wraps(func)
        def decorated(*args, **kwargs):
            method = getattr(self, self.method)
            if not method():
                abort(401, message='Authentication failed!')
            return func(*args, **kwargs)
        return decorated

    def basic_auth(self):
        """
        Local login
        """
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return False

        if auth.username not in admins.list():
            return False

        admin = Admin(auth.username)

        if check_password_hash(admin.password, auth.password):
            return True

        return False
