'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

import subprocess
from time import sleep

from app.utils import check_connect

def remote(app_logger, uuidcode, node, action):
    app_logger.trace("{} - Try to check remote action for {} {}".format(uuidcode, node, action))
    if check_connect(app_logger,
                     uuidcode,
                     'remote',
                     node) == 255:
        app_logger.warning("{} - Check Connection responsed 255 for {}".format(uuidcode, node))
        return 255
    cmd_forward = ['ssh', 'remote_{}'.format(node), '{}'.format(action)]
    app_logger.trace("{} - Command: {}".format(uuidcode, cmd_forward))
    if action == 'start':
        p_action = subprocess.Popen(cmd_forward)
        code_action = p_action.returncode
        app_logger.trace("{} - Popen command returned: {}".format(uuidcode, code_action))
        cmd_forward = ['ssh', 'remote_{}'.format(node), 'status']
        app_logger.trace("{} - Update Command to: {}. Then sleep 0.5 seconds.".format(uuidcode, cmd_forward))
        sleep(0.5)
    p_action = subprocess.Popen(cmd_forward, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    app_logger.trace("{} - Popen command called".format(uuidcode))
    out, err = p_action.communicate()
    app_logger.trace("{} - Popen communicate called".format(uuidcode))
    p_action.stdout.close()
    app_logger.trace("{} - Popen closed".format(uuidcode))
    code_action = p_action.returncode
    app_logger.trace("{} - Popen Result: returncode:{} out:{} err:{}".format(uuidcode, code_action, out, err))
    return code_action
