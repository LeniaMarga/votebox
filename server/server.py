#!/usr/bin/env python3
import logging, os, json, pymongo
from pymongo import MongoClient
from flask import Flask, Response, Blueprint, escape

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
    return "OK", 200


@votebox.route('ping', methods=['GET'])
def ping():
    return "OK", 200


@votebox.route('vote', methods=['POST'])
def vote():
    log.debug(escape(request.form['vote']))
    return Response(json.dumps( {'response':'OK'} ), mimetype='application/json')



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
    app.run()
