txPachube
=========

txPachube is a Python wrapper of the v2 Pachube `API <http://api.pachube.com/v2/>`_, based on the Twisted networking framework.
Use it to integrate non blocking access to the Pachube API into your Python Twisted application.

It currently contains API functions for all API calls (Feeds, Datastreams, Datapoints, Triggers, Users, Keys).

**txPachube is currently under development**

Software Dependencies
---------------------

* Python
* Twisted
  - zope.interface
  - pyOpenSSL (used by Twisted for https - in our case for secure access to Pachube)


Install
=======

1. Install txPachube module
    python setup.py install


Examples
========

These examples require you to have a Pachube account as an appropriately configured
(permissions set to create, update, read, delete) Pachube API key is required. 

List Pachube feeds visible to the API key supplied::

    # This example demonstrates a request for feeds visible to the
    # supplied API key. It initialises the Pachube object with a
    # default API key that will be used if no apiKey argument is
    # passed to the various API methods.

    from twisted.internet import reactor
    import txPachube

    # Paste your Pachube API key here
    API_KEY = ""

    def list_feeds(pachubeClient):
        """ List feeds visible to the api key used """
        d = pachubeClient.list_feeds()
        d.addCallback(lambda feed_list: print "Received feed list content:\n%s\n" % feed_list )
        d.addErrback(lambda reason: print "Error listing visible feeds: %s" % str(reason))
        d.addCallback(reactor.stop)


    if __name__ == "__main__":
        pachubeClient = txPachube.Client(api_key=API_KEY)
        reactor.callWhenRunning(list_feeds, pachubeClient)
        reactor.run()


Create a new feed::

    # This example demonstrates the ability to create new feeds. It also
    # shows an API key being passed to the update_feed method directly 
    # because no default key was passed to the Pachube object initialiser.
   
    from twisted.internet import reactor
    import txPachube
    import json

    # Paste your Pachube API key here
    API_KEY = ""

    # example feed update data
    feed_data = {"title" : "A Temporary Test Feed",
                 "version" : "1.0.0"}
    
    json_feed_data = json.dumps(feed_data)


    def create_feed(pachubeClient, api_key, format, data):
        """ Create a feed """
        d = pachubeClient.create_feed(apiKey=api_key, feed_id=feed_id, format=format, data=data)
        d.addCallback(lambda new_feed_id: print "Feed created. New feed id is: %s" % new_feed_id)
        d.addErrback(lambda reason: print "Error creating feed: %s" % str(reason))
        d.addCallback(reactor.stop)


    if __name__ == "__main__":
        pachubeClient = txPachube.Client()
        reactor.callWhenRunning(create_feed, pachubeClient, API_KEY, txPachube.DataFormats.JSON, json_feed_data)
        reactor.run()


Update a feed::
  
    # This example show how a feed can be updated. The Pachube object
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


    def update_feed(pachubeClient, format, xml_data):
        """ Update a feed """
        d = pachubeClient.update_feed(format=format, data=data)
        d.addCallback(lambda result: print "Feed updated successfully:\n%s\n" % result )
        d.addErrback(lambda reason: print "Error updating feed: %s" % str(reason))
        d.addCallback(reactor.stop)


    if __name__ == "__main__":
        pachubeClient = txPachube.Client(api_key=API_KEY, feed_id=FEED_ID)
        reactor.callWhenRunning(update_feed, pachubeClient, txPachube.DataFormats.XML, feed_data)
        reactor.run()


Stitch it all together::

    


Todo
====

* Add classes for environments (feeds), datastreams, datapoints, etc so that
  these can be passes between the txPachube funcitons instead of the current
  strings containing json or xml or csv data.

