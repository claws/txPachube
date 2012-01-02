txPachube
=========

txPachube is a Python wrapper of the v2 Pachube API, based on the Twisted networking framework.
Use it to integrate non blocking access to the Pachube API into your Python Twisted application.

** txPachube is currently under development**

Software Dependencies
---------------------

 - Python
 - Twisted
  - zope.interface
  - pyOpenSSL (used by Twisted for https - in our case for secure access to Pachube)


Install
=======

    python setup.py install


Examples
========

These examples require you to have a Pachube account as an appropriately configured
(permissions set to create, update, read, delete) Pachube API key is required. 

List Pachube feeds visible to the API key supplied::

    from twisted.internet import reactor
    import txpachube

    # Paste your Pachube API key here
    API_KEY = ""

    def list_feeds(pachube):
        """ List feeds visible to the api key used """
        d = pachube.list_feeds()
        d.addCallback(lambda feed_list: print "Received feed list content:\n%s\n" % feed_list )
        d.addErrback(lambda reason: print "Error listing visible feeds: %s" % str(reason))
        d.addCallback(reactor.stop)


    if __name__ == "__main__":
        pachube = txpachube.Pachube(api_key=API_KEY)
        reactor.callWhenRunning(list_feeds, pachube)
        reactor.run()


Create a new feed::
   
    from twisted.internet import reactor
    import txpachube
    import json

    # Paste your Pachube API key here
    API_KEY = ""

    # example feed update data
    feed_data = {"title" : "A Temporary Test Feed", "version" : "1.0.0"}
    
    json_feed_data = json.dumps(feed_data)


    def create_feed(pachube, api_key, format, data):
        """ Create a feed """
        d = pachube.update_feed(apiKey=api_key, feed_id=feed_id, format=format, data=data)
        d.addCallback(lambda new_feed_id: print "Feed created. New feed id is: %s" % new_feed_id)
        d.addErrback(lambda reason: print "Error creating feed: %s" % str(reason))
        d.addCallback(reactor.stop)


    if __name__ == "__main__":
        pachube = txpachube.Pachube()
        reactor.callWhenRunning(create_feed, pachube, API_KEY, FEED_ID, txPachube.DataFormats.JSON, json_feed_data)
        reactor.run()


Update a feed::
   
    from twisted.internet import reactor
    import txpachube
    import json

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste you feed identifier here
    FEED_ID = ""

    # example feed update data
    feed_data = {"version" : "1.0.0", 
                        "datastreams":[
                                               {"id":"0", "current_value":"100"},
                                               {"id":"two", "current_value":"500"},
                                               {"id":"3.0", "current_value":"300"}
                                              ]
                       }

    json_feed_data = json.dumps(feed_data)


    def update_feed(pachube, api_key, feed_id, format, data):
        """ Update a feed """
        d = pachube.update_feed(apiKey=api_key, feed_id=feed_id, format=format, data=data)
        d.addCallback(lambda result: print "Feed updated successfully:\n%s\n" % result )
        d.addErrback(lambda reason: print "Error updating feed: %s" % str(reason))
        d.addCallback(reactor.stop)


    if __name__ == "__main__":
        pachube = txpachube.Pachube()
        reactor.callWhenRunning(update_feed, pachube, API_KEY, FEED_ID, txPachube.DataFormats.JSON, json_feed_data)
        reactor.run()


