'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import traceback

from flask import request
from flask_restful import Resource
from flask import current_app as app

from app import available_utils
from app.utils import validate_auth

class Available(Resource):
    def get(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Get Available status of node".format(uuidcode))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers))
        
        validate_auth(app.log,
                      uuidcode,
                      request.headers.get('Intern-Authorization'))
        
        if not 'node' in request.args:
            app.log.warning("uuidcode={} - Invalid Parameters: {}".format(uuidcode, request.args))
            return "{} - Invalid Parameters: {}. Please use only this parameter: node".format(uuidcode, request.args), 422
        
        try:
            if available_utils.available(app.log,
                                         uuidcode,
                                         request.args.get('node')):
                return 'True', 200
            else:
                return 'False', 200
        except:
            app.log.warning("uuidcode={} - Availability check failed. Traceback: {}".format(uuidcode, traceback.format_exc()))
            return 'False', 200
        return '', 404
