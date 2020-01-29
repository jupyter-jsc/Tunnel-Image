'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import subprocess
import psycopg2
from contextlib import closing

from flask import request
from flask_restful import Resource
from flask import current_app as app

from app.utils import validate_auth, is_tunnel_active, build_tunnel, kill_tunnel

class Tunnel(Resource):
    def get(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Get Tunnel Status".format(uuidcode))
        app.log.trace("uuidcode={} - Arguments: {}".format(uuidcode, request.args))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
        
        validate_auth(app.log,
                      uuidcode,
                      request.headers.get('Intern-Authorization'))
        
        where = ""
        port = 0
        arglist = []
        for arg in request.args:
            if arg not in ['account', 'node', 'hostname', 'port', 'port']:
                app.log.warning("uuidcode={} - Invalid Parameters: {}".format(uuidcode, request.args))
                return "Invalid Parameter: {}. Please use only these parameters: account, node, hostname, port".format(arg), 422
            if where == "":
                where += "WHERE {} = %s".format(arg, request.args.get(arg))
            else:
                where += " AND {} = %s".format(arg, request.args.get(arg))
            arglist.append(request.args.get(arg))
              
        with closing(psycopg2.connect(host=app.database.get('host'), port=app.database.get('port'), user=app.database.get('user'), password=app.database.get('password'), database=app.database.get('database'))) as con: # auto closes
            with closing(con.cursor()) as cur: # auto closes
                with con: # auto commit
                    app.log.debug("uuidcode={} - Execute: 'SELECT * FROM tunnels {}' with params: {}".format(uuidcode, where, tuple(arglist)))
                    cur.execute("SELECT * FROM tunnels {}".format(where), tuple(arglist))
                    tunnels = cur.fetchall()
        app.log.debug("uuidcode={} - Results: {}".format(uuidcode, tunnels))
        if len(tunnels) == 0:
            return "No Entry Found", 204
        if 'port' in where:
            if not is_tunnel_active(app.log,
                                    uuidcode,
                                    port):
                return "Tunnel should be there, but isn't", 404                
        return tunnels, 200
                
    def post(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Start tunnel".format(uuidcode))
        app.log.trace("uuidcode={} - Arguments: {}".format(uuidcode, request.args))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
        app.log.trace("uuidcode={} - JSON: {}".format(uuidcode, request.json))
        
        validate_auth(app.log,
                      uuidcode,
                      request.headers.get('Intern-Authorization'))
        
        where = ""
        s = set(['account', 'system', 'hostname', 'port'])
        arglist = []
        if not s.issubset(set(request.json.keys())):
            return "Invalid Parameter: {}. Please use exactly these four parameters: account, system, hostname, port".format(request.json), 422
        for arg in s: 
            if where == "":
                where += "WHERE {} = %s".format(arg, request.json.get(arg))
            else: 
                where += " AND {} = %s".format(arg, request.json.get(arg))
            arglist.append(request.json.get(arg))
            
        try:
            node = build_tunnel(app.log,
                                uuidcode,
                                request.json.get('system'),
                                request.json.get('hostname'),
                                request.json.get('port'))
        except subprocess.TimeoutExpired:            
            app.log.exception('uuidcode={} - Timeout in build_tunnel with args: {}'.format(uuidcode, request.json))
            return 'Timeout', 255
        except Exception as e:
            app.log.exception('uuidcode={} - Unknown error in build_tunnel with args: {}'.format(uuidcode, request.json))
            return str(e), 255
        
        with closing(psycopg2.connect(host=app.database.get('host'), port=app.database.get('port'), user=app.database.get('user'), password=app.database.get('password'), database=app.database.get('database'))) as con: # auto closes
            with closing(con.cursor()) as cur: # auto closes
                with con: # auto commit
                    cmd = "SELECT * FROM tunnels WHERE port=%s"
                    app.log.debug("uuidcode={} - Database execute: {} with port: {}".format(uuidcode, cmd, request.json.get('port')))
                    cur.execute(cmd, (request.json.get('port'), ))
                    check = cur.fetchall()
                    app.log.debug("uuidcode={} - Result: {}".format(uuidcode, check))
                    if len(check) > 0:
                        app.log.warning("uuidcode={} - Tried to create a tunnel for a port, which is already in use. {}".format(uuidcode, request.json))
                        return "{} - Port {} already used. Please choose another one. {}".format(uuidcode, request.json.get('port'), check), 513
                    cmd = "INSERT INTO tunnels (account, system, node, hostname, port, date) VALUES (%s, %s, %s, %s, %s, now())"
                    app.log.debug("uuidcode={} - Database execute: {} with args: {} {} {} {} {}".format(uuidcode,
                                                                                               cmd,
                                                                                               request.json.get('account'),
                                                                                               request.json.get('system').upper(),
                                                                                               node,
                                                                                               request.json.get('hostname'),
                                                                                               request.json.get('port')))
                    cur.execute(cmd,
                                (request.json.get('account'),
                                 request.json.get('system').upper(),
                                 node,
                                 request.json.get('hostname'),
                                 request.json.get('port')))
                    
                    cmd = "SELECT * FROM tunnels WHERE account = %s AND node = %s AND hostname = %s AND port = %s"
                    app.log.debug("uuidcode={} - Database execute: {} with args like before".format(uuidcode, cmd))
                    cur.execute(cmd,
                                (request.json.get('account'),
                                 node,
                                 request.json.get('hostname'),
                                 request.json.get('port')))
                    added = cur.fetchall()
        if added:
            app.log.info("uuidcode={} - Added {} to database".format(uuidcode, added))
            return "Added entry: {}".format(added), 201
        return "Unknown Error", 500


    def delete(self):
        # Track actions through different webservices.
        uuidcode = request.headers.get('uuidcode', '<no uuidcode>')
        app.log.info("uuidcode={} - Delete Tunnel".format(uuidcode))
        app.log.trace("uuidcode={} - Arguments: {}".format(uuidcode, request.args))
        app.log.trace("uuidcode={} - Headers: {}".format(uuidcode, request.headers.to_list()))
        
        validate_auth(app.log,
                      uuidcode,
                      request.headers.get('Intern-Authorization'))
        
        where = ""
        arglist = []
        if set(['servername']).issubset(set(request.args)):
            where = 'WHERE account = %s'
            arglist.append(request.args.get('servername'))
        else:
            s = set(['hostname', 'port'])
            if not s.issubset(set(request.args)):
                return "Invalid Parameter: {}. Please use exactly these two parameters: hostname, port".format(request.args), 422
            for arg in s:
                if where == "":
                    where += "WHERE {} = %s".format(arg)
                else:
                    where += " AND {} = %s".format(arg)
                arglist.append(request.args.get(arg))
        
        #nodes = []
        with closing(psycopg2.connect(host=app.database.get('host'), port=app.database.get('port'), user=app.database.get('user'), password=app.database.get('password'), database=app.database.get('database'))) as con: # auto closes
            with closing(con.cursor()) as cur: # auto closes
                with con: # auto commit
                    cmd = "SELECT node, hostname, port FROM tunnels {}".format(where)
                    app.log.debug("uuidcode={} - Database execute: {} with args: {}".format(uuidcode, cmd, arglist))
                    cur.execute(cmd, tuple(arglist))
                    results = cur.fetchall()
                    app.log.debug("uuidcode={} - Results: {}".format(uuidcode, results))
        for result in results:
            node, hostname, port = result
            kill_tunnel(app.log,
                        uuidcode,
                        node,
                        hostname,
                        port)
        
        #toDelete = None
        with closing(psycopg2.connect(host=app.database.get('host'), port=app.database.get('port'), user=app.database.get('user'), password=app.database.get('password'), database=app.database.get('database'))) as con: # auto closes
            with closing(con.cursor()) as cur: # auto closes
                with con: # auto commit
                    cmd = "SELECT * FROM tunnels {}".format(where)
                    app.log.debug("uuidcode={} - Database execute: {} with args: {}".format(uuidcode, cmd, arglist))
                    cur.execute(cmd, tuple(arglist))
                    toDelete = cur.fetchall()
                    app.log.debug("uuidcode={} - Result: {}".format(uuidcode, toDelete))
                    if len(toDelete) > 0:
                        cmd = "DELETE FROM tunnels {}".format(where)
                        app.log.debug("uuidcode={} - Database execute: {} with args: {}".format(uuidcode, cmd, arglist))
                        cur.execute(cmd, tuple(arglist))
        if toDelete:
            if len(toDelete) > 0:
                return "Following entries were deleted:\n{}".format(toDelete), 200
        return "No Entries to delete", 204
