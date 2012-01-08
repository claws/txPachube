txPachube
=========

txPachube is a Python wrapper for the v2 Pachube `API <http://api.pachube.com/v2/>`_, based on the Twisted networking framework.
Use it to integrate non blocking access to the Pachube API into your Python Twisted application.

It implements the full Pachube API (Feeds, Datastreams, Datapoints, Triggers, Users, Keys) and many 
of the data structures (Unit, Location, Datapoint, Datastream, Environment, EnvironmentList, Trigger,
TriggerList Key, KeyList, User, UserList) contained in requests and responses.

The data structures support encoding and decoding from JSON/XML formats. These strucutres are useful
when building data to send to Pachube and also for processing Pachube data returned from queries.


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
  
    sudo python setup.py install


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

        pachubeClient = txPachube.client.Client(api_key=API_KEY)

        d = pachubeClient.list_feeds()
        d.addCallback(lambda environment_list: print "Received feed list content:\n%s\n" % environment_list)
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

        pachubeClient = txPachube.client.Client()

        d = pachubeClient.create_feed(api_key=API_KEY, data=json_feed_data)
        d.addCallback(lambda new_feed_id: print "Feed created. New feed id is: %s" % new_feed_id)
        d.addErrback(lambda reason: print "Error creating feed: %s" % str(reason))
        d.addCallback(reactor.stop)

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

        pachubeClient = txPachube.client.Client(api_key=API_KEY, feed_id=FEED_ID)

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
        
        pachubeClient = txPachube.client.Client(api_key=API_KEY, feed_id=FEED_ID)

        d = pachubeClient.read_feed(parameters={txPachube.DataFields.Datastreams : 'temperature'})
        d.addCallback(lambda environment: print "Received feed content:\n%s\n" % environment)
        d.addErrback(lambda reason: print "Error retrieving feed data: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()


Delete a feed::

    #!/usr/bin/env python 
    # This example demonstrates the ability to delete a feed.
    # WARNING: This will REALLY delete the feed identifier listed. Make sure it is only a test feed. 
 
    from twisted.internet import reactor
    import txPachube

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to be DELETED here
    FEED_ID = ""


    if __name__ == "__main__":

        pachubeClient = txPachube.client.Client(api_key=API_KEY)

        d = pachubeClient.delete_feed(feed_id=FEED_ID)
        d.addCallback(lambda result: print "Feed was deleted: %s" % result)
        d.addErrback(lambda reason: print "Error deleting feed: %s" % str(reason))
        d.addCallback(reactor.stop)

        reactor.run()


Example use case::

    #!/usr/bin/env python
    
    # This example demonstrates how you could use the txPachube module to
    # help upload sensor data (in this scenario a CurrentCost device) to
    # Pachube.
    # A txPachube.Environment data structure is generated and populated
    # with current value data. All the implemented data structures
    # support encoding to JSON (default) and XML (EEML).
    #
    # In this example the CurrentCost sensor object is only for demonstration
    # purposes which means that this is not a self contained runnable
    # script. However, you could implement the CurrentCost object to make 
    # it work.
    
    from twisted.internet import reactor
    import txPachube

    # Paste your Pachube API key here
    API_KEY = ""

    # Paste the feed identifier you wish to be DELETED here
    FEED_ID = ""

	
    class Monitor(object):
    
        def __init__(self, config):
            self.temperature_datastream_id = "temperature"
            self.energy_datastream_id = "energy"
            self.pachube = txPachube.client.Client(api_key=API_KEY, feed_id=FEED_ID)
            self.sensor = CurrentCost()
            self.sensor.setRealtimeMsgHandler(self.handleDataUpdate)
            
        def start(self):
            """ Start sensor """
            self.sensor.connect()
            
        def stop(self):
            """ Stop the sensor """
            self.sensor.stop()
            
        def handleDataUpdate(self, data):
            """ Receive sensor data """
            datastreams_data = []
            if data.temperature:
                datastream_data = (self.temperature_datastream_id, data.temperature)
                datastreams_data.append(datastream_data)
            if data.energy:
                datastream_data = (self.energy_datastream_id, data.energy)
                datastreams_data.append(datastream_data)
            
            if datastreams_data:
                self.updatePachube(datastreams_data)

        def updatePachube(self, datastreams_data)
            """ Update the Pachube service with latest value(s) """
            
            # Populate a txPachube.Environment object which supports
            # encoding to JSON (default) and XML (EEML).
            env_kwargs = {txPachube.DataFields.Version : "1.0.0"}
            environment = txPachube.Environment(**env_kwargs)
            for datastream_data in datastreams_data:
                datastream_id, current_value = datastream_data
                environment.setCurrentValue(datastream_id, current_value)
                
            d = self.pachube.update_feed(data=environment.encode())
            d.addCallback(self._cbPachubeUpdateSuccess)
            d.addErrback(self._cbPachubeUpdateFailed)
        

        def _cbPachubeUpdateSuccess(self, result):
            print "Pachube updated"
        

        def _cbPachubeUpdateFailed(self, reason):
            print "Pachube update failed: %s" % str(reason)           


    if __name__ == "__main__":
        monitor = Monitor()
        reactor.callWhenRunning(monitor.start)
        reactor.run()        
        
        
        
Todo
====

* Add test cases
* Investigate alternative installers that support uninstall/update options.


