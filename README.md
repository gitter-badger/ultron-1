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
| Authenntication method | ULTRON_AUTH_METHOD | 'pam_auth' |
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
sudo apt-get install -y tmux build-essential libssl-dev libffi-dev python3-dev sshpass virtualennv

# RHEL / CentOS / Fedora
sudo yum install -y tmux gcc libffi-devel python3-devel openssl-devel sshpass virtualenv
```

***Also install [MongoDB](https://www.mongodb.com), [redis](https://redis.io) and [RabbitMQ](https://www.rabbitmq.com) from their official site***

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

* Run application

```bash
# Start important services
sudo systemctl start mongod
sudo systemctl start redis
sudo systemctl start rabbitmq-server

# Run app
ultron-run
```


### API docs and examples

* URL format for v1.0

```bash
base_url='http://localhost:8080'
api_url=$base_url/api/v1.0
```

* Credentials

```bash
user=$USER
echo -en 'Enter login password for '$user': ' && read -s pass
```

* Example: Perform ping check on 2 hosts

```bash
reportname='ping_check'

# Create report
curl --request POST \
  --url $api_url/reports/$user/$reportname \
  --form 'clientnames=localhost,127.0.0.1' \
  --user $user:$pass

# Get report
curl --request GET \
  --url $api_url/reports/$user/$reportname \
  --user $user:$pass

# Get client
curl --request GET \
  --url $api_url/report/$user/$reportname/localhost \
  --user $user:$pass

# Modify client state
curl --request POST \
  --url $api_url/report/$user/$reportname/localhost \
  --form 'data={"newattr": "test"}' \
  --user $user:$pass

# Start task (ping)
curl --request POST \
  --url $api_url/task/$user/$reportname \
  --form task=ping \
  --user $user:$pass

# Finish current task
curl --request GET \
  --url $api_url/task/$user/$reportname \
  --user $user:$pass

# Delete client
curl --request DELETE \
  --url $api_url/report/$user/$reportname/localhost \
  --user $user:$pass

# Delete report
curl --request DELETE \
  --url $api_url/reports/$user/$reportname \
  --user $user:$pass
```


* Example: Admin management

***Note: Non readonly features are restricted to ultron admin only***
***If auth method is 'pam_auth', ultron admin is someone who is running the server***

```bash
# Get all admins
curl --request GET \
  --url $api_url/admins \
  --user $user:$pass

# Get one admin info and all his created report names
curl --request GET \
  --url $api_url/admin/$user \
  --user $user:$pass

# Modify admin parameters
curl --request POST \
  --url $api_url/admin/$user \
  --form 'data={"newattr": "test"}' \
  --user $user:$pass

# Delete admin
curl --request DELETE \
  --url $api_url/admin/$user \
  --user $user:$pass
```
