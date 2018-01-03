# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

from __future__ import absolute_import, unicode_literals
import socket
import datetime
from bson.json_util import dumps
from ultron import tasks, models
from ultron.config import BASE_URL, API_VERSION
from werkzeug.security import generate_password_hash


# class Client:

#     def __init__(self, host, login_user=None, login_pass=None, login_timeout=120,
#                  scp_timeout=120, execute_timeout=120,
#                  key_filename=None, ssh_port=22, login_shell='/bin/sh',
#                  virtual=None):
#         self.host = host
#         self.login_user = login_user if login_user != None else os.getlogin()
#         self.login_pass = login_pass
#         self.login_timeout = login_timeout
#         self.scp_timeout = scp_timeout
#         self.execute_timeout = execute_timeout
#         self.ssh_key_filename = key_filename
#         self.ssh_port = ssh_port
#         self.login_shell = login_shell
#         self.virtual = virtual
#         INVENTORY = HOSTSDUMP
#         self.history = []
#         self.dns_lookup()
#         self.ping_check()
#         self.ssh_accessible = None

#     def __repr__(self):
#         return '{} ({}) <{}>'.format(self.host, self.ip, self.fqdn)

#     def __str__(self):
#         return self.host

#     def last_task_result(self):
#         return self.history[-1]

#     def save(self):
#         if not os.path.exists(INVENTORY):
#             os.makedirs(INVENTORY, exist_ok=True)
#         with open(INVENTORY+'/'+self.host, 'wb') as f:
#             pickle.dump(self, f)

#     def cleanup(self):
#         path = INVENTORY+'/'+self.host
#         if os.path.exists(path):
#             os.remove(path)

#     def dns_lookup(self):
#         try:
#             self.ip = socket.gethostbyname(self.host)
#             self.dns = socket.gethostbyaddr(self.ip)
#             self.hostname = self.dns[0]
#             self.fqdn = socket.getfqdn(self.ip)
#         except:
#             self.dns = self.ip = self.hostname = self.fqdn = None

#     def perform(self, task, args=[], kwargs={}):
#         method = getattr(self, task)
#         method(*args, **kwargs)

#     def ping_check(self):
#         if self.dns == None: return
#         act = {'task': 'Ping check', 'start': datetime.utcnow()}
#         try:
#             act['result'] = ping(self.hostname)
#             self.online = True if act['result']['exit_status'] == 0 else False
#             act['exception'] = None
#         except Exception as e:
#             act['exception'] = e
#             if DEBUG: print(traceback.format_exc())
#         finally:
#             act['end'] = datetime.utcnow()
#             act['execution_time'] = (act['end']-act['start']).seconds
#             self.history.append(act)


#     def execute(self, commands, inputs=None, hide=[], task='Execute commands'):
#         if self.dns == None: return
#         if self.online == False: return
#         if self.ssh_accessible == None: self.os_check
#         if self.ssh_accessible == False: return
#         act = {'task': task, 'start': datetime.utcnow()}
#         try:
#             result = ssh(self.hostname, commands=commands, inputs=inputs, hide=[],
#                          username=self.login_user, password=self.login_pass,
#                          key_filename=self.ssh_key_filename, port=self.ssh_port,
#                          shell=self.login_shell, timeout=self.execute_timeout)
#             act['result'] = result
#             act['exception'] = None
#             self.ssh_accessible = True
#         except Exception as e:
#             self.ssh_accessible = False
#             act['exception'] = e
#             if DEBUG: print(traceback.format_exc())
#         finally:
#             act['end'] = datetime.utcnow()
#             act['execution_time'] = (act['end']-act['start']).seconds
#             self.history.append(act)

