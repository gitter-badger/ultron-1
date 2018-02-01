# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

import string
from datetime import datetime, timedelta
from random import choice
from bson.json_util import dumps
from ultron import tasks, models
from ultron.config import BASE_URL, API_VERSION, TOKEN_TIMEOUT
from werkzeug.security import generate_password_hash, check_password_hash


class TaskPool(object):
    """
    Keeps all celery tasks as DB wont support it
    """
    def __init__(self):
        self.pool = {}

    def submit(self, client, task):
        """
        Submit a celery task to pool
        """
        if client.reportname not in self.pool:
            self.pool[client.reportname] = {}
        report = self.pool[client.reportname]
        report[client.name] = task
        return True

    def get(self, client):
        """
        Get last submitted celery task
        """
        try:
            return self.pool[client.reportname][client.name]
        except:
            return None

    def purge_all(self, reportname=None):
        """
        Purge all submitted tasks
        """
        if reportname is not None and reportname in self.pool:
            result = list(map(
                lambda x: tasks.celery_app.control.revoke(x.id),
                self.pool[reportname].values()
            ))
            self.pool[reportname] = {}
            return result
        return tasks.celery_app.control.purge()


class BaseObject(object):
    """
    Parent class for all objects
    """
    def __init__(self, name, modelname):
        self.name = name
        self.props = {}
        self.state = {}
        self._modelname = modelname

    def __repr__(self):
        return self.json(indent=4, sort_keys=True)

    def __str__(self):
        return self.name

    def model(self):
        """
        Returns an instance of model
        """
        return getattr(models, self._modelname)()

    def dict(self):
        """
        Converts into json encodable dict
        """
        data = self.__dict__.copy()
        return data

    def json(self, *args, **kwargs):
        """
        Formats into json
        """
        return dumps(self.dict(), *args, **kwargs)

    def save(self):
        """
        Saves admin into DB
        """
        self.model().save(self)
        return True

    def cleanup(self):
        """
        Deletes admin from DB
        """
        return self.model().cleanup(self)

    def update(self, data):
        """
        data: type: dict
        Used to update multiple attributes at once.
        Returns false if no action required and True if state changed successfully.
        """
        if '_id' in data: del data['_id']
        old = self.__dict__.copy()
        self.__dict__.update(data)
        if self.__dict__ == old:
            return False
        self.save()
        return True


class Client(BaseObject):
    """
    A Client is the basic unit of Inventory.
    It holds the current state of a host.
    Client can be initialized by passing a single string as name
    (must be DNS resolvable) or by passing both name and data from
    exported/saved Client object.
    If it is being initialized for the first time, it will
    perform DNS lookup. so task_pool must be given.
    """
    def __init__(self, name, adminname, reportname, task_pool):
        self.adminname = adminname
        self.reportname = reportname
        self.ref_url = '{}/api/{}/report/{}/{}/{}'.format(
            BASE_URL, API_VERSION, adminname, reportname, name
        )
        BaseObject.__init__(self, name, 'Reports')

        if not self.model().load(self) and task_pool:
            self.perform('dns_lookup', task_pool)

    def perform(self, taskname, task_pool, **kwargs):
        """
        Runs a method imported from tasks with self and kwargs as arguments.
        """
        method = getattr(tasks, taskname)

        # Start the task
        task = method.delay(self.name, self.adminname, self.reportname, **kwargs)
        task_pool.submit(self, task)
        self.task = {'taskname': taskname, 'exception': None, 'finished': False,
                     'state': task.state, 'result': None}
        self.save()
        return True

    def finished(self, task_pool):
        """
        Returns the status of last performed task.
        If the task is finished, updates the current state.
        """
        task = task_pool.get(self)
        if task is None or self.task is None:
            return True

        if not task.ready():
            self.task['state'] = task.state
            return False

        try:
            self.task['result'] = task.get(self)
        except Exception as e:
            self.task['exception'] = str(e)
        finally:
            self.task.update({'finished': True, 'state': task.state})
            self.save()
        return True


class Admin(BaseObject):
    """
    An admin is someone who is authorized to use this app
    """
    def __init__(self, name):
        self.ref_url = '{}/api/{}/admin/{}'.format(
            BASE_URL, API_VERSION, name
        )
        BaseObject.__init__(self, name, 'Admins')

        if not self.model().load(self):
            self.password = generate_password_hash(
                'admin', method='pbkdf2:sha256'
            )
            self.created = datetime.utcnow()
            self.generate_token()
            self.model().load(self)
        self.last_login = datetime.utcnow()
        self.save()

    def generate_token(self):
        """
        Generates new auth token
        """
        token = "".join(map(lambda x: choice(string.ascii_letters + string.digits), range(64)))
        self.token = {
            'hash': generate_password_hash(token, method='pbkdf2:sha256'),
            'expires': datetime.utcnow() + timedelta(seconds=TOKEN_TIMEOUT)
        }
        self.save()
        return dict(token=self.name+":"+token, validity=TOKEN_TIMEOUT, metric='seconds')

    def renew_token(self):
        """
        Renew current token if not already expired, returns boolean
        """
        if self.token.get('expires') < datetime.utcnow():
            result = False
        self.token.update({
            'expires': datetime.utcnow() + timedelta(seconds=TOKEN_TIMEOUT)
        })
        result = self.save()
        validity = (self.token.get('expires') - datetime.utcnow()).seconds
        return dict(renewed=result, validity=validity, metric='seconds')

    def validate_token(self, token):
        """
        Compares hashed tokens
        """
        if self.token.get('expires') < datetime.utcnow():
            return False
        return check_password_hash(self.token.get('hash'), token)

    def validate_password(self, password):
        """
        Compares hashed password
        """
        return check_password_hash(self.password, password)

    def revoke_token(self):
        """
        Revokes current auth token
        """
        self.token.update({
            'expires': datetime.utcnow()
        })
        return dict(revoked=self.save())

