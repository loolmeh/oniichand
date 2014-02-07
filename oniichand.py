from bottle import route, run
import urllib
import MeCab

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
    return furi

run(host='localhost', port=8080)
