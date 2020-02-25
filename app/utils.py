'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import subprocess
from random import randint

from flask import abort
from app import utils_file_loads
from app.available_utils import available
from app.utils_file_loads import get_j4j_tunnel_token


def remove_secret(json_dict):
    if type(json_dict) != dict:
        return json_dict
    secret_dict = {}
    for key, value in json_dict.items():
        if type(value) == dict:
            secret_dict[key] = remove_secret(value)
        elif key.lower() in ["authorization", "accesstoken", "refreshtoken", "jhubtoken"]:
            secret_dict[key] = '<secret>'
        else:
            secret_dict[key] = value
    return secret_dict


def validate_auth(app_logger, uuidcode, intern_authorization):
    if not intern_authorization == None:
        token = get_j4j_tunnel_token()
        if intern_authorization == token:
            app_logger.info("uuidcode={} - Intern-Authorization validated".format(uuidcode))
            return
    app_logger.warning("uuidcode={} - Could not validate Token:\n{}".format(uuidcode, intern_authorization))
    abort(401)


def check_connect(app_logger, uuidcode, pre, node):
    cmd_check = ['ssh', '-O', 'check', '{}_{}'.format(pre, node)]
    app_logger.trace("uuidcode={} - Try to check the connection with the command: {}".format(uuidcode, cmd_check))
    code_check = subprocess.call(cmd_check, stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=3)
    app_logger.trace("uuidcode={} - After subprocess call. ReturnCode: {}".format(uuidcode, code_check))
    if code_check == 255:
        cmd_connect = ['ssh', '{}_{}'.format(pre, node)]
        app_logger.trace("uuidcode={} - ReturnCode was 255, try to start connection with cmd: {}".format(uuidcode, cmd_connect))
        code_connect = subprocess.call(cmd_connect, stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=3)
        app_logger.trace("uuidcode={} - After subprocess call. ReturnCode: {}".format(uuidcode, code_connect))
        app_logger.trace("uuidcode={} - Check connection again".format(uuidcode))
        code_check = subprocess.call(cmd_check, stderr=subprocess.PIPE, stdout=subprocess.PIPE, timeout=3)
        app_logger.trace("uuidcode={} - After subprocess call. ReturnCode: {}".format(uuidcode, code_check))
    return code_check

def is_tunnel_active(app_logger, uuidcode, port):
    app_logger.trace("uuidcode={} - Try to check for active tunnel with port: {}".format(uuidcode, port))
    cmd1 = ['netstat', '-ltn']
    cmd2 = ['grep', '0.0.0.0:{}'.format(port)]
    p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
    p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    app_logger.trace("uuidcode={} - Popen called with {} | {}".format(uuidcode, cmd1, cmd2))
    p1.stdout.close()
    app_logger.trace("uuidcode={} - Popen closed".format(uuidcode))
    out, err = p2.communicate()
    app_logger.trace("uuidcode={} - Popen communicated. Out:{} Err:{}".format(uuidcode, out, err))
    pid_s = out.decode('utf-8').split()
    app_logger.trace("uuidcode={} - Return: {}".format(uuidcode, len(pid_s) != 0))
    return len(pid_s) != 0


def build_tunnel(app_logger, uuidcode, system, hostname, port, node=''):
    app_logger.trace('uuidcode={} - Try to build tunnel. Arguments: {} {} {} {}'.format(uuidcode, system, hostname, port, node))
    if node == '':
        unicore = utils_file_loads.get_unicore()
        nodelist = unicore.get(system.upper(), {}).get('nodes', [])
        app_logger.trace('uuidcode={} - Nodelist: {}'.format(uuidcode, nodelist))
        while len(nodelist) > 0:
            i = randint(0, len(nodelist)-1)
            if available(app_logger,
                         uuidcode,
                         nodelist[i]):
                node = nodelist[i]
                break
            else:
                del nodelist[i]
        if len(nodelist) == 0:
            raise Exception("{} - Nodelist empty".format(uuidcode))
        app_logger.trace('uuidcode={} - Use Node: {}'.format(uuidcode, node))
        
    if check_connect(app_logger, uuidcode, 'tunnel', node) == 255:
        raise Exception("{} - Could not connect to node".format(uuidcode))
    
    cmd_forward = ['ssh', '-O', 'forward', 'tunnel_{}'.format(node), '-L', '0.0.0.0:{port}:{hostname}:{port}'.format(port=port, hostname=hostname)]
    app_logger.trace("uuidcode={} - Build tunnel with Popen command: {}".format(uuidcode, cmd_forward))
    p_forward = subprocess.Popen(cmd_forward, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    app_logger.trace("uuidcode={} - After Popen. Call communicate".format(uuidcode))
    out, err = p_forward.communicate()
    app_logger.trace("uuidcode={} - Communicated. Out:{} Err:{}".format(uuidcode, out, err))
    code_forward = p_forward.returncode
    app_logger.trace("uuidcode={} - ReturnCode of Popen: {}".format(uuidcode, code_forward))
    return node

def kill_tunnel(app_logger, uuidcode, node, hostname, port):
    if isinstance(node, tuple):
        node = node[0]
    cmd_cancel = ['ssh', '-O', 'cancel', 'tunnel_{}'.format(node), '-L', '0.0.0.0:{port}:{hostname}:{port}'.format(port=port, hostname=hostname)]
    app_logger.trace("uuidcode={} - Try to kill tunnel with cmd: {}".format(uuidcode, cmd_cancel))
    p_cancel = subprocess.Popen(cmd_cancel, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    app_logger.trace("uuidcode={} - After Popen".format(uuidcode))
    out, err = p_cancel.communicate()
    app_logger.trace("uuidcode={} - Communicated. Out:{} Err:{}".format(uuidcode, out, err))
    code_cancel = p_cancel.returncode
    app_logger.trace("uuidcode={} - ReturnCode: {}".format(uuidcode, code_cancel))
    return code_cancel == 0
