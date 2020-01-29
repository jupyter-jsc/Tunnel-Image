'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import subprocess

from flask import request
from flask import current_app as app 
from flask_restful import Resource

from app import remote_utils
from app.utils import validate_auth

class RemoteTunnel(Resource):
    def get(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Get Remote tunnel status".format(uuidcode))
        app.log.trace("uuidcode={} - Arguments: {}".format(uuidcode, request.args))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
        
        validate_auth(app.log,
                      uuidcode,
                      request.headers.get('Intern-Authorization'))
        
        if not 'node' in request.args:
            app.log.warning("uuidcode={} - Invalid Parameters: {}.".format(uuidcode, request.args))
            return "Invalid Parameters: {}. Please use only this parameter: node".format(request.args), 422
        
        try:
            code = remote_utils.remote(app.log,
                                       uuidcode,
                                       request.args.get('node'),
                                       'status')
        except subprocess.TimeoutExpired:
            app.log.exception("uuidcode={} - Timeout while getting status of remote tunnel. {}".format(uuidcode, request.args))
            return 'Timeout', 512
        except:
            app.log.exception("uuidcode={} - Exception while getting status of remote tunnel. {}".format(uuidcode, request.args))
            return '', 512
        
        if code == 217:
            return "", 217
        elif code == 218:
            return "", 218
        else:
            return "{}".format(code), 200
                
    def post(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Start remote tunnel".format(uuidcode))
        app.log.trace("uuidcode={} - Arguments: {}".format(uuidcode, request.args))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
        app.log.trace("uuidcode={} - Json: {}".format(uuidcode, request.json))
        
        validate_auth(app.log,
                      uuidcode,
                      request.headers.get('Intern-Authorization'))
        
        if not 'node' in request.json:
            app.log.warning("uuidcode={} - Invalid Parameters: {}.".format(uuidcode, request.json))
            return "Invalid Parameters: {}. Please use only this parameter: node".format(request.json), 422
        
        try:
            code = remote_utils.remote(app.log,
                                       uuidcode,
                                       request.json.get('node'),
                                       'start')
        except subprocess.TimeoutExpired:
            app.log.exception("uuidcode={} - Timeout while starting remote tunnel. {}".format(uuidcode, request.json))
            return 'Timeout', 512
        except:
            app.log.exception("uuidcode={} - Exception while starting remote tunnel. {}".format(uuidcode, request.json))
            return '', 512
        
        if code == 217:
            return "", 217
        elif code == 218:
            return "", 218
        else:
            return "{}".format(code), 200

    def delete(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Delete remote tunnel".format(uuidcode))
        app.log.trace("uuidcode={} - Arguments: {}".format(uuidcode, request.args))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
        
        validate_auth(app.log,
                      uuidcode,
                      request.headers.get('Intern-Authorization'))
        
        if not 'node' in request.args:
            app.log.warning("uuidcode={} - Invalid Parameters: {}.".format(uuidcode, request.args))
            return "Invalid Parameters: {}. Please use only this parameter: node".format(request.args), 422
                
        try:
            code = remote_utils.remote(app.log,
                                       uuidcode,
                                       request.args.get('node'),
                                       'stop')
        except subprocess.TimeoutExpired:
            app.log.exception("uuidcode={} - Timeout while stopping remote tunnel. {}".format(uuidcode, request.args))
            return 'Timeout', 512
        except:
            app.log.exception("uuidcode={} - Exception while stopping remote tunnel. {}".format(uuidcode, request.args))
            return '', 512
        
        if code == 217:
            return "", 217
        elif code == 218:
            return "", 218
        else:
            return "{}".format(code), 200
