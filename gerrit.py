#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    gerrit.py
    
    Get Gerrit events!

    Ideas:
    - Growl notification!
    - RSS / Atom feed!
    - Twitter / identica updates!
    - Bullet points with exclamation marks!

    Requires paramiko 

    Based on http://code.google.com/p/gerritbot/
    Apache license.

    :author: Ori Livneh <ori@wikimedia.org>
"""

import ConfigParser
import Queue
import json
import logging
import threading
import time

import paramiko


queue = Queue.Queue()

# Logging

logging.basicConfig(level=logging.INFO)
logger = paramiko.util.logging.getLogger()
logger.setLevel(logging.INFO)

# Config

config = ConfigParser.ConfigParser()
config.read('gerrit.conf')

options = dict(timeout=60)
options.update(config.items('Gerrit'))
options['port'] = int(options['port'])


class GerritStream(threading.Thread):
    """Threaded job; listens for Gerrit events and puts them in a queue."""

    def run(self):
        while 1:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(**options)
                client.get_transport().set_keepalive(60)
                _, stdout, _ = client.exec_command('gerrit stream-events')
                for line in stdout:
                    queue.put(json.loads(line))
            except:
                logging.exception('Gerrit error')
            finally:
                client.close()
            time.sleep(5)


# For a description of the JSON structure of events emitted by Gerrit's
# stream-events command, see the Gerrit documentation.
# http://gerrit.googlecode.com/svn/documentation/2.1.2/cmd-stream-events.html

templates = {
    'comment-added':     ('Comment added ({0[author][name]}): "{0[comment]}" '
                          '[{0[change][project]}] - {0[change][url]}'),

    'change-merged':     ('Change merged ({0[submitter][name]}):'
                          '{0[change][subject]} [{0[change][project]}] - '
                          '{0[change][url]}'),

    'patchset-added':    ('Change merged ({0[submitter][name]}):'
                          '{0[change][subject]} [{0[change][project]}] - '
                          '{0[change][url]}'),

    'change-abandoned':  ('Change merged ({0[submitter][name]}):'
                          '{0[change][subject]} [{0[change][project]}] - '
                          '{0[change][url]}'),
}


gerrit = GerritStream()
gerrit.daemon = True
gerrit.start()


while 1:
    event = queue.get()
    # If you just want json output, ...
    print event
    # Or if you want something more human-readable
    template = templates[event['type']]
    print template.format(event)

gerrit.join()
