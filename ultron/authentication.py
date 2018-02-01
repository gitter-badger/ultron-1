# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

from __future__ import absolute_import, unicode_literals
import os
import pexpect
from flask import request
from flask_restful import abort
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

    def parse_header(self):
        """
        Returns adminname and token parsed from request header
        """
        try:
            adminname, token = request.headers.get('Authorization').split()[-1].split(':')
        except:
            abort(401, message='Authentication Failed: Invalid token format. Try username:token')
        return (adminname, token)

    def authenticate(self, func):
        """
        Returns a decorator for authentication
        """
        @wraps(func)
        def decorated(*args, **kwargs):
            # Try token auth first
            auth_header = request.headers.get('Authorization')
            if auth_header is not None and 'Basic' not in auth_header:
                adminname, token = self.parse_header()
                if Admin(adminname).validate_token(token):
                    return func(*args, **kwargs)

            # Else default auth method
            method = getattr(self, self.method)
            if not method():
                abort(401, message='Authentication failed: Invalid credentials')
            return func(*args, **kwargs)
        return decorated

    def restrict_to_owner(self, func):
        """
        Decorator that restricts URL only to it's owner.
        It doesn't perform any authentication. So authenticate
        decorator must be used before using this. It only matches adminname
        from URL with adminname in auth/token header. So it will work on
        URL that gets adminname as it's first parameter.
        """
        @wraps(func)
        def decorated(obj, adminname, *args, **kwargs):
            authadmin = None
            auth_header = request.headers.get('Authorization')
            if auth_header is not None and 'Basic' not in auth_header:
                authadmin = self.parse_header()[0]
            auth = request.authorization
            if auth is not None:
                authadmin = auth.get('username')
            if authadmin != adminname:
                abort(401, message='You are not authorized for this action!')
            return func(obj, adminname, *args, **kwargs)
        return decorated

    def restrict_to_ultron_admin(self, func):
        """
        Decorator to restrict URL only to ultron admin only.
        Again it doesn't perform any authentication. It works same
        as restrict_to_owner except that the admin must be the user
        under who's id the server is running.
        """
        @wraps(func)
        def decorated(obj, *args, **kwargs):
            authadmin = None
            auth_header = request.headers.get('Authorization')
            if auth_header is not None and 'Basic' not in auth_header:
                authadmin == self.parse_header()[0]
            auth = request.authorization
            if auth is not None:
                authadmin = auth.get('username')
            if authadmin != os.environ.get('USER'):
                abort(401, message='You are not authorized for this action!')
            return func(obj, *args, **kwargs)
        return decorated

    def db_auth(self):
        """
        Validates password with password stored in DB
        """
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return False
        if auth.username not in admins.list():
            return False
        if Admin(auth.username).validate_password(auth.password):
            return True
        return False

    def pam_auth(self):
        """
        Validates password with local unix password
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
            return False
        return False

