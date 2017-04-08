import pystache


def render(fname, dat):
    #    print len(dat['entries']), len(dat['entries'][0])
    #    return
    f = open(fname)
    template = f.read()
    print pystache.render(template, dat)

if __name__ == '__main__':
    import feeds
    entries = feeds.scrape(feeds.feeds)
    render('/home/ygreif/learndjango/blur/crawler/index.tmpl',
           {'rows': [{'entries': entries[i:i + 3]}for i in range(2, len(entries) - 6, 3)],
            'lead': entries[0],
            'second': entries[1],
            'title': 'The Discerning Whig'})
