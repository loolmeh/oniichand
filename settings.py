import os

base_path = os.path.dirname(os.path.abspath(__file__))
SETTINGS = {
    'port': 8080,
    'log_dir': os.path.join(
                    base_path,
                    'oniichan.log'
                    ),
    'log_level': 'debug', # info/warn/debug
    'pid_dir': os.path.join(
                    base_path,
                    'oniichan.pid'
                    ),
    'plugin_dir': os.path.join(
                       base_path,
                       'plugins'
                       ),
    'host': 'localhost',
    'dic_path': os.path.join(
                    base_path,
                    'plugins',
                    'dic'
                    )
}
