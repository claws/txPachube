txpachube (is now `txcosm <https://github.com/claws/txcosm>`_)
=========

IMPORTANT NOTE: Further development on the capability provided by this package will be performed in `txcosm <https://github.com/claws/txcosm>`_

.. contents::


Introduction
------------

NOTE: Pachube was the old name of what is now Cosm.com. This package continues to work with Cosm.com even though it is named after the old site name.
However, no further development is planned in this txpachube package. Instead this repository has been copied and recreated as txcosm to mirror the new Cosm.com site name.

txpachube is a Python package implementing the v2 Cosm/Pachube `API <https://cosm.com/docs/v2/>`_, based on the Twisted networking framework.
Use txpachube to integrate non blocking access to the Pachube API into your Python Twisted application.


Details
-------

txpachube implements the full v2 Cosm/Pachube API (Feeds, Datastreams, Datapoints, Triggers, Users, Keys) and many
of the data structures (Unit, Location, Datapoint, Datastream, Environment, EnvironmentList, Trigger,
TriggerList Key, KeyList, User, UserList) contained in requests and responses.

The data structures support encoding and decoding from JSON/XML formats. These structures are useful
when building data to send to Cosm/Pachube and also for processing Cosm/Pachube data returned from queries.

The txpachube client methods take a data string argument that will be used as the body of the
message sent to Pachube. How you generate this body data is up to you. You might choose to
manually create the data something like this::

    # manually create feed data message body content
    feed_data = {"title" : "A Temporary Test Feed",
                 "version" : "1.0.0"}
    json_feed_data = json.dumps(feed_data)

The txpachube package implements many of the data structures used in Pachube requests and
response as Python objects. So the JSON formatted feed data above could also be generated
using these txpachube data structure objects like this::

    # Define a dict of valid data structure keywords for use as
    # key word arguments to the data structure initialiser.
    #
    env_kwargs = {txpachube.DataFields.Title : "A Temporary Test Feed",
                  txpachube.DataFields.Version : "1.0.0"}
    environment = txpachube.Environment(**env_kwargs)
    json_feed_data = environment.encode()

Or in a more compact form once you are familiar with a data strcture's valid DataField items::

    environment = txpachube.Environment(title="A Temporary Test Feed", version="1.0.0")
    json_feed_data = environment.encode()

txpachube also implements a client that connects to the beta PAWS service. This allows long
running, persistent, connections to be made to the Pachube service. This type of client is
useful for applications which require realtime updates on change of status. Such realtime
updates are available through the subscription feature exposed in the beta PAWS service.



Software Dependencies
---------------------

* Python
* Twisted

  - zope.interface
  - pyOpenSSL (used by Twisted for https - in our case for secure access to Pachube)


Install
-------

1. Download txpachube archive::

    $ git clone git://github.com/claws/txPachube.git

For other download options (zip, tarball) visit the github web page of `txpachube <https://github.com/claws/txPachube>`_

2. Install txpachube module into your Python distribution::

    sudo python setup.py install

3. Test::

    $ python
    >>> import txpachube
    >>>


Examples
--------

These examples require you to have a Pachube account and an appropriately configured
(permissions set to create, update, read, delete) Pachube API key is required.

List Pachube feeds visible to the API key supplied::

    #!/usr/bin/env python
    # This example demonstrates a request for feeds visible to the
    # supplied API key. It initialises the Client object with a
    # default API key that will be used if no api_key argument is
    # passed to the various API methods.
    # Parameters can be passed to customise the default results.
    # In this case only 'live' feeds and 'summary' content is
    # being requested.

    from twisted.internet import reactor, defer
    import txpachube.client

    # Paste your Pachube API key here
    API_KEY = ""


    @defer.inlineCallbacks
    def demo():
        client = txpachube.client.Client(api_key=API_KEY)
        try:
            feed_list = yield client.list_feeds(parameters={'status' : 'live', 'content' : 'summary'})
            print "Received feed list content:\n%s\n" % feed_list
        except Exception, ex:
            print "Error listing visible feeds: %s" % str(ex)

        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)


    if __name__ == "__main__":

        reactor.callWhenRunning(demo)
        reactor.run()


