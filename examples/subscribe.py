#!/usr/bin/env python

"""
Subscribe to a feed or a datastream that is visible to the supplied Pachube user API key

To use this script you must create a text file containing your API key 
and pass it to this script using the --keyfile argument as follows:

Subscribe for updates to a particular feeds:
$ subscribe.py --keyfile=/path/to/apikey/file --feed=XXX --time=60

Subscribe for updates to a particular datastream within a feed:
$ subscribe.py --keyfile=path/to/apikey/file --feed=XXX --datastream=YYY --time=60
"""

import logging
import sys
from optparse import OptionParser
from twisted.internet import reactor
try:
    from txpachube.client import PAWSClient
except ImportError:
    # cater for situation where txpachube is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from txpachube.client import PAWSClient
    

parser = OptionParser("")
parser.add_option("-k", "--keyfile", dest="keyfile", default=None, help="Path to file containing your Pachube API key")
parser.add_option("-f", "--feed", dest="feed", default=None, help="The feed to subscribe to")
parser.add_option("-d", "--datastream", dest="datastream", default=None, help="The datastream within the feed to subscribe to")
parser.add_option("-t", "--time", dest="time", default="60", help="The time duration (in seconds) to remain subscribed for")
(options, args) = parser.parse_args()


# confirm keyfile is suppplied and valid
if options.keyfile is None:
    print parser.get_usage()
    sys.exit(1)

keyfile = os.path.expanduser(options.keyfile)
if not os.path.exists(keyfile):
    print "Invalid API key file path: %s" % keyfile
    sys.exit(1)

fd = open(keyfile, 'r')
key = fd.read().strip()
fd.close()

if options.feed is None:
    print "No feed identifier specified"
    print parser.get_usage()
    sys.exit(1)

if options.datastream:
    resource = "/feeds/%s/datastreams/%s" % (options.feed, options.datastream)
else:
    resource = "/feeds/%s" % (options.feed)
    
SubscribeDurationTime = int(options.time)
    

#   
# Set up callback handlers for use in subscribe/unsubscribe demonstration
#


def updateHandler(dataStructure):
    """
    Handle a txpachube data structure object generated as a result of a
    subscription update message received from Pachube. 
    
    The data structure returned will vary depending on the resource subscribed to. 
    If a datastream is specified the returned data structure will be a txpachube.Datastream
    object. If just a feed specified then the returned data structure will be a 
    txpachube.Environment object.
    """
    logging.info("Subscription update message received:\n%s\n" % str(dataStructure))


def connect(client, resource):
    """
    Connect the PAWS client to the service and subscribe for updates
    to the specified resource.
    """
    logging.info("Connecting to PAWS service")
    d = client.connect()
    d.addCallback(lambda result: logging.info("Connected: %s" % result))
    d.addCallback(subscribe, client, resource)
    
    
def subscribe(_, client, resource):
    """
    Subscribe to the specified resource and schedule an unsubcribe
    after a brief interval of monitoring subscription updates.
    """
    if client.connected:
        logging.info("Sending subscribe request")
        token, d = client.subscribe(resource, updateHandler)
        d.addCallback(lambda result: logging.info("Subscribe response status: %s" % result))
        logging.info("Scheduling an unsubscribe to be sent in %i seconds" % SubscribeDurationTime)
        reactor.callLater(SubscribeDurationTime, unsubscribe, client, resource, token)
    else:
        logging.error("Client did not connect. Can't continue demonstration, stopping")
        reactor.callLater(0.5, reactor.stop)
        
        
def unsubscribe(client, resource, token):
    """
    Unsubscribe for updates on the specified resource
    """
    logging.info("Sending unsubscribe request")
    d = client.unsubscribe(resource, token)
    d.addCallback(lambda result: logging.info("Unsubscribe response status: %s" % result))

    # demo complete - disconnect client from PAWS interface.
    d.addCallback(lambda _: reactor.callLater(0.2, disconnect, client))        


def disconnect(client):
    """
    Disconnect from the PAWS interface and stop the reactor.
    """
    logging.info("Disconnecting from PAWS service")
    d = client.disconnect()
    d.addCallback(lambda result: logging.info("Disconnected: %s" % result))
    
    # stop the reactor to cleanly finish up the demonstration.
    d.addCallback(lambda _: logging.info("Stopping reactor"))
    d.addCallback(lambda _: reactor.callLater(0.5, reactor.stop))
          
          

    


if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s : %(message)s")
    client = PAWSClient(api_key=key)    
    reactor.callWhenRunning(connect, client, resource)
    reactor.run()

