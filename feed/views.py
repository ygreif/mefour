from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
#from django.views.generic.base import TemplateView
from bakery.views import BuildableTemplateView

from models import Story
from collections import defaultdict
from itertools import chain, izip_longest

from crawler import feeds
from builtins import super
# Create your views here.


class IndexPageView(BuildableTemplateView):
    template_name = "feed/index.tmpl"
    build_path = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        latest_stories = Story.objects.order_by('-pub_date')

        # group by src
        grouped = defaultdict(list)
        for story in latest_stories:
            if story.source in feeds.advice_feeds.keys():
                grouped[story.source].append(story)
        # inerweave
        interweaved = [entry for entry in chain.from_iterable(
            izip_longest(*grouped.values()))]
        rows = [interweaved[i:i + 3]
                for i in range(2, min(27, len(interweaved)) - 6, 3)]
        context['lead'] = interweaved[0]
        context['rows'] = rows
        context['site'] = 'AdviceBee'
        context['tagline'] = 'My favorite advice columns, updated daily'
        return context


def index(request):
    latest_stories = Story.objects.order_by('-pub_date')

    # group by src
    grouped = defaultdict(list)
    for story in latest_stories:
        if story.source in feeds.advice_feeds.keys():
            grouped[story.source].append(story)
    # inerweave
    interweaved = [entry for entry in chain.from_iterable(
        izip_longest(*grouped.values()))]
    rows = [interweaved[i:i + 3]
            for i in range(2, max(30, len(interweaved)) - 6, 3)]
    template = loader.get_template('feed/index.tmpl')
    context = {
        'lead': interweaved[0],
        'rows': rows,
    }
    return HttpResponse(template.render(context, request))
