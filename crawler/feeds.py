from itertools import chain, izip_longest
import string
import sys
import datetime
import collections

from concurrent.futures import ProcessPoolExecutor
from dateutil import parser

import goose
import feedparser
from lxml import html
import requests
import re

g = goose.Goose()


from HTMLParser import HTMLParser


class MLStripper(HTMLParser):

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


class RSSEntry(collections.OrderedDict):

    def __init__(self, *args, **kwargs):
        super(RSSEntry, self).__init__(*args, **kwargs)
        self._initialized = True

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if hasattr(self, '_initialized'):
            super(RSSEntry, self).__setitem__(name, value)
        else:
            super(RSSEntry, self).__setattr__(name, value)

miss_manners = {
    'Advice Godess': {'url': 'http://www.freeweekly.com/category/advice/advice-goddess/feed/'},
}

advice_feeds = {
    'Ask Amy': {'url': 'http://amydickinson.com/rss'},
    'Ask Polly': {'url': 'http://feeds.feedburner.com/nymag/askpolly'},
    'Carolyn Hax': {'url': 'http://feeds.washingtonpost.com/rss/linksets/lifestyle/carolyn-hax'},
    'Miss Manners': {'url': 'http://feeds.washingtonpost.com/rss/linksets/lifestyle/miss-manners'},
    'Ask a Manager': {'url': 'http://www.askamanager.org/feed'}
}
#     'Bad Advice': {'url': 'http://thatbadadvice.tumblr.com/rss'},

extra = {
    'Commentary Magazine': {'url': 'https://www.commentarymagazine.com/feed/'},
}

middleeast = {
    'Mosiac Magazine': {'url': 'https://mosaicmagazine.com/rss-feeds/'},
    'Eli Lake': {'url': 'https://www.bloomberg.com/view/contributors/ASD1bG3hdiI/eli-lake'},
    'World Affairs Journal': {'url': 'http://www.worldaffairsjournal.org/blog/feed'},
    'Adam Garfinkle': {'url': 'http://www.the-american-interest.com/byline/garfinkle/feed/'},
    'Charles Krauthammer': {'url': 'https://www.washingtonpost.com/people/charles-krauthammer/?outputType=rss'},
    'Jackson Diehl': {'url': 'https://www.washingtonpost.com/people/ej-dionne-jr/?outputType=rss'},
    'Jeffrey Goldberg': {'url': 'https://www.theatlantic.com/feed/author/jeffrey-goldberg/'},
    'Jerusalem Center For Public Affairs': {'url': 'http://jcpa.org/feed/'},
    'Glenn Greenwald': {'url': 'https://theintercept.com/staff/glenn-greenwald/feed/?rss'},
    'David Gordis': {'url': 'https://www.bloomberg.com/view/contributors/AR-c1SHy6pw/daniel-gordis'},
    'New York Times': {'url': 'http://rss.nytimes.com/services/xml/rss/nyt/MiddleEast.xml'},
    'Washington Post': {'url': 'http://feeds.washingtonpost.com/rss/world'},
    'Volokh Conspiracy': {'url': 'http://feeds.feedburner.com/volokh/mainfeed'},
    'Juan Cole': {'url': 'https://www.juancole.com/feed'},
    'The Economist': {'url': 'http://www.economist.com/sections/middle-east-africa/rss.xml'},
    'Lebanon Star': {'url': 'http://www.dailystar.com.lb/RSS.aspx?id=17'},
}

#     'Hurry Up Harry': {'url': 'http://hurryupharry.org/feed/'},
#     'MEMRI': {'url': 'https://www.memri.org/rss.xml'},
#     'CAMERA': {'url': 'http://www.camera.org/rss/rss.asp'}

