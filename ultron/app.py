# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import re
import json
import urllib
from flask import Flask, jsonify, request
from flask_restful import Resource, Api, abort
from flask_restful.reqparse import RequestParser
from jinja2 import evalcontextfilter, Markup, escape
from gevent.wsgi import WSGIServer
from ultron.objects import Client, Admin
from ultron.models import Reports
from ultron.authentication import Authentication
from ultron.config import API_VERSION, PORT


app = Flask(__name__)
app.config['BUNDLE_ERRORS'] = True
api = Api(app, prefix='/api/'+API_VERSION, catch_all_404s=True)
server = WSGIServer(('', PORT), app)
auth = Authentication()

clients = list()


# Custom filters ---------------------------------------------------------------

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter('urlencode')
def urlencode_filter(s):
    """
    Encodes string into url
    """
    s = urllib.parse.quote(s.encode())
    return Markup(s)

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    """
    new line to <br/>
    """
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
        return result


# Helper functions -------------------------------------------------------------

def form2list(string, regex='[^a-zA-Z0-9._-]', lowercase=True, uniq=True):
    """
    Takes a string and returns regex seperated list
    """
    if lowercase:
        string = string.lower()
    lst = list(map(lambda x: x.strip(), re.split(regex, string)))
    while '' in lst: lst.remove('')
    return list(set(lst)) if uniq else lst

def init_clients(clientnames, admin, reportname):
    """
    Initialize client objects from passed clientnames
    """
    valid, invalid = [], []
    for x in clientnames:
        try:
            valid.append(Client(x, admin, reportname))
        except Exception as e:
            invalid.append([x, str(e)])
    return valid, invalid


# Core -------------------------------------------------------------------------

class ReportsApi(Resource):
    """
    Methods: GET, POST
    """
    @auth.authenticate
    def get(self, admin, reportname, clientname=None):
        """
        Returns current state of clients
        """
        admin = Admin(admin)
        parser = RequestParser()
        parser.add_argument('query', type=str,
                help='Expected JSON formatted pymongo query')
        parser.add_argument('projection', type=str,
                help='Expected JSON formatted pymongo projection')
        args = parser.parse_args()

        if clientname is not None:
            query = {'clientname': clientname}
        elif args['query'] is not None:
            try:
                query = dict(json.loads(args['query']))
            except Exception as e:
                abort(
                    400,
                    query='{}. Expected JSON encoded pymongo filter'.format(e)
                )
        else:
            query = {}

        if args['projection'] is not None:
            try:
                projection = dict(json.loads(args['projection']))
            except Exception as e:
                abort(
                    400,
                    query='{}. Expected JSON encoded pymongo projection'.format(e)
                )
        else:
            projection = {}

        query.update({'admin': admin.name, 'name': reportname})
        projection.update({'_id': 0})
        reports = Reports()
        result = list(reports.collection.find(query, projection))
        return result

    @auth.authenticate
    def post(self, admin, reportname):
        """
        Starts/loads clients for an ultron
        """
        admin = Admin(admin)
        parser = RequestParser()
        parser.add_argument('clientnames', type=str, required=True,
                help='Expected comma seperated hostnames')
        args = parser.parse_args()

        clients, not_found = init_clients(form2list(args['clientnames']),
                                          admin, reportname)
        if len(clients) == 0:
            abort(400, clientnames="No clientname is DNS resolvable report")

        result = list(map(lambda x: {x.name: x.dict()}, clients))
        return result

    def delete(self, admin, reportname, clientname=None):
        """
        Deletes a report
        """
        admin = Admin(admin)

        if clientname is None:
            reports = Reports()
            clientnames = list(map(
                        lambda x: x['clientname'],
                        reports.collection.find({'admin': admin.name,
                            'name': reportname})
                    ))
        else:
            clientnames = [clientname]

        clients, not_found = init_clients(clientnames, admin, reportname)
        if len(clients) == 0:
            abort(400, clientnames="No clientname is DNS resolvable report")

        result = list(map(lambda x: {x.name: x.cleanup()}, clients))
        return result


class TaskApi(Resource):
    """
    Methods: GET, POST
    """
    @auth.authenticate
    def get(self, admin, reportname):
        """
        Updates task state in clients and returns if the task in finished
        """
        global clients

        admin = Admin(admin)
        parser = RequestParser()
        parser.add_argument('clientnames', type=str,
                help='Expected comma seperated hostnames')
        args = parser.parse_args()

        if args['clientnames'] is not None:
            clientnames = form2list(args['clientnames'])
            targets = list(map(lambda x: x.name in clientnames, clients))
            if len(targets) == 0:
                abort(400, clientnames="No client found")
        else:
            targets = clients

        result = list(map(lambda x: {x.name: x.finished()}, targets))
        return result

    @auth.authenticate
    def post(self, admin, reportname):
        """
        Performs a task for specified clients in an ultron
        """
        global clients

        admin = Admin(admin)
        parser = RequestParser()
        parser.add_argument('task', type=str, required=True,
                help='Missing task to be performed')
        parser.add_argument('kwargs', type=str,
                help='Expected JSON encoded key-value pairs')
        parser.add_argument('clientnames', type=str,
                help='Expected comma seperated hostnames')
        args = parser.parse_args()

        task = args['task']
        if args['kwargs'] is not None:
            try:
                kwargs = dict(json.loads(args['kwargs']))
            except Exception as e:
                abort(
                    400,
                    kwargs='{}. Expected JSON encoded key-value pairs'.format(e)
                )
        else:
            kwargs = {}

        if args['clientnames'] is not None:
            clientnames = form2list(args['clientnames'])
        else:
            reports = Reports()
            clientnames = list(map(
                lambda x: x['clientname'],
                reports.collection.find({
                    'admin': admin.name,
                    'name': reportname
                })
            ))
        clients, not_found = init_clients(clientnames, admin, reportname)
        if len(clients) == 0:
            abort(400, clientnames="No clientname is DNS resolvable report")

        result = list(map(lambda x: {x.name: x.perform(task, **kwargs)},
                                    clients))
        admin.log_history(request)
        return result


# Error handlers ---------------------------------------------------------------

class InvalidUsage(Exception):
    """
    Default error handler for invalid usage
    """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


# Routes -----------------------------------------------------------------------

api.add_resource(ReportsApi,
                 '/<admin>/<reportname>/reports',
                 '/<admin>/<reportname>/reports/<clientname>')
api.add_resource(TaskApi, '/<admin>/<reportname>/task')


# Run app ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run('0.0.0.0', port=PORT, debug=True)
