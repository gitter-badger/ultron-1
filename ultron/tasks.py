# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

import os
from subprocess import Popen, PIPE
from shlex import quote
from celery import Celery
from ultron.config import CELERY_BACKEND, CELERY_BROKER
from ultron import objects


celery_app = Celery('tasks', backend=CELERY_BACKEND, broker=CELERY_BROKER)


@celery_app.task
def ping(clientname, adminname, reportname):
    """
    Function to ping referenced client
    """
    client = objects.Client(clientname, adminname, reportname)
    # Prepare shell command
    options = client.props.get('ping_options', ['-c1', '-w5'])
    target = client.fqdn
    cmd = ['ping'] + options + [target]

    # Execute shell command
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(timeout=20)
    stdout, stderr = stdout.decode('latin1'), stderr.decode('latin1')
    exit_status = p.returncode

    # Set/reset client properties
    client.state.update({'online': (exit_status == 0)})
    client.save()

    # return result
    return {'stdout': stdout, 'stderr': stderr,
            'command': ' '.join(p.args), 'exit_status': exit_status}

@celery_app.task
def shell(clientname, adminname, reportname, command, timeout=120, stdin=None, hide=[]):
    """
    Function to execute wildcard shell commands with client as argument
    Usage:
        It renders the supplied command by passing whole client
            object as: '...'.format(client = Client(clientname, adminname, reportname))
        If stdin is mentioned, it can also be formatted with client object.
        If some word containg sensitive information, it can be hidden
            by passing it in 'hidden' list.
    Example:
        shell('localhost', 'admin', 'test', 'nslookup {client.ip}')
    """
    client = objects.Client(clientname, adminname, reportname)
    cmd = command.format(client=client)

    # Execute shell command
    if stdin:
        echo = Popen(['echo', '-en', stdin.format(client=client)], stdout=PIPE)
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, stdin=echo.stdout, shell=True)
        echo.stdout.close()
    else:
        p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    stdout, stderr = p.communicate(timeout=timeout)
    stdout, stderr = stdout.decode('latin1'), stderr.decode('latin1')
    exit_status = p.returncode

    for h in hide:
        if stdin:
            stdin = stdin.replace(h, '***')
        stdout = stdout.replace(h, '***')
        stderr = stderr.replace(h, '***')

    # return result
    return {'stdin': stdin, 'stdout': stdout, 'stderr': stderr,
            'command': p.args, 'exit_status': exit_status}

@celery_app.task
def ssh(clientname, adminname, reportname, command, timeout=120, tty=False, stdin=None, hide=[]):
    """
    Function to execute command over SSH protocol
    """
    client = objects.Client(clientname, adminname, reportname)
    # Prepare shell command
    options = client.props.get('ssh_options', ['-o', 'StrictHostKeyChecking=no'])
    target = client.props.get('fqdn', client.name)
    ssh_user = client.props.get('ssh_user', os.getlogin())
    ssh_pass = client.props.get('ssh_pass', 'dummy')
    ssh_key = client.props.get('ssh_key', None)
    login_shell = client.props.get('ssh_login_shell', '/bin/sh')
    if ssh_key and '-i' not in options:
        options += ['-i', ssh_key]
    if tty and '-tt' not in options:
        options += ['-tt']
    cmd = ['sshpass', '-p', ssh_pass, 'ssh'] + options
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

    ssh_error_codes = {
        255: 'Not accessible',
        5: 'Authentication failed'
    }
    # Set/reset client properties
    client.state.update(
        {'ssh_status': ssh_error_codes.get(exit_status, 'Accessible')}
    )
    client.save()

    # return result
    return {'stdin': stdin, 'stdout': stdout, 'stderr': stderr,
            'command': ' '.join(p.args), 'exit_status': exit_status}
