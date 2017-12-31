# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

from __future__ import absolute_import, unicode_literals
from flask import request
from flask_restful import abort
from activity3.models import Admins
from activity3.objects import Admin
from activity3.config import AUTH_METHOD, SECRET
from werkzeug.security import check_password_hash


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
        def wrapper(*args, **kwargs):
            method = getattr(self, self.method)
            if not method():
                abort(401, message='Authentication failed!')
            return func(*args, **kwargs)
        return wrapper


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
