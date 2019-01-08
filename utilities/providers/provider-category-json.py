#!/usr/bin/env python3

# scrapes provider information from Hashicorp's online documentation
# groups related resources together according to documentation structure,
# and outputs json useful for categorical coloration...

# e.g.
# 
# { 'aws_vpc'     : 1,
#   'aws_subnet   : 1,
#   'aws_instance : 2,
#   ... }

# TODO: only handles "Resources." "Data Sources" Sometimes overlap, sometimes
# don't. So we're not catching all of them, or handling appropriately.

import re
import json
import itertools

import requests
from bs4 import BeautifulSoup

def main():

    providers = {}
    resources = {}

    provider_re = re.compile(r'\/docs\/providers\/(?P<provider>\S+)\/index.html')
    resource_re = re.compile(r'\/docs\/providers\/(?P<provider>\S+)\/r/(?P<resource>\S+).html')

    # group_counter_fn() will increment the counter and return it.
    group_counter_fn = itertools.count().__next__

    providers_url = 'https://www.terraform.io/docs/providers/index.html'
    provider_soup = BeautifulSoup(requests.get(providers_url).text, 'lxml')

    provider_links = { 'https://www.terraform.io' + tag['href'] \
        for tag in provider_soup.findAll('a', {'href' : provider_re}) }

    # for each provider's documentation, do our best to extract
    # resource "groups"...     
    for url in provider_links:
        soup = BeautifulSoup(requests.get(url).text, 'lxml')
        for a in soup.findAll('a', {'href' : '#'}):
            if re.match(r'Data\s+Sources', a.getText()):
                continue
            else:
                group = a.getText()
                group_counter = group_counter_fn()                
                ul = a.find_next('ul')
                links = { a.getText() : group_counter for a in ul.findAll('a', {'href' : resource_re})}
                resources = { **resources, **links }

    # this persists as a bit of a hack, because we see these, but
    # they don't appear in HC docs in an easily scraped way.
    defaults = {
        ''         : 10000,
        'provider' : 10000,
        'meta'     : 10000,
        'var'      : 10001,
        'output'   : 10002   
    }

    resources = { **resources, **defaults }

    print(json.dumps(resources, indent=4, sort_keys=True))


if __name__ == '__main__':
    main()