econ = {
    'Naked Capatilism': {'url': 'http://feeds.feedburner.com/NakedCapitalism'},
    'Matt Levine': {'url': 'https://www.bloomberg.com/view/rss/contributors/matt-levine.rss'},
    'Musings on Markets': {'url': 'http://aswathdamodaran.blogspot.nl/atom.xml'},
    'Mainly Macro': {'url': 'http://feeds.feedburner.com/MainlyMacro'},
    'Noah Smith': {'url': 'http://noahpinionblog.blogspot.com/feeds/posts/default'},
    'Palul Krugman': {'url': 'http://www.nytimes.com/svc/collections/v1/publish/www.nytimes.com/column/paul-krugman/rss.xml'},
    'Buttonwood': {'url': 'http://www.economist.com/blogs/buttonwood/index.xml'},
    'Megan Mcardle': {'url': 'https://www.bloomberg.com/view/contributors/AQjVOcPejrY/megan-mcardle'},
    'John Gordon Steele': {'url': 'https://www.commentarymagazine.com/author/jsgjohnsteelegordoncom/feed/'},
    'Tyler Cowen': 'https://www.bloomberg.com/view/rss/contributors/tyler-cowen.rss',
}

#     'Cafe Hayek': {'url': 'http://feeds.feedburner.com/CafeHayek'},
#     'Oddball Stocks': {'url': 'http://feeds.feedburner.com/OddballStocks'},

bloomberg = {
    'Megan Mcardle': {'url': 'https://www.bloomberg.com/view/rss/contributors/megan-mcardle.rss'},
    'Eli Lake': {'url': 'https://www.bloomberg.com/view/rss/contributors/eli-lake.rss'},
    'Matt Levine': {'url': 'https://www.bloomberg.com/view/rss/contributors/matt-levine.rss'},
}

# 'EconLib':   {'url': 'http://feeds.feedburner.com/econlib'},
#     'John Cochrane': {'url': 'http://johnhcochrane.blogspot.com/feeds/posts/default'},
#     'Marginal Revolution': {'url': 'http://marginalrevolution.com/feed'},

primary_sources = {
    'Pew Research': 'http://www.pewresearch.org/feed/',
    'Federal Reserve': 'https://www.federalreserve.gov/feeds/datadownload.xml',
    'Census Bureau': 'https://www.census.gov/economic-indicators/indicator.xml',
    'International Monetary Fund': 'http://www.imf.org/en/publications/rss?language=eng&series=IMF%20Staff%20Country%20Reports',
    'FBI Press Releases': 'https://www.fbi.gov/feeds/national-press-releases/rss.xml',
    'Justice Department': 'https://www.justice.gov/feeds/opa/justice-news.xml',
    'Amnesty International': 'http://www.amnestyusa.org/rss/report/all/rss.xml'

}


feeds = {
    'The Economist': {'url': 'http://www.economist.com/sections/middle-east-africa/rss.xml'},
    'Nate Silver': {'url': 'https://fivethirtyeight.com/contributors/nate-silver/feed/'},
    'Charles Krauthammer': {'url': 'https://www.washingtonpost.com/people/charles-krauthammer/?outputType=rss'},
    'Jackson Diehl': {'url': 'https://www.washingtonpost.com/people/ej-dionne-jr/?outputType=rss'},
    'David Frum': {
        'url': 'https://www.theatlantic.com/feed/author/david-frum/'
    },
    'David Brooks': {
        'url': 'http://www.nytimes.com/svc/collections/v1/publish/www.nytimes.com/column/david-brooks/rss.xml'
    },
    'Ross Douhat': {
        'url': 'http://www.nytimes.com/svc/collections/v1/publish/www.nytimes.com/column/ross-douthat/rss.xml'
    },
    'The American Interest': {
        'url': 'https://www.the-american-interest.com/feed/'
    },
    'The Federalist': {
        'url': 'http://thefederalist.com/feed/'
    },
    'Matt Welch': {
        'url': 'http://reason.com/people/matt-welch/all.xml'
    },
    'Michael Barone': {
        'url': 'http://www.washingtonexaminer.com/rss/michael+-barone'
    },
    'National Review': {
        'url': 'https://www.rsssearchhub.com/feed/a54c2c760342ac0e2836bee09ffe3c91/national-review-online-the-corner'
    },
    'City Journal': {'url': 'http://feeds.feedburner.com/city-journal'},
    'Megan Mcardle': {'url': 'https://www.bloomberg.com/view/rss/contributors/megan-mcardle.rss'},
    'Eli Lake': {'url': 'https://www.bloomberg.com/view/rss/contributors/eli-lake.rss'},
    'Commentary Magazine': {'url': 'https://www.commentarymagazine.com/feed/'},
}


