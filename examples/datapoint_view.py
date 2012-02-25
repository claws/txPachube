#!/usr/bin/env python

"""
Lists the last 10 minutes of datapoints from the specified feed and datastream 
that are visible to the supplied Pachube user API key

To use this script you must create a text file containing your API key 
and pass it to this script using the --keyfile argument as follows:

$ datapoint_view.py --keyfile=path/to/apikey/file --feed=XXX --datastream=YYY [--timestamp=2012-02-25T01:01:10.793443Z]
"""

import datetime
import logging
import sys
from optparse import OptionParser
from twisted.internet import reactor, defer
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
parser.add_option("-d", "--datastream", dest="datastream_id", default=None, help="A datastream id from the feed")
parser.add_option("-t", "--timestamp", dest="timestamp", default=None, help="The timestamp of the datapoint to request")



@defer.inlineCallbacks
def demo(key, feed_id=None, datastream_id=None, timestamp=None):

    client = Client()

    if feed_id and datastream_id:
        
        if timestamp:
            # read the datapoint at the specified timestamp

            try:
                logging.info("Reading the datapoint at %s" % timestamp)
                datapoint = yield client.read_datapoint(api_key=key, 
                                                        feed_id=feed_id, 
                                                        datastream_id=datastream_id, 
                                                        timestamp=timestamp)
                if datapoint:
                    logging.info("Success reading the datapoint:\n%s\n" % datapoint)
                else:
                    logging.error("Problem occurred reading the datapoint")
            except Exception, ex:
                logging.error("Problem reading the datapoint: %s" % str(ex))
                                
        else:
            # no specific datapoint was requested so just show the last 10 minutes worth
            
            # create historical query parameters spanning the last 10 minutes
            ten_minutes_ago_timestamp = datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
            start_timestamp = "%sZ" % (ten_minutes_ago_timestamp.isoformat())
            parameters = {'start':start_timestamp, 'interval':0}
            
            try:
                logging.info("Requesting to view the last 10 minutes of historical datapoints for datastream %s in feed %s starting from %s" % (datastream_id, feed_id, start_timestamp))
                datastream = yield client.read_datastream(api_key=key, 
                                                          feed_id=feed_id, 
                                                          datastream_id=datastream_id,
                                                          parameters=parameters)
                if datastream:
                    logging.info("Success retrieving datastream historical datapoints:\n%s\n" % datastream)
                else:
                    logging.error("Problem reading datastream")                
            except Exception, ex:
                logging.error("Error reading datastream: %s" % str(ex))

    else:
        logging.error("Feed and datastream must be specified. Got feed=%s, datastream=%s" % (feed_id, datastream_id))
    
    
    reactor.callLater(0.1, reactor.stop)
    defer.returnValue(True)
    


if __name__ == '__main__':
    
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s : %(message)s")

    (options, args) = parser.parse_args()

    # confirm keyfile is suppplied and valid
    if options.keyfile is None:
        print parser.get_usage()
        sys.exit(1)
    
    keyfile = os.path.expanduser(options.keyfile)
    if not os.path.exists(keyfile):
        logging.error("Invalid API key file path: %s" % keyfile)
        sys.exit(1)
    
    fd = open(keyfile, 'r')
    key = fd.read().strip()
    fd.close()
   
    reactor.callWhenRunning(demo, key, options.feed_id, options.datastream_id, options.timestamp)
    reactor.run()

    