# ultron

Just another infrastructure management tool


### Dependencies

Only Linux platform with systemd supports this.

* [Python 3+](https://www.python.org)
* [mongoDB](https://www.mongodb.com)
* [redis](https://redis.io)
* [RabbitMQ](https://www.rabbitmq.com)
* [tmux](https://github.com/tmux/tmux)
* [sshpass](https://linux.die.net/man/1/sshpass)


### Configuration

| Parameter | Environment variable | Default (if not set) |
| --------- | -------------------- | -------------------- |
| Default port | ULTRON_PORT | '8080' |
| Base URL | ULTRON_BASE_URL | Local server's http://FQDN:PORT. e.g. http://localhost.localdomain:8080 |
| Application secret | ULTRON_SECRET | Random string |
| Authenntication method | ULTRON_AUTH_METHOD | 'basic_auth' |
| mongoDB username | ULTRON_DB_USER | None |
| mongoDB password | ULTRON_DB_PASS | None |
| mongoDB host | ULTRON_DB_HOST | 'localhost:27017' |
| Celery backend | ULTRON_CELERY_BACKEND | 'redis://localhost/1' |
| Celery broker | ULTRON_CELERY_BROKER | 'pyamqp://' |


### Installation

First make sure your default python interpreter is python 3+

* Install dependencies

```bash
# Ubuntu / Debian
sudo apt-get install -y tmux build-essential libssl-dev libffi-dev python3-dev sshpass

# RHEL / CentOS / Fedora
sudo yum install -y tmux gcc libffi-devel python3-devel openssl-devel sshpass
```

***Also install [redis](https://redis.io) and [RabbitMQ](https://www.rabbitmq.com) from their official site***


* It is optional but recommended to use virtual python3 environment

```bash
# Install virtualenv

### Ubuntu / Debian
sudo apt-get install -y virtualenv

### RHEL / CentOS / Fedora
sudo yum install -y virtualenv


# Activate virtual environment

virtualenv -p python3 ~/.venv
source ~/.venv/bin/activate
```


* Install and setup

```bash
# Install package

pip install ultron


# Start important services

sudo systemctl start mongod
sudo systemctl start redis-server
sudo systemctl start rabbitmq-server


# Set admin password

python -c '
from ultron.objects import Admin
from werkzeug.security import generate_password_hash

password = "admin"    # Admin password

Admin("admin").set("password", generate_password_hash(password, method="pbkdf2:sha256"))
quit()'
```

* Run application

```
ultron-run
```

### API docs

```bash
# URL format for v1.0

base_url='http://localhost:8080'
report_name='ping_check'
api_url=$base_url/api/v1.0/$USER/$report_name
creds='admin:admin'


# Create report

curl --request POST \
  --url $api_url/reports \
  --form 'clientnames=localhost,127.0.0.1' \
  --user $creds


# Get report

curl --request GET \
  --url $api_url/reports \
  --user $creds


# Get client

curl --request GET \
  --url $api_url/reports/localhost \
  --user $creds


# Start task (ping)

curl --request POST \
  --url $api_url/task \
  --form task=ping \
  --user $creds


# Finish current task

curl --request GET \
  --url $api_url/task \
  --user $creds


# Delete client

curl --request DELETE \
  --url $api_url/reports/localhost \
  --user $creds


# Delete report

curl --request DELETE \
  --url $api_url/reports \
  --user $creds
```
