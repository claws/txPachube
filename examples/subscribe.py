#!/usr/bin/env python

"""
Subscribe to a feed or a datastream that is visible to the supplied Pachube user API key

To use this script you must create a text file containing your API key 
and pass it to this script using the --keyfile argument as follows:

Subscribe for updates to a particular feeds:
$ simple_subscribe.py --keyfile=/path/to/apikey/file --feed=XXX

Subscribe for updates to a particular datastream within a feed:
$ simple_subscribe.py --keyfile=path/to/apikey/file --feed=XXX --datastream=YYY
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

    

#   
# Set up callback handlers
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



          
def do_subscribe(connected, client, resource):
    """ Subscribe to the specified resource if the connection is established """
        
    if connected:
        def handleSubscribeResponse(status):
            print "Subscribe response status: %s" % status
            
        token, d = client.subscribe(resource, updateHandler)
        print "Subscription token is: %s" % token
        d.addCallback(handleSubscribeResponse)
                
    else:
        print "Connection failed"
        reactor.callLater(0.1, reactor.stop)
        return          

    


if __name__ == '__main__':
    
    logging.basicConfig(level=logging.INFO, format="%(asctime)s : %(message)s")

    client = PAWSClient(api_key=key)
    d = client.connect()
    d.addCallback(do_subscribe, client, resource)
    reactor.run()
    
    