Create a new feed::

    #!/usr/bin/env python
    # This example demonstrates the ability to create new feeds. It also
    # shows an API key being passed to the create_feed method directly
    # as no default key was passed to the Client object initialiser.
    # No format needs to be specified because json is the default format
    # used.

    from twisted.internet import reactor, defer
    import txpachube
    import txpachube.client

    # Paste your Pachube API key here
    API_KEY = ""


    @defer.inlineCallbacks
    def demo():

        client = txpachube.client.Client()
        try:
            environment = txpachube.Environment(title="A Temporary Test Feed", version="1.0.0")
            new_feed_id = yield client.create_feed(api_key=API_KEY, data=environment.encode())
            print "Created new feed with id: %s" % new_feed_id
        except Exception, ex:
            print "Error creating new feed: %s" % str(ex)

        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)


    if __name__ == "__main__":

        reactor.callWhenRunning(demo)
        reactor.run()


Update a feed::

    #!/usr/bin/env python
    # This example show how a feed can be updated using your own generated
    # data, in this case XML data.
    # The Client object has been initialised with an API key and a feed id
    # so they don't need to be passed to the update_feed method. The format
    # argument is JSON by default so it must be explicitly set as this
    # example is using XML.

    from twisted.internet import reactor
    import txpachube
    import txpachube.client

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

        pachubeClient = txpachube.client.Client(api_key=API_KEY, feed_id=FEED_ID)

        d = pachubeClient.update_feed(format=txpachube.DataFormats.XML, data=feed_data)
        d.addCallback(lambda result: print "Feed updated successfully:\n%s\n" % result)
        d.addErrback(lambda reason: print "Error updating feed: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()


Read a feed::

    #!/usr/bin/env python
    # This example demonstrates a request for feed data and uses
    # additional parameters to restrict the datastreams returned.
    # It initialises the Client object with a default API key and
    # feed id so they do not need to be passed to the read_feed
    # method.

    from twisted.internet import reactor, defer
    import txpachube.client

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to be read here
    FEED_ID = ""


    @defer.inlineCallbacks
    def demo():

        client = txpachube.client.Client(api_key=API_KEY, feed_id=FEED_ID)
        try:
            feed = yield client.read_feed(parameters={'datastream':'temperature'})
            print "Received feed content:\n%s\n" % feed
        except Exception, ex:
            print "Error reading feed: %s" % str(ex)

        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)


    if __name__ == "__main__":

        reactor.callWhenRunning(demo)
        reactor.run()



Delete a feed::

    #!/usr/bin/env python
    # This example demonstrates the ability to delete a feed.
    # WARNING: This will REALLY delete the feed identifier listed. Make sure it is only a test feed.

    from twisted.internet import reactor, defer
    import txpachube.client

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to be DELETED here
    FEED_ID = ""


    @defer.inlineCallbacks
    def demo():

        client = txpachube.client.Client()
        try:
            feed_delete_status = yield client.delete_feed(api_key=API_KEY, feed_id=FEED_ID)
            print "Deleted feed: %s" % feed_delete_status
        except Exception, ex:
            print "Error deleting feed: %s" % str(ex)

        reactor.callLater(0.1, reactor.stop)
        defer.returnValue(True)


    if __name__ == "__main__":

        reactor.callWhenRunning(demo)
        reactor.run()



Use the beta PAWS API to subscribe to a feed or datastream and receive updates
whenever the feed/datastream value changes::

    #!/usr/bin/env python

    from twisted.internet import reactor
    import txpachube
    import txpachube.client

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to monitor here
    FEED_ID = ""

    # Paste a datastream identifier from the feed here if you only want to
    # monitor a particular datastream instead of the whole feed.
    DATASTREAM_ID = ""

    #
    # Set up callback handlers
    #

    def updateHandler(dataStructure):
        """
        Handle a txpachube data structure object generated as a result of a
        subscription update message received from Pachube.

        The data structure returned will vary depending on the resource subscribed to.
        If a datastream is specified the returned data structure will be a txpachube.Datastream
        object. If just a feed is specified then the returned data structure will be a
        txpachube.Environment object.
        """
        print "Subscription update message received:\n%s\n" % str(dataStructure)


    def do_subscribe(connected, client, resource):
        """ Subscribe to the specified resource if the connection is established """

        if connected:
            print "Connected to PAWS service"

            def handleSubscribeResponse(status):
                print "Subscribe response status: %s" % status

            print "Subscribing for updates to: %s" % resource
            token, d = client.subscribe(resource, updateHandler)
            print "Subscription token is: %s" % token
            d.addCallback(handleSubscribeResponse)

        else:
            print "Connection failed"
            reactor.callLater(0.1, reactor.stop)
            return


    if __name__ == '__main__':

        if DATASTREAM_ID:
            resource = "/feeds/%s/datastreams/%s" % (FEED_ID, DATASTREAM_ID)
        else:
            resource = "/feeds/%s" % (FEED_ID)

        client = txpachube.client.PAWSClient(api_key=API_KEY)
        d = client.connect()
        d.addCallback(do_subscribe, client, resource)
        reactor.run()




