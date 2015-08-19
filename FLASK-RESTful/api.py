#!flask/bin/python

"""Alternative version of the ToDo RESTful server implemented using the
Flask-RESTful extension."""

from flask import Flask, jsonify, abort, make_response
from flask.ext.restful import Api, Resource, reqparse, fields, marshal
from flask.ext.httpauth import HTTPBasicAuth
from flask import g
from flask import Response
from flask import request
import json
import MySQLdb

app = Flask(__name__, static_url_path="")
api = Api(app)
auth = HTTPBasicAuth()

@app.before_request
def db_connect():
  g.conn = MySQLdb.connect(host='localhost',
                              user='root',
                              passwd='root',
                              db='test')
  g.cursor = g.conn.cursor()

@app.after_request
def db_disconnect(response):
  g.cursor.close()
  g.conn.close()
  return response

def query_db(query, args=(), one=False):
  g.cursor.execute(query, args)
  rv = [dict((g.cursor.description[idx][0], value)
  for idx, value in enumerate(row)) for row in g.cursor.fetchall()]
  return (rv[0] if rv else None) if one else rv

@auth.get_password
def get_password(username):
    if username == 'glow':
        return 'python'
    return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)


task_fields = {
    'title': fields.String,
    'description': fields.String,
    'done': fields.Boolean,
    'uri': fields.Url('task')
}


class TaskListAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, required=True,
                                   help='No task title provided',
                                   location='json')
        self.reqparse.add_argument('description', type=str, default="",
                                   location='json')
        super(TaskListAPI, self).__init__()

    def get(self):
         result = query_db("SELECT * FROM test.test")
         data = json.dumps(result)
         resp = Response(data, status=200, mimetype='application/json')
         return resp

    def post(self):
        req_json = request.get_json()
        g.cursor.execute("INSERT INTO test.test (title,description,done) VALUES (%s,%s,%s)", (req_json['title'], req_json['description'],req_json['done']))
        g.conn.commit()
        resp = Response("Updated", status=201, mimetype='application/json')
        return resp

class TaskAPI(Resource):
    decorators = [auth.login_required]

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('title', type=str, location='json')
        self.reqparse.add_argument('description', type=str, location='json')
        self.reqparse.add_argument('done', type=bool, location='json')
        super(TaskAPI, self).__init__()

    def get(self, id):
        req_json = request.get_json()
        result=query_db("SELECT * FROM test.test WHERE id=%s ", (req_json['id']))
        data=json.dumps(result)
        resp = Response(data, status=200, mimetype='application/json')
        return resp

    def delete(self, id):
        req_json = request.get_json()
        g.cursor.execute("DELETE test.test WHERE id=%s", (req_json['id']))
        g.conn.commit()
        resp = Response("Updated", status=201, mimetype='application/json')
        return resp

api.add_resource(TaskListAPI, '/todo/api/v1.0/tasks', endpoint='tasks')
api.add_resource(TaskAPI, '/todo/api/v1.0/tasks/<int:id>', endpoint='task')


if __name__ == '__main__':
    app.run(debug=True)
