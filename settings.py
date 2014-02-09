import os

SETTINGS = {
    'port': 8080,
    'log_dir': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'oniichan.log'
                    ),
    'log_level': 'debug', # info/warn/debug
    'pid_dir': os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'oniichan.pid'
                    ),
    'plugin_dir': os.path.join(
                       os.path.dirname(os.path.abspath(__file__)),
                       'plugins'
                       ),
}
