from bottle import route, run
from daemon import runner
import urllib
import MeCab
import re
import os

@route('/parse/<sent>')
def parse(sent):
    sent = urllib.unquote(sent).decode('utf8')
    tagger = MeCab.Tagger('-Owakati')
    parsed = tagger.parse(sent.encode('utf8')).decode('utf8')
    return parsed

@route('/kana/<sent>')
def kana(sent):
    sent = urllib.unquote(sent).decode('utf8')
    tagger = MeCab.Tagger('-Oyomi')
    kana = tagger.parse(sent.encode('utf8')).decode('utf8')
    return kana

@route('/furi/<sent>')
def furi(sent):
    sent = urllib.unquote(sent).decode('utf8')
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
        self.pidfile_path = os.path.dirname(os.path.abspath(__file__)) + '/oniichan.pid'
        self.pidfile_timeout = 5

    def run(self):
        run(host='localhost', port=8080)

app = App()
d_runner = runner.DaemonRunner(app)
d_runner.do_action()
