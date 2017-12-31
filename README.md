# ultron

Just another infrastructure management tool


### Dependencies

Only Linux platform with systemd supports this.

* [Python 3+](https://www.python.org)
* [mongoDB](https://www.mongodb.com)
* [Redis](https://redis.io)
* [RabbitMQ](https://www.rabbitmq.com)
* [tmux](https://github.com/tmux/tmux)
* [sshpass](https://linux.die.net/man/1/sshpass)


### Installation

First make sure your default python interpreter is python 3+


* Install dependencies

```bash
# Ubuntu / Debian
sudo apt-get install -y mongodb tmux rabbitmq-server build-essential libssl-dev libffi-dev python3-dev sshpass

# RHEL / CentOS / Fedora
sudo yum install -y mongodb tmux rabbitmq-server gcc libffi-devel python3-devel openssl-devel sshpass
```


* It is optional but recommended to use virtual python3 environment)

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


# Set admin password

python
from ultron.objects import Admin
from werkzeug.security import generate_password_hash

password = 'admin'    # Admin password

Admin('admin').set('password', generate_password_hash(password, method='pbkdf2:sha256'))
quit()
```

* Run application

```
ultron-run
```

### API docs

```bash
# Create report

curl --request POST \
  --url http://localhost:8080/api/v1.0/admin/test/reports \
  --form 'clientnames=localhost,pc' \
  --user admin:admin


# Get report

curl --request GET \
  --url http://localhost:8080/api/v1.0/admin/test/reports \
  --user admin:admin


# Get client

curl --request GET \
  --url http://localhost:8080/api/v1.0/admin/test/reports/localhost \
  --user admin:admin


# Start task (ping)

curl --request POST \
  --url http://localhost:8080/api/v1.0/admin/test/task \
  --form task=ping \
  --user admin:admin


# Finish current task

curl --request GET \
  --url http://localhost:8080/api/v1.0/admin/test/task \
  --user admin:admin


# Delete client

curl --request DELETE \
  --url http://localhost:8080/api/v1.0/admin/test/reports/localhost \
  --user admin:admin


# Delete report

curl --request DELETE \
  --url http://localhost:8080/api/v1.0/admin/test/reports \
  --user admin:admin
```


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
