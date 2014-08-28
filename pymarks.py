#!/usr/bin/python
# -*- coding: utf-8 -*-

"""pymarks

Identifies duplicate and dead links in Chrome bookmarks.

Usage:
  pymarks.py <source> <destination> [--deadlinks] [--duplicates] [--emptyfolders]
  pymarks.py (-h | --help)

Options:
  -d --duplicates    Wheter the duplicate bookmarks should be checked and removed.
  -l --deadlinks     Whether the dead links should be checked and removed.
  -e --emptyfolders  Whether the empty folders sould be checked and removed.
  -h --help          Show this screen.
"""

import json
import requests
import sys
import thread
from docopt import docopt
from zlib import crc32

thread_count = 0

def check_link(url, name, level):
    global thread_count
    thread_count += 1
    try:
        req = requests.head(url, allow_redirects=True)
        if req.status_code != 200:
            print("Dead link (%s) - %s: %s" % (req.status_code, level, name))
        thread_count -= 1
    except Exception as e:
        print "%s: %s" % (e, url)
        thread_count -= 1

def iterate_items(node, level):
    items = []
    for item in node:
        if item['type'] == 'folder':
            # recurse to folder
            iterate_items(item['children'], "%s -> %s" % (level, item['name']))

            # check for empty folder
            if check_empty and len(item['children']) == 0:
                print("Empty - %s: %s" % (level, item['name']))
                continue
        elif item['type'] == 'url':
            # check for duplicate
            if check_duplicates:
                crc = crc32(item['url'])
                if crc in hashes:
                    print("Duplicate - %s: %s" % (level, item['name']))
                    continue
                else:
                    hashes.append(crc)

            # check for dead link
            if check_links:
                thread.start_new_thread(check_link, (item['url'], item['name'], level,))
                #check_link(item['url'], item['name'], level)

        items.append(item)
    node[:] = items

if __name__ == '__main__':
    # parse script arguments
    arguments = docopt(__doc__)
    source = arguments['<source>']
    destination = arguments['<destination>']
    check_duplicates = arguments['--duplicates']
    check_links = arguments['--deadlinks']
    check_empty = arguments['--emptyfolders']

    # load file contents
    file = open(source, 'r')
    content = json.load(file)
    file.close()

    hashes = []

    # iterate over bookmark bar
    iterate_items(content['roots']['bookmark_bar']['children'], 'Bookmark Bar')
    iterate_items(content['roots']['other']['children'], 'Other')

    hashes = []

    # second pass to delete empty folders
    if check_empty:
      iterate_items(content['roots']['bookmark_bar']['children'], 'Bookmark Bar')
      iterate_items(content['roots']['other']['children'], 'Other')

    while thread_count > 0:
        pass

    # save modified contents to file
    file = open(destination, 'w+')
    json.dump(content, file, indent=3)
    file.close()