#     def os_check(self):
#         if self.dns == None: return
#         if self.online == False: return
#         if self.ssh_accessible == False: return
#         comm = ['uname -srm',
#                 'python -c '+quote('import platform; print(" ".join(platform.dist()));')]
#         self.execute(comm, task='OS check')
#         lar = self.last_task_result()
#         if lar['exception'] != None: return
#         result = lar['result']
#         self.ssh_accessible = True if result[0]["exit_status"] == 0 else False
#         uname = result[0]["stdout"].split()
#         if len(uname) != 3: return False
#         self.kernel_name, self.kernel_release, self.arch = uname
#         if uname[0] == 'Linux' and len(result[1]["stdout"].split()) > 1:
#             distnfo = result[1]['stdout'].split()
#             self.dist_name = distnfo[0]
#             self.dist_release = distnfo[1]
#         else:
#             self.dist_name, self.dist_release = None, None

#     def find_consoles(self):
#         if self.dns == None: return
#         cons = ['ilo', 'con', 'imm', 'ilom', 'alom', 'xscf', 'power']
#         act = {'task': 'Find online consoles', 'start': datetime.utcnow()}
#         try:
#             act['result'] = find_consoles(self.hostname)
#             self.available_consoles = act['result']
#             if len(act['result']) > 0:
#                 self.virtual = False
#             act['exception'] = None
#         except Exception as e:
#             act['exception'] = e
#             if DEBUG: print(traceback.format_exc())
#         finally:
#             act['end'] = datetime.utcnow()
#             act['execution_time'] = (act['end']-act['start']).seconds
#             self.history.append(act)

#     def scp_from(self, from_path, from_host='localhost',
#                  to_path='/tmp/', options={}):
#         if self.dns == None: return
#         if self.online == False: return
#         if self.ssh_accessible == None: self.os_check
#         if self.ssh_accessible == False: return
#         act = {'task': 'SCP', 'start': datetime.utcnow()}
#         try:
#             target = from_host+':'+from_path
#             destination = self.login_user+'@'+self.hostname+':'+to_path
#             if self.ssh_key_filename != None:
#                 options['-i'] = self.ssh_key_filename
#             act['result'] = scp(target, destination, options,
#                                 password=self.login_pass,timeout=self.scp_timeout)
#             act['exception'] = None
#             if act['result']['exit_status'] == 0:
#                 self.ssh_accessible = True
#         except Exception as e:
#             act['exception'] = e
#             if DEBUG: print(traceback.format_exc())
#         finally:
#             act['end'] = datetime.utcnow()
#             act['execution_time'] = (act['end']-act['start']).seconds
#             self.history.append(act)

#     def scp_to(self, from_path, to_host='localhost',
#                to_path='/tmp/', options={}):
#         if self.dns == None: return
#         if self.online == False: return
#         if self.ssh_accessible == None: self.os_check
#         if self.ssh_accessible == False: return
#         act = {'task': 'SCP', 'start': datetime.utcnow()}
#         try:
#             target = self.login_user+'@'+self.hostname+':'+from_path
#             destination = to_host+':'+to_path
#             if self.ssh_key_filename != None:
#                 options['-i'] = self.ssh_key_filename
#             act['result'] = scp(target, destination, options,
#                                 password=self.login_pass,timeout=self.scp_timeout)
#             act['exception'] = None
#             if act['result']['exit_status'] == 0:
#                 self.ssh_accessible = True
#         except Exception as e:
#             act['exception'] = e
#             if DEBUG: print(traceback.format_exc())
#         finally:
#             act['end'] = datetime.utcnow()
#             act['execution_time'] = (act['end']-act['start']).seconds
#             self.history.append(act)
#             self.history.append(act)


