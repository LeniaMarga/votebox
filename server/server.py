#!/usr/bin/env python3
import logging, os, json, pymongo, time, markdown
from pymongo import MongoClient
from flask import Flask, Response, Blueprint, Markup, escape, request, redirect, url_for
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

Used internally by the votepi client to check if the API is there. Returns "OK"
on success. 

### /vote
_Methods:_ `POST`   

Post a "vote" to the database to store. Votes must be contained in the POST body
and be of the form:   
```
    {'button': 2, 'uuid': '16129e6d-4b62-48d0-8c01-224b905d55bd', 'timestamp': 1463164336}
```

"""

# Set up logger
log = logging.getLogger(__name__)

# Create flask app
app = Flask(__name__)

# Set up blueprint
APPLICATION_ROOT = os.environ.get('PROXY_PATH', '/').strip() or '/'
votebox = Blueprint('votebox', __name__, template_folder='templates')
# Look at end of file for where this blueprint is actually registered to the app

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
        CONFIG_JSON = os.environ.get('CONFIG_JSON', '{}')
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
    Application Routes
'''
@votebox.route('/', methods=['GET'])
def index():
    return Markup("<!DOCTYPE html>\n<title>VoteBox API</title>\n") \
            + Markup(markdown.markdown(HELPSTRING)) , 200


@votebox.route('query', methods=['GET'])
def query():
    ix = int(request.args.get('ix'))
    limit = int(request.args.get('limit') or 50)
    if ix is None:
        return redirect( url_for('.query', **{'ix':0, **request.args}) ) 
    
    votes = db.votes.find().skip(ix).limit(limit).sort("_id",pymongo.DESCENDING)
    return Response(dumps( votes ), mimetype='application/json'), 200


@votebox.route('ping', methods=['GET'])
def ping():
    return "OK", 200


@votebox.route('vote', methods=['POST'])
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

