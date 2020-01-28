'''
Created on May 16, 2019

@author: Tim Kreuzer
'''

from subprocess import STDOUT, check_output, CalledProcessError

def available(app_logger, uuidcode, node):
    cmd_check = ['ssh', 'available_{}'.format(node)]
    app_logger.trace("uuidcode={} - CheckOutput: {}".format(uuidcode, cmd_check))
    try:
        output = check_output(cmd_check, stderr=STDOUT, timeout=5)
    except CalledProcessError:
        return False
    app_logger.trace("uuidcode={} - Result: {}".format(uuidcode, output))
    out = output.decode("utf-8")
    app_logger.trace("uuidcode={} - Return: {}".format(uuidcode, 'Jupyter@JSC is running' in out))
    return 'Jupyter@JSC is running' in out
