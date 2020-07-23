from flask import Flask, request, Response, jsonify
from sqlalchemy import create_engine, MetaData, Table, Column, TEXT
from urllib.parse import urlparse, parse_qs
import json


db_connect = create_engine('sqlite:///login_status.db')
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Server running<h1>"


@app.route('/callback')
def callback():

    metadata = MetaData(db_connect)
    # Create a table with the appropriate Columns
    logindb = Table("logindb", metadata,
                    Column('state', TEXT, primary_key=True, nullable=False),
                    Column('authcode', TEXT, nullable=False),
                    )
    metadata.create_all()
    url = request.url
    parsed = urlparse(url)
    query = parse_qs(parsed.query, True)
    mfp_state = str(query["state"][0])
    auth_code = str(query["code"][0])
    conn = db_connect.connect()  # connect to database
    _sql_query = "INSERT INTO "
    _sql_query += "logindb"
    _sql_query += " (state, authcode) "
    _sql_query += " SELECT ?, ? "
    _var = (
        mfp_state,
        auth_code
    )
    conn.execute(_sql_query, _var)
    # query = conn.execute("INSERT INTO logindb (state, authcode) VALUES (mfp_state, auth_code);)  # This line performs query and returns json result
    return "<h1>Close the browser<h1>"


@app.route('/poll/<state>')
def polling(state):

    metadata = MetaData(db_connect)
    # Create a table if not exists with the appropriate Columns
    logindb = Table("logindb", metadata,
                    Column('state', TEXT, primary_key=True, nullable=False),
                    Column('authcode', TEXT, nullable=False),
                    )
    metadata.create_all()

    message = {
            'result' : {"state": "", "code": ""},
            'message': "Authorization Successful",
    }
    conn = db_connect.connect()  # connect to database
    query = conn.execute("select * from logindb")  # This line performs query and returns json result
    state_list = [i[0] for i in query.cursor.fetchall()]  # Fetches first column that is State
    if state in state_list:
        _sql_query = "SELECT * from " + "logindb" + " WHERE state=?"
        _var = (state,)
        query = conn.execute(_sql_query, _var)
        response = query.cursor.fetchone()
        message["result"]["state"] = response[0]
        message["result"]["code"] = response[1]
        js = json.dumps(message)
        resp = Response(js, status=200, mimetype='application/json')
        return resp
    else:
        return not_found()


@app.errorhandler(404)
def not_found(error=None):
    message = {
            'result' : "auth_pending",
            'message': "Waiting for authorization",
    }
    resp = jsonify(message)
    resp.status_code = 404

    return resp