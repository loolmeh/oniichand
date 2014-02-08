import os

SETTINGS = {
    'log_dir': os.path.dirname(os.path.abspath(__file__)) + 'oniichan.log', 
    'log_level': 'debug', # info/warn/debug
    'pid_dir': os.path.dirname(os.path.abspath(__file__)) + '/oniichan.pid',
}
