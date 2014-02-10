from bottle import route, run
from daemon import runner
from settings import SETTINGS
from importlib import import_module
import urllib
import MeCab
import logging
import sys
import os
import json

@route('/parse/<sent>')
def parse(sent):
    sent = url_decode(sent)
    logger.info('Parse request for %s' % (sent))
    sent = process(sent, 'pre', 'parse')
    parsed = mecab_parse(sent)
    parsed = process(parsed, 'post', 'parse')
    return parsed


@route('/kana/<sent>')
def kana(sent):
    sent = url_decode(sent)
    logger.info('Kana generation request for %s' % (sent))
    sent = process(sent, 'pre', 'kana')
    kana = mecab_kana(sent)
    kana = process(kana, 'post', 'kana')
    return kana


@route('/furi/<sent>')
def furi(sent):
    sent = url_decode(sent)
    logger.info('Furigana generation request for %s' % (sent))
    sent = process(sent, 'pre', 'furi')
    furi = mecab_furi(sent)
    furi = process(furi, 'post', 'furi')
    return furi


@route('/correction/add/<entry>')
def dic_add(entry):
    entry = url_decode(entry)
    entry = entry.split()
    word = entry[0]
    reading = entry[1]
    try:
        proxy = entry[2]
        proxy = proxy.split(',')
    except IndexError:
        proxy = []
    logger.info('Add correction request for %s[%s]' % (word, reading))
    try:
        if dic[word]:
            proxy_list = dic[word]['proxy']
            if proxy not in proxy_list:
                for item in proxy:
                    proxy_list.append(item)
                dic[word]['proxy'] = proxy_list
    except KeyError:
        dic[word] = {'reading': reading, 'proxy': proxy}
    dic_dump()
    return 'Successfully added %s[%s] %s' % (word, reading, proxy)


@route('/correction/remove/<entry>')
def dic_remove(entry):
    entry = url_decode(entry)
    logger.info('Remove correction request for %s[%s]' % (word))
    del dic[word]
    dic_dump()
    return 'Successfully removed %s[%s]' % (word, reading)

@route('/correction/lookup/<entry>')
def dic_lookup(entry):
    word = url_decode(entry)
    logger.info('Lookup correction request for %s' % (word))
    try:
        reading = dic[word]['reading']
        proxy = dic[word]['proxy']
        return "%s[%s] %s" % (word, reading, proxy)
    except KeyError:
        return "Does not exist"


def url_decode(input):
    return urllib.unquote(input).decode('utf8')


wakati = ''
yomi = ''

def mecab_init():
    global wakati
    global yomi
    wakati = MeCab.Tagger('-Owakati')
    yomi = MeCab.Tagger('-Oyomi')


def mecab_parse(input):
    return wakati.parse(
                input.encode('utf8')
                ).decode('utf8')


def mecab_kana(input):
    return yomi.parse(
                input.encode('utf8')
                ).decode('utf8')


def mecab_furi(input):
    parsed = wakati.parse(input.encode('utf8')).decode('utf8')
    words = parsed.split()
    output = ' '.join(
        '%s[%s]' % (
            word, 
            yomi.parse(word.encode('utf8')).decode('utf-8').strip()
            ) 
        for word in words
        )
    return output


logger = logging.getLogger("DaemonLog")

LOG_DIC = {
    'debug': logging.DEBUG,
    'warn': logging.WARNING,
    'info': logging.INFO,
}

def set_logger():
    log_set = SETTINGS['log_level']
    logger.setLevel(LOG_DIC[log_set])
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
    plugin_list = [item.replace('.py', '') for item in plugin_list if item.endswith('.py')]
    logger.debug('Plugins loaded: %s' % (plugin_list))
    global plugins
    plugins = [import_module('plugins.' + item) for item in plugin_list]


def process(input, mode='post', target='', args=[], kwargs={}):
    output = input
    for plugin in plugins:
        try:
            output, args, kwargs = getattr(plugin, 'handle_%s_%s' % (mode, target))(output, args, kwargs)
        except AttributeError:
            pass
    for plugin in plugins:
        try:
            output, args, kwargs = getattr(plugin, 'handle_%s_all' % (mode))(output, args, kwargs)
        except AttributeError:
            pass
    return output


dic = {}
dic_path = SETTINGS['dic_path']

def dic_load():
    global dic
    try:
        with open(dic_path, 'r') as f:
            dic = json.loads(f.read())
    except IOError:
        logger.error('Could not load dictionary file.')

def dic_dump():
    with open(dic_path, 'w') as f:
        f.write(json.dumps(dic, indent=4, separators=(',', ': ')))
        
     
class App(object):

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = SETTINGS['pid_dir']
        self.pidfile_timeout = 5

    @classmethod
    def run(self):
        set_logger()
        mecab_init()
        plugin_init()
        dic_load()
        run(host=SETTINGS['host'], port=SETTINGS['port'])

if sys.argv[1] == 'normal':
    App.run()
else:
    app = App()
    d_runner = runner.DaemonRunner(app)
    d_runner.do_action()
