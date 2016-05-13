#!/usr/bin/env python3
import logging, os
from flask import Flask, Response, Blueprint

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
    return Response(json.dumps( {'response':'OK'} ), mimetype='application/json')



# Register blueprint to the app
app.register_blueprint(votebox, url_prefix=APPLICATION_ROOT)

'''
    Main. Does not run when running with WSGI
'''
if __name__ == "__main__":
    strh = logging.StreamHandler() 
    strh.setLevel(logging.DEBUG)
    log.addHandler(strh)
    log.setLevel(logging.DEBUG) 

    log.debug(app.url_map)
    app.run()

