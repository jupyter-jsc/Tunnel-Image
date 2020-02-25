'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import logging.config
import socket
import os
import json
import random
import psycopg2
from time import sleep
from contextlib import closing
from logging.handlers import SMTPHandler

from flask import Flask
from flask_restful import Api

from app import utils
from app import utils_file_loads
from app import remote_utils
from app.tunnel import Tunnel
from app.health import HealthHandler
from app.remote_tunnel import RemoteTunnel
from app.available import Available

with open('/etc/j4j/j4j_mount/j4j_common/mail_receiver.json') as f:
    mail = json.load(f)

logger = logging.getLogger('J4J_Tunnel')
logging.addLevelName(9, "TRACE")
def trace_func(self, message, *args, **kws):
    if self.isEnabledFor(9):
        # Yes, logger takes its '*args' as 'args'.
        self._log(9, message, args, **kws)
logging.Logger.trace = trace_func
mail_handler = SMTPHandler(
    mailhost='mail.fz-juelich.de',
    fromaddr='jupyter.jsc@fz-juelich.de',
    toaddrs=mail.get('receiver'),
    subject='J4J_Tunnel Error'
)
mail_handler.setLevel(logging.ERROR)
mail_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
))


# Override logging.config.file_config, so that the logfilename will be send to the parser, each time the logging.conf will be updated
def j4j_file_config(fname, defaults=None, disable_existing_loggers=True):
    if not defaults:
        defaults={'logfilename': '/etc/j4j/j4j_mount/j4j_tunnel/logs/{}_{}_t.log'.format(socket.gethostname(), os.getpid())}
    import configparser

    if isinstance(fname, configparser.RawConfigParser):
        cp = fname
    else:
        cp = configparser.ConfigParser(defaults)
        if hasattr(fname, 'readline'):
            cp.read_file(fname)
        else:
            cp.read(fname)

    formatters = logging.config._create_formatters(cp)

    # critical section
    logging._acquireLock()
    try:
        logging._handlers.clear()
        del logging._handlerList[:]
        # Handlers add themselves to logging._handlers
        handlers = logging.config._install_handlers(cp, formatters)
        logging.config._install_loggers(cp, handlers, disable_existing_loggers)
    finally:
        logging._releaseLock()

logging.config.fileConfig = j4j_file_config
logging.config.fileConfig('/etc/j4j/j4j_mount/j4j_tunnel/logging.conf')

num_procs = 1
try:
    with open('/etc/j4j/J4J_Tunnel/uwsgi.ini', 'r') as f:
        uwsgi_ini = f.read()
    num_procs = int(uwsgi_ini.split('processes = ')[1].split('\n')[0])
except:
    num_procs = 1

port_list = []
for i in range(num_procs):
    port_list.append(9990+i)

s = random.randint(0,num_procs*100)
sleep(s/100)
t_logs = None
while True:
    port = random.choice(port_list)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        res = sock.connect_ex(('localhost', port))
        if res == 111:
            t_logs = logging.config.listen(port)
            t_logs.start()
            logger.info("Listen on Port: {}".format(port))
            break
    port_list.remove(port)
    if len(port_list) == 0:
        break
    s = random.randint(0, 200)
    sleep(s/100)

def startup(app):
    with app.app_context():
        # close all remote tunnel
        unicore = utils_file_loads.get_unicore()
        for infos in unicore.values():
            for node in infos.get('nodes', []):
                try:
                    remote_utils.remote(app.log,
                                        '<StartUp Call>',
                                        node,
                                        'stop')
                    sleep(0.5)
                    remote_utils.remote(app.log,
                                        '<StartUp Call>',
                                        node,
                                        'start')
                except:
                    app.log.warning("Could not setup remote tunnel {}".format(node))
        tunnels = []
        while True:
            try:
                with closing(psycopg2.connect(host=app.database.get('host'), port=app.database.get('port'), user=app.database.get('user'), password=app.database.get('password'), database=app.database.get('database'))) as con: # auto closes
                    with closing(con.cursor()) as cur: # auto closes
                        with con: # auto commit
                            cmd = "SELECT system, hostname, port, node FROM tunnels"
                            app.log.debug("Execute: {}".format(cmd))
                            cur.execute(cmd)
                            tunnels = cur.fetchall()
                            app.log.debug("Result: {}".format(tunnels))
            except:
                app.log.debug("StartUp - Could not connect to database. Sleep for 5 seconds.")
                sleep(5)
                continue
            break
        for tunnel in tunnels:
            if not utils.is_tunnel_active(app.log, '<StartUp Call>', tunnel[2]):                
                try:
                    utils.build_tunnel(app.log, '<StartUP Call>', tunnel[0], tunnel[1], tunnel[2], tunnel[3])
                except:
                    app.log.exception("Could not build tunnel. Arguments: {} {} {} {}".format(tunnel[0], tunnel[1], tunnel[2], tunnel[3]))

class FlaskApp(Flask):
    log = None
    with open('/etc/j4j/j4j_mount/j4j_tunnel/database.json') as f:
        database = json.loads(f.read())
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger('J4J_Tunnel')
        super(FlaskApp, self).__init__(*args, **kwargs)

application = FlaskApp(__name__)
if not application.debug:
    application.log.addHandler(mail_handler)
api = Api(application)

api.add_resource(Tunnel, "/tunnel")
api.add_resource(HealthHandler, "/health")
api.add_resource(RemoteTunnel, "/remote")
api.add_resource(Available, "/available")
startup(application)
if __name__ == "__main__":
    application.run(host='0.0.0.0', port=9004)
    logging.config.stopListening()
    t_logs.join()