Example use case scenario::

    #!/usr/bin/env python

    # This example demonstrates how you could use the txpachube module to
    # help upload sensor data (in this scenario a CurrentCost device) to
    # Cosm/Pachube.
    # A txpachube.Environment data structure is generated and populated
    # with current value data. All the implemented data structures
    # support encoding to JSON (default) and XML (EEML).
    #
    # In this example the CurrentCost sensor object is derived from the
    # separate txcurrentcost package. If you want to run this script
    # you would need to obtain that package.
    #

    from twisted.internet import reactor
    import txpachube
    import txcurrentcost.monitor

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to be DELETED here
    FEED_ID = ""

    CurrentCostMonitorConfigFile = "/path/to/your/config/file"


    class MyCurrentCostMonitor(txcurrentcost.monitor.Monitor):
        """
        Extends the txcurrentCost.monitor.Monitor by implementing periodic update
        handler to call a supplied data handler.
        """

        def __init__(self, config_file, periodicUpdateDataHandler):
            super(MyCurrentCostMonitor, self).__init__(config_file)
            self.periodicUpdateDataHandler = periodicUpdateDataHandler

        def periodicUpdateReceived(self, timestamp, temperature, sensor_type, sensor_instance, sensor_data):
            if sensor_type == txcurrentcost.Sensors.ElectricitySensor:
                if sensor_instance == txcurrentcost.Sensors.WholeHouseSensorId:
                    self.periodicUpdateDataHandler(timestamp, temperature, sensor_data)


    class Monitor(object):

        def __init__(self, config):
            self.temperature_datastream_id = "temperature"
            self.energy_datastream_id = "energy"
            self.pachube = txpachube.client.Client(api_key=API_KEY, feed_id=FEED_ID)
            currentCostMonitorConfig = txcurrentcost.monitor.MonitorConfig(CurrentCostMonitorConfigFile)
            self.sensor = txcurrentcost.monior.Monitor(currentCostMonitorConfig,
                                                       self.handleCurrentCostPeriodicUpdateData)

        def start(self):
            """ Start sensor """
            self.sensor.start()

        def stop(self):
            """ Stop the sensor """
            self.sensor.stop()

        def def handleCurrentCostPeriodicUpdateData(self, timestamp, temperature, watts_on_channels):
            """ Handle latest sensor periodic update """

            # Populate a txpachube.Environment data structure object with latest data

            environment = txpachube.Environment(version="1.0.0")
            environment.setCurrentValue(self.temperature_datastream_id, "%.1f" % temperature)
            environment.setCurrentValue(self.energy_datastream_id, str(watts_on_channels[0]))

            # Update the Pachube service with latest value(s)

            d = self.pachube.update_feed(data=environment.encode())
            d.addCallback(lambda result: print "Pachube updated")
            d.addErrback(lambda reason: print "Pachube update failed: %s" % str(reason))


    if __name__ == "__main__":
        monitor = Monitor()
        reactor.callWhenRunning(monitor.start)
        reactor.run()



Todo
----

* Add test cases
* Investigate alternative installers that support uninstall/update options.
* Complete implementation of PAWS client. Currently it only supports subscribe/unsubscribe
  but it should implement everything the standard client supports.


.. image:: https://ga-beacon.appspot.com/UA-29867375-2/txPachube/readme?pixel
   :target: https://github.com/claws/txPachube
