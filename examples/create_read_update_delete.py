#!/usr/bin/env python

# NOTE: 
# Prior to running this test you must:
# 1. Sign up to Pachube,
# 2. You must create a key with sufficient privileges to allow access to
#    any stream and all permission (create, read, update, delete). When
#    creating the key choose the 'All' option to be sure your key will
#    have the appropriate permissions.
#

from twisted.internet import reactor
import json
import logging
try:
    import txPachube
except ImportError:
    # cater for situation where txPachube is not installed into Python distribution
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import txPachube
    
    

CREATE_FEED_DATA = json.dumps({"title" : "A Temporary Test Feed", "version" : "1.0.0"})
UPDATE_FEED_DATA = json.dumps({"version" : "1.0.0", "datastreams":[{"id":"0", "current_value":"100"},{"id":"two", "current_value":"500"},{"id":"3.0", "current_value":"300"}]})

CREATE_KEY = json.dumps({
  "key":{
    "label":"TemporaryTestKey",
    "permissions":[
      {
        "access_methods":["get","put","post","delete"],
      },
    ]
  }
})

def handleError(failure):
    """ """
    logging.error(str(failure))
    reactor.stop()
    

def sheduleShutdown(result):
    logging.debug("Scheduling a shutdown in 1.0 seconds")
    reactor.callLater(1.0, reactor.stop)

def read_created_feed(feed_id, pachube):
    """ Read the new feed """
    logging.debug("Test feed created with feed_id: %s" % feed_id)
    
    def displayCreatedFeed(data, feed_id):
        logging.debug("Received new feed content:\n%s\n" % data)
        return feed_id
    
    logging.debug("Attempting to read from the created test feed_id: %s" % feed_id)
    d = pachube.read_feed(feed_id=feed_id)
    d.addCallback(displayCreatedFeed, feed_id)
    d.addErrback(handleError)
    d.addCallback(update_feed, pachube)
    


def create_feed(result, pachube):
    """ Create a new feed """
    logging.debug("Attempting to create the test feed")
    d = pachube.create_feed(data=CREATE_FEED_DATA)
    d.addCallback(read_created_feed, pachube)
    d.addErrback(handleError)
    
    

def read_updated_feed(updateSuccess, feed_id, pachube):
    """ Read the updated feed """
    logging.debug("Test feed updated: %s" % updateSuccess)
    
    def displayUpdatedFeed(data, feed_id):
        logging.debug("Received updated feed content:\n%s\n" % data)
        return feed_id
    
    logging.debug("Attempting to read from the updated test feed_id: %s" % feed_id)
    d = pachube.read_feed(feed_id=feed_id)
    d.addCallback(displayUpdatedFeed, feed_id)
    d.addErrback(handleError)
    d.addCallback(delete_feed, pachube)
    
    
    
def update_feed(feed_id, pachube):
    """ Update the feed """
    logging.debug("Attempting to update the test feed_id: %s" % feed_id)
    d = pachube.update_feed(feed_id=feed_id, data=UPDATE_FEED_DATA)
    d.addCallback(read_updated_feed, feed_id, pachube)
    d.addErrback(handleError)
    
    
def delete_feed(feed_id, pachube):
    """ Delete the feed """
    
    def cbDeleteStatus(result, feed_id):
        logging.debug("Delete feed %s successful: %s" % (feed_id, result))
        return True
    
    logging.debug("Attempting to delete the test feed_id: %s" % feed_id)
    d = pachube.delete_feed(feed_id=feed_id)
    d.addCallback(cbDeleteStatus, feed_id)
    d.addErrback(handleError)
    d.addCallback(sheduleShutdown)
    

    
def list_feeds(pachube):
    """ List feeds visible to the api key used """
    def handleFeedList(feedData):
        logging.debug("Received feed list content:\n%s\n" % feedData)
        return True
    d = pachube.list_feeds()
    d.addCallback(handleFeedList)
    d.addErrback(handleError)
    d.addCallback(create_feed, pachube)




def create_key():
    d = pachube.create_api_key()





def begin



if __name__ == "__main__":
    import os
    import sys
    from twisted.python import log


    # Send Twisted log messages to logging logger
    observer = log.PythonLoggingObserver()
    observer.start()

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s [%(funcName)s] %(message)s",
                        logfile=sys.stdout)
        
    if len(sys.argv) == 2:
        api_file = sys.argv[1]
        if os.path.exists(api_file):
            fd = open(api_file, 'r')
            API_KEY = fd.read()
            fd.close()
            
            API_KEY = API_KEY.strip()
            
            # initialise pachube object with API key so it does not
            # have to added at every method call.
            pachube = txPachube.client.Client(api_key=API_KEY)
            reactor.callWhenRunning(list_feeds, pachube)
            reactor.run()
        else:
            print "Invalid api_key file"
            sys.exit(1)
    else:
        print "Error: missing api_key file"
        sys.exit(1)


# list_feeds
# create_feed
# read_feed
# update_feed

# create_datastream
# read_datastream
# update_datastream

# list_datapoints
# create_datapoint
# read_datapoint
# update_datapoint

# delete_datapoint
# delete_datastream
# delete_feed