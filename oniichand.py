from bottle import route, run, request, abort
from daemon import runner
from settings import SETTINGS
from importlib import import_module
import urllib
import MeCab
import logging
import sys
import json
import os

@route('/parse')
def parse():
    sent = url_decode(request.query.str)
    logger.info('Parse request for %s' % (sent))
    sent = process(sent, 'pre', 'parse')
    parsed = mecab_parse(sent)
    parsed = process(parsed, 'post', 'parse')
    return parsed


@route('/kana')
def kana():
    sent = url_decode(request.query.str)
    logger.info('Kana generation request for %s' % (sent))
    sent = process(sent, 'pre', 'kana')
    kana = mecab_kana(sent)
    kana = process(kana, 'post', 'kana')
    return kana


@route('/furigana')
def furigana():
    sent = url_decode(request.query.str)
    logger.info('Furigana generation request for %s' % (sent))
    sent = process(sent, 'pre', 'furi')
    furi = mecab_furi(sent)
    furi = process(furi, 'post', 'furi')
    return furi


@route('/correction/add')
def dic_add():
    word = url_decode(request.query.word)
    if not word:
        abort(400, "Error no word field.")
    reading = url_decode(request.query.reading)
    if not reading:
        abort(400, "Error no reading field.")
    proxy = url_decode(request.query.proxy) or []
    if proxy:
        proxy = proxy.split(',')
    proximity = url_decode(request.query.proximity) or 0
    proximity = int(proximity)
    logger.info('Add correction request for %s[%s]' % (word, reading))
    try:
        if dic[word]:
            entry_list = dic[word]
            for num, entry in enumerate(entry_list):
                if reading == entry['reading']:
                    proxy_list = entry['proxy']
                    for item in proxy:
                        if item not in proxy_list:
                            proxy_list.append(item)
                    dic[word][num]['proxy'] = proxy_list
                    if proximity != entry['proximity']:
                        dic[word][num]['proximity'] = proximity
                else:
                    if proximity == entry['proximity'] and not entry['proxy'] and not proxy:
                        abort(400, "Error, proximity and proxy clash.")
                    new_entry['reading'] = reading
                    new_entry['proxy'] = proxy
                    new_entry['proximity'] = proximity
                    dic[word].append(new_entry)
    except KeyError:
        dic[word] = [{'reading': reading, 'proxy': proxy, 'proximity': proximity}]
    dic_dump()
    return 'Successfully added %s[%s] %s %s' % (word, reading, proxy, proximity)


@route('/correction/remove')
def dic_remove():
    word = url_decode(request.query.word)
    reading = url_decode(request.query.reading)
    logger.info('Remove correction request for %s[%s]' % (word, reading))
    if not reading:
        del dic[word]
    try:
        for num, entry in enumerate(dic[word]):
            entry_reading = entry['reading']
            if entry_reading == reading:
                del dic[word][num]
                if not dic[word]:
                    del dic[word]
    except KeyError:
        pass
    dic_dump()
    return 'Successfully removed %s[%s]' % (word, reading)

@route('/correction/lookup')
def dic_lookup():
    word = url_decode(request.query.word)
    logger.info('Lookup correction request for %s' % (word))
    try:
        entries = dic[word]
        output = ''
        for entry in entries:
            reading = entry['reading']
            proxy = entry['proxy']
            proximity = entry['proximity']
            output += '%s[%s] %s %s| ' % (word, reading, proxy, proximity) 
        return output
    except KeyError:
        abort(400, "Does not exist.")


def url_decode(input):
    return urllib.unquote(input)


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
    del plugin_list[0]
    logger.debug('Plugins loaded: %s' % (plugin_list))
    global plugins
    plugins = [import_module('plugins.' + item) for item in plugin_list]


def process(input, mode='post', target='', args=[], kwargs={}):
    output = input
    kwargs['mecab_parse'] = mecab_parse
    kwargs['mecab_kana'] = mecab_kana
    kwargs['dic'] = dic
    kwargs['logger'] = logger
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
        logger.error('Could not open dictionary file.')
    except ValueError:
        logger.error('Could not load dictionary, empty file.')

def dic_dump():
    with open(dic_path, 'w') as f:
        f.write(json.dumps(dic, indent=4, separators=(',', ': '), ensure_ascii=False, encoding='utf-8').encode('utf-8'))
        
     
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
