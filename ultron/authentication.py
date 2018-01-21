# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

from __future__ import absolute_import, unicode_literals
import os
import pexpect
from secrets import token_urlsafe
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
        self.tokens = {}

    def get_token_user(self, token):
        token = token.split()[-1]
        for k, v in self.tokens.items():
            if v == token:
                return k

    def authenticate(self, func):
        """
        Returns a decorator for authentication
        """
        @wraps(func)
        def decorated(*args, **kwargs):
            if request.headers.get('Authorization') is not None:
                token = request.headers.get('Authorization').split()[-1]
                if token in self.tokens.values():
                    return func(*args, **kwargs)
            method = getattr(self, self.method)
            if not method():
                abort(401, message='Authentication failed!')
            return func(*args, **kwargs)
        return decorated

    def logout(self):
        """
        Destroys a session for specified username
        """
        if request.headers.get('Authorization') is None:
            return False
        token = request.headers.get('Authorization').split()[-1]
        user = self.get_token_user(token)
        if user is not None:
            del self.tokens[user]
            return True
        return False

    def restrict_to_owner(self, func):
        """
        Decorator to restrict URL only to owner only
        """
        @wraps(func)
        def decorated(obj, adminname, *args, **kwargs):
            if request.headers.get('Authorization') is not None:
                token = request.headers.get('Authorization').split()[-1]
                if token == self.tokens.get(adminname):
                    return func(obj, adminname, *args, **kwargs)
            auth = request.authorization
            if not auth or adminname != auth.username:
                abort(401, message='You are not authorized for this action!')
            return func(obj, adminname, *args, **kwargs)
        return decorated

    def restrict_to_ultron_admin(self, func):
        """
        Decorator to restrict URL only to ultron admin only
        """
        @wraps(func)
        def decorated(obj, *args, **kwargs):
            if request.headers.get('Authorization') is not None:
                token = request.headers.get('Authorization').split()[-1]
                if token == self.tokens.get(os.getlogin()):
                    return func(obj, *args, **kwargs)
            auth = request.authorization
            if not auth or os.getlogin() != auth.username:
                abort(401, message='You are not authorized for this action!')
            return func(obj, *args, **kwargs)
        return decorated

    def simple_auth(self):
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
            self.tokens.update({auth.username: token_urlsafe(100)})
            return True
        return False

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
                self.tokens.update({auth.username: token_urlsafe(100)})
                return True
        except:
            return False
        return False
