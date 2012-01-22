#!/usr/bin/env python

"""
Lists feed visible to the supplied Pachube user API key

To use this script you must create a text file containing your API key 
and pass it to this script using the --keyfile argument as follows:

List all feeds visible to supplied key:
$ list_feeds.py --keyfile=/path/to/apikey/file

List a particular feed
$ list_feeds.py --keyfile=path/to/apikey/file --feed=XXX
"""

import sys
from optparse import OptionParser
from twisted.internet import reactor
try:
    from txpachube.client import Client
except ImportError:
    # cater for situation where txpachube is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from txpachube.client import Client
    


parser = OptionParser("")
parser.add_option("-k", "--keyfile", dest="keyfile", default=None, help="Path to file containing your Pachube API key")
parser.add_option("-f", "--feed", dest="feed_id", default=None, help="A specific Pachube feed id to list")

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
key = fd.read()
fd.close()



def sheduleShutdown(result):
    """
    Stop reactor after a brief interval
    """
    print "Stopping script"
    reactor.callLater(0.5, reactor.stop)


def cbSuccess(dataStructure):
    """
    Handle the txpachube data structure object returned. If a feed id was supplied this 
    will be a txpachube.Environment data structure object otherwise this will be a 
    txpachube.EnvironmentList data structure object.
    """
    print "Received response from Pachube:\n%s\n" % dataStructure

    
def cbFailure(reason):
    """
    Handle any errors by printing them out
    """
    print "Error: %s" % str(reason)




client = Client()

if options.feed_id:
    # request feed details for the supplied identifier only
    d = client.read_feed(api_key=key, feed_id=options.feed_id)
    
else:
    # request feed details for all feeds visible to the key supplied
    d = client.subscribe()


d.addCallback(cbSuccess)
d.addErrback(cbFailure)

d.addCallback(sheduleShutdown)
d.addErrback(sheduleShutdown)
        
reactor.run()

    