# -*-coding: utf-8 -*-

"""
Author          : Arijit Basu
Email           : sayanarijit@gmail.com
"""

import re
import markdown
import atexit
from tqdm import tqdm
from mdx_gfm import GithubFlavoredMarkdownExtension
from bson.json_util import loads, dumps
from os import path
from flask import Flask, jsonify, make_response, Markup
from flask_restful import Resource, Api, abort
from flask_restful.reqparse import RequestParser
from flask_cors import CORS
from gevent.wsgi import WSGIServer
from ultron.objects import Client, Admin, TaskPool
from ultron.models import Reports, Admins
from ultron.authentication import Authentication
from ultron.config import API_VERSION, PORT, SECRET, SSL_KEY_FILE, SSL_CERT_FILE


app = Flask(__name__)
app.debug = True
app.config['BUNDLE_ERRORS'] = True
app.config['SECRET_KEY'] = SECRET
CORS(app)
api = Api(app, prefix='/api/'+API_VERSION, catch_all_404s=True)
server = WSGIServer(('', PORT), app, keyfile=SSL_KEY_FILE, certfile=SSL_CERT_FILE)
auth = Authentication()
task_pool = TaskPool()
atexit.register(task_pool.purge_all)


# APP overwrites ---------------------------------------------------------------

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


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

def init_clients(clientnames, adminname, reportname):
    """
    Initialize client objects from passed clientnames
    """
    valid, invalid = [], []
    for x in tqdm(clientnames):
        try:
            valid.append(Client(x, adminname, reportname))
        except Exception as e:
            invalid.append([x, str(e)])
    return valid, invalid


# Web GUI ----------------------------------------------------------------------

@app.route('/')
def indexPage():
    here = path.dirname(path.realpath(__file__))
    md = markdown.Markdown(extensions=[GithubFlavoredMarkdownExtension()])
    with open(path.join(path.dirname(here), 'ultron', 'README.md')) as f:
        content = f.read()
    return Markup(md.convert(content))

# @app.route('/<path:path>')
# def serve_page(path):
#     return send_from_directory('static', path)


# API --------------------------------------------------------------------------

class TokenApi(Resource):
    """
    Methods: GET, POST, DELETE
    """
    @auth.authenticate
    @auth.restrict_to_owner
    def get(self, adminname):
        """
        Generates access token
        """
        return Admin(adminname).generate_token()

    @auth.authenticate
    @auth.restrict_to_owner
    def post(self, adminname):
        """
        Renew token if not already expired
        """
        return Admin(adminname).renew_token()

    @auth.authenticate
    @auth.restrict_to_owner
    def delete(self, adminname):
        """
        Revokes current token
        """
        return Admin(adminname).revoke_token()


class ReportApi(Resource):
    """
    Methods: GET, POST, DELETE
    """
    @auth.authenticate
    def get(self, adminname, reportname, clientname):
        """
        Current state of client
        """
        reports = Reports()
        found = reports.collection.find_one(
            {'clientname': clientname, 'adminname': adminname},
            {'_id': 0, '_modelname': 0}
        )
        return dict(result=found)

    @auth.authenticate
    @auth.restrict_to_owner
    def post(self, adminname, reportname, clientname):
        """
        Update client state
        """
        parser = RequestParser()
        parser.add_argument('data', type=str,
                help='Expected BSON encoded key-value pairs')
        args = parser.parse_args()
        data = {}
        if args['data'] is not None:
            try:
                data = dict(loads(args['data']))
            except Exception as e:
                abort(
                    400,
                    data='{}. Expected BSON encoded key-value pairs'.format(e)
                )
        try:
            client = Client(clientname, adminname, reportname)
        except Exception as e:
            abort(
                400,
                data='{}. Invalid client name'.format(e)
            )
        client.props.update(data)
        client.save()
        return dict(result=client.dict())

    @auth.authenticate
    @auth.restrict_to_owner
    def delete(self, adminname, reportname, clientname):
        """
        Deletes a report
        """
        try:
            client = Client(clientname, adminname, reportname)
        except Exception as e:
            abort(
                400,
                data='{}. Invalid client name'.format(e)
            )
        return dict(result=client.cleanup())


