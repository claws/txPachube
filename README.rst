txPachube
=========

txPachube is a Python wrapper of the v2 Pachube `API <http://api.pachube.com/v2/>`_, based on the Twisted networking framework.
Use it to integrate non blocking access to the Pachube API into your Python Twisted application.

It implements the full Pachube API - Feeds, Datastreams, Datapoints, Triggers, Users, Keys.

**txPachube is currently under development**

Software Dependencies
---------------------

* Python
* Twisted

  - zope.interface
  - pyOpenSSL (used by Twisted for https - in our case for secure access to Pachube)


Install
=======

1. Download txPachube archive.

2. Install txPachube module into your Python distribution.
    python setup.py install


Examples
========

These examples require you to have a Pachube account and an appropriately configured
(permissions set to create, update, read, delete) Pachube API key is required. 

List Pachube feeds visible to the API key supplied::

    #!/usr/bin/env python 
    # This example demonstrates a request for feeds visible to the
    # supplied API key. It initialises the Client object with a
    # default API key that will be used if no api_key argument is
    # passed to the various API methods.

    from twisted.internet import reactor
    import txPachube

    # Paste your Pachube API key here
    API_KEY = ""


    if __name__ == "__main__":

        pachubeClient = txPachube.Client(api_key=API_KEY)

        d = pachubeClient.list_feeds()
        d.addCallback(lambda feed_list: print "Received feed list content:\n%s\n" % feed_list)
        d.addErrback(lambda reason: print "Error listing visible feeds: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()


Create a new feed::

    #!/usr/bin/env python 
    # This example demonstrates the ability to create new feeds. It also
    # shows an API key being passed to the create_feed method directly 
    # because no default key was passed to the Client object initialiser.
    # No format needs to be specified because json is the default format
    # used.
 
    from twisted.internet import reactor
    import txPachube
    import json

    # Paste your Pachube API key here
    API_KEY = ""

    # example create feed data
    feed_data = {"title" : "A Temporary Test Feed",
                 "version" : "1.0.0"}
    
    json_feed_data = json.dumps(feed_data)


    if __name__ == "__main__":

        pachubeClient = txPachube.Client()

        d = pachubeClient.create_feed(api_key=API_KEY, data=json_feed_data)
        d.addCallback(lambda new_feed_id: print "Feed created. New feed id is: %s" % new_feed_id)
        d.addErrback(lambda reason: print "Error creating feed: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()


Update a feed::
  
    #!/usr/bin/env python 
    # This example show how a feed can be updated. The Client object
    # has been initialised with an API key and a feed id so they don't
    # need to be passed to the update_feed method. The format argument
    # is defaulted to json so it must be passed as this example is using
    # XML.
 
    from twisted.internet import reactor
    import txPachube

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste you feed identifier here
    FEED_ID = ""

    # example feed update data
    feed_data = """<?xml version="1.0" encoding="UTF-8"?>
    <eeml xmlns="http://www.eeml.org/xsd/0.5.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="0.5.1" xsi:schemaLocation="http://www.eeml.org/xsd/0.5.1 http://www.eeml.org/xsd/0.5.1/0.5.1.xsd">
      <environment>
        <title>bridge19</title>
        <status>live</status>
        <description>bridge environment 19</description>
        <tag>Tag1</tag>
        <tag>Tag2</tag>
        <data id="3">
          <current_value>-312</current_value>
          <max_value>999.0</max_value>
          <min_value>7.0</min_value>
        </data>
        <data id="0">
          <current_value>11</current_value>
          <max_value>211.0</max_value>
          <min_value>7.0</min_value>
        </data>
        <data id="4">
          <current_value>-3332</current_value>
        </data>
      </environment>
    </eeml>"""


    if __name__ == "__main__":

        pachubeClient = txPachube.Client(api_key=API_KEY, feed_id=FEED_ID)

        d = pachubeClient.update_feed(format=txPachube.DataFormats.XML, data=feed_data)
        d.addCallback(lambda result: print "Feed updated successfully:\n%s\n" % result)
        d.addErrback(lambda reason: print "Error updating feed: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()


Read a feed::
   
    #!/usr/bin/env python 
    # This example demonstrates a request for feed data and uses
    # additonal parameters to restrict the datastreams returned.
    # It initialises the Client object with a default API key and
    # feed id so they do not need to be passed to the read_feed
    # method.

    from twisted.internet import reactor
    import txPachube

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to be DELETED here
    FEED_ID = ""


    if __name__ == "__main__":
        
        pachubeClient = txPachube.Client(api_key=API_KEY, feed_id=FEED_ID)

        d = pachubeClient.read_feed(parameters={'datastreams' : 'temperature'})
        d.addCallback(lambda feed_dict: print "Received feed content:\n%s\n" % feed_dict)
        d.addErrback(lambda reason: print "Error retrieving feed data: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()


Delete a feed::

    #!/usr/bin/env python 
    # This example demonstrates the ability to delete a feed.
    WARNING: This will REALLY delete the feed identifier listed. Make sure it is only a test feed. 
 
    from twisted.internet import reactor
    import txPachube

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to be DELETED here
    FEED_ID = ""


    if __name__ == "__main__":

        pachubeClient = txPachube.Client(api_key=API_KEY)

        d = pachubeClient.delete_feed(feed_id=FEED_ID)
        d.addCallback(lambda result: print "Feed was deleted: %s" % result)
        d.addErrback(lambda reason: print "Error deleting feed: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()

Todo
====

* Add classes for environments (feeds), datastreams, datapoints, etc so that
  these can be passes between the txPachube functions instead of the current
  strings containing json or xml or csv data.

