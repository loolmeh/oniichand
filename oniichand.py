from bottle import route, run
from daemon import runner
from settings import SETTINGS
import urllib
import MeCab
import re
import logging


@route('/parse/<sent>')
def parse(sent):
    sent = urllib.unquote(sent).decode('utf8')
    logger.info('Parse request for %s' % (sent))
    tagger = MeCab.Tagger('-Owakati')
    parsed = tagger.parse(sent.encode('utf8')).decode('utf8')
    return parsed


@route('/kana/<sent>')
def kana(sent):
    sent = urllib.unquote(sent).decode('utf8')
    logger.info('Kana generation request for %s' % (sent))
    tagger = MeCab.Tagger('-Oyomi')
    kana = tagger.parse(sent.encode('utf8')).decode('utf8')
    return kana


@route('/furi/<sent>')
def furi(sent):
    sent = urllib.unquote(sent).decode('utf8')
    logger.info('Furigana generation request for %s' % (sent))
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
    return furi


class App():

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = SETTINGS['pid_dir']
        self.pidfile_timeout = 5

    def run(self):
        run(host='localhost', port=8080)


app = App()

logger = logging.getLogger("DaemonLog")

log_set = SETTINGS['log_level']
if log_set == 'debug':
    logger.setLevel(logging.DEBUG)
if log_set == 'warn':
    logger.setLevel(logging.WARNING)
if log_set == 'info':
    logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
f = SETTINGS['log_dir']
open(f, 'a').close()
handler = logging.FileHandler(f)
handler.setFormatter(formatter)
logger.addHandler(handler)

d_runner = runner.DaemonRunner(app)
d_runner.do_action()
