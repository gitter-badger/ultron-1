# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

import os
from subprocess import Popen, PIPE
from shlex import quote
from celery import Celery
from ultron import objects, models
from ultron.config import CELERY_BACKEND, CELERY_BROKER

app = Celery('tasks', backend=CELERY_BACKEND, broker=CELERY_BROKER)


@app.task
def ping(client, admin):
    """
    Function to ping referenced client
    """
    # Prepare shell command
    _options = client.get('ping_options', ['-c1', '-w5'])
    target = client.get('fqdn', client.name)
    cmd = ['ping'] + _options + [target]

    # Execute shell command
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(timeout=20)
    stdout, stderr = stdout.decode('latin1'), stderr.decode('latin1')
    exit_status = p.returncode

    # Set/reset client properties
    if exit_status == 0:
        state_changed = client.set('online', True)
    else:
        state_changed = client.set('online', False)

    # return result
    return {'stdout': stdout, 'stderr': stderr,
            'state_changed': state_changed, 'command': ' '.join(p.args),
            'exit_status': exit_status}


@app.task
def ssh(client, admin, command, timeout=120, tty=False, stdin=None, hide=[]):
    """
    Function to execute command over SSH protocol
    """
    # Prepare shell command
    _options = client.get('ssh_options', ['-o', 'StrictHostKeyChecking=no'])
    target = client.get('fqdn', client.name)
    ssh_user = client.get('ssh_user', os.getlogin())
    ssh_pass = client.get('ssh_pass', 'dummy')
    ssh_key = client.get('ssh_key', None)
    login_shell = client.get('ssh_login_shell', '/bin/sh')
    if ssh_key and '-i' not in _options:
        _options += ['-i', ssh_key]
    if tty and '-tt' not in _options:
        _options += ['-tt']
    cmd = ['sshpass', '-p', ssh_pass, 'ssh'] + _options
    cmd += [ssh_user + '@' + target, login_shell + ' -c ' + quote(command)]

    # Execute shell command
    if stdin:
        echo = Popen(['echo', '-en', stdin], stdout=PIPE)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=echo.stdout)
        echo.stdout.close()
    else:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(timeout=timeout)
    stdout, stderr = stdout.decode('latin1'), stderr.decode('latin1')
    exit_status = p.returncode

    # Hide sensetive keywords
    hide.append(ssh_pass)
    for h in hide:
        if stdin:
            stdin = stdin.replace(h, '***')
        stdout = stdout.replace(h, '***')
        stderr = stderr.replace(h, '***')

    # return result
    return {'stdin': stdin, 'stdout': stdout, 'stderr': stderr,
            'state_changed': False, 'command': ' '.join(p.args),
            'exit_status': exit_status}
