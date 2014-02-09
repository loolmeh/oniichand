from bottle import route, run
from daemon import runner
from settings import SETTINGS
from importlib import import_module
import urllib
import MeCab
import re
import logging
import sys
import os

@route('/parse/<sent>')
def parse(sent):
    sent = urllib.unquote(sent).decode('utf8')
    logger.info('Parse request for %s' % (sent))
    sent = process(sent, 'pre')
    tagger = MeCab.Tagger('-Owakati')
    parsed = tagger.parse(sent.encode('utf8')).decode('utf8')
    parsed = process(parsed)
    return parsed


@route('/kana/<sent>')
def kana(sent):
    sent = urllib.unquote(sent).decode('utf8')
    logger.info('Kana generation request for %s' % (sent))
    sent = process(sent, 'pre')
    tagger = MeCab.Tagger('-Oyomi')
    kana = tagger.parse(sent.encode('utf8')).decode('utf8')
    kana = process(kana)
    return kana


@route('/furi/<sent>')
def furi(sent):
    sent = urllib.unquote(sent).decode('utf8')
    logger.info('Furigana generation request for %s' % (sent))
    sent = process(sent, 'pre')
    wakati = MeCab.Tagger('-Owakati')
    yomi = MeCab.Tagger('-Oyomi')
    parsed = wakati.parse(sent.encode('utf8')).decode('utf8')
    words = parsed.split()
    furi = ' '.join(
        '%s[%s]' % (
            word, 
            yomi.parse(word.encode('utf8')).decode('utf-8')
            ) 
        for word in words
        )
    furi = re.sub(r'\s\]', ']', furi)
    furi = process(furi)
    return furi


logger = logging.getLogger("DaemonLog")

log_dict = {
    'debug': logging.DEBUG,
    'warn': logging.WARNING,
    'info': logging.INFO,
}


def set_logger():
    log_set = SETTINGS['log_level']
    logger.setLevel(log_dict[log_set])
    formatter = logging.Formatter(fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(SETTINGS['log_dir'])
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


plugins = []

def plugin_init():
    plugin_dir = SETTINGS['plugin_dir']
    try:
        plugin_list = os.listdir(plugin_dir)
    except OSError:
        plugin_list = []
        logger.error('Cannot find or open plugin directory.')
    plugin_list = [item for item in plugin_list if re.compile(r'.*\.py$').match(item)]
    plugin_list = [item.replace('.py', '') for item in plugin_list]
    logger.debug('Plugins loaded: %s' % (plugin_list))
    global plugins
    plugins = [import_module('plugins.' + item) for item in plugin_list]


def process(input, mode='post'):
    output = input
    for plugin in plugins:
        try:
            if mode == 'pre':
                output = plugin.handle_pre(output)
            if mode == 'post':
                output = plugin.handle_post(output)
        except AttributeError:
            pass
    return output

     
class App(object):

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = SETTINGS['pid_dir']
        self.pidfile_timeout = 5

    def run(self):
        set_logger()
        plugin_init()
        run(host='localhost', port=8080)

app = App()

if sys.argv[1] == 'normal':
    set_logger()
    run(host='localhost', port=SETTINGS['port'])
else:
    d_runner = runner.DaemonRunner(app)
    d_runner.do_action()
