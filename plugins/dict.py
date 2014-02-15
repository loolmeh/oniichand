
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
            logger.debug('entries for %s: %s' % (word, dic[word]))
            proxy_dic[word] = []
            for entry in dic[word]:
                reading = entry['reading']
                proxy = entry['proxy']
                if proxy:
                    proximity = entry['proximity']
                    proxy_entry = {}
                    proxy_entry['reading'] = reading
                    proxy_entry['proxy'] = proxy
                    proxy_entry['proximity'] = proximity
                    proxy_dic[word].append(proxy_entry)
                else:
                    sub_dic[word] = reading
        except KeyError:
            pass
    logger.debug('sub_dic: %s' % (sub_dic))
    logger.debug('proxy_dic: %s' % (proxy_dic))
    
    logger.debug('initial string list: %s' % (parsed))
    furi = ''
    for num, word in enumerate(parsed):
        logger.debug('running %s through sub loop' % (word))
        try:
            reading = sub_dic[word]
            fword = '%s[%s] ' % (word, reading)
            logger.debug('exists in sub_dic')
        except KeyError:
            try:
                entries = proxy_dic[word]
                logger.debug('exists in proxy_dic, entries: %s' % (entries))
                subs_done = []
                level_sub = []
                for entry in entries:
                    logger.debug('checking entry: %s' %(entry))
                    reading = entry['reading']
                    proxies = entry['proxy']
                    proximity = entry['proximity']
                    found = []
                    for proxy in proxies:
                        logger.debug('checking word: %s against proxy: %s' % (word, proxy))
                        if not proximity and not level_sub:
                            logger.debug('proximity is 0, checking the whole sentence')
                            if proxy in parsed:
                                logger.debug('proximity 0, found the proxy')
                                found.append(True)
                                subs_done.append(True)
                        else:
                            logger.debug('proximity level, checking according to specified distance')
                            if proxy == parsed[num+proximity] or proxy == parsed[num-proximity]:
                                logger.debug('found proxy at proximity level')
                                found.append(True)
                                subs_done.append(True)
                                level_sub.append(True)
                    if found:
                        logger.debug('some proxy matched, applying entry reading: %s' % (reading))
                        fword = '%s[%s] ' % (word, reading)
                    elif not found and not subs_done:
                        logger.debug('no proxies match, running it through mecab')
                        fword = '%s[%s] ' % (word, mecab_kana(word).strip())
                furi += fword
                                                     
            except KeyError:
                logger.debug('not found in sub/proxy dics, running it straight through mecab')
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
