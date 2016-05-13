#!/usr/bin/env python3
import logging, os, json, pymongo, time, markdown, base64
from pymongo import MongoClient
from functools import wraps
from flask import Flask, Response, Blueprint, Markup, escape, request, redirect, url_for, abort
from bson.json_util import dumps

HELPSTRING="""

# Votebox API Routes
All API routes (except `/`) must be accompanied by an API key and API secret
set in the header.

### /
_Methods:_ `GET`   

Return a help string

### /query
_Methods:_ `GET`   
_Parameters:_ ix (integer, index), limit (integer, limit records returned)

Make a database query and return stored records

### /ping
_Methods:_ `GET`  
_Requires authorization_

Used internally by the votepi client to check if the API is there. Returns "OK"
on success. 

### /vote
_Methods:_ `POST`   
_Requires authorization_

Post a "vote" to the database to store. Votes must be contained in the POST body
and be of the form:   
```
    {'button': 2, 'uuid': '16129e6d-4b62-48d0-8c01-224b905d55bd', 'timestamp': 1463164336}
```

### /key
_Methods:_ `GET`   
_Parameters:_ uuid 

Generate an API key and API secret. These must be activated in the database
by an admin before they can be used to authenticate a client. 

# Authorization
Authorization is accomplished by setting the HTTP basic auth headers with the
username being the uuid and the password beign a generated (and active) API key.

"""

# Set up logger
log = logging.getLogger(__name__)

# Create flask app
app = Flask(__name__)

# Set up blueprint
APPLICATION_ROOT = os.environ.get('PROXY_PATH', '/').strip() or '/'
votebox = Blueprint('votebox', __name__, template_folder='templates')
# Look at end of file for where this blueprint is actually registered to the app

# Configuration
CONFIG_JSON = os.environ.get('CONFIG_JSON', '{}')

DEBUG = True
app.config.from_object(__name__)

flask_options = {
    'host':'0.0.0.0',
    'threaded':True
}


'''
    Auxilliary functions
'''
# Connect to the mongodb database
# Need CONFIG_JSON in ENV for this to work.
# e.g. export CONFIG_JSON="$(cat db.json | sed 's/ //g' | tr '\n' ' ')"
def connect_mongodb():
    try:
        log.debug( "Using config: {}".format(CONFIG_JSON) )
        config = json.loads(CONFIG_JSON)

        client = MongoClient(config['host'], config['port'])
        db = client[config['db']]

        db.authenticate(config['user'], password=config['pwd'])

        log.debug( "Total votes: {}".format(db.votes.count()) )

    except KeyError as e:
        log.critical("Could not connect to database. Did you put CONFIG_JSON in the environment?")
        raise

    return db


'''
    API key validating wrapper
    https://coderwall.com/p/4qickw/require-an-api-key-for-a-route-in-flask-using-only-a-decorator
'''
# The actual decorator function
def require_api_key(view_function):

    @wraps(view_function)
    # the new, post-decoration function. Note *args and **kwargs here.
    def decorated_function(*args, **kwargs):
        auth=request.authorization

        if auth:
            verify=db.devices.find_one(auth['username'])
            if verify['active'] and verify['key'] == auth['password']:
                return view_function(*args, **kwargs)

        # Auth failed if not all conditions met 
        abort(401)

    return decorated_function


'''
    Application Routes
'''
@votebox.route('/', methods=['GET'])
def index():
    return Markup("<!DOCTYPE html>\n<title>VoteBox API</title>\n") \
            + Markup(markdown.markdown(HELPSTRING)) , 200


@votebox.route('query', methods=['GET'])
def query():
    ix = request.args.get('ix')
    limit = request.args.get('limit') or 50
    if ix is None:
        return redirect( url_for('.query', **{'ix':0, **request.args}) ) 
    
    votes = db.votes.find().skip(int(ix)).limit(int(limit)).sort("_id",pymongo.DESCENDING)
    return Response(dumps( votes ), mimetype='application/json'), 200


@votebox.route('ping', methods=['GET'])
@require_api_key
def ping():
    return "OK", 200


@votebox.route('vote', methods=['POST'])
@require_api_key
def vote():
    v = request.get_json()
    v['timestamp'] = int(time.time())
    
    # Sanity check record before insert
    if 'uuid' not in v or 'button' not in v:
        return Response(json.dumps( {'response':'invalid'} ), mimetype='application/json'), 400

    # Insert into database
    log.info(v)
    db.votes.insert_one(v)
    return Response(json.dumps( {'response':'ok'} ), mimetype='application/json')


@votebox.route('key', methods=['GET'])
def key():
    # Sign the uuid to create the API key
    uuid = request.args.get('uuid')
    if not uuid:
        return Response(json.dumps( {'response':'bad uuid'} ), mimetype='application/json'), 400

    # Generate a cryptographically secure random number for the secret
    key = base64.b64encode(os.urandom(32)).decode('utf-8') 
    auth = {
        '_id':   uuid,
        'key':    key,
        'active': False
    }
    try:
        db.devices.insert_one(auth)
    except pymongo.errors.DuplicateKeyError as e:
        return "{}. \nLooks like a key was already generated for this uuid".format(str(e))

    return Response( dumps(auth) )


# Register blueprint to the app
app.register_blueprint(votebox, url_prefix=APPLICATION_ROOT)

'''
    Main. Does not run when running with WSGI
'''
if __name__ == "__main__":
    strh = logging.StreamHandler() 
    strh.setLevel(logging.DEBUG)
    strh.setFormatter(logging.Formatter('[%(asctime)s - %(levelname)s] %(message)s'))
    log.addHandler(strh)
    log.setLevel(logging.DEBUG) 
    
    db = connect_mongodb()

    #log.debug(app.url_map)
    app.run(**flask_options)

