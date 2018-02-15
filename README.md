[![PyPI version](https://img.shields.io/pypi/v/ultron.svg)](https://pypi.python.org/pypi/ultron)
[![Build Status](https://travis-ci.org/rapidstack/ultron.svg?branch=master)](https://travis-ci.org/rapidstack/ultron)


# ultron

[![Join the chat at https://gitter.im/rapidstack/ultron](https://badges.gitter.im/rapidstack/ultron.svg)](https://gitter.im/rapidstack/ultron?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Not just another infrastructure management tool


### Dependencies

Only Linux platform with systemd supports this.

* [Python 3.6+](https://www.python.org)
* [mongoDB](https://www.mongodb.com)
* [redis](https://redis.io)
* [tmux](https://github.com/tmux/tmux)
* [sshpass](https://linux.die.net/man/1/sshpass)
* [openssl](https://linux.die.net/man/1/openssl)


### Configuration

| Parameter | Environment variable | Default (if not set) |
| --------- | -------------------- | -------------------- |
| Default port | ULTRON_PORT | 5050 |
| Base URL | ULTRON_BASE_URL | Local server's https://FQDN:PORT. e.g. https://localhost:5050 |
| SSL key file | ULTRON_SSL_KEY_FILE | '~/.ultron_key.pem' |
| SSL certification file | ULTRON_SSL_CERT_FILE | '~/.ultron_cert.pem' |
| Application secret | ULTRON_SECRET | Random string |
| Authenntication method | ULTRON_AUTH_METHOD | 'pam_auth' |
| Auth token validity | ULTRON_TOKEN_TIMEOUT | 3600 |
| mongoDB host | ULTRON_DB_HOST | 'localhost:27017' |
| mongoDB username | ULTRON_DB_USER | None |
| mongoDB password | ULTRON_DB_PASS | None |
| mongoDB data path | ULTRON_DB_PATH | '~/.ultron_data' |
| Celery backend | ULTRON_CELERY_BACKEND | 'rpc://' |
| Celery broker | ULTRON_CELERY_BROKER | 'redis://localhost:6379/' |
| Auto scaling (max,min) concurrency | ULTRON_AUTOSCALE | '100,3' |
| Plugins path | ULTRON_PLUGINS_PATH | '~/python_modules' |


### Installation

First make sure your default python interpreter is python 3+

* Install dependencies

```bash
# Ubuntu / Debian
sudo apt-get install -y tmux build-essential libssl-dev libffi-dev python3-dev sshpass openssl
sudo pip install virtualenv

# RHEL / CentOS / Fedora
sudo yum install -y tmux gcc libffi-devel python3-devel openssl-devel sshpass openssl
sudo pip install virtualenv
```

***Also install [MongoDB](https://www.mongodb.com) and [redis](https://redis.io) from their official site***

* It is optional but recommended to use virtual python3 environment

```bash
# Activate virtual environment
virtualenv -p python3 ~/.venv
source ~/.venv/bin/activate
```

* Install

```bash
pip install ultron
```

* Generate SSL certificate and key file

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out ~/.ultron_cert.pem -keyout ~/.ultron_key.pem -days 365
```

* Run application

```bash
# Run app
ultron-run
```


### API docs and examples

* URL format for v1.0

```bash
base_url='https://localhost:5050'
api_url=$base_url/api/v1.0
```

* Credentials

```bash
user=$USER
echo -en 'Enter login password for '$user': ' && read -s pass
```

* Example: List allowed tasks

```bash
curl -k --request GET \
  --url $api_url/tasks/$user
  --user $user:$pass
```

* Example: Perform ping check on 2 hosts

```bash
# Report name
reportname='ping_check'

# Create report
curl -k --request POST \
  --url $api_url/reports/$user/$reportname \
  --form 'clientnames=localhost,127.0.0.1' \
  --user $user:$pass

# Get report
curl -k --request GET \
  --url $api_url/reports/$user/$reportname \
  --user $user:$pass

# Get client
curl -k --request GET \
  --url $api_url/report/$user/$reportname/localhost \
  --user $user:$pass

# Modify client state
curl -k --request POST \
  --url $api_url/report/$user/$reportname/localhost \
  --form 'data={"newattr": "test"}' \
  --user $user:$pass

# Start task (ping)
curl -k --request POST \
  --url $api_url/task/$user/$reportname \
  --form task=ping \
  --user $user:$pass

# Finish current task
curl -k --request GET \
  --url $api_url/task/$user/$reportname \
  --user $user:$pass

# Cancel any pending task
curl -k --request DELETE \
  --url $api_url/task/$user/$reportname \
  --user $user:$pass

# Delete client
curl -k --request DELETE \
  --url $api_url/report/$user/$reportname/localhost \
  --user $user:$pass

# Delete report
curl -k --request DELETE \
  --url $api_url/reports/$user/$reportname \
  --user $user:$pass
```


* Example: publish report

Published report will be visible with /public urls

```bash
# Publish report
curl -k --request POST \
  --url $api_url/reports/$user/$reportname \
  --form 'published=1' \
  --user $user:$pass

# Get public report without auth
curl -k --request GET \
  --url $api_url/public/$user/$reportname
```


* Example: Admin management

***Note: Non readonly features are restricted to ultron admin only***
***If auth method is 'pam_auth', ultron admin is someone who is running the server***

```bash
# Get all admins
curl -k --request GET \
  --url $api_url/admins \
  --user $user:$pass

# Get one admin info and all his created report names
curl -k --request GET \
  --url $api_url/admin/$user \
  --user $user:$pass

# Modify admin parameters
curl -k --request POST \
  --url $api_url/admin/$user \
  --form 'data={"newattr": "test"}' \
  --user $user:$pass

# Delete admin
curl -k --request DELETE \
  --url $api_url/admin/$user \
  --user $user:$pass
```


* Example: Token based auth
```bash
# Get auth token
curl -k --request GET \
  --url $api_url/token/$user \
  --user $user:$pass

# Save token
echo -en 'Enter received token: ' && read token

# Use access token
curl -k --request GET \
  --url $api_url/admin/$user \
  --header Authorization:$token

# Renew token
curl -k --request POST \
  --url $api_url/token/$user \
  --header Authorization:$token

# Revoke token
curl -k --request DELETE \
  --url $api_url/token/$user \
  --header Authorization:$token
```


### Plugins

For more info about plugin tasks, click here: [ultron-plugins](https://github.com/rapidstack/ultron-plugins)
