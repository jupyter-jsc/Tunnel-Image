'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import json

def get_nodes():
    with open('/etc/j4j/j4j_mount/j4j_common/nodes.json', 'r') as f:
        nodes = json.load(f)
    return nodes

def get_j4j_tunnel_token():
    with open('/etc/j4j/j4j_mount/j4j_token/tunnel.token', 'r') as f:
        token = f.read().rstrip()
    return token
