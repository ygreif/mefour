import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'blur.settings'

import django
from cloudinary import uploader
django.setup()
from feed.models import Story

from crawler import feeds


def transform_url(story):
    try:
        r = uploader.upload(story.img_url, api_key="353386115152271", api_secret="VIEfUz6kAWJlE_7Pl5h_YB5cUkE",
                            cloud_name="dans2oyow", width=312, height=172, crop="scale")
        story.cdn_img_url = r['url']
    except:
        print "failed", story.img_url
        story.cdn_img_url = ''

stories = Story.objects.all()
links = set([story.link_url for story in stories])

all_feeds = dict(feeds.advice_feeds.items(
) + feeds.middleeast.items() + feeds.feeds.items())
for entry in feeds.scrape(feeds.extra):
    try:
        if entry['link'] not in links:
            s = Story(title_text=entry['title'], full_text=entry['text'], teaser_text=entry[
                'summary'], link_url=entry['link'], img_url=entry['img'], pub_date=entry['published'], source=entry['src'], author=entry['author'])
            cdn_img_url = transform_url(s)
            s.save()
            links.add(s.link_url)
    except Exception as e:
        print entry, e
