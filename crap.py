
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
