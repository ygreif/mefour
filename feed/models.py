import re

from django.db import models
from django.utils import timezone

from bs4 import BeautifulSoup
from HTMLParser import HTMLParser


class Story(models.Model):
    title_text = models.CharField(max_length=400)
    full_text = models.TextField()
    teaser_text = models.TextField(default='')
    summary_text = models.TextField()
    link_url = models.URLField()
    img_url = models.URLField()
    cdn_img_url = models.URLField()
    pub_date = models.DateTimeField()
    source = models.CharField(max_length=100)
    author = models.CharField(max_length=100)

    def __str__(self):
        if self.summary_text:
            return "[done] " + self.title_text + "---" + self.summary_text
        else:
            return self.title_text + '---' + self.teaser_text

    def Title(self):
        if self.source == 'Ask a Manager':
            return self.title_text[0].title() + self.title_text[1:]
        else:
            return HTMLParser().unescape(re.sub("\[.*?\]", "", self.title_text))

    def clean_teaser(self, text):
        for regex in ['(.*?)(read.{1,2}more)', '(.*?)the post']:
            match = re.match(regex, text, re.IGNORECASE | re.DOTALL)
            if match:
                text = match.group(1)
        if self.source == 'The Economist':
            for regex in ['([A-Z][A-Z].*?[.?!])']:
                match = re.search(regex, text)
                if match:
                    text = match.group(1)
        if self.source == 'Michael Barone':
            text = re.sub(self.source, '', text)
        return re.sub("\[.*?\]", "", text)

    def Teaser(self):
        if self.source in ['Commentary Magazine', 'Mainly Macro']:
            text = self.full_text.split('\n')[0]
        elif self.source in ['Ask Amy']:
            text = ' '.join(
                filter(lambda x: x, self.full_text.split('\n'))[0:2])
        elif self.source in ['Ask a Manager']:
            soup = BeautifulSoup(self.teaser_text, "lxml")
            text = soup.p.get_text()
        elif self.source in ['Jeffrey Goldberg', 'David Frum']:
            return re.match('.*?[.!?]', self.full_text or self.teaser_text, re.DOTALL).group(0)
        elif self.source in ['Juan Cole', 'World Affairs Journal', 'Noah Smith', 'Musings on Markets']:
            text = ' '.join(re.split('[.!?]', self.full_text)[0:2]) + '.'
        else:
            text = self.summary_text or self.teaser_text
        soup = BeautifulSoup(text.encode("ascii", "ignore"), "lxml")
        for script in soup(["script", "style"]):
            script.extract()    # rip it out

        return self.clean_teaser(soup.get_text())

    def ImgUrl(self):
        return self.cdn_img_url or self.img_url