class ReportsApi(Resource):
    """
    Methods: GET, POST, DELETE
    """
    @auth.authenticate
    def get(self, adminname, reportname):
        """
        Returns current state of clients
        """
        parser = RequestParser()
        parser.add_argument('clientnames', type=str,
                help='Expected comma seperated hostnames')
        parser.add_argument('query', type=str,
                help='Expected JSON formatted pymongo query')
        parser.add_argument('projection', type=str,
                help='Expected JSON formatted pymongo projection')
        args = parser.parse_args()

        if args['clientnames'] is not None:
            query = {'name': {'$in': form2list(args['clientnames'])}}
        elif args['query'] is not None:
            try:
                query = dict(loads(args['query']))
            except Exception as e:
                abort(
                    400,
                    query='{}. Expected JSON encoded pymongo filter'.format(e)
                )
        else:
            query = {}

        if args['projection'] is not None:
            try:
                projection = dict(loads(args['projection']))
            except Exception as e:
                abort(
                    400,
                    query='{}. Expected JSON encoded pymongo projection'.format(e)
                )
        else:
            projection = {}

        query = dict(adminname=adminname, name=reportname)
        projection.update({'_id': 0, '_modelname': 0})
        reports = Reports()
        return dict(results=list(reports.collection.find(query, projection)))

    @auth.authenticate
    @auth.restrict_to_owner
    def post(self, adminname, reportname):
        """
        Starts/loads clients for an ultron
        """
        parser = RequestParser()
        parser.add_argument('clientnames', type=str, required=True,
                help='Expected comma seperated hostnames')
        args = parser.parse_args()

        clients, not_found = init_clients(form2list(args['clientnames']),
                                          adminname, reportname)
        if len(clients) == 0:
            abort(400, clientnames="No clientname is DNS resolvable report")
        return dict(results=list(map(
            lambda x: {x.name: x.dict()},
            tqdm(clients)
        )))

    @auth.authenticate
    @auth.restrict_to_owner
    def delete(self, adminname, reportname):
        """
        Deletes a report
        """
        reports = Reports()
        clientnames = list(map(
            lambda x: x['clientname'],
            reports.collection.find({
                'adminname': adminname, 'name': reportname
            })
        ))
        clients, not_found = init_clients(clientnames, adminname, reportname)
        if len(clients) == 0:
            abort(400, clientnames="No clientname is DNS resolvable report")
        return dict(results=list(map(
            lambda x: {x.name: x.cleanup()}, tqdm(clients)
        )))


class TaskApi(Resource):
    """
    Methods: GET, POST
    """
    @auth.authenticate
    def get(self, adminname, reportname):
        """
        Updates task state in clients and returns if the task in finished
        """
        global clients

        parser = RequestParser()
        parser.add_argument('clientnames', type=str,
                help='Expected comma seperated hostnames')
        args = parser.parse_args()

        if args['clientnames'] is not None:
            clientnames = form2list(args['clientnames'])
        else:
            reports = Reports()
            clientnames = list(map(
                lambda x: x['clientname'],
                reports.collection.find({
                    'adminname': adminname,
                    'name': reportname
                })
            ))
        clients, not_found = init_clients(clientnames, adminname, reportname)
        if len(clients) == 0:
            abort(400, clientnames="No clientname is DNS resolvable")
        return dict(result={x.name: x.finished(task_pool) for x in tqdm(clients)})

    @auth.authenticate
    @auth.restrict_to_owner
    def post(self, adminname, reportname):
        """
        Performs a task for specified clients in an ultron
        """
        global clients

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
                kwargs = dict(loads(args['kwargs']))
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
                    'adminname': adminname,
                    'name': reportname
                })
            ))
        clients, not_found = init_clients(clientnames, adminname, reportname)
        if len(clients) == 0:
            abort(400, clientnames="No clientname is DNS resolvable")
        task_pool.purge_all(reportname)
        return dict(result={x.name: x.perform(task, task_pool, **kwargs) for x in tqdm(clients)})


class AdminsApi(Resource):
    """
    Methods: GET
    """
    @auth.authenticate
    def get(self):
        """
        List admins and properties
        """
        admins = Admins()
        return dict(results=list(admins.collection.find(
            {}, {'_id': 0, 'password': 0, '_modelname': 0}
        )))


class AdminApi(Resource):
    """
    Methods: GET, POST, DELETE
    """
    @auth.authenticate
    def get(self, adminname):
        """
        List admin properties
        """
        admins = Admins()
        result = dict(result=admins.collection.find_one(
            {'name': adminname}, {'_id': 0, 'password': 0, 'token': 0})
        )
        reports = Reports()
        if result['result'] is not None:
            result['result']['reportnames'] = reports.list(adminname, unique=True)
        return result

    @auth.authenticate
    @auth.restrict_to_ultron_admin
    def post(self, adminname):
        """
        Change admin properties
        """
        parser = RequestParser()
        parser.add_argument('data', type=str, required=True,
                help='Data is missing')
        args = parser.parse_args()
        if args['data'] is not None:
            try:
                data = dict(loads(args['data']))
            except Exception as e:
                abort(
                    400,
                    data='{}. Expected BSON encoded key-value pairs'.format(e)
                )
        admin = Admin(adminname)
        admin.props.update(data)
        admin.save()
        return dict(result=admin.dict())

    @auth.authenticate
    @auth.restrict_to_ultron_admin
    def delete(self, admin):
        """
        Deletes admin
        """
        admin = Admin(admin)
        return dict(result=admin.cleanup())


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


# API routes -------------------------------------------------------------------

api.add_resource(TokenApi, '/token/<adminname>')
api.add_resource(ReportApi, '/report/<adminname>/<reportname>/<clientname>')
api.add_resource(ReportsApi, '/reports/<adminname>/<reportname>')
api.add_resource(TaskApi, '/task/<adminname>/<reportname>')
api.add_resource(AdminsApi, '/admins')
api.add_resource(AdminApi, '/admin/<adminname>')


# Run app ----------------------------------------------------------------------
if __name__ == '__main__':
    app.run('0.0.0.0', port=PORT, ssl_context='adhoc')