class BaseObject(object):
    """
    Parent class for all objects
    """
    def __init__(self, modelname):
        self._modelname = modelname
        self.load()

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
        for k, v in data.copy().items():
            if k.startswith('_'):
                del data[k]
            try:
                dumps([v])
            except:
                data[k] = None
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

    def get(self, attr, default=None):
        """
        Returns attribute if initialized else returns the passed default value.
        """
        if hasattr(self, attr):
            return getattr(self, attr)
        else:
            return default

    def set(self, attr, value):
        """
        Used to change attributes of admin. Returns false if no action required
        and True if state changed successfully.
        """
        if hasattr(self, attr):
            if getattr(self, attr) == value:
                return False
        setattr(self, attr, value)
        self.save()
        return True

    def update(self, data):
        """
        Used to update multiple attributes at once.
        Returns false if no action required
        and True if state changed successfully.
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
    """
    def __init__(self, name, admin, reportname):
        self.name = name
        self.admin = admin.name
        self.reportname = reportname
        self._task = None
        self.result = None
        self.ref_url = '{}/api/{}/report/{}/{}/{}'.format(BASE_URL, API_VERSION,
                                                admin.name, reportname, name)
        BaseObject.__init__(self, 'Reports')

    def dns_lookup(self):
        """
        Initializes fqdn, ip, hostname etc. for the given client.
        """
        self.ip = socket.gethostbyname(self.name)
        self.fqdn = socket.getfqdn(self.ip)
        self.dns = socket.gethostbyaddr(self.ip)
        self.hostname = self.dns[0]
        self.save()
        return True

    def load(self):
        """
        Import saved state from inventory. If not exists,
        and dns_lookup is not set to False, performs self.dns_lookup()
        """
        if not self.model().load(self):
            self.dns_lookup()
        return True


    def perform(self, task, force=False, **kwargs):
        """
        Runs a method imported from tasks with self and kwargs as arguments.
        If force is True and a task is already running, it will override the task,
        i.e. the first result will not be logged but both tasks will be executed in parallel.
        """
        if not self.finished() and not force:
            return False

        method = getattr(tasks, task)

        # Start the task
        self._task = method.delay(self, self.admin, **kwargs)
        self.result = {'task': task, 'exception': None, 'finished': False,
                       'state': self._task.state, 'result': None}
        self.save()
        return True

    def finished(self):
        """
        Returns the status of last performed task.
        If the task is finished, updates the current state.
        """
        if self._task is None:
            return True

        if not self._task.ready():
            self.result['state'] = self._task.state
            return False

        try:
            self.result['result'] = self._task.get()
        except Exception as e:
            self.result['exception'] = str(e)
        finally:
            self.result.update({'finished': True, 'state': self._task.state})
            self._task = None
            self.save()
        return True


class Admin(BaseObject):
    """
    An admin is someone who is authorized to use this app
    """
    def __init__(self, name):
        self.name = name
        self.ref_url = '{}/api/{}/admin/{}'.format(BASE_URL, API_VERSION, name)
        BaseObject.__init__(self, 'Admins')

    def load(self):
        """
        Loads admin from DB else creates new
        """
        if not self.model().load(self):
            self.password = generate_password_hash(
                    'admin', method="pbkdf2:sha256"
            )
            self.created = datetime.datetime.utcnow()
            self.restrict = []
            # self.history = []
            self.save()
            self.model().load(self)
        self.last_login = datetime.datetime.utcnow()
        self.save()
        return True

    # def log_history(self, request):
    #     """
    #     Logs important url requests in history
    #     """
    #     data = {'method': request.method,
    #             'path': request.path,
    #             'args': request.args.to_dict(),
    #             'form': request.form.to_dict(),
    #             'datetime': datetime.datetime.utcnow()}
    #     self.history.append(data)
    #     return self.save()
    #
    # def clean_history(self, start=None, end=None):
    #     """
    #     Cleans history
    #     """
    #     if start is not None and end is not None:
    #         for x in self.history:
    #             if x['datetime'] >= start and x['datetime'] <= end:
    #                 self.history.pop(x)
    #     elif start is not None:
    #         for x in self.history[::-1]:
    #             if x['datetime'] >= start:
    #                 self.history.remove(x)
    #     elif end is not None:
    #         for x in self.history:
    #             if x['datetime'] <= end:
    #                 self.history.remove(x)
    #     else:
    #         self.history = []
    #     return self.save()
