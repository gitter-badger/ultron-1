# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

from __future__ import absolute_import, unicode_literals
import os
import pexpect
import simplepam
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

    def restrict_to_owner(self, func):
        """
        Decorator to restrict URL only to owner only
        """
        @wraps(func)
        def decorated(obj, admin, *args, **kwargs):
            auth = request.authorization
            if not auth or admin != auth.username:
                abort(401, message='You are not authorized for this action!')
            return func(obj, admin, *args, **kwargs)
        return decorated

    def restrict_to_ultron_admin(self, func):
        """
        Decorator to restrict URL only to ultron admin only
        """
        @wraps(func)
        def decorated(obj, *args, **kwargs):
            auth = request.authorization
            if not auth or os.getlogin() != auth.username:
                abort(401, message='You are not authorized for this action!')
            return func(obj, *args, **kwargs)
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
        return check_password_hash(admin.password, auth.password)

    def pam_auth(self):
        """
        Unix PAM authentication
        """
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return False
        try:
            p = pexpect.spawn('su', [auth.username, '-c', 'echo'], timeout=.5)
            p.expect('[Pp]assword.*', timeout=.5)
            p.sendline(auth.password)
            p.interact()
            p.close()
            if p.exitstatus == 0:
                Admin(auth.username)
                return True
        except:
            pass
        return False