def generic(url, src):
    entries = feedparser.parse(url).entries
    for entry in entries:
        page = requests.get(entry['link'])
        tree = html.fromstring(page.content)
        try:
            entry['img'] = tree.xpath(
                "//meta[contains(@property, 'og:image')]//@content")[0]
        except:
            pass
        if 'author' not in entry:
            entry['author'] = src
        if 'By' in entry['author']:
            entry['author'] = ' '.join(
                entry['author'].split(' ')[1:2])
        entry['src'] = src

    return entries


def scrape_commentary(url, src):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    authors = [author for author in tree.xpath(
        "//a[contains(@class, 'author')]//text()") if not author == 'Our Readers']
    titles = tree.xpath("//h2[contains(@itemprop, 'headline')]//a//text()")
    images = tree.xpath(
        "//a[contains(@class, 'vw-post-box-thumbnail')]//img//@src")
    pubDates = tree.xpath(
        "//meta[contains(@itemprop, 'datePublished')]//@content")
    links = tree.xpath(
        "//a[contains(@class, 'vw-post-box-thumbnail')]//@href")
    entries = []
    for title, image, author, link, pubDate in zip(titles, images, authors, links, pubDates):
        entries.append(RSSEntry(
            title=title,
            img=image,
            author=author,
            link=link,
            pubDate=pubDate[0:19],
            src=src)
        )
    return entries


def scrape_bloomberg(url, src):
    page = requests.get(url)
    tree = html.fromstring(page.content)
    titles = tree.xpath("//h1[contains(@class, 'title')]//a//text()")
    images = tree.xpath('//article//@style')
    authors = tree.xpath("//a[contains(@class, 'byline')]//text()")
    links = tree.xpath("//h1[contains(@class, 'title')]//a//@href")

    entries = []
    for title, image, author, link in zip(titles, images, authors, links):
        entries.append(RSSEntry(
            title=title.strip(),
            link='https://bloomberg.com' + '/' + link.strip(),
            author=author.strip(),
            pubDate=datetime.datetime.now(),
            img=re.search('http[^ )]*', image).group().strip(),
            src=src
        ))
    return entries


def clean(entry):
    try:
        if 'published' in entry:
            entry['published'] = parser.parse(entry['published'])
        elif 'pubDate' in entry:
            entry['published'] = parser.parse(entry['pubDate'])
        elif re.search('\d\d\d\d.\d\d.\d\d', entry['link']):
            entry['published'] = parser.parse(
                re.search('\d\d\d\d.\d\d.\d\d', entry['link']).group())
        else:
            entry['published'] = datetime.datetime.now()
        entry['author'] = re.sub('[By]y', '', entry['author']).strip()
        article = g.extract(entry['link'])
        entry['text'] = article.cleaned_text
        if 'img' not in entry:
            entry['img'] = article.top_image.src
        entry['title'] = entry['title'].strip()
        if 'summary' not in entry:
            entry['summary'] = entry['text']
#        entry['summary'] = re.match(
#            r'(?:[^.:!?]+[.:!?]){0,4}', entry['summary']).group()

        for key in entry:
            if type(entry[key]) == unicode:
                entry[key] = entry[key].encode('ascii', errors='ignore')
    except Exception as e:
        print >> sys.stderr, "failed to parse", entry, e

    return entry


def scrape(feeds):
    entries = []
    for src, feed in feeds.iteritems():
        url = feed['url']
        print >> sys.stderr, url, len(entries)
        entries.append(generic(url, src))
    with ProcessPoolExecutor(max_workers=10) as executor:
        entries = [entry for entry in chain.from_iterable(
            izip_longest(*entries)) if entry]
        return list(executor.map(clean, entries))

if __name__ == '__main__':
    entries = scrape(miss_manners)
    for entry in entries:
        print entry['link'], entry['published']
