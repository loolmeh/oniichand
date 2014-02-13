

def handle_pre_furi(input, args, kwargs):
    mecab_parse = kwargs['mecab_parse']
    mecab_kana = kwargs['mecab_kana']
    dic = kwargs['dic']
    logger = kwargs['logger']
    parsed = mecab_parse(input)
    parsed = parsed.split()
    sub_dic = {}
    proxy_dic = {}
    
    logger.debug('dic: %s' % (dic))
    for word in parsed:
        try:
            entry = dic[word]
            reading = dic[word]['reading']
            try:
                proxy = dic[word]['proxy']
                proxy = dic[word]['proximity']
                proxy_dic[word]['reading'] = reading
                proxy_dic[word]['proxy'] = proxy
            except KeyError:
                sub_dic[word] = reading
        except KeyError:
            pass
    logger.debug('sub_dic: %s' % (sub_dic))
    
    logger.debug('initial string list: %s' % (parsed))
    furi = ''
    for word in parsed:
        try:
            reading = sub_dic[word]
            fword = '%s[%s] ' % (word, reading)
            logger.debug('exists in sub_dic, furi generated')
        except KeyError:
            kana = mecab_kana(word).strip()
            if word == kana:
                fword = word + ' '
            else:
                fword = '%s[%s] ' % (word, kana)
        furi += fword
                
    kwargs['furi'] = furi
    return input, args, kwargs
    
def handle_post_furi(input, args, kwargs):
    input = kwargs['furi']
    return input, args, kwargs
