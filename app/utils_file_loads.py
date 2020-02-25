'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import json

def get_unicore():
    with open('/etc/j4j/j4j_mount/j4j_common/unicore.json', 'r') as f:
        unicore = json.load(f)
    return unicore

def get_j4j_tunnel_token():
    with open('/etc/j4j/j4j_mount/j4j_token/tunnel.token', 'r') as f:
        token = f.read().rstrip()
    return token